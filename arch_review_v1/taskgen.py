"""Deterministic task decomposition and generation (spec issue #12).

Decompose: split a hard/medium task into one easy sub-task per gold defect.
The sub-task isolates one defect mechanism in a minimal diff, so a low-rank
reviewer model finds it without competition from louder defects. Generation:
materialize a task directory from a curated mechanism template by diffing a
base file against a defective file.

The transform is a pure function of its inputs: no model calls, no clocks. The
same input task produces byte-identical output directories. Curation stays
manual; a sub-diff the splitter cannot make coherent is marked
``needs-hand-write`` in its _meta file instead of being silently shipped.

Deterministic properties (tested):
- containment: every line of a sub-diff exists in the parent diff;
- isolation: a sub-diff never carries a line owned by a different defect;
- gold inheritance: the sub-task defect copies the parent defect verbatim;
- contract validity: every emitted task passes validate_gold and the taskset.
"""

from __future__ import annotations

import ast
import builtins
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from arch_review_v1.contract import validate_gold

GENERATOR_VERSION = "1.0.0"

_PREFIX = {" ", "-", "+"}


@dataclass
class Hunk:
    """One unified-diff hunk. ``lines`` items are prefix + text, no trailing newline."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str] = field(default_factory=list)


@dataclass
class _Line:
    """A parsed diff line with its file-side line numbers."""

    prefix: str  # ' ', '-', or '+'
    text: str
    old: int | None  # line number in the old file; None for pure additions
    new: int | None  # line number in the new file; None for pure deletions


# --------------------------------------------------------------------------- #
# unified diff parse / emit
# --------------------------------------------------------------------------- #

def parse_diff(text: str) -> dict[str, list[Hunk]]:
    """Parse a unified diff into per-path hunk lists.

    Supports ``diff --git``, new files (``--- /dev/null``), and deleted files.
    The ``index`` line is ignored.
    """
    files: dict[str, list[Hunk]] = {}
    current: str | None = None
    hunk: Hunk | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("diff --git "):
            current = _path_of(line, "+++ b/") or _path_of(line, "--- a/")
            if current is None:
                current = _git_path(line)
            files.setdefault(current, [])
            hunk = None
        elif line.startswith("+++ ") or line.startswith("--- ") or line.startswith("index "):
            continue
        elif line.startswith("@@"):
            old_start, old_count, new_start, new_count = _parse_hunk_header(line)
            hunk = Hunk(old_start, old_count, new_start, new_count)
            if current is not None:
                files[current].append(hunk)
        elif current is not None and hunk is not None and line[:1] in _PREFIX:
            hunk.lines.append(line)
        # any other line (trailing marker, blank separator) is ignored
    return files


def emit_diff(file_hunks: dict[str, list[Hunk]]) -> str:
    """Serialize per-path hunks back to a unified diff string."""
    out: list[str] = []
    for path in sorted(file_hunks):
        hunks = file_hunks[path]
        if not hunks:
            continue
        out.append(f"diff --git a/{path} b/{path}")
        out.append(f"--- a/{path}")
        out.append(f"+++ b/{path}")
        for h in hunks:
            out.append(f"@@ -{h.old_start},{h.old_count} +{h.new_start},{h.new_count} @@")
            out.extend(h.lines)
    return "\n".join(out) + "\n"


def _parse_hunk_header(line: str) -> tuple[int, int, int, int]:
    m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if not m:
        raise ValueError(f"malformed hunk header: {line!r}")
    old_count = int(m.group(2) or 1)
    new_count = int(m.group(4) or 1)
    return int(m.group(1)), old_count, int(m.group(3)), new_count


def _git_path(line: str) -> str:
    # "diff --git a/foo b/foo"
    parts = line.split()
    return parts[-1][2:] if parts[-1].startswith("b/") else parts[-2][2:]


def _path_of(line: str, marker: str) -> str | None:
    idx = line.find(marker)
    if idx == -1:
        return None
    return line[idx + len(marker):]


# --------------------------------------------------------------------------- #
# line ownership
# --------------------------------------------------------------------------- #

def _annotate(hunk: Hunk) -> list[_Line]:
    """Assign old/new line numbers to each line of a hunk."""
    out: list[_Line] = []
    old, new = hunk.old_start, hunk.new_start
    for line in hunk.lines:
        p = line[0]
        text = line[1:]
        if p == " ":
            out.append(_Line(p, text, old, new))
            old += 1
            new += 1
        elif p == "-":
            out.append(_Line(p, text, old, None))
            old += 1
        else:  # '+'
            out.append(_Line(p, text, None, new))
            new += 1
    return out


def _owns(span: tuple[int, int], line: _Line, prev_new: int | None) -> bool:
    """Whether ``line`` belongs to a defect whose new-file span is ``span``."""
    lo, hi = span
    if line.prefix == "+":
        return line.new is not None and lo <= line.new <= hi
    if line.prefix == "-":
        if line.new is not None:
            return lo <= line.new <= hi  # a - with an explicit new number cannot occur
        # pure deletion: attribute to the defect whose span covers the line that
        # follows the deletion (its position is the next retained new line).
        return prev_new is not None and lo <= prev_new <= hi
    return False


def _owner_spans(defects: list[dict], path: str) -> list[tuple[str, tuple[int, int]]]:
    return [
        (d["id"], tuple(d["lines"]))
        for d in defects
        if d["file"] == path
    ]


def _owned_line_sets(hunk: Hunk, spans: list[tuple[str, tuple[int, int]]]) -> dict[str, set[int]]:
    """Index owned + and - lines per defect id for one hunk.

    A deletion run and the addition run that follows it pair positionally: the
    k-th deleted line is the old form of the k-th added line. A deletion with no
    paired addition is a pure deletion; it belongs to the defect whose span
    covers the line that follows it. A changed line inside two spans is owned by
    both, so a caller can detect the interleave.
    """
    owned: dict[str, set[int]] = {did: set() for did, _ in spans}
    annotated = _annotate(hunk)
    n = len(annotated)
    i = 0
    while i < n:
        line = annotated[i]
        if line.prefix == " ":
            i += 1
            continue
        if line.prefix == "-":
            del_run: list[int] = []
            while i < n and annotated[i].prefix == "-":
                del_run.append(i)
                i += 1
            add_run: list[int] = []
            while i < n and annotated[i].prefix == "+":
                add_run.append(i)
                i += 1
            for k, d in enumerate(del_run):
                if k < len(add_run):
                    paired_new = annotated[add_run[k]].new
                else:
                    # no positional pair: the deletion's position is the next
                    # retained new line after the deletion itself
                    paired_new = None
                    for j in range(d + 1, n):
                        if annotated[j].new is not None:
                            paired_new = annotated[j].new
                            break
                for did, span in spans:
                    if _owns(span, annotated[d], paired_new):
                        owned[did].add(d)
            for a in add_run:
                for did, span in spans:
                    if _owns(span, annotated[a], None):
                        owned[did].add(a)
            continue
        # a '+' not attached to a deletion run
        for did, span in spans:
            if _owns(span, line, None):
                owned[did].add(i)
        i += 1
    return owned


# --------------------------------------------------------------------------- #
# sub-diff emission
# --------------------------------------------------------------------------- #

def _split_hunk(hunk: Hunk, kept: set[int]) -> list[Hunk]:
    """Emit the kept lines of a hunk as contiguous sub-hunks.

    A sub-hunk is a maximal run of kept lines with no dropped line and no gap
    in old-file line numbers. Pure-context runs (no +/- line) are dropped.
    Headers are recomputed from the run's own line numbers; a pure-addition run
    reports its insertion point as the old line just before the run.
    """
    annotated = _annotate(hunk)
    runs: list[list[_Line]] = []
    current: list[_Line] = []
    last_old: int | None = None
    for i, line in enumerate(annotated):
        if i not in kept:
            if _run_has_change(current):
                runs.append(current)
            current = []
            last_old = None
            continue
        if line.old is not None and last_old is not None and line.old != last_old + 1:
            if _run_has_change(current):
                runs.append(current)
            current = []
        current.append(line)
        if line.old is not None:
            last_old = line.old
    if _run_has_change(current):
        runs.append(current)

    out: list[Hunk] = []
    for run in runs:
        old_lines = [l for l in run if l.old is not None]
        new_lines = [l for l in run if l.new is not None]
        old_at = [l.old for l in run if l.old is not None]
        new_at = [l.new for l in run if l.new is not None]
        old_start = old_at[0] if old_at else _insertion_old(hunk, run)
        new_start = (
            new_at[0]
            if new_at
            else _deletion_new_start(hunk, old_at[-1] if old_at else None)
        )
        h = Hunk(
            old_start=old_start,
            old_count=len(old_lines),
            new_start=new_start,
            new_count=len(new_lines),
            lines=[l.prefix + l.text for l in run],
        )
        out.append(h)
    return out


def _deletion_new_start(hunk: Hunk, last_old: int | None) -> int:
    """New-file position of a deletion-only run, from the parent hunk."""
    if last_old is None:
        return hunk.new_start
    seen_deletion = False
    for line in _annotate(hunk):
        if line.old is not None and line.old > last_old:
            seen_deletion = True
        if seen_deletion and line.new is not None:
            return line.new
    return hunk.new_start + hunk.new_count


def _insertion_old(hunk: Hunk, run: list[_Line]) -> int:
    """Old-file line just before a pure-addition run, from the parent hunk."""
    first_new = run[0].new
    if first_new is None:
        return hunk.old_start
    for line in _annotate(hunk):
        if line.new is not None and line.new < first_new and line.old is not None:
            return line.old + 1
    return hunk.old_start


def _run_has_change(run: list[_Line]) -> bool:
    return any(l.prefix in ("-", "+") for l in run)


# --------------------------------------------------------------------------- #
# sub-task construction
# --------------------------------------------------------------------------- #

@dataclass
class SubTask:
    """A decomposed sub-task, ready to write to disk."""

    id: str
    parent_id: str
    parent_defect_id: str
    defect: dict
    distractors: list[dict]
    prompt_notes: str
    source: dict
    difficulty: str
    diff_text: str
    context_text: str
    status: str = "clean"
    reason: str | None = None


def _file_hunks_for(hunks: dict[str, list[Hunk]], path: str) -> dict[str, list[Hunk]]:
    return {path: hunks.get(path, [])}


def decompose_one(task_dir: Path, parent_gold: dict, parent_context: str) -> list[SubTask]:
    """Split one task into per-defect sub-tasks.

    A file that carries a single gold defect yields that defect's sub-task with
    the whole file's hunks. A file carrying several defects is split line by
    line by ownership. A sub-diff that references an undefined name pulls the
    defining import from the parent; if none exists the sub-task is marked
    needs-hand-write.
    """
    diff_text = (task_dir / "diff.patch").read_text()
    file_hunks = parse_diff(diff_text)
    defects = parent_gold["defects"]
    distractors = parent_gold.get("distractors", [])

    subs: list[SubTask] = []
    for d in defects:
        path = d["file"]
        spans = _owner_spans(defects, path)
        single = len({did for did, _ in spans}) <= 1
        if single:
            kept_hunks = file_hunks.get(path, [])
        else:
            kept_hunks = _split_multi(file_hunks.get(path, []), spans, d["id"])
        kept_hunks = _close_undefined_names(
            kept_hunks, file_hunks.get(path, []), spans, d["id"]
        )
        diff = emit_diff(_file_hunks_for({path: kept_hunks}, path))
        gold_lines = _gold_lines(kept_hunks)
        defect = {
            "id": "d1",  # the sub-task's sole defect is always d1
            "category": d["category"],
            "file": d["file"],
            "lines": gold_lines,
            "summary": d["summary"],
            "rationale": d["rationale"],
        }
        context = _prune_context(parent_context, path, defects)
        parent_hunks = file_hunks.get(path, [])
        status, reason = _coherence_status(
            kept_hunks, parent_hunks, spans, d["id"], defect
        )
        # Inherit parent distractors that reference the same file as this
        # defect.  Subtask distractors must explain why a suspicious pattern
        # in the sub-diff is NOT a defect; only distractors that point at the
        # defect's file can do that.  The contract caps easy tasks at 1
        # distractor, so we take the first match and renumber to x1.
        sub_distractors: list[dict] = []
        for xd in distractors:
            if xd.get("file") == d["file"] and len(sub_distractors) < 1:
                sub_distractors.append({**xd, "id": "x1"})
        sub = SubTask(
            id=f"{parent_gold['id']}-{d['id']}",
            parent_id=parent_gold["id"],
            parent_defect_id=d["id"],
            defect=defect,
            distractors=sub_distractors,
            prompt_notes=parent_gold.get("prompt_notes", ""),
            source=parent_gold["source"],
            difficulty="easy",
            diff_text=diff,
            context_text=context,
            status=status,
            reason=reason,
        )
        subs.append(sub)
    return subs


def _split_multi(
    hunks: list[Hunk],
    spans: list[tuple[str, tuple[int, int]]],
    target: str,
    context: int = 2,
) -> list[Hunk]:
    """Line-split a multi-defect file's hunks, keeping only ``target``'s lines.

    Each owned line keeps its surrounding context lines so the sub-hunk reads as
    a real change. ``context`` is the number of context lines kept each side.
    """
    out: list[Hunk] = []
    for h in hunks:
        owned = _owned_line_sets(h, spans).get(target, set())
        if not owned:
            continue
        annotated = _annotate(h)
        kept = set(owned)
        for i in owned:
            for j in range(max(0, i - context), min(len(annotated), i + context + 1)):
                if annotated[j].prefix == " ":
                    kept.add(j)
        out.extend(_split_hunk(h, kept))
    return out


def _coherence_status(
    hunks: list[Hunk],
    parent_hunks: list[Hunk],
    spans: list[tuple[str, tuple[int, int]]],
    target: str,
    defect: dict,
) -> tuple[str, str | None]:
    """Gate a sub-diff as clean or needs-hand-write.

    A sub-diff is clean only when its changed lines form a structurally
    complete change that does not reach into another defect's lines. Three
    signals force needs-hand-write:
    - unbalanced delimiters (a change cut mid-expression);
    - a name used by an added line that the parent diff binds only inside
      another defect's lines (a structural leak);
    - a deletion-only change that removes nothing the defect's mechanism needs.
    """
    if not hunks:
        return "needs-hand-write", "no hunks survived the split"
    changed = [l[1:].strip() for h in hunks for l in h.lines if l[0] in ("-", "+")]
    if not changed:
        return "needs-hand-write", "sub-diff is pure context with no change"
    if _delimiter_imbalance(changed):
        return "needs-hand-write", "changed lines are cut mid-expression"
    conflict = _line_conflict(parent_hunks, spans, target)
    if conflict:
        return "needs-hand-write", conflict
    if _name_closure_incomplete(hunks, parent_hunks):
        return "needs-hand-write", "changed lines reference a name bound only in the parent diff"
    if _empty_gold_lines(defect["lines"]):
        return "needs-hand-write", "cannot derive a line anchor for the defect"
    return "clean", None


def _line_conflict(
    parent_hunks: list[Hunk],
    spans: list[tuple[str, tuple[int, int]]],
    target: str,
) -> str | None:
    """Return a reason when the target shares a changed line with another defect.

    A changed line owned by two defects cannot be assigned to either, so each
    of those defects must be hand-written. This is the spec's interleave case.
    """
    for h in parent_hunks:
        owned = _owned_line_sets(h, spans)
        annotated = _annotate(h)
        target_idxs: set[int] = set()
        other_idxs: set[int] = set()
        for i, line in enumerate(annotated):
            if line.prefix not in ("-", "+"):
                continue
            owner = next((did for did, idxs in owned.items() if i in idxs), None)
            if owner is None:
                continue
            if owner == target:
                target_idxs.add(i)
            else:
                other_idxs.add(i)
        if target_idxs & other_idxs:
            return "shares changed lines with another defect"
    return None


def _delimiter_imbalance(changed: list[str]) -> bool:
    openers = sum(s.count("(") + s.count("[") + s.count("{") for s in changed)
    closers = sum(s.count(")") + s.count("]") + s.count("}") for s in changed)
    return openers != closers


def _name_closure_incomplete(hunks: list[Hunk], parent_hunks: list[Hunk]) -> bool:
    """True when an added line loads a name the parent diff binds but the sub-diff omits.

    A self-contained sub-diff must bind every name it loads that the change
    itself introduces. A name the parent binds only in a changed line the
    sub-diff does not include means the split dropped part of the mechanism.
    """
    added = [l[1:].strip() for h in hunks for l in h.lines if l[0] == "+"]
    if not added:
        return False
    used = _used_names(added)
    bound = _bound_names(added)
    unbound = used - bound - set(dir(builtins))
    if not unbound:
        return False
    parent_bound: set[str] = set()
    for h in parent_hunks:
        for line in h.lines:
            if line[0] not in ("+", "-"):
                continue
            text = line[1:].strip()
            # a def param is declared by the sibling sub-task; its name is
            # self-evident in a fragment, so it does not demand closure
            parent_bound.update(_bound_names([text]) - _param_names(text))
    return bool(unbound & parent_bound)


def _empty_gold_lines(lines: list[int]) -> bool:
    return not lines or lines[0] < 1


def _gold_lines(hunks: list[Hunk]) -> list[int]:
    """Derive the sub-task defect's new-file line anchor from its hunks.

    Uses the hunk that carries the most changed lines. The anchor is the span of
    its '+' lines, or the new-file context span when the hunk only deletes
    lines. This mirrors the hand-written anchors: a region, not a point.
    """
    best: tuple[int, int] | None = None
    best_change = -1
    for h in hunks:
        change = sum(1 for l in h.lines if l[0] in ("-", "+"))
        if change <= best_change:
            continue
        # walk the hunk to find the changed lines' new-file numbers
        new = h.new_start
        plus_nums: list[int] = []
        for l in h.lines:
            if l[0] == " ":
                new += 1
            elif l[0] == "+":
                plus_nums.append(new)
                new += 1
        if plus_nums:
            best = (min(plus_nums), max(plus_nums))
            best_change = change
        elif h.new_count:  # deletion-only hunk: use the surrounding context span
            best = (h.new_start, h.new_start + h.new_count - 1)
            best_change = change
    if best is None:
        return []
    return [best[0], best[1]]


def _prune_context(context: str, path: str, defects: list[dict]) -> str:
    """Keep the paragraphs that do not reference another defect's file only.

    A paragraph that names a different defect's file but not this one's is
    dropped. Everything else stays, so the sentences that make the defect
    defensible survive the split.
    """
    other_files = {d["file"] for d in defects if d["file"] != path}
    kept: list[str] = []
    for para in context.split("\n\n"):
        if any(f in para for f in other_files) and path not in para:
            continue
        kept.append(para)
    return "\n\n".join(kept)


def _close_undefined_names(
    hunks: list[Hunk], parent_hunks: list[Hunk], spans: list[tuple[str, tuple[int, int]]], target: str
) -> list[Hunk]:
    """Pull supporting imports from the parent for names the sub-diff uses.

    If a '+' line uses an identifier the sub-diff itself does not bind, and the
    parent diff binds that identifier in a line no other defect owns, that line
    and its removed counterpart are added to the sub-diff. This closes cases
    like t001 d1, whose pre-check calls get_balance but whose import line falls
    outside the defect's line anchor.
    """
    changed = [l[1:].strip() for h in hunks for l in h.lines if l[0] == "+"]
    if not changed:
        return hunks
    used = _used_names(changed)
    bound = _bound_names(changed)
    unbound = used - bound - set(dir(builtins))
    if not unbound:
        return hunks

    extra: list[_Line] = []
    seen: set[tuple[int | None, str, str]] = set()
    for h in parent_hunks:
        owned = _owned_line_sets(h, spans)
        other: set[int] = set()
        for did, idxs in owned.items():
            if did != target:
                other.update(idxs)
        annotated = _annotate(h)
        for i, line in enumerate(annotated):
            if i in other or line.prefix not in ("+", "-"):
                continue
            if line.text.strip().startswith(("def ", "class ", "async def ")):
                continue  # a function body cannot be isolated by one line
            line_bound = _bound_names([line.text])
            if not (line_bound & unbound) or not _looks_like_binding(line.text):
                continue
            pair = [line]
            if i > 0 and annotated[i - 1].prefix == "-":
                pair.insert(0, annotated[i - 1])
            for l in pair:
                key = (l.old, l.prefix, l.text)
                if key not in seen:
                    seen.add(key)
                    extra.append(l)
    if not extra:
        return hunks
    extra.sort(key=lambda l: (l.old if l.old is not None else 0))
    merged = list(hunks) + [_hunk_from_lines(extra)]
    merged.sort(key=lambda h: h.new_start)
    return merged


def _hunk_from_lines(lines: list[_Line]) -> Hunk:
    old_at = [l.old for l in lines if l.old is not None]
    new_at = [l.new for l in lines if l.new is not None]
    return Hunk(
        old_start=old_at[0] if old_at else 0,
        old_count=len(old_at),
        new_start=new_at[0] if new_at else 0,
        new_count=len(new_at),
        lines=[l.prefix + l.text for l in lines],
    )


_KEYWORDS = frozenset(
    {
        "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "False", "finally", "for",
        "from", "global", "if", "import", "in", "is", "lambda", "None",
        "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
        "while", "with", "yield",
    }
)
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _used_names(snippets: list[str]) -> set[str]:
    """Names loaded by the snippets. Falls back to tokens for incomplete lines."""
    names: set[str] = set()
    for s in snippets:
        try:
            tree = ast.parse(s)
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    names.add(node.id)
        else:
            # the line is an incomplete fragment; fall back to tokens, which
            # also picks up names inside string literals (acceptable here)
            names.update(_IDENT.findall(s))
    return names - _KEYWORDS


def _bound_names(snippets: list[str]) -> set[str]:
    """Names bound by the snippets: imports, definitions, and assignments."""
    names: set[str] = set()
    for s in snippets:
        m = re.match(r"^\s*from\s+[\w.]+\s+import\s+(.+)$", s)
        if m:
            for part in m.group(1).split(","):
                p = part.strip()
                if " as " in p:
                    src, _, alias = p.partition(" as ")
                    names.add(src.split(".")[0])
                    names.add(alias.split(".")[0])
                else:
                    names.add(p.split(".")[0])
        m = re.match(r"^\s*import\s+(.+)$", s)
        if m:
            for part in m.group(1).split(","):
                p = part.strip()
                if " as " in p:
                    src, _, alias = p.partition(" as ")
                    names.add(src.split(".")[0])
                    names.add(alias.split(".")[0])
                else:
                    names.add(p.split(".")[0])
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", s):
            names.add(m.group(1))
        m = re.match(
            r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)",
            s,
            re.S,
        )
        if m:
            names.add(m.group(1))
            for param in m.group(2).split(","):
                param = param.strip().lstrip("*")
                param = param.split(":")[0].split("=")[0].strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", param):
                    names.add(param)
        else:
            m = re.match(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\b", s)
            if m:
                names.add(m.group(1))
        m = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\b", s)
        if m:
            names.add(m.group(1))
        try:
            tree = ast.parse(s)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
    return names


def _param_names(snippet: str) -> set[str]:
    """Parameter names declared by one def line."""
    m = re.match(
        r"^(?:async\s+)?def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(([^)]*)\)",
        snippet,
        re.S,
    )
    if not m:
        return set()
    params: set[str] = set()
    for param in m.group(1).split(","):
        param = param.strip().lstrip("*")
        param = param.split(":")[0].split("=")[0].strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", param):
            params.add(param)
    return params


def _looks_like_binding(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith(("import ", "from ")):
        return True
    if re.match(r"^(def|class|async def)\s+", stripped):
        return True
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", stripped))


# --------------------------------------------------------------------------- #
# write / generate / CLI
# --------------------------------------------------------------------------- #

def write_task(out_dir: Path, sub: SubTask, meta: dict) -> Path | None:
    """Write one sub-task directory. Returns None when the gold is invalid.

    An invalid gold marks the sub-task needs-hand-write; the directory is not
    written, so a broken draft never loads through the taskset.
    """
    gold = {
        "id": sub.id,
        "difficulty": sub.difficulty,
        "source": sub.source,
        "defects": [sub.defect],
        "distractors": sub.distractors,
        "prompt_notes": sub.prompt_notes,
    }
    target = out_dir / sub.id
    try:
        validate_gold(gold, target)
    except Exception as exc:
        meta.update(
            {
                "status": "needs-hand-write",
                "reason": f"gold contract rejected: {exc}",
                "generator": "arch_review_v1.taskgen",
                "generator_version": GENERATOR_VERSION,
            }
        )
        (out_dir / "_invalid.yaml").open("a").write(
            yaml.safe_dump({sub.id: meta}, sort_keys=False, width=88)
        )
        return None
    target.mkdir(parents=True, exist_ok=True)
    (target / "diff.patch").write_text(sub.diff_text)
    (target / "context.md").write_text(sub.context_text)
    (target / "gold.yaml").write_text(
        yaml.safe_dump(gold, sort_keys=False, width=88)
    )
    meta.update(
        {
            "generator": "arch_review_v1.taskgen",
            "generator_version": GENERATOR_VERSION,
        }
    )
    (target / "_meta.yaml").write_text(yaml.safe_dump(meta, sort_keys=False, width=88))
    return target


def decompose(task_dir: Path, out_dir: Path) -> list[Path]:
    """Decompose one task directory into per-defect sub-task directories."""
    gold = yaml.safe_load((task_dir / "gold.yaml").read_text())
    context = (task_dir / "context.md").read_text()
    subs = decompose_one(task_dir, gold, context)
    written: list[Path] = []
    for sub in subs:
        meta = {
            "mode": "decomposed",
            "parent": sub.parent_id,
            "parent_defect": sub.parent_defect_id,
            "status": sub.status,
        }
        if sub.reason:
            meta["reason"] = sub.reason
        result = write_task(out_dir, sub, meta)
        if result is not None:
            written.append(result)
    return written


def generate(template_path: Path, out_dir: Path) -> Path:
    """Materialize one mechanism template into a task directory.

    The template declares the base and defective file contents, the defect,
    and the defect's line anchor in the defective file. The generator diffs the
    two files deterministically with difflib.
    """
    import difflib

    tpl = yaml.safe_load(template_path.read_text())
    base_files: dict[str, str] = tpl["base"]
    defective_files: dict[str, str] = tpl["defective"]
    file_hunks: dict[str, list[Hunk]] = {}
    for path in base_files:
        base_lines = base_files[path].splitlines()
        defective_lines = defective_files[path].splitlines()
        hunks = _diff_to_hunks(path, base_lines, defective_lines)
        file_hunks[path] = hunks
    diff_text = emit_diff(file_hunks)

    defect = {
        "id": tpl["defect_id"],
        "category": tpl["category"],
        "file": tpl["file"],
        "lines": tpl["lines"],
        "summary": tpl["summary"],
        "rationale": tpl["rationale"],
    }
    gold = {
        "id": tpl["id"],
        "difficulty": tpl.get("difficulty", "easy"),
        "source": tpl.get("source", {"kind": "synthetic"}),
        "defects": [defect],
        "distractors": tpl.get("distractors", []),
        "prompt_notes": tpl.get("prompt_notes", ""),
    }
    sub = SubTask(
        id=tpl["id"],
        parent_id=tpl.get("parent", ""),
        parent_defect_id=defect["id"],
        defect=defect,
        distractors=tpl.get("distractors", []),
        prompt_notes=tpl.get("prompt_notes", ""),
        source=gold["source"],
        difficulty=gold["difficulty"],
        diff_text=diff_text,
        context_text=tpl["context"],
    )
    written = write_task(out_dir, sub, {"mode": "generated", "family": tpl.get("family", "")})
    if written is None:
        raise ValueError(
            f"{template_path}: generated gold is invalid; the sub-task needs a hand-written gold"
        )
    return written


def _diff_to_hunks(path: str, base_lines: list[str], defective_lines: list[str]) -> list[Hunk]:
    import difflib

    sm = difflib.SequenceMatcher(a=base_lines, b=defective_lines)
    hunks: list[Hunk] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        # build a hunk with a small context window
        ctx = 1
        ci1, cj1 = max(0, i1 - ctx), max(0, j1 - ctx)
        ci2, cj2 = min(len(base_lines), i2 + ctx), min(len(defective_lines), j2 + ctx)
        lines: list[str] = []
        old_start, new_start = ci1 + 1, cj1 + 1
        for k in range(ci1, ci2):
            if k < i1:
                lines.append(" " + base_lines[k])
            elif k < i2:
                lines.append("-" + base_lines[k])
        # interleave base and defective for the changed region
        for k in range(i1, i2):
            lines.append("-" + base_lines[k])
        for k in range(j1, j2):
            lines.append("+" + defective_lines[k])
        for k in range(i2, ci2):
            lines.append(" " + base_lines[k])
        old_count = sum(1 for l in lines if l[0] in (" ", "-"))
        new_count = sum(1 for l in lines if l[0] in (" ", "+"))
        hunks.append(Hunk(old_start, old_count, new_start, new_count, lines))
    return hunks


def _main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="taskgen")
    parser.add_argument("--decompose", metavar="TASK_DIR")
    parser.add_argument("--generate", metavar="TEMPLATE.yaml")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    if args.decompose:
        task_dir = Path(args.decompose)
        out = Path(args.out) if args.out else task_dir.parent / "decomposed"
        written = decompose(task_dir, out)
        for w in written:
            meta = yaml.safe_load((w / "_meta.yaml").read_text())
            print(f"{w.name}: {meta.get('status')}")
        return 0
    if args.generate:
        tpl = Path(args.generate)
        out = Path(args.out) if args.out else tpl.parent / "generated"
        p = generate(tpl, out)
        print(p.name)
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(__import__("sys").argv[1:]))
