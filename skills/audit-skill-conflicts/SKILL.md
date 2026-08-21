---
name: audit-skill-conflicts
description: Audit two or more Codex or agent skills for pairwise conflicts in activation triggers, mandatory instructions, tool choices, permissions, output contracts, shared resources, dependencies, or skill identity. Use when asked to compare, validate, inventory, or diagnose skills for overlaps or contradictions. Keep the audit read-only unless the user separately asks to modify the skills.
---

# Audit Skill Conflicts

Perform a read-only audit that names both sides of every confirmed conflict and shows evidence from each skill.

## Establish scope

- Use skill roots or individual skill directories supplied by the user.
- When no paths are supplied, include the current repository's discovered `.agents/skills` directories and readable personal Codex skill directories. State every root actually scanned.
- Do not silently broaden the scan to unrelated repositories, remote sources, or disabled skills.
- Treat two skills with the same `name` as separate skills by their resolved paths.

## Build the inventory

Run the bundled scanner from this skill directory:

```text
python scripts/scan_skill_conflicts.py --root <skill-root> [--root <skill-root> ...] --format json --output <temporary-report.json>
```

The scanner inventories metadata and restrictive directives, creates the complete unordered pair list, and flags deterministic candidates. Its candidates are leads, not confirmed semantic conflicts.

Read [references/conflict-taxonomy.md](references/conflict-taxonomy.md) before judging pairs. Inspect the full `SKILL.md` and relevant `agents/openai.yaml` for both members of every candidate pair. Also compare non-candidate pairs when broad descriptions, shared targets, or extracted directives make coexistence uncertain.

## Decide whether a pair conflicts

Review every unordered pair once. Confirm a conflict only when at least one of these is true:

- The same realistic request can activate both skills and their required behavior is incompatible.
- Following both skills would require and forbid the same action, tool, format, order, permission, or side effect.
- Both skills claim the same identity or shared resource in a way that makes selection or execution ambiguous.
- Their declared dependencies or invocation policies cannot coexist in the target environment.

Do not call mere topic overlap, different optional recommendations, complementary specialization, or system-enforced instruction precedence a conflict. Mark a conflict as `conditional` when it occurs only under a specific trigger, environment, or invocation order, and state that condition.

For every finding, capture:

- both skill names and resolved paths;
- conflict type and severity;
- a plain-language explanation of the incompatible requirements;
- evidence from each side with file and line number;
- the request or condition that exposes the conflict;
- the smallest remediation that preserves both skills' intent.

## Report the results

Match the user's language. Use this structure:

1. **Summary** -- roots scanned, skill count, pair count, confirmed conflict count, and severity counts.
2. **Conflict table** -- one row per conflict with ID, Skill A, Skill B, severity, type, conflict, triggering condition, and concise evidence from both sides.
3. **Conflict details** -- explain each finding and recommend a minimal fix. Separate confirmed and conditional findings.
4. **Per-skill index** -- list every scanned skill and its conflict IDs; explicitly write `none` for skills with no confirmed conflicts.
5. **Coverage and limitations** -- inaccessible roots, unreadable files, truncated scans, or unresolved ambiguity.

If no conflicts are found, say so explicitly and still report the number of skills and pairs reviewed. Never present scanner similarity scores as proof of conflict. Do not edit, disable, install, or delete any skill during an audit unless the user separately authorizes remediation.

