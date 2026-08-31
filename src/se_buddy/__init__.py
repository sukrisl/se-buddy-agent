"""SE Buddy's deterministic CLI layer (spec Sec.1.1).

Parses, searches, traces, validates and records. It does not reason - the
reasoning layer is Claude Code, in the session that invokes this CLI.

This module deliberately imports nothing beyond the standard library at
package-init time: bin/_bootstrap.py needs to import se_buddy._pin under the
bare system interpreter, before capellambse (or anything else in
vendor/.venv) exists.
"""

__version__ = "0.1.0"
