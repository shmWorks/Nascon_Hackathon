# AI Hackathon: Coding-Agent Handoff

Prepared: 17 October 2026. Audience: Codex and Claude Code working with Sheraz Malik.

## 1. Read first

Build the smallest complete solution whose value, correctness and technical contribution a judge can verify quickly. Use this document as a selected reference map, not a requirement to install every resource.

This handoff summarizes the supplied conversation. The earlier assistant reported inspecting repositories and organizer announcements, but those checks were not independently reproduced while preparing this file. Award claims, archive dates, licenses, repository paths, model identifiers and installation commands must be rechecked before relying on them. None of the recommended projects was demonstrated running on the user's laptop. A repository README or award is not proof of runtime compatibility or general task accuracy.

2026 competition projects are prioritized because the user explicitly requested contemporary, competition-relevant examples. Older foundations remain useful when they reduce implementation risk. Do not invent completed 2027 winners or treat announced event requirements as NaSCon rules.

## 2. User, constraints and missing inputs

- Sheraz has React/TypeScript, Python, SQL, Gemini and LangGraph experience; prefer familiar tools.
- The conversation planned around a solo 12-hour sprint. Confirm actual team size, permitted reuse, schedule, deadline, rubric, required outputs and available credentials from the official brief.
- The problem/theme is not supplied here. Do not preselect a domain or architecture from illustrative examples.
- Earlier guidance used 21:00 PKT on 17 October 2026 as a conservative build boundary, not a verified organizer deadline. Replace it with the official deadline; do not assume presentation-day gaps allow development.
- Communicate concisely. Explain consequential tradeoffs and execute within agreed scope. Keep claims measurable and source-linked.

## 3. First implementation sequence

1. Capture exact brief, rubric, submission requirements, permitted reuse and unresolved assumptions.
2. Define one primary user task, simplest baseline and observable acceptance cases.
3. Test the riskiest dependency: real model call, data access, document extraction or external integration.
4. Choose one application base. Use other repositories only as references for specific mechanisms.
5. Complete a vertical slice: real input → model/tool execution → validated action or analysis → visible, inspectable result.
6. Evaluate ordinary and failure cases; improve the demonstrated bottleneck.
7. Freeze architecture, rehearse, submit early and preserve the submitted version.

Suggested allocation: first hour for scope and risk; hours 1–3 baseline; 3–6 core improvement; 6–8 evaluation; 8–10 UI and reproducibility; 10–11 rehearsal; final hour submission. This is a planning allocation, not an event schedule.

Base acceptance gate: fresh terminal → installation/start → real input → real model/tool execution → visible result → controlled failure → restart. Timebox initial base validation to 45 minutes; if it fails, downgrade it to reference material and use a smaller working base.

## 4. Priority 2026 project references

The competition descriptions below were reported in the earlier conversation and need source verification before public attribution. File paths are navigation leads; confirm they exist at the chosen commit.

