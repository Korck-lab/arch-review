"""Contract validators at the model-extraction seam (ADR-0022).

A raised ContractError parks the trace as a TaskError; invalid judge output is
never scored. The dataset contract (validate_gold) is enforced at load time so a
bad task fails the taskset build instead of being skipped (ADR-0003). Fields are
normalized at the seam before validation (whitespace, case) rather than rejected.
"""

from __future__ import annotations

from pathlib import Path

from arch_review_v1.schemas import ClaimExtraction, Defect, Distractor, MatchResult

GENERAL_SENTINEL = "general"

# The distinct-category rule (medium/hard) requires every defect in one task to
# carry a different term, so the vocabulary is split finely where one bucket
# would hide variance. Security-family terms are disjoint (ADR-0028):
# authorization (access control), injection (input reaching an interpreter),
# traversal (path escape), and security (the residue: secrets, crypto, SSRF,
# CSRF, TLS). A task may carry two security-family defects when they are
# different review skills.
CATEGORIES = frozenset(
    {
        "concurrency",
        "data",
        "contracts",
        "resilience",
        "architecture",
        "operability",
        "security",
        "authorization",
        "injection",
        "traversal",
    }
)
DIFFICULTIES = frozenset({"easy", "medium", "hard"})
# difficulty -> (defect_lo, defect_hi, distractor_lo, distractor_hi, distinct_categories)
DIFFICULTY_RULES = {
    "easy": (1, 1, 0, 1, False),
    "medium": (2, 2, 1, None, True),
    "hard": (3, 4, 2, None, True),
}
PERMISSIVE_LICENSES = frozenset(
    {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "Unlicense", "CC0-1.0"}
)

_DEFECT_KEYS = {"id", "category", "file", "lines", "summary", "rationale"}
_DISTRACTOR_KEYS = {"id", "file", "lines", "concern", "why_ok"}


class ContractError(ValueError):
    """A dataset or judge-contract violation."""


def _validate_lines(lines, where: str) -> None:
    if not isinstance(lines, list) or len(lines) != 2:
        raise ContractError(f"{where}: lines must be [start, end]")
    start, end = lines
    if (
        not isinstance(start, int)
        or not isinstance(end, int)
        or isinstance(start, bool)
        or isinstance(end, bool)
    ):
        raise ContractError(f"{where}: lines must be integers")
    if start < 1 or start > end:
        raise ContractError(f"{where}: lines must satisfy 1 <= start <= end, got {lines}")


def _sequential_ids(entries: list[dict], prefix: str, where: str) -> None:
    expected = [f"{prefix}{i}" for i in range(1, len(entries) + 1)]
    actual = [entry["id"] for entry in entries]
    if actual != expected:
        raise ContractError(f"{where} ids must be sequential {prefix}1..{prefix}{len(entries)}, got {actual}")


def validate_gold(raw, task_dir: Path) -> dict:
    """Validate one parsed gold.yaml against the dataset contract.

    Returns the normalized gold dict on success; raises ContractError on the
    first violation.
    """
    if not isinstance(raw, dict):
        raise ContractError("gold.yaml must map to a mapping")
    required = {"id", "difficulty", "source", "defects", "distractors"}
    if missing := required - set(raw):
        raise ContractError(f"gold.yaml missing keys: {sorted(missing)}")

    task_id = raw["id"]
    if task_id != task_dir.name:
        raise ContractError(f"gold id {task_id!r} != directory name {task_dir.name!r}")

    difficulty = raw["difficulty"]
    if difficulty not in DIFFICULTIES:
        raise ContractError(f"unknown difficulty {difficulty!r}")

    source = raw["source"]
    if not isinstance(source, dict) or "kind" not in source:
        raise ContractError("source must be a mapping with a 'kind' discriminator")
    kind = source["kind"]
    if kind not in {"synthetic", "oss"}:
        raise ContractError(f"unknown source.kind {kind!r}")
    if kind == "synthetic":
        if extra := set(source) - {"kind"}:
            raise ContractError(f"synthetic source must not carry extra fields: {sorted(extra)}")
    else:
        for field in ("url", "license", "attribution"):
            if field not in source:
                raise ContractError(f"oss source missing {field!r}")
        if source["license"] not in PERMISSIVE_LICENSES:
            raise ContractError(f"non-permissive or unknown license {source['license']!r}")
        if extra := set(source) - {"kind", "url", "license", "attribution"}:
            raise ContractError(f"oss source has unknown fields: {sorted(extra)}")

    defects_raw = raw["defects"]
    if not isinstance(defects_raw, list) or not isinstance(raw["distractors"], list):
        raise ContractError("defects and distractors must be lists")
    if not (1 <= len(defects_raw) <= 4):
        raise ContractError(f"defects must number 1-4, got {len(defects_raw)}")

    defects = []
    for entry in defects_raw:
        for field in _DEFECT_KEYS:
            if field not in entry:
                raise ContractError(f"defect missing {field!r}")
        if extra := set(entry) - _DEFECT_KEYS:
            raise ContractError(f"defect {entry['id']!r} has unknown keys: {sorted(extra)}")
        if entry["category"] not in CATEGORIES:
            raise ContractError(f"unknown category {entry['category']!r}")
        _validate_lines(entry["lines"], f"defect {entry['id']}")
        defects.append(Defect(**entry))

    distractors_raw = raw["distractors"]
    distractors = []
    for entry in distractors_raw:
        for field in _DISTRACTOR_KEYS:
            if field not in entry:
                raise ContractError(f"distractor missing {field!r}")
        if extra := set(entry) - _DISTRACTOR_KEYS:
            raise ContractError(f"distractor {entry['id']!r} has unknown keys: {sorted(extra)}")
        if entry.get("lines") is not None:
            _validate_lines(entry["lines"], f"distractor {entry['id']}")
        distractors.append(Distractor(**entry))

    # difficulty rules: defect count, distractor count, distinct categories, sequential ids.
    defect_lo, defect_hi, distractor_lo, distractor_hi, distinct = DIFFICULTY_RULES[difficulty]
    if not (defect_lo <= len(defects) <= defect_hi):
        raise ContractError(
            f"difficulty {difficulty!r} requires {defect_lo}-{defect_hi} defects, got {len(defects)}"
        )
    if len(distractors) < distractor_lo or (distractor_hi is not None and len(distractors) > distractor_hi):
        lo = distractor_lo
        hi = "unbounded" if distractor_hi is None else distractor_hi
        raise ContractError(
            f"difficulty {difficulty!r} requires {lo}-{hi} distractors, got {len(distractors)}"
        )
    if distinct and len({d.category for d in defects}) != len(defects):
        raise ContractError(f"difficulty {difficulty!r} requires distinct defect categories")
    _sequential_ids(defects_raw, "d", "defect")
    _sequential_ids(distractors_raw, "x", "distractor")

    if extra := set(raw) - required - {"prompt_notes"}:
        raise ContractError(f"unknown gold.yaml keys: {sorted(extra)}")

    return {
        "id": task_id,
        "difficulty": difficulty,
        "source": source,
        "defects": defects,
        "distractors": distractors,
        "prompt_notes": raw.get("prompt_notes", ""),
    }


