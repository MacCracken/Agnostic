#!/usr/bin/env bash
# gen-presets.sh — embed src/presets/*.json into a Cyrius source file.
#
# Cyrius has no `include_str!`: `include` is textual and takes a path to
# *source*, so a data file has to be turned into source first. That is all this
# script does — a build step written down rather than a design. The same
# reasoning, and very nearly the same script, is in agnosai; filed upstream as
# cyrius/docs/development/proposals/2026-08-10-embed-data-files-as-source-strings.md
#
#   ./scripts/gen-presets.sh            regenerate src/presets_data.cyr
#   ./scripts/gen-presets.sh --check    fail if the checked-in file has drifted
#
# The generated file IS committed, so a clone builds without running this.
# `--check` is what keeps that copy honest: edit a preset, forget to regenerate,
# and the gate says so instead of shipping stale bytes.
#
# ⚠ THE ORDER IS DELIBERATE AND IS NOT THE GLOB ORDER. Presets are looked up by
# name through a map, so order is invisible to a lookup — but `GET /api/v1/presets`
# renders in this order, and a listing that runs
# `complete-lean, data-engineering-large, data-engineering-lean, …` reads as
# accidental because it is. Grouped by domain, lean → standard → large, with the
# three off-pattern documents last. PRESETS below is the order; it is asserted by
# tests/presets.tcyr so it cannot drift silently.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

OUT="src/presets_data.cyr"
MODE="${1:-generate}"