| Priority / resource | Role and specific material | Adoption boundary |
| --- | --- | --- |
| 1. [Blackbox](https://github.com/alejandro-publius/blackbox-datahub) | Data-incident investigation, evidence-gated repair and judge evidence. Inspect `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE.md`, `docs/JUDGE_SCORECARD.md`, `docs/DEMO_SCRIPT.md`, `examples/sample-incident/`, `evals/`, `tests/`. | Best engineering/submission reference. Fork for a matching operations/data problem. Earlier report: Apache-2.0, credential-free `make judge-check`; full workflow needs Anthropic and DataHub. Authored incident examples do not prove general accuracy. |
| 2. [Aisle](https://github.com/ergjus/aisle) | Shared human–agent workspace, deterministic constraints, pinned choices, undo and minimal-change repair. Inspect `src/actions.ts`, `src/store.ts`, `src/constraints.ts`, `src/solver.ts`, `src/webmcp/tools.ts`, `src/webmcp/adapter.ts`. | Strong product architecture for allocation/scheduling. Earlier report: MIT. WebMCP requires a compatible browser/client or bridge; ordinary coding-agent sessions do not automatically connect. |
| 3. [Sach Batao](https://github.com/codewithfourtix/sachbatao) | Pakistan/Urdu scam-verification workflow. Inspect `scam_patterns.json`, `system_prompt.txt`, `src/`, `tests/`, Docker setup. | Local-language and narrow-task reference. Earlier report: MIT, WhatsApp/media integration and 24 authored evaluation cases. Separate classifier quality from adapter reliability. |
| 4. [Interpretable AutoResearch](https://github.com/BarishNamazov/interpretable-autoresearch) | Coding-agent experiment discipline. Inspect `performance-engineering/`, `program.md`, `bench_e2e.py`, event logs and correctness contract. | Borrow baseline → prediction → change → measurement → keep/discard reasoning. Repository-wide reuse license was not established; do not assume copying rights. |
| 5. [Mulder](https://github.com/calebevans/mulder) | Evidence identifiers, typed tool boundaries, completion gates and alternative-explanation checks. Inspect `docs/`, `src/mulder/`, `tests/`, example reports. | Verification reference; forensic infrastructure is too specialized for an unrelated sprint. Earlier report: Apache-2.0. |
| Conditional. [Alza](https://github.com/Elioz404/Alza) | Agent-editable floor plans, geometry and spatial constraints. | Use only for spatial/visual briefs. Earlier report: MIT; WebMCP compatibility still needs validation. |

Competition attribution leads:

- Blackbox: reported Grand Prize, DataHub Agent Hackathon 2026. [Organizer results](https://datahub.com/blog/meet-the-winners-of-build-with-datahub-the-agent-hackathon/).
- Aisle and Alza: reported WebMCP Challenge 2026 winners. [Organizer results](https://webmcp.devpost.com/updates/46049-meet-the-winners).
- Sach Batao: reported First Prize, AI for Civic Innovation Hackathon 2026, Pakistan. [Submission](https://devpost.com/software/sach-batao).
- Mulder: reported First Place, SANS Find Evil! 2026. [Organizer announcement](https://www.sans.org/press/announcements/sans-names-the-five-winners-of-find-evil-2026).
- Interpretable AutoResearch: reported second place, Claude Builders @ MIT Spring Sprint, May 2026. [Organizer site](https://www.claudeatmit.com/).

## 5. Practical fallback bases

| Brief / need | Resource | Decision |
| --- | --- | --- |
| Full-stack Gemini research application | [Google Gemini Fullstack LangGraph Quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart) | React/Vite + Python/LangGraph, search, citations and bounded loops. Inspect `backend/src/agent/graph.py`. Verify current model IDs and a live request; prior discussion flagged deprecated defaults. Start locally. |
| Business workflow and human review | [Agents From Scratch](https://github.com/langchain-ai/agents-from-scratch) | Email routing, tools, review and evaluation. Inspect `src/email_assistant/`, `notebooks/evaluation.ipynb`, `tests/`. Mock tools do not establish Gmail integration. |
| Minimal LangGraph base | [New LangGraph Project](https://github.com/langchain-ai/new-langgraph-project) + [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) | Small skeleton plus interface. Chat UI expects the LangGraph server contract and `messages` state, not an arbitrary FastAPI endpoint. |
| Dataset exploration | [Microsoft Data Formulator](https://github.com/microsoft/data-formulator) | Run as an exploration tool or borrow one mechanism; whole-app adoption has substantial scope. Match checkout, installed version and docs. |
| Typed document workflows | [ExtractThinker](https://github.com/enoch3712/ExtractThinker) | Document → fields → deterministic validation → action. Inspect contracts, loaders, examples and tests. Schema validity does not prove factual extraction accuracy. Check differences between main and published release. |
| Simple TypeScript model/tool application | [Vercel AI SDK](https://ai-sdk.dev/docs/introduction) | Alternative to Python/LangGraph when Python adds little. [Agent setup](https://ai-sdk.dev/docs/getting-started/coding-agents). Check locally bundled docs for the installed version. |
| Closely matched SQL/PDF task | [Mastra SQL](https://github.com/mastra-ai/template-text-to-sql), [Mastra PDF](https://github.com/mastra-ai/template-chat-with-pdf) | Conditional TypeScript bases. Studio is not a finished custom product UI. Confirm licenses; enforce database permissions and query boundaries. |

Other conditional tools: [Docling](https://github.com/docling-project/docling) for layout/OCR; [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) for valid preprocessing/splits; [Pydantic AI](https://ai.pydantic.dev/) for Python structured extraction when it materially simplifies the implementation.

Vanna and Open Deep Research were described as archived in the prior conversation; recheck status rather than choosing them by reputation. Do not introduce overlapping frameworks, enterprise scaffolds or memory infrastructure without a demonstrated need.

## 6. Coding-agent context and tools

Keep initial context short; retrieve specific files/docs for the active implementation question.

- [LangChain Skills](https://github.com/langchain-ai/langchain-skills): select `ecosystem-primer`, `langchain-dependencies`, `langgraph-fundamentals`; add persistence and human-review skills only when the task needs them. Verify current skill names/install instructions.
- [Context7](https://github.com/upstash/context7): retrieve version-matching API documentation. Inspect lockfile and installed signatures first; do not upgrade simply to fit a newer example.
- [Playwright CLI](https://github.com/microsoft/playwright-cli): exercise the actual application and inspect visible results. Prove the browser setup before depending on it.
- [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) and [Vercel web-design-guidelines](https://github.com/vercel-labs/agent-skills): optional UI creation/review. Prioritize one workflow, legibility and useful state/error feedback.
- [Promptfoo](https://www.promptfoo.dev/docs/getting-started/): optional outcome evaluation for central LLM behavior. Ordinary tests and task metrics may be sufficient.

Do not blindly execute installation commands from this conversation. Check current upstream instructions, client compatibility, license, dependencies and package version; pin what passes the readiness gate.

## 7. Architecture rules, including MCP and WebMCP

Let the model interpret ambiguous input and propose actions. Let deterministic application code enforce permissions, calculations, quantities, constraints and state transitions. Bound loops, tool calls, retries, timeouts and cost. Distinguish proposed actions, tool observations and persisted outcomes.

| Interface | Meaning | Use when |
| --- | --- | --- |
| Ordinary tool/function call | The model requests a typed operation implemented by your own application. | Internal model-to-application integration; often sufficient. |
| MCP | A client–server protocol exposing tools/resources through local or remote servers. | Connecting agents to services, APIs and data independently of a live webpage. |
| WebMCP | A browser-mediated mechanism for a live page to advertise structured operations. MCP-inspired; not an automatically compatible MCP transport. | Person and agent operate the same active page, including current draft state. |

Shared-workspace pattern: human controls and agent tools call the same validated application actions. This can avoid forcing the agent to infer every click from screenshots/DOM. It does not automatically provide authorization, approval, undo or correctness. Backend MCP can access draft state if explicitly integrated; the boundary is architecture-dependent.

For scheduling, an agent can propose a change to the visible draft while locked appointments remain enforced by application logic. If live page context adds no value, WebMCP may not earn its integration cost.

Authoritative references to verify before implementation: [WebMCP proposal](https://github.com/webmachinelearning/webmcp), [Chrome comparison](https://developer.chrome.com/docs/ai/webmcp/compare-mcp), [MCP architecture](https://modelcontextprotocol.io/docs/learn/architecture).

## 8. Verification and demonstration contract

Keep labeled expected outcomes separate from editable implementation. Do not alter expected answers merely to make tests pass. Use roughly 10–20 cases when practical: normal, missing information, contradictions, invalid actions, tool/API failure and out-of-scope input.

| Claim | Required evidence |
| --- | --- |
| Works | Unseen input completes the actual task; inspect resulting state/artifact. |
| Better | Baseline and final system evaluated on the same cases and metric. |
| Saves effort | Measured manual steps/time against the assisted workflow. |
| Efficient | Recorded latency, calls and approximate cost. |
| Handles uncertainty | Missing/contradictory input and failures produce controlled behavior. |
| Technical contribution | Trace input → model/tool decisions → validation → persisted result. |

For consequential claims, run a check designed to disprove them and report what was checked. Compilation, HTTP 200 and a fluent answer alone do not prove task completion. Authored demos and small test sets do not establish deployment-scale accuracy.

Rehearse: problem/baseline → live task → measured result → mechanism → limitation. Prepare a three-minute version, then follow the actual announced limit. Label recorded fallback demonstrations clearly. Preserve setup instructions, dependency pins, attribution, sample inputs and submitted artifacts.

## 9. Repository context layout

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Short objective, commands, constraints, verification rules and links. |
| `CLAUDE.md` | Import shared instructions using `@AGENTS.md` where supported; verify client loading. |
| `docs/brief.md` | Exact official brief/rubric/deadline/reuse rules; explicit assumptions. |
| `docs/acceptance.md` | Observable success/failure cases and demo sequence. |
| `docs/resources.md` | Chosen base + pinned commit/license; specific reference files and why. |
| `docs/state.md` | Working features, evidence, failed attempts, blockers and next action. |

Suggested shared instruction body:

```text
Read docs/brief.md, docs/acceptance.md and docs/state.md first.
Build the smallest complete solution satisfying the official brief.
Use the existing stack and lockfile. Justify new dependencies.
Retrieve documentation for the active question and installed version.
Implement one vertical slice at a time.
Keep constraints, calculations and state transitions deterministic.
Bound loops, retries, timeouts and external calls.
Distinguish model proposals, tool evidence and persisted outcomes.
Verify observable task completion, including an expected failure.
For UI work, exercise the real browser flow and inspect visible output.
Report commands, results and remaining failures without overstating them.
Update docs/state.md after meaningful changes; preserve attribution.
```

## 10. Short study map

- [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph): divide the task into model reasoning, data access, deterministic actions and human review.
- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents): justify workflow versus autonomy and every additional agent.
- [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): decide what loads at startup and what gets retrieved.
- [Demystifying Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): evaluate actual outcomes independently of agent narratives.
- [Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps): reference for generation/evaluation coordination; verify current page availability.
- [HETIC 2026–2027 competition](https://ai-agents-founders-hetic-26.devpost.com/): previously cited as an announced benchmark for demos, checkpoints, disclosures and limitations, not as completed winning work or NaSCon requirements.

Next executing agent: obtain the official brief, select one matching base, pin it and prove the complete readiness gate before expanding scope.
