# SE Buddy

SE Buddy is a reusable systems-engineering collaborator for Model-Based Systems Engineering (MBSE) in Eclipse Capella. It uses the Arcadia method. One installation serves a project in any engineering domain.

It helps an engineer to examine an architecture that changes, to think about a change against the design intent of that architecture, to keep decisions and the reasons for them, and to keep traceability. It changes the model only with authorisation.

Three parties do the work. Claude Code is the reasoning layer. The `se-buddy` command-line interface is the deterministic layer: it reads, queries, validates and records, and it does not reason. The engineer makes every architecture decision and gives every authorisation.

> [!warning] Note
> SE Buddy is not an autonomous systems engineer. It advises, and the engineer decides.

## Status

Phases 0–2 — see [log/log-0001-se_buddy_agent_spec.md](log/log-0001-se_buddy_agent_spec.md) Sec.11 for the phasing, and [SPEC-COVERAGE.md](SPEC-COVERAGE.md) for what is enforced so far. `se-buddy` can bootstrap itself, load a real Capella model, answer `inspect`/`search`/`show`/`trace`/`asks` against it (`trace` now also reaches into registers), and read/write the six registers and baselines — every write gated behind a real TTY confirmation, not a flag. The model itself still can't be modified — that starts in Phase 3.

## Prerequisites

- Python 3.11+ on `PATH` as `python3` or `python`.
- Network, the first time `bin/se-buddy` (or `bin\se-buddy.cmd`) runs in a clone, to install the pinned dependencies.
- `git submodule update --init --recursive`, so `vendor/py-capellambse` is checked out — never `--remote` together with `--recursive` (spec Sec.7.1).
- **A Rust toolchain (`rustc`, `cargo`).** capellambse 0.8.1 builds a Rust extension, and the bootstrap installs it from the vendored source rather than a prebuilt index wheel (spec Sec.5.1), so building it locally needs one. On Windows, the GNU-target toolchain (`winget install Rustlang.Rust.GNU`, or <https://rustup.rs> with the `x86_64-pc-windows-gnu` target) avoids also needing Visual Studio Build Tools — verified working on this repo. `se-buddy doctor` refuses with a clear message if no toolchain is found.

Then:

```bash
git clone --recursive <this-repo-url>
cd se-buddy-agent
bin/se-buddy doctor
```

On Windows, use `bin\se-buddy.cmd doctor` instead.