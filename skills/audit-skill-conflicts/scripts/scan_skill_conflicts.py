#!/usr/bin/env python3
"""Inventory skills and surface deterministic pairwise conflict candidates.

This script deliberately does not decide semantic conflicts. It produces a complete
pair list, extracts restrictive directives with line numbers, and identifies signals
that a reasoning pass should inspect.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


SKILL_FILE = "SKILL.md"
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__"}
DIRECTIVE_RE = re.compile(
    r"(?:\b(?:must|required|always|never|only|do not|don't|shall|should not|cannot|can't|"
    r"prefer|avoid)\b|禁止|必须|务必|始终|永不|不得|不要|只能|仅限|优先|避免)",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[a-z0-9][a-z0-9_-]*|[\u3400-\u9fff]", re.IGNORECASE)
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "the", "to", "use", "when", "with",
    "skill", "skills", "codex", "user", "task",
}


@dataclass
class Directive:
    line: int
    text: str


@dataclass
class SkillRecord:
    id: str
    name: str
    description: str
    path: str
    root: str
    name_line: int | None
    description_line: int | None
    implicit_invocation: bool | None
    directives: list[Directive]
    parse_warnings: list[str]


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], dict[str, int], int, list[str]]:
    warnings: list[str] = []
    if not lines or lines[0].strip() != "---":
        return {}, {}, 0, ["missing YAML frontmatter"]

    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, {}, 0, ["unterminated YAML frontmatter"]

    values: dict[str, str] = {}
    line_numbers: dict[str, int] = {}
    i = 1
    while i < end:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[i])
        if not match:
            i += 1
            continue
        key, raw = match.group(1), match.group(2)
        line_numbers[key] = i + 1
        if raw in {">", ">-", "|", "|-"}:
            block: list[str] = []
            i += 1
            while i < end and (not lines[i].strip() or lines[i][:1].isspace()):
                block.append(lines[i].strip())
                i += 1
            values[key] = (" " if raw.startswith(">") else "\n").join(block).strip()
            continue
        values[key] = scalar(raw)
        i += 1
    return values, line_numbers, end + 1, warnings


def parse_implicit_policy(skill_path: Path) -> bool | None:
    policy_path = skill_path.parent / "agents" / "openai.yaml"
    if not policy_path.is_file():
        return None
    try:
        text = policy_path.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    match = re.search(r"^\s*allow_implicit_invocation:\s*(true|false)\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "true"


def find_skill_files(root: Path) -> Iterable[Path]:
    if root.is_file() and root.name.lower() == SKILL_FILE.lower():
        yield root
        return
    if (root / SKILL_FILE).is_file():
        yield root / SKILL_FILE
        return
    if not root.is_dir():
        return
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if SKILL_FILE in files:
            yield Path(current) / SKILL_FILE
            dirs[:] = []


def default_roots() -> list[Path]:
    roots: list[Path] = []
    current = Path.cwd().resolve()
    for parent in (current, *current.parents):
        candidate = parent / ".agents" / "skills"
        if candidate.is_dir():
            roots.append(candidate)
        if (parent / ".git").exists():
            break

    roots.append(Path.home() / ".agents" / "skills")
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    roots.append(codex_home / "skills")
    return roots


def unique_existing_roots(raw_roots: Iterable[str]) -> tuple[list[Path], list[str]]:
    requested = [Path(p).expanduser() for p in raw_roots]
    if not requested:
        requested = default_roots()
    roots: list[Path] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for raw in requested:
        try:
            resolved = raw.resolve()
        except OSError as exc:
            warnings.append(f"cannot resolve {raw}: {exc}")
            continue
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        if not resolved.exists():
            warnings.append(f"root does not exist: {resolved}")
            continue
        roots.append(resolved)
    return roots, warnings


def parse_skill(path: Path, root: Path, index: int) -> SkillRecord:
    warnings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        return SkillRecord(
            id=f"S{index:03d}", name=path.parent.name, description="", path=str(path),
            root=str(root), name_line=None, description_line=None, implicit_invocation=None,
            directives=[], parse_warnings=[f"cannot read file: {exc}"],
        )

    metadata, line_numbers, body_start, frontmatter_warnings = parse_frontmatter(lines)
    warnings.extend(frontmatter_warnings)
    name = metadata.get("name", "").strip() or path.parent.name
    description = metadata.get("description", "").strip()
    if "name" not in metadata:
        warnings.append("missing frontmatter name; using directory name")
    if not description:
        warnings.append("missing frontmatter description")

    directives = [
        Directive(line=i + 1, text=line.strip())
        for i, line in enumerate(lines[body_start:], start=body_start)
        if DIRECTIVE_RE.search(line) and line.strip()
    ]
    return SkillRecord(
        id=f"S{index:03d}", name=name, description=description,
        path=str(path.resolve()), root=str(root),
        name_line=line_numbers.get("name"), description_line=line_numbers.get("description"),
        implicit_invocation=parse_implicit_policy(path), directives=directives[:200],
        parse_warnings=warnings + (["directive extraction truncated at 200 lines"] if len(directives) > 200 else []),
    )


def tokens(text: str) -> set[str]:
    return {token.lower() for token in WORD_RE.findall(text) if token.lower() not in STOP_WORDS and len(token) > 1}


def similarity(left: str, right: str) -> tuple[float, float, float]:
    left_norm = " ".join(left.lower().split())
    right_norm = " ".join(right.lower().split())
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio() if left_norm and right_norm else 0.0
    left_tokens, right_tokens = tokens(left), tokens(right)
    union = left_tokens | right_tokens
    jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
    return max(sequence, jaccard), sequence, jaccard


def make_pairs(skills: list[SkillRecord], threshold: float) -> list[dict[str, object]]:
    pairs: list[dict[str, object]] = []
    for i, left in enumerate(skills):
        for right in skills[i + 1:]:
            score, sequence, jaccard = similarity(left.description, right.description)
            signals: list[dict[str, object]] = []
            if left.name.casefold() == right.name.casefold():
                signals.append({
                    "type": "identity-collision",
                    "reason": "both skills declare the same name",
                    "deterministic": True,
                })
            if score >= threshold:
                signals.append({
                    "type": "trigger-overlap-candidate",
                    "reason": "descriptions are lexically similar; semantic confirmation required",
                    "deterministic": False,
                })
            if (
                left.name.casefold() == right.name.casefold()
                and left.implicit_invocation is not None
                and right.implicit_invocation is not None
                and left.implicit_invocation != right.implicit_invocation
            ):
                signals.append({
                    "type": "invocation-policy-candidate",
                    "reason": "same-name skills declare different implicit invocation policies",
                    "deterministic": False,
                })
            pairs.append({
                "left": left.id,
                "right": right.id,
                "description_similarity": round(score, 4),
                "sequence_similarity": round(sequence, 4),
                "token_jaccard": round(jaccard, 4),
                "signals": signals,
            })
    return pairs


def markdown_report(payload: dict[str, object]) -> str:
    coverage = payload["coverage"]
    lines = [
        "# Skill conflict scan candidates",
        "",
        f"Roots scanned: {len(payload['roots'])}",
        f"Skills found: {coverage['skill_count']}",
        f"Pairs enumerated: {coverage['pair_count']}",
        "",
        "> Candidate signals require semantic confirmation; similarity is not proof of conflict.",
        "",
        "| Pair | Similarity | Signals |",
        "|---|---:|---|",
    ]
    skill_names = {item["id"]: item["name"] for item in payload["skills"]}
    candidates = [pair for pair in payload["pairs"] if pair["signals"]]
    for pair in candidates:
        signal_names = ", ".join(signal["type"] for signal in pair["signals"])
        label = f"{skill_names[pair['left']]} <-> {skill_names[pair['right']]}"
        lines.append(f"| {label} | {pair['description_similarity']:.4f} | {signal_names} |")
    if not candidates:
        lines.append("| none | none | No deterministic candidates |")
    if payload["warnings"]:
        lines.extend(["", "## Warnings", ""] + [f"- {warning}" for warning in payload["warnings"]])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", default=[], help="Skill root, skill directory, or SKILL.md path; repeatable")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="Write the report to this file instead of stdout")
    parser.add_argument("--similarity-threshold", type=float, default=0.55)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not 0.0 <= args.similarity_threshold <= 1.0:
        raise SystemExit("--similarity-threshold must be between 0 and 1")

    roots, warnings = unique_existing_roots(args.root)
    found: dict[str, tuple[Path, Path]] = {}
    for root in roots:
        try:
            for skill_file in find_skill_files(root):
                key = os.path.normcase(str(skill_file.resolve()))
                found[key] = (skill_file, root)
        except OSError as exc:
            warnings.append(f"cannot scan {root}: {exc}")

    skills = [
        parse_skill(path, root, index)
        for index, (path, root) in enumerate(sorted(found.values(), key=lambda item: str(item[0]).casefold()), start=1)
    ]
    pairs = make_pairs(skills, args.similarity_threshold)
    payload: dict[str, object] = {
        "schema_version": 1,
        "roots": [str(root) for root in roots],
        "warnings": warnings,
        "coverage": {
            "skill_count": len(skills),
            "pair_count": len(pairs),
            "candidate_pair_count": sum(1 for pair in pairs if pair["signals"]),
        },
        "skills": [asdict(skill) for skill in skills],
        "pairs": pairs,
    }

    output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else markdown_report(payload)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

