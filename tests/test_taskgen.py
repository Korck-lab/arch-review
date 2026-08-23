"""Tests for the deterministic task generator: the decompose/generate seam.

The seam is the task-directory contract: decompose writes task directories,
write_task validates each against validate_gold, and the taskset loads them.
These tests check external behavior only, matching the spec's testing
decisions (spec issue #12): determinism, containment, isolation, gold
inheritance, contract validity, difficulty rules, and generated syntax.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import yaml

from arch_review_v1.config import ArchReviewTasksetConfig
from arch_review_v1.contract import validate_gold
from arch_review_v1.taskgen import (
    _annotate,
    _owned_line_sets,
    decompose,
    generate,
    parse_diff,
)
from arch_review_v1.taskset import ArchReviewTaskset

_ALL_TASKS = sorted((Path(__file__).parent.parent / "arch_review_v1/tasks").glob("t[0-9][0-9][0-9]-*"))
_TASKS = [t for t in _ALL_TASKS if not re.search(r"-d[0-9]+$", t.name)]

# Defects that interleave on lines or names cannot be split cleanly; the
# splitter must hand them to the curator (spec: "the author hand-writes").
NEEDS_HAND_WRITE = {
    "t002-shop-orders-d1",
    "t002-shop-orders-d2",
    "t004-warehouse-sync-d3",
    "t004-warehouse-sync-d4",
}


def _decompose_all(out_dir: Path) -> dict[str, Path]:
    written: dict[str, Path] = {}
    for task in _TASKS:
        for path in decompose(task, out_dir):
            written[path.name] = path
    return written


def _read(parent: Path, sub: str, name: str) -> str:
    return (parent / sub / name).read_text()


def test_decompose_is_deterministic(tmp_path: Path) -> None:
    a = _decompose_all(tmp_path / "a")
    b = _decompose_all(tmp_path / "b")
    assert set(a) == set(b)
    for name in a:
        for fname in ("diff.patch", "context.md", "gold.yaml", "_meta.yaml"):
            assert _read(tmp_path / "a", name, fname) == _read(tmp_path / "b", name, fname)


def test_decompose_classification_matches_curation(tmp_path: Path) -> None:
    written = _decompose_all(tmp_path)
    clean, hand = set(), set()
    for name, path in written.items():
        meta = yaml.safe_load((path / "_meta.yaml").read_text())
        (clean if meta["status"] == "clean" else hand).add(name)
    assert hand == NEEDS_HAND_WRITE
    assert len(clean) == len(written) - len(hand)


def test_clean_subtask_is_single_defect_easy(tmp_path: Path) -> None:
    written = _decompose_all(tmp_path)
    for name, path in sorted(written.items()):
        meta = yaml.safe_load((path / "_meta.yaml").read_text())
        if meta["status"] != "clean":
            continue
        gold = yaml.safe_load((path / "gold.yaml").read_text())
        assert gold["difficulty"] == "easy"
        assert len(gold["defects"]) == 1
        assert gold["defects"][0]["id"] == "d1"
        assert len(gold["distractors"]) <= 1
        assert gold["source"] == {"kind": "synthetic"}
        parent = next(t for t in _TASKS if t.name == meta["parent"])
        parent_gold = yaml.safe_load((parent / "gold.yaml").read_text())
        parent_defect = next(
            d for d in parent_gold["defects"] if d["id"] == meta["parent_defect"]
        )
        assert gold["defects"][0]["summary"] == parent_defect["summary"]
        assert gold["defects"][0]["category"] == parent_defect["category"]
        assert gold["defects"][0]["file"] == parent_defect["file"]


def _parent_hunks(task: Path, path: str) -> list:
    return parse_diff((task / "diff.patch").read_text()).get(path, [])


def test_clean_subtask_diff_is_contained_in_parent(tmp_path: Path) -> None:
    written = _decompose_all(tmp_path)
    for name, path in sorted(written.items()):
        meta = yaml.safe_load((path / "_meta.yaml").read_text())
        if meta["status"] != "clean":
            continue
        parent = next(t for t in _TASKS if t.name == meta["parent"])
        parent_text = (parent / "diff.patch").read_text()
        for file_hunks in parse_diff((path / "diff.patch").read_text()).values():
            for h in file_hunks:
                for line in h.lines:
                    assert line in parent_text, f"{name}: {line!r} not in parent diff"


def test_clean_subtask_is_isolated_from_other_defects(tmp_path: Path) -> None:
    """No changed line in a clean sub-diff is owned by another parent defect."""
    written = _decompose_all(tmp_path)
    for name, path in sorted(written.items()):
        meta = yaml.safe_load((path / "_meta.yaml").read_text())
        if meta["status"] != "clean":
            continue
        target = meta["parent_defect"]
        parent = next(t for t in _TASKS if t.name == meta["parent"])
        parent_gold = yaml.safe_load((parent / "gold.yaml").read_text())
        sub_gold = yaml.safe_load((path / "gold.yaml").read_text())
        fpath = sub_gold["defects"][0]["file"]
        spans = [
            (d["id"], tuple(d["lines"]))
            for d in parent_gold["defects"]
            if d["file"] == fpath
        ]
        owners: dict[tuple[str, str], set[str]] = {}
        for h in _parent_hunks(parent, fpath):
            owned = _owned_line_sets(h, spans)
            annotated = _annotate(h)
            for i, line in enumerate(annotated):
                if line.prefix not in ("-", "+"):
                    continue
                owner = next(
                    (did for did, idxs in owned.items() if i in idxs), None
                )
                owners.setdefault((line.prefix, line.text), set()).add(
                    owner if owner is not None else ""
                )
        for file_hunks in parse_diff((path / "diff.patch").read_text()).values():
            for h in file_hunks:
                for line in h.lines:
                    if line[0] not in ("-", "+"):
                        continue
                    claimed = owners.get((line[0], line[1:]), {""})
                    foreign = claimed - {target, ""}
                    assert not foreign, f"{name}: {line!r} owned by {sorted(foreign)}"


def test_every_written_subtask_loads_through_taskset(tmp_path: Path) -> None:
    written = _decompose_all(tmp_path)
    ts = ArchReviewTaskset(ArchReviewTasksetConfig())
    for name, path in sorted(written.items()):
        raw = yaml.safe_load((path / "gold.yaml").read_text())
        validate_gold(raw, path)
        task = ts._build_task(path)
        assert task.data.task_id == name


def test_needs_hand_write_subtasks_are_flagged(tmp_path: Path) -> None:
    written = _decompose_all(tmp_path)
    for name in NEEDS_HAND_WRITE:
        meta = yaml.safe_load((written[name] / "_meta.yaml").read_text())
        assert meta["status"] == "needs-hand-write"
        assert meta["reason"]


def test_generate_emits_contract_valid_task(tmp_path: Path) -> None:
    tpl_dir = tmp_path / "tpl"
    tpl_dir.mkdir()
    base = (
        "def price(units: int, unit_cost: int) -> int:\n"
        "    return units * unit_cost\n"
    )
    defective = (
        "def price(units: int, unit_cost: int) -> int:\n"
        "    if units <= 0:\n"
        "        return 0\n"
        "    return units * unit_cost\n"
    )
    template = {
        "id": "gen-001-negative-units",
        "difficulty": "easy",
        "source": {"kind": "synthetic"},
        "family": "pricing-guard",
        "defect_id": "d1",
        "category": "contracts",
        "file": "pricing/quote.py",
        "lines": [2, 4],
        "summary": "negative unit count is coerced to zero instead of raising",
        "rationale": (
            "A negative units argument silently prices the order as free. "
            "The caller cannot distinguish an empty order from an invalid one. "
            "A reviewer would raise ValueError on units <= 0."
        ),
        "context": (
            "`pricing/quote.py` computes an order total. `price` multiplies "
            "the unit count by the unit cost."
        ),
        "base": {"pricing/quote.py": base},
        "defective": {"pricing/quote.py": defective},
        "distractors": [],
    }
    tpl_path = tpl_dir / "template.yaml"
    tpl_path.write_text(yaml.safe_dump(template, sort_keys=False, width=88))

    out = tmp_path / "out"
    out.mkdir()
    path = generate(tpl_path, out)
    assert path.name == "gen-001-negative-units"

    raw = yaml.safe_load((path / "gold.yaml").read_text())
    validate_gold(raw, path)
    assert ArchReviewTaskset(ArchReviewTasksetConfig())._build_task(path).data.task_id == raw["id"]

    # generated base and defective files must parse (spec testing decision)
    for source in (base, defective):
        ast.parse(source)

    diff = (path / "diff.patch").read_text()
    assert "+    if units <= 0:" in diff
    assert "+        return 0" in diff
    assert "     return units * unit_cost" in diff
