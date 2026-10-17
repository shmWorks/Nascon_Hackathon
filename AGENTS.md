# AGENTS.md

Hackathon project: a **personal morning paper** (NaSCon'26, sponsor/judge Eynvision). Code freeze 20:00 PKT, deadline 21:00 PKT, 2026-10-17. Check `date` before scoping any task.

## Where things live

Each fact has one home. Read the home; link to it rather than restating it.

| Need | Read |
| --- | --- |
| Start of any session; what to do next; blockers; past decisions | `docs/state.md` |
| Scope, requirement IDs (R*/A*), constraints, judge-evidence mapping | `docs/spec.md` |
| Organizer's exact wording | `docs/brief.md` |
| Sponsor-fit choices, differentiators or demo framing | `docs/eynvision.md` — research findings and evidence limits |
| Setup, run, test, demo commands; architecture; attribution | `README.md` (created with the first runnable command) |
| Choosing a base repo or reference; doc-layout rules; evaluation guidance | `HACKATHON_AGENT_HANDOFF.md` — read only the section the task needs |
| Exact API fields, validation, dependency versions, test expectations | Schema/code, lockfile, tests |

## Commands

None yet. Add each command to `README.md` when it first runs successfully.

## Work rules

- Build the smallest complete workflow that satisfies `docs/spec.md`; finish one input-to-output slice before widening scope.
- Use the existing stack and lockfile. Name the required capability before adding a dependency.
- Retrieve documentation for the installed version of the library in question.
- Keep constraints, calculations, ranking, permissions and state transitions in deterministic code; models interpret and propose.
- Give every loop, retry, timeout and external call an explicit bound.
- Keep model proposals, fetched evidence (articles, tool results) and committed state (profiles, editions) distinct.
- Verify real task completion and required failure behavior; for UI changes, exercise the browser flow and inspect visible output.
- Report executed commands, results and unresolved failures.
- Commit in small, meaningful steps referencing requirement IDs; the organizer monitors commits.
- When a contract, decision or verified status changes, update only its home file.
- Before choosing new features, check the judge-evidence mapping in `docs/spec.md` for unproven criteria.
- Preserve attribution for reused code (license, pinned commit) in `README.md`.
