# Hackathon Agent Handoff

Updated: 2026-10-17
User: Sheraz Malik
Clients: Codex, Claude Code

## 1. Objective and operating constraints

Deliver one complete workflow whose value, correctness and technical contribution judges can verify.

- Prefer the user's existing React/TypeScript, Python, SQL, Gemini and LangGraph experience.
- Read the official brief before selecting the domain, application base or architecture.
- Record the actual rubric, deadline, team size, submission format and reuse restrictions in `docs/spec.md`.
- Treat the 12-hour solo sprint as a planning assumption until the official brief confirms it.
- No organizer deadline is established by this handoff. Do not assume development is permitted between submission and presentation.
- Use one application base. Borrow specific mechanisms from other repositories.
- Use a fixed workflow unless autonomous tool selection provides a measurable benefit.
- Complete and verify the baseline before optimizing it.
- Explain consequential tradeoffs concisely; execute within the authorized scope.

## 2. Execution order

1. Extract mandatory requirements and judging criteria into `docs/spec.md`.
2. Define the primary task, simplest baseline and observable success/failure cases.
3. Test the dependency most likely to block delivery: model access, external integration, data access or extraction.
4. Select a matching base, record its commit and license, and run it.
5. Complete one vertical slice: input → model/tool execution → validation → resulting state or artifact → visible output.
6. Test ordinary input, invalid input and dependency failure. Inspect actual results.
7. Improve the weakest requirement or highest-weight judging criterion lacking evidence.
8. Freeze architecture, rehearse, verify submission files/links and preserve the submitted version.

### Base validation gate

From a fresh terminal:

- Install using documented commands and pinned dependencies.
- Start the application.
- Submit a real input.
- Execute the real model/tool path.
- Inspect the resulting state or artifact in the interface.
- Trigger one failure and verify controlled behavior.
- Restart and verify required persistence or documented reset behavior.

Budget at most 45 minutes for initial base validation. If unresolved setup prevents this gate, use the base as reference material and switch to a smaller runnable implementation.

## 3. Documentation: four maintained files

| File | Required content | Update trigger |
| --- | --- | --- |
| `AGENTS.md` | Objective, work rules, essential commands, links to authoritative files | Work rules, commands or file ownership change |
| `README.md` | Setup, run/test/demo commands, environment-variable names, architecture summary, attribution | Reproduction steps, component boundaries or adopted resources change |
| `docs/spec.md` | Exact brief, rubric, deadline, constraints, scope, acceptance cases, judge-evidence mapping | Official requirements change or evidence for a criterion changes |
| `docs/state.md` | Verified status, unresolved failures, blockers, next action, consequential decisions | A milestone passes/fails, a blocker changes, a consequential decision changes, or work is handed off |

For Claude Code, use a minimal `CLAUDE.md` importing `@AGENTS.md` when supported by the installed client. Verify loading. Keep shared instructions in `AGENTS.md`.

This handoff is reference material. Do not load every resource into startup context or copy its contents across project files.

### Content ownership

| Information | Authoritative location |
| --- | --- |
| Objective, scope, required outcomes | `docs/spec.md` |
| Agent working rules | `AGENTS.md` |
| Setup and system boundaries | `README.md` |
| Current status, decisions and next action | `docs/state.md` |
| Exact API fields and validation | Schema and implementation |
| Exact dependency versions | Lockfile |
| Test inputs, expected results and checks | Evaluation fixtures and tests |
| Current pass/fail evidence | Execution results linked from state/spec |

Link to authoritative content. Do not maintain duplicate descriptions of schemas, dependency versions, acceptance cases or decisions.

### Architecture section in README

Describe only:

- Components and their responsibilities.
- Input-to-output data flow.
- State ownership and persistence.
- Model/tool boundaries and deterministic validation.
- External dependencies and relevant failure behavior.

Add a diagram only when it clarifies these relationships.

### Decision section in state

Record decisions that materially affect correctness, dependencies, interfaces, delivery time or evaluation.

Format:

`Decision | Reason | Consequence | Reconsider when`

Example:

`Use SQLite locally | Durable transactions without another service | One local database file | Deployment requires concurrent writers across instances`

Do not log routine edits, naming choices or the full conversation.

### Judge-evidence mapping in spec

Use official criteria and weights. Mark absent criteria/weights as unknown; label proposed criteria provisional.