def _verbatim_norm(text: str) -> str:
    """Normalize a quote or review for verbatim comparison.

    Reviewers wrap identifiers and commands in inline code backticks; the
    extractor's quote routinely strips them, which is not a paraphrase. Remove
    backticks and collapse whitespace runs on both sides so formatting does not
    fail the verbatim check. A genuinely reworded quote still differs after
    normalization.
    """
    import re as _re

    return _re.sub(r"\s+", " ", text.replace("`", "")).strip()


def validate_extraction(
    extraction: ClaimExtraction,
    file_list: list[str],
    review: str | None = None,
) -> ClaimExtraction:
    """Gold-blind extraction contract.

    Claims reference files in the diff (or the general sentinel), have dense
    sequential ids (c1..cN), carry a verbatim quote from the review, and have
    non-empty summaries. The validator never sees gold. The verbatim check
    compares normalized text, so inline-code backticks in the review do not
    fail an otherwise exact quote.
    """
    allowed = set(file_list) | {GENERAL_SENTINEL}
    expected_ids = [f"c{i}" for i in range(1, len(extraction.claims) + 1)]
    actual_ids = [claim.id for claim in extraction.claims]
    if actual_ids != expected_ids:
        raise ContractError(
            f"claim ids must be dense c1..c{len(extraction.claims)}, got {actual_ids}"
        )
    norm_review = _verbatim_norm(review) if review is not None else None
    for claim in extraction.claims:
        if claim.file not in allowed:
            raise ContractError(
                f"claim {claim.id!r} cites file {claim.file!r} not in the diff"
            )
        if not claim.quote:
            raise ContractError(f"claim {claim.id!r} has empty quote")
        if norm_review is not None and _verbatim_norm(claim.quote) not in norm_review:
            raise ContractError(f"claim {claim.id!r} quote is not verbatim in the review")
        if not claim.summary.strip():
            raise ContractError(f"claim {claim.id!r} has empty summary")
    return extraction


def validate_matching(
    result: MatchResult, claims, defects, distractors
) -> MatchResult:
    """Matching contract.

    Exactly one verdict per claim (bijection), closed defect and distractor
    sets, and a closed kind enum.
    """
    claim_ids = {c.id for c in claims}
    defect_ids = {d.id for d in defects}
    distractor_files = {d.file for d in distractors}
    seen = set()
    for verdict in result.verdicts:
        if verdict.claim_id not in claim_ids:
            raise ContractError(f"verdict references unknown claim {verdict.claim_id!r}")
        if verdict.claim_id in seen:
            raise ContractError(f"claim {verdict.claim_id!r} has more than one verdict")
        seen.add(verdict.claim_id)
        if verdict.kind == "matched":
            if verdict.defect_id is None:
                raise ContractError(f"matched verdict for claim {verdict.claim_id!r} has no defect")
            if verdict.defect_id not in defect_ids:
                raise ContractError(f"verdict credits unknown defect {verdict.defect_id!r}")
            if verdict.second_defect_id is not None:
                if verdict.second_defect_id not in defect_ids:
                    raise ContractError(
                        f"verdict credits unknown defect {verdict.second_defect_id!r}"
                    )
                if verdict.second_defect_id == verdict.defect_id:
                    raise ContractError(
                        f"verdict for claim {verdict.claim_id!r} credits the same defect twice"
                    )
        elif verdict.kind == "distractor":
            if (
                verdict.distractor_file is None
                or verdict.distractor_file not in distractor_files
            ):
                raise ContractError(
                    f"distractor verdict cites unknown file {verdict.distractor_file!r}"
                )
        elif verdict.kind != "false_alarm":
            raise ContractError(f"verdict has invalid kind {verdict.kind!r}")
    if missing := claim_ids - seen:
        raise ContractError(f"claims with no verdict: {sorted(missing)}")
    return result
