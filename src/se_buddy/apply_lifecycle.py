"""The apply lifecycle (spec Sec.10.2): check tree -> check drift ->
validate targets -> snapshot -> apply -> re-parse -> validate -> diff ->
record.

Gate-free on purpose - `commands/write_apply.py` puts the TTY gate above
`apply_cp()`, and tests call it directly (spec Sec.2.3's testing
philosophy: "Tests exercise the layer beneath the gate directly").

"MUST leave the model exactly as it was on any failure" (spec Sec.10.2):
before the write, by refusing before anything is snapshotted; after the
write, by restoring the snapshot. Every exception path below does one of
the two - including the final record-writing step, which a code review
found was not originally covered (see `apply_cp`'s docstring).
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import date
from pathlib import Path

from se_buddy.changes import any_followup_open, changes_dir, file_change
from se_buddy.decl_ops import DeclError, dry_run
from se_buddy.memory import allocate_id
from se_buddy.model import ModelResolutionError, hash_model_files, load_model, resolve_model_path
from se_buddy.proposals import load_cp
from se_buddy.validate import run_all_layers, summarize


class ApplyError(Exception):
    """An apply precondition failed, or the apply itself failed - the
    model is guaranteed unchanged (or restored) whenever this is raised.
    """


def _git(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def check_tree_clean(root: Path, aird_path: Path) -> None:
    """spec Sec.10.2: "The .capella and .aird files are clean in git...
    refusing on any uncommitted change anywhere would block apply during
    most real sessions" - so only the model files are checked, not the
    whole working tree.

    Runs git from `aird_path`'s own directory, not `root` - the se-buddy
    project root and the git repository root are not guaranteed to be the
    same directory (e.g. the model could live in a subdirectory of a
    larger repo), and git itself walks upward to find `.git` regardless of
    exactly which directory under it you start from, so anchoring on the
    model file's real location is the only assumption-free choice.

    The path arguments given to `git status` are bare filenames
    (`aird_path.name`, not `str(aird_path)`), never the full path - a code
    review found that passing the full path here, on top of a `cwd` that's
    already that path's own parent directory, doubled the parent segment
    (`model/model/Project.aird`) whenever the model lived in a
    subdirectory, so git silently matched nothing and this function
    reported "clean" on a genuinely dirty tree. Confirmed live before the
    fix, and covered by a regression test that specifically uses a
    subdirectory layout (the case every prior test happened to avoid).
    """
    capella_path = aird_path.with_suffix(".capella")
    proc = _git(["status", "--porcelain", "--", aird_path.name, capella_path.name], aird_path.parent)
    if proc.returncode != 0:
        raise ApplyError(f"could not check git status: {proc.stderr.strip()}")
    if proc.stdout.strip():
        raise ApplyError(
            f"{aird_path.name}/{capella_path.name} have uncommitted changes - "
            "commit or stash them first (a revert needs a point to return to)"
        )


def check_drift(cp: dict, aird_path: Path) -> None:
    """spec Sec.10.2: "The model hash matches what was last parsed... If
    they have edited since, apply would overwrite their work. On mismatch,
    refuse and name the drift." Checked against the hash `write propose`
    captured (see `se_buddy.proposals` - spec Sec.9 doesn't literally name
    this field; documented as a completion in SPEC-COVERAGE.md).
    """
    current = hash_model_files(aird_path)
    if current != cp.get("model_hash"):
        raise ApplyError(
            f"the model has changed since {cp['id']} was proposed - the answer is "
            "`write record` to capture what changed, not a retry"
        )


def snapshot_dir(root: Path, change_id: str) -> Path:
    return root / "se-buddy" / "snapshots" / change_id


def take_snapshot(root: Path, aird_path: Path, change_id: str) -> Path:
    directory = snapshot_dir(root, change_id)
    directory.mkdir(parents=True, exist_ok=True)
    for suffix in (".afm", ".aird", ".capella"):
        sibling = aird_path.with_suffix(suffix)
        if sibling.exists():
            shutil.copy2(sibling, directory / sibling.name)
    return directory


def restore_snapshot(aird_path: Path, directory: Path) -> None:
    for suffix in (".afm", ".aird", ".capella"):
        sibling = aird_path.with_suffix(suffix)
        snapshot_file = directory / sibling.name
        if snapshot_file.exists():
            shutil.copy2(snapshot_file, sibling)


def _load_model_or_apply_error(root: Path, model_arg: str | None):
    """`load_model()` wrapped so `ModelResolutionError` becomes `ApplyError`
    at every call site in this module - a code review found two call sites
    that loaded the model without this wrapping, letting a resolution
    failure escape uncaught past `write_apply.py`'s `except ApplyError`.
    """
    try:
        return load_model(root, model_arg)
    except ModelResolutionError as exc:
        raise ApplyError(str(exc)) from exc


def _check_no_diagram_references(root: Path, model_arg: str | None, deleted_uuids: frozenset) -> None:
    """spec Sec.10.2's `--delete` precondition: refuse outright if any
    diagram still references the target (decision 3 in the Phase 3 plan -
    the spec's other offered option, emit-and-proceed, would leave the
    model and `.aird` mutually inconsistent for however long the followup
    takes).

    Uses a fresh, unmutated model load - the model that produced
    `deleted_uuids` has already had those elements removed from its own
    in-memory tree by the time `dry_run` returns.
    """
    check_model = _load_model_or_apply_error(root, model_arg)
    for target_uuid in deleted_uuids:
        try:
            element = check_model.by_uuid(target_uuid)
        except KeyError:
            continue
        diagrams = list(element.visible_on_diagrams)
        if diagrams:
            names = ", ".join(d.name for d in diagrams[:3])
            raise ApplyError(
                f"cannot delete {target_uuid} - it still appears on {len(diagrams)} "
                f"diagram(s) ({names}): remove it from those diagrams in Capella "
                "first (spec Sec.7.4)"
            )


def _draw_followup_for_created(model, created_uuids: frozenset) -> list[dict]:
    """Every newly-created element has no diagram representation yet by
    definition - each becomes a DRAW followup (spec Sec.7.4, Sec.10.3).
    """
    followup = []
    for target_uuid in sorted(created_uuids):
        try:
            element = model.by_uuid(target_uuid)
        except KeyError:
            continue
        name = getattr(element, "name", "") or target_uuid
        followup.append(
            {
                "object": f"{type(element).__name__} {name!r} ({target_uuid})",
                "done_when": "it is drawn on the relevant diagram(s) in Capella",
                "blocks": "nothing",
                "default": "none - the diagram will not reflect the model until this is done",
            }
        )
    return followup


def apply_cp(
    root: Path,
    cp_id: str,
    authorized_by: str,
    *,
    model_arg: str | None = None,
    delete: bool = False,
    today: str | None = None,
) -> dict:
    """Runs the full spec Sec.10.2 sequence for `cp_id`. Returns the
    written `CHANGE` record. Raises `ApplyError` on any precondition or
    mid-apply failure, and restores the snapshot whenever the failure
    happens after one was taken - including a failure while writing the
    `CHANGE` record itself. A code review found that step originally sat
    outside the restore-guarded block: a failure there (e.g. a malformed
    pre-existing followup file elsewhere in the project) left the model
    saved and modified with no record and no restore, and raised
    `ChangeError`, a type this function's own caller never caught. Both are
    fixed here: the record write is inside the same guard as the save, and
    any exception during it - not only `ChangeError` - triggers a restore.

    Also fixed here: `--delete` is now actually enforced. The diagram-
    reference safety check previously only ran `if delete and
    preflight_result.deleted`, with no refusal when a proposal deleted
    elements and `--delete` simply wasn't passed - the deletion went
    through unchecked. It now refuses first if deletions are attempted
    without the flag, exactly as spec Sec.2.3 requires ("Deletion requires
    a distinct flag").

    Also simplified: earlier versions loaded and applied the model twice
    (once to preflight, once for real), which always produced an identical
    result once `check_tree_clean`/`check_drift` had already confirmed
    nothing changed in between - removed as pure duplicated work, not a
    behaviour change.
    """
    today = today or date.today().isoformat()

    if not authorized_by or not authorized_by.strip():
        raise ApplyError(
            "--authorized-by is required (spec Sec.2.3) - only words the engineer actually said"
        )

    if any_followup_open(root):
        raise ApplyError(
            "a followup checklist is still open (spec Sec.10.3) - tick it with "
            "`se-buddy write answer` before applying anything new"
        )

    cp = load_cp(root, cp_id)
    if cp is None:
        raise ApplyError(f"{cp_id} is not a known proposal")
    decl_text = cp.get("proposed_changes")
    if not decl_text:
        raise ApplyError(f"{cp_id} has no proposed_changes to apply")

    try:
        aird_path = Path(resolve_model_path(root, model_arg))
    except ModelResolutionError as exc:
        raise ApplyError(str(exc)) from exc

    check_tree_clean(root, aird_path)
    check_drift(cp, aird_path)

    preflight_model = _load_model_or_apply_error(root, model_arg)
    try:
        preflight_result = dry_run(preflight_model, decl_text)
    except DeclError as exc:
        raise ApplyError(f"{cp_id}'s proposed_changes does not apply cleanly: {exc}") from exc

    if preflight_result.deleted and not delete:
        raise ApplyError(
            f"{cp_id} deletes {len(preflight_result.deleted)} element(s) but --delete was not "
            "passed (spec Sec.2.3: deletion requires a distinct flag)"
        )
    if delete and preflight_result.deleted:
        _check_no_diagram_references(root, model_arg, preflight_result.deleted)

    change_id = allocate_id("CHANGE", changes_dir(root))
    snap_dir = take_snapshot(root, aird_path, change_id)

    try:
        # `preflight_model` already has `decl_text` applied in memory (from
        # the `dry_run` call above) - saving it directly, rather than
        # loading and re-applying to a second model object, is what removes
        # the duplicated work described in this function's docstring.
        preflight_model.save()
    except Exception as exc:
        restore_snapshot(aird_path, snap_dir)
        raise ApplyError(f"apply failed - the model was restored from snapshot: {exc}") from exc

    try:
        reparsed = _load_model_or_apply_error(root, model_arg)
        findings = run_all_layers(root, reparsed)
    except ApplyError:
        restore_snapshot(aird_path, snap_dir)
        raise
    except Exception as exc:
        restore_snapshot(aird_path, snap_dir)
        raise ApplyError(f"post-apply validation failed - the model was restored from snapshot: {exc}") from exc

    diff_summary = f"{len(preflight_result.created)} element(s) created, {len(preflight_result.deleted)} deleted"
    validation_summary = summarize(findings)
    followup = _draw_followup_for_created(reparsed, preflight_result.created)

    try:
        change = file_change(
            root,
            change_id,
            {
                "claim": cp["claim"],
                "tier": cp.get("tier", "judgement"),
                "date": today,
                "supersedes": [],
                "proposal": cp_id,
                "authority": authorized_by,
                "diff_summary": diff_summary,
                "validation_summary": validation_summary,
                "manual_followup": followup,
            },
            followup,
        )
    except Exception as exc:
        restore_snapshot(aird_path, snap_dir)
        raise ApplyError(
            f"recording the CHANGE failed - the model was restored from snapshot: {exc}"
        ) from exc

    return change