| Criterion / official weight | Evidence required | Current proof | Gap / next action |
| --- | --- | --- | --- |
| Technical implementation / unknown | Core mechanism executes correctly | Test result and execution trace | Verify API-failure handling |
| Impact / unknown | Improvement over simplest baseline | Same-task comparison | Measure manual baseline |
| Usability / unknown | User completes primary task | Browser walkthrough | Verify invalid-input recovery |

- Acceptance cases define required behavior.
- Tests check that behavior.
- The judge mapping links criteria to proof.
- Do not invent numerical self-scores.
- Update proof/gaps when checks pass or fail, requirements change, or scope changes.
- Review the mapping before choosing additional features and before the final rehearsal.

### Additional-file rules

Create a separate file only when a specific reader or update cycle needs it and the combined file causes retrieval, ownership or editing failures.

| Additional file | Creation trigger |
| --- | --- |
| `docs/architecture.md` | Component contracts are repeatedly misunderstood or independently maintained |
| `docs/acceptance.md` | Acceptance cases require independent maintenance/review |
| `docs/decisions.md` | Consequential decisions are buried or repeatedly reopened |
| `docs/resources.md` | Multiple actively used references need version/commit/file navigation |
| `docs/JUDGE_SCORECARD.md` | Judge mapping needs independent use during prioritization or presentation preparation |

When splitting, move the authoritative section and replace it with a link. Do not retain two editable copies. Do not create empty placeholder files.

### Documentation stop rule

Before adding content, identify the specific error it prevents or information the next agent cannot recover cheaply.

Stop documenting when a fresh agent can:

1. Identify the objective and constraints.
2. Run the project.
3. Verify required outcomes.
4. Identify the current failure/blocker.
5. Execute the next action without reconstructing the conversation.

Use a fresh session or agent to check this when available. If the handoff fails, add the missing information only. Do not claim this check passed unless it was executed.

Do not update prose after every code edit. Stop documentation work that displaces implementation or verification without resolving a demonstrated coordination failure.

## 4. Resource adoption rules

The resources below are research leads. Runtime compatibility on the user's laptop is unverified. Verify current contents before using a path or command.

Before incorporating code:

1. Check competition rules permit reuse.
2. Inspect the repository license and attribution requirements.
3. Pin the selected commit or package version.
4. Check installed API signatures and matching documentation.
5. Execute the base validation gate.
6. Record adopted components and local changes in README.

Competition placement, repository popularity and README claims do not establish task accuracy. Verify organizer sources before citing awards. Do not describe announced 2027 competitions as completed results.

## 5. Priority contemporary project references