gen=$(python3 - <<'PY'
import json
import os
import sys

# Grouped by domain, lean -> standard -> large. The three documents that do not
# fit that pattern come last, and `complete-lean` is last of all because its
# domain is off-canon — see the note in src/engine/presets.cyr.
PRESETS = [
    ("Quality", ["quality-lean", "quality-standard", "quality-large"]),
    ("Software Engineering", ["software-engineering-lean",
                              "software-engineering-standard",
                              "software-engineering-large"]),
    ("DevOps", ["devops-lean", "devops-standard", "devops-large"]),
    ("Data Engineering", ["data-engineering-lean", "data-engineering-standard",
                          "data-engineering-large"]),
    ("Design", ["design-lean", "design-standard", "design-large"]),
    ("Specialised", ["quality-performance", "quality-security", "complete-lean"]),
]

# One physical line stays under this many characters, because `cyrius lint`
# warns past 120 and the largest document is 8.3 KB.
#
# ⚠ A trailing backslash continues a Cyrius string literal across lines and it
# DOES keep the newline — then `cyrius fmt` indents the continuation and those
# spaces land inside the string too. Both are invisible here only because a break
# is taken between JSON tokens, where whitespace is insignificant. That is why
# `atoms` splits on token boundaries rather than counting characters: a break
# inside a `"backstory"` value would splice a newline and four spaces into text a
# consumer displays.
WRAP = 88

flat = [name for _, names in PRESETS for name in names]

missing = [n for n in flat if not os.path.exists("src/presets/%s.json" % n)]
if missing:
    sys.stderr.write("missing preset files: %s\n" % ", ".join(missing))
    sys.exit(2)

on_disk = sorted(f[:-5] for f in os.listdir("src/presets") if f.endswith(".json"))
if on_disk != sorted(flat):
    sys.stderr.write(
        "src/presets/ does not match PRESETS in scripts/gen-presets.sh, so a\n"
        "document's position in the listing would be accidental. Add it to the\n"
        "list deliberately.\n"
        "  on disk but not listed: %s\n"
        "  listed but not on disk: %s\n"
        % (", ".join(sorted(set(on_disk) - set(flat))) or "none",
           ", ".join(sorted(set(flat) - set(on_disk))) or "none"))
    sys.exit(2)


def atoms(text):
    """Split compact JSON into indivisible, already-escaped pieces.

    A piece is a whole string literal or a single non-string character. Breaking
    anywhere else would put a newline plus fmt's indentation *inside* a value.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            out.append(text[i:j + 1].replace("\\", "\\\\").replace('"', '\\"'))
            i = j + 1
        else:
            out.append(text[i])
            i += 1
    return out


def literal(text, prefix):
    """A Cyrius string literal, greedily packed to WRAP with continuations."""
    lines, line = [], ""
    room = WRAP - prefix - 1          # the opening quote sits on the first line
    for piece in atoms(text):
        # A trailing backslash continues the literal, so it costs a character.
        if line and len(line) + len(piece) + 1 > room:
            lines.append(line)
            line = ""
            room = WRAP
        line += piece
    lines.append(line)
    return '"' + "\\\n".join(lines) + '"'


L = []
L.append("# " + "=" * 71)
L.append("# agnostic/presets_data — GENERATED FILE. Do not edit by hand.")
L.append("#")
L.append("# Regenerate with `./scripts/gen-presets.sh`; that script's `--check` mode")
L.append("# fails when this file has drifted from `src/presets/*.json`, and")
L.append("# `scripts/check-clean.sh` runs it.")
L.append("#")
L.append("# Cyrius has no `include_str!` — `include` is textual and takes a path to")
L.append("# source — so the documents are turned into source here.")
L.append("#")
L.append("# ⚠ The ORDER is deliberate: grouped by domain, lean -> standard -> large,")
L.append("# with the three off-pattern documents last. `GET /api/v1/presets` renders")
L.append("# in this order. `tests/presets.tcyr` asserts it.")
L.append("#")
L.append("# Each document is whitespace-collapsed to a single logical line. JSON")
L.append("# whitespace between tokens is insignificant, so the parse is unaffected.")
L.append("# " + "=" * 71)
L.append("")
L.append("# How many documents `agnostic_preset_json` will answer for.")
L.append("var AGNOSTIC_PRESET_JSON_COUNT = %d;" % len(flat))
L.append("")

idx = 0
for group, names in PRESETS:
    L.append("# --- %s %s" % (group, "-" * max(0, 66 - len(group))))
    for name in names:
        raw = open("src/presets/%s.json" % name).read()
        # Reserialized rather than passed through: it proves the document parses
        # at generation time, and collapses the indentation the sources carry.
        compact = json.dumps(json.loads(raw), separators=(",", ":"))
        L.append("")
        L.append("# %s.json" % name)
        decl = "var _AGNOSTIC_PRESET_JSON_%02d = " % idx
        L.append(decl + literal(compact, len(decl)) + ";")
        idx += 1
    L.append("")

L.append("# The `i`th embedded preset document as a NUL-terminated C string, or 0 when")
L.append("# `i` is out of range.")
L.append("#")
L.append("# A chain rather than a table because a `var` array of string literals has no")
L.append("# spelling in Cyrius, and the only caller is a one-shot loop at mount.")
L.append("fn agnostic_preset_json(i): i64 {")
for n in range(len(flat)):
    L.append("    if (i == %d) { return _AGNOSTIC_PRESET_JSON_%02d; }" % (n, n))
L.append("    return 0;")
L.append("}")
L.append("")
sys.stdout.write("\n".join(L))
PY
)

status=$?
if [ $status -ne 0 ]; then
    echo "gen-presets: generation failed" >&2
    exit $status
fi

# Run the result through `cyrius fmt` before comparing or installing. fmt
# reindents the continuation lines inside the literals, so a raw generation would
# satisfy this script and fail `./scripts/check-clean.sh` — the two gates have to
# be reconciled here or they contradict each other forever.
tmp=$(mktemp /tmp/gen-presets.XXXXXX.cyr)
trap 'rm -f "$tmp"' EXIT
printf '%s' "$gen" > "$tmp"
# ⚠ `cyrius fmt` formats IN PLACE and prints nothing on stdout. Redirecting its
# stdout and reading that back captures an EMPTY file — agnosai shipped that bug
# and `--check` reported "stale" unconditionally. Read the formatted file itself.
if ! cyrius fmt "$tmp" >/dev/null 2>&1; then
    echo "gen-presets: cyrius fmt failed on the generated source" >&2
    exit 1
fi
gen=$(cat "$tmp")

if [ "$MODE" = "--check" ]; then
    if [ ! -f "$OUT" ]; then
        echo "gen-presets: $OUT is missing — run ./scripts/gen-presets.sh" >&2
        exit 1
    fi
    if ! printf '%s\n' "$gen" | diff -u "$OUT" - >/dev/null; then
        echo "gen-presets: $OUT is stale — run ./scripts/gen-presets.sh" >&2
        printf '%s\n' "$gen" | diff -u "$OUT" - | head -40 >&2
        exit 1
    fi
    echo "gen-presets: $OUT is up to date"
    exit 0
fi

# `$(...)` strips trailing newlines; fmt wants the file to end with one.
printf '%s\n' "$gen" > "$OUT"
echo "gen-presets: wrote $OUT"
