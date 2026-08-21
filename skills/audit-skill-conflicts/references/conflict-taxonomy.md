# Skill conflict taxonomy

Use this taxonomy to classify pairwise conflicts consistently. A difference is a conflict only when both instructions can apply in the same situation and cannot both be satisfied.

## Conflict types

### Identity collision

Two discoverable skills declare the same `name`, or indistinguishable names and triggers make invocation ambiguous. Different paths do not resolve the user-facing ambiguity by themselves.

### Trigger collision

Both descriptions claim the same request class but route it to incompatible workflows. Broad overlap alone is not enough; show a realistic request that activates both and produces incompatible requirements.

### Instruction contradiction

One skill requires what the other forbids, or their unconditional requirements cannot both be completed. Examples include always versus never, mutually exclusive source priorities, or incompatible stopping conditions.

### Tool-selection conflict

Both skills require mutually exclusive tools or execution surfaces for the same operation. A preferred tool versus an allowed fallback is normally compatible.

### Permission or side-effect conflict

The skills disagree about approval, external writes, messaging, deletion, publication, deployment, or other state-changing actions. Escalate severity when the combination could bypass review or cause irreversible effects.

### Output-contract conflict

The same requested deliverable is required to satisfy incompatible schemas, file formats, destinations, languages, or presentation rules. Different defaults are compatible when the user can choose one without violating either skill.

### Shared-resource conflict

Both skills write, replace, lock, rename, or delete the same file, directory, branch, configuration key, cache, or remote object using incompatible ownership rules.

### Ordering or lifecycle conflict

The workflows require contradictory step order, retry behavior, termination conditions, cleanup, or ownership of the same lifecycle event.

### Dependency conflict

Declared tool, plugin, runtime, version, transport, or environment requirements cannot coexist. A missing dependency affecting one skill alone is a defect, not an inter-skill conflict.

## Severity

- **Critical** — combined behavior can plausibly cause unauthorized access, irreversible deletion, unsafe publication, credential exposure, or another severe impact.
- **High** — ordinary overlapping use produces incompatible required actions, corrupts shared state, or blocks successful completion.
- **Medium** — conflict causes unreliable routing, incompatible outputs, or repeated manual intervention but has a bounded workaround.
- **Low** — identity duplication or maintainability ambiguity with little immediate execution impact.

## Non-conflicts

Do not report these as conflicts without additional incompatible evidence:

- Similar subject matter or vocabulary.
- One general skill and one compatible specialization.
- Different examples that do not impose requirements.
- Optional recommendations that can both be ignored or selected contextually.
- A skill requiring a tool that is simply unavailable.
- Rules that are resolved by explicit user choice.
- Higher-priority system, developer, permission, or safety rules overriding a skill.

## Evidence standard

Use the smallest relevant excerpt from each side, with file and line number. Explain the incompatible pair of requirements in your own words. When evidence supports only possible overlap, label it as a candidate or conditional issue rather than a confirmed conflict.