| Resource | Mechanism to inspect | Files to locate | Adoption rule |
| --- | --- | --- | --- |
| [Blackbox](https://github.com/alejandro-publius/blackbox-datahub) | Evidence-gated data incident investigation/repair; evaluation and judge proof | `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE.md`, `docs/JUDGE_SCORECARD.md`, `docs/DEMO_SCRIPT.md`, `examples/sample-incident/`, `evals/`, `tests/` | Primary engineering/submission reference. Fork only for a matching operations/data problem. Verify credential-free checks separately from the full DataHub/model workflow. |
| [Aisle](https://github.com/ergjus/aisle) | Shared human/agent actions; constraints; pinned choices; undo; minimal-change repair | `src/actions.ts`, `src/store.ts`, `src/constraints.ts`, `src/solver.ts`, `src/webmcp/tools.ts`, `src/webmcp/adapter.ts` | Application reference for allocation/scheduling. Validate browser/client compatibility before adopting WebMCP. |
| [Sach Batao](https://github.com/codewithfourtix/sachbatao) | Urdu scam-verification workflow; knowledge/prompt separation; classifier evaluation | `scam_patterns.json`, `system_prompt.txt`, `src/`, `tests/`, Docker configuration | Pakistan/language-accessibility reference. Test core classification separately from WhatsApp/media integration. |
| [Interpretable AutoResearch](https://github.com/BarishNamazov/interpretable-autoresearch) | Baseline → predicted improvement → change → measurement → keep/discard | `performance-engineering/`, `program.md`, `bench_e2e.py`, experiment records | Coding-agent experimentation reference. Reuse license is unresolved; establish permission before copying code. |
| [Mulder](https://github.com/calebevans/mulder) | Evidence identifiers; typed tool boundaries; phase completion; alternative-explanation checks | `docs/`, `src/mulder/`, `tests/`, example reports | Verification reference. Do not import forensic infrastructure into an unrelated application. |
| [Alza](https://github.com/Elioz404/Alza) | Agent-editable geometry and spatial constraints | Application actions, geometry validation, WebMCP tools | Conditional base for spatial/layout briefs. |

Competition sources for verification:

- Blackbox: [DataHub 2026 results](https://datahub.com/blog/meet-the-winners-of-build-with-datahub-the-agent-hackathon/).
- Aisle/Alza: [WebMCP Challenge 2026 results](https://webmcp.devpost.com/updates/46049-meet-the-winners).
- Sach Batao: [competition submission](https://devpost.com/software/sach-batao).
- Mulder: [SANS Find Evil! 2026 results](https://www.sans.org/press/announcements/sans-names-the-five-winners-of-find-evil-2026).
- Interpretable AutoResearch: [Claude Builders at MIT](https://www.claudeatmit.com/).

## 6. Bases selected by task

| Task | Resource | Inspect / verify |
| --- | --- | --- |
| Full-stack Gemini research with search/citations | [Gemini Fullstack LangGraph Quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart) | React/Vite frontend, Python backend, `backend/src/agent/graph.py`. Verify model IDs, credentials and live search. |
| Routing, business tools and human review | [Agents From Scratch](https://github.com/langchain-ai/agents-from-scratch) | `src/email_assistant/`, `notebooks/evaluation.ipynb`, `tests/`. Mock email/calendar success does not prove Gmail integration. |
| Minimal Python/LangGraph application | [New LangGraph Project](https://github.com/langchain-ai/new-langgraph-project) + [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) | Verify the LangGraph server and `messages` state contract. An arbitrary FastAPI endpoint is insufficient. |
| Dataset exploration and visualization | [Data Formulator](https://github.com/microsoft/data-formulator) | Match source/docs/package version. Prefer running for exploration or borrowing one mechanism over an unnecessary whole-app fork. |
| Typed document extraction and processing | [ExtractThinker](https://github.com/enoch3712/ExtractThinker) | Contracts, loaders, examples, tests; compare checkout with published release. Validate extracted values against source documents. |
| TypeScript model calls, streaming and tools | [Vercel AI SDK](https://ai-sdk.dev/docs/introduction) | [Agent setup](https://ai-sdk.dev/docs/getting-started/coding-agents); installed package docs/signatures. Select instead of LangGraph unless integration has a concrete benefit. |
| Closely matched text-to-SQL task | [Mastra Text-to-SQL](https://github.com/mastra-ai/template-text-to-sql) | Schema access, query execution, permissions, seeded data and license. Budget custom UI work separately from Studio. |
| Closely matched PDF Q&A task | [Mastra Chat with PDF](https://github.com/mastra-ai/template-chat-with-pdf) | Indexing, retrieval, page citations, storage, license and custom UI integration. |

Conditional components:

- [Docling](https://github.com/docling-project/docling): document layout/OCR; pretest model downloads and extraction.
- [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html): valid splits, pipelines and leakage prevention.
- [Pydantic AI](https://ai.pydantic.dev/): Python structured extraction/tool application when it reduces implementation work.

Avoid overlapping agent frameworks, broad skill bundles, enterprise generators and long-term-memory infrastructure without a required capability that the current implementation lacks.

## 7. Coding-agent support

| Resource | Use | Boundary |
| --- | --- | --- |
| [LangChain Skills](https://github.com/langchain-ai/langchain-skills) | Framework selection, dependencies and graph fundamentals | Select relevant skills only. Add persistence/human review when required. Verify current skill names and installation. |
| [Context7](https://github.com/upstash/context7) | Retrieve documentation for the active API question | Inspect lockfile and installed signatures first. Do not upgrade to match a newer example. |
| [Playwright CLI](https://github.com/microsoft/playwright-cli) | Exercise UI behavior and inspect visible results | Prove browser setup before relying on it. |
| [frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Build the primary workflow interface | Prioritize readable evidence and clear loading/error states. |
| [web-design-guidelines](https://github.com/vercel-labs/agent-skills) | Review interactions, accessibility and forms | Review actual implementation and visible behavior. |
| [Promptfoo](https://www.promptfoo.dev/docs/getting-started/) | Evaluate central LLM behavior | Use ordinary tests/task metrics when sufficient. |

Retrieve specific files for the current question. Keep the full resource catalog out of startup instructions.

## 8. Architecture and interface selection

- Use models for ambiguous input interpretation and action proposals.
- Enforce permissions, calculations, quantities, constraints and state transitions in deterministic code.
- Set explicit limits for model/tool loops, retries, timeouts and spend.
- Distinguish proposed actions, tool observations and committed state.
- Add approval where the workflow requires it; expose inspectable results.

| Interface | Connection | Select when |
| --- | --- | --- |
| Ordinary tool/function calling | Model requests an operation implemented by the application | Internal integration requires no separate protocol |
| MCP | Client connects to a local/remote server exposing tools/resources | Agents need service/API/data integrations independent of a live webpage |
| WebMCP | Live webpage advertises structured operations through browser-mediated APIs | Human and agent must manipulate the same active page/draft |

WebMCP is MCP-inspired, not an automatically compatible MCP transport. A compatible browser/client or bridge is required.

For a shared workspace, route human controls and agent tools through the same validated application actions. Implement authorization, approval, undo and validation explicitly. Backend MCP can access draft state if the application exposes it; draft access is an architectural choice.

References: [WebMCP proposal](https://github.com/webmachinelearning/webmcp), [Chrome comparison](https://developer.chrome.com/docs/ai/webmcp/compare-mcp), [MCP architecture](https://modelcontextprotocol.io/docs/learn/architecture).

## 9. Evaluation and judge evidence

Keep labeled expectations separate from implementation. Do not change expected outcomes to conceal a failure. Correct invalid tests with an explicit reason.

Cover normal input, missing information, contradictions, invalid actions, tool/API failure and out-of-scope requests. For an LLM-centered task, start with 10–20 labeled cases when the sprint allows; coverage of required behavior takes priority over the count.

| Claim | Evidence |
| --- | --- |
| Works | Unseen input completes the task; resulting state/artifact inspected |
| Improves performance | Baseline/final system evaluated on the same cases and metric |
| Saves effort | Measured manual/assisted steps or time on the same task |
| Efficient | Recorded latency, call count and approximate cost |
| Handles uncertainty | Missing/contradictory input and failures produce expected behavior |
| Technical contribution | Trace from input through model/tools and validation to final state |

For consequential claims, execute a check designed to disprove them and record the check/result. Compilation, HTTP status and fluent text alone are insufficient.

Verify the browser flow for successful input, invalid input, dependency failure, loading/empty/error states and restart. Inspect visible output and persisted state where applicable.

Present: problem/baseline → live task → measured result → mechanism → limitation. Follow the organizer's time limit. Label recorded fallbacks. Preserve setup, pins, attribution, sample inputs and submitted artifacts.

## 10. Short shared instruction body

Place the following rules in AGENTS.md, adapting commands to the actual project:

```text
Read docs/spec.md and docs/state.md. Use README.md for commands and architecture.
Build the smallest complete workflow satisfying the official brief.
Use the existing stack and lockfile. Identify the required capability before adding a dependency.
Retrieve documentation for the active implementation question and installed version.
Complete one input-to-output slice before expanding scope.
Keep constraints, calculations, permissions and state transitions deterministic.
Bound loops, retries, timeouts and external calls.
Distinguish model proposals, tool evidence and committed outcomes.
Verify actual task completion and required failure behavior.
For UI changes, exercise the real browser flow and inspect visible output.
Report executed commands, results and unresolved failures.
Update only the authoritative document affected by a changed contract, decision or verified status.
Use the judge-evidence mapping to identify unproven criteria.
Preserve attribution and submitted artifacts.
```

## 11. Study references

| Reading | Decision it supports |
| --- | --- |
| [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph) | Separate model reasoning, data access, deterministic actions and review |
| [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | Choose workflow/autonomy; justify additional agents |
| [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Select startup context versus retrieved context |
| [Demystifying Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Measure task outcomes independently of agent narratives |
| [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Coordinate implementation and evaluation |
| [HETIC 2026–2027 specification](https://ai-agents-founders-hetic-26.devpost.com/) | Compare demonstration/checkpoint/disclosure requirements; do not apply them as NaSCon rules |
