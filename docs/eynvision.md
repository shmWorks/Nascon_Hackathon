# Eynvision: sponsor fit and MVP priorities

Researched 2026-10-17, PKT. Read before choosing differentiators, evaluating sponsor fit, or preparing the demo. Requirements and acceptance cases: [spec.md](spec.md). Organizer wording: [brief.md](brief.md). Source limitations: [provenance](eynvision.provenance.md).

## Decision

Build the required personal morning paper as a usable product with traceable sources, reliable editions and demonstrable learning. Eynvision's published product patterns support that direction; they do not establish private judging preferences. A paper for an AI product builder is a useful demonstration persona, not evidence that Eynvision wants an internal news tool.

## Evidence and implications

**Evidence labels:** Published = observed first-party statement, not independently tested functionality or performance. Inference = our interpretation. Proposal = implementation or demonstration advice, pending design validation.

| Finding | Evidence | Consequence for this project |
| --- | --- | --- |
| Eynvision presents itself as an applied AI studio delivering operational automation and complete products. **Published.** | Its [website](https://www.eynvision.com/) and [company profile](https://www.linkedin.com/company/eynvision) describe its positioning. These are one interested source, not two independent confirmations. | **Inference:** prioritize a working reader journey and concrete value over architecture spectacle. |
| Its portfolio includes document/report workflows and consumer software, rather than one mandatory industry. **Published.** | [Case-study index](https://www.eynvision.com/case-studies) lists property, freight, commercial work, Business Case Guru, Bezeen and Ascent AI. | **Inference:** retain the consumer morning-paper brief; enterprise branding and property integrations are unnecessary. |
| Source traceability is advertised on Eynvision and a separate product site. **Published.** | [Leo](https://www.eynvision.com/solutions/leo) describes file/page citations. [Business Case Guru](https://www.businesscaseguru.com/bcg-work) describes evidence links, user approval and revision history. Separate ownership/control was not established. | **Proposal:** show original publisher, URL and publication date; derive each summary from retrieved evidence. Make relevance inspectable. |
| Repeated inputs become scheduled, formatted outputs. **Published.** | [Digest](https://www.eynvision.com/solutions/digest) describes scheduled reports and decks from existing records, using customer templates and human review. | **Inference:** the closest transferable pattern is evidence → structured edition → web/PDF, with one saved edition supplying both views. |
| AI cost attribution and enforceable caps are part of its offering. **Published.** | [Watchtower](https://www.eynvision.com/solutions/watchtower) describes per-project attribution, audit records and budget ceilings. | **Proposal:** bound fetch/model work and measure generation latency and usage. A separate monitoring dashboard is unnecessary. |
| Its education materials emphasize delivery discipline. **Published.** | [Eynvision Labs](https://www.eynvisionlabs.com/) describes tickets, branches, review and product launch. Its [public workshop](https://github.com/eynvision/Agentic-Coding-Workshop) contains a runnable example. | **Inference:** reproducible setup, honest limitations and visible completion are stronger evidence than framework names. |

These are recurring product patterns, not measured causes of Eynvision's commercial success. Adoption, reliability, client ROI and source accuracy were not independently tested.

## Event and identity boundaries

- The local organizer brief names Eynvision and its domain. Sponsor/judge status and the complete-MVP quality bar come from the user; no public NaSCon'26 judge roster, official scoring weights or private evaluation standard was verified.
- Hashim Muhammad Nadeem's public judging announcement concerns **Hacktoberfest Islamabad 2026**, a different event. Company identity, team context and excluded numerical claims are documented in the [source ledger](eynvision.provenance.md). No source establishes Eynvision's internal demand for this product.

## Competitive baseline

The brief's fragmented-news problem is a product opportunity, not proof that aggregation or personalization is new. Compare against real substitutes before claiming differentiation.

| Substitute | Documented capability; not tested | Implication |
| --- | --- | --- |
| [Feedly](https://docs.feedly.com/article/523-getting-started-with-feedly) | Source aggregation, AI topic prioritization, deduplication, summaries, mute filters and team newsletters. | Aggregation plus summarization is baseline capability. |
| [Google News](https://support.google.com/googlenews/answer/9005601?hl=en-UM) | Interest/activity personalization, saved topics and multiple perspectives. | A personalized feed alone is insufficient differentiation. |
| Manual reading and a general AI assistant | Local baseline to test: open the same source set, choose relevant items, compile a brief. No comparative performance claim established. | Measure task completion against the same inputs; include source discovery/setup time consistently. |

**Reader-value hypothesis:** a bounded morning edition reduces selection effort and yields useful takeaways. The required newspaper/archive/learning combination is a product proposition, not demonstrated competitive differentiation. Test the first real edition with a target reader; record relevance and useful takeaways. No demand or retention study was conducted. Feature access may depend on plan or region. This comparison covers immediate substitutes, not an exhaustive market census.

## Execution priorities

Apply these as recommendations within R1–R4; they add no official requirements. Existing A1–A10 remain authoritative. Ratify new acceptance expectations in `spec.md` before treating them as gates.

1. **Complete the journey.** Follow the dependency/base validation gate in [state.md](state.md) first. Finish onboarding → real retrieval → saved edition → web/PDF before archive and learning. Completion: A1–A10 have running-product evidence or explicit unverified status. Defer optional analytics, extra integrations and presentation flourishes while core cases lack proof.
2. **Separate evidence, interpretation and state.** Store source identity/dates separately from generated text and profile state. Define a substantive, attributed summary format supported by accessible evidence before choosing sources. Exclude insufficient-evidence items or label them as links only; links alone do not demonstrate complete reading. Completion: inspect source → supported summary → saved web/PDF. Never infer full-article details from an unread title/snippet.
3. **Prove adaptation.** Hold reader/candidates constant, record explicit feedback, then save another edition with a predictable selection or presentation change. Inspect persisted preferences and both editions. Changed scores alone are insufficient; adaptation does not establish improved reader value. Keep ordinary Skip as visibility plus an uninterpreted event; use explicit topic feedback for the demo. Clicks and skips have ambiguous intent.
4. **Preserve edition identity and dates.** Proposed A5/A7 design: retain the committed article set for PDF/history; apply skips as a reading overlay. Ratify that interpretation before implementation. Separately demonstrate today's fresh retrieval, the real generation trigger, and a clearly labeled simulated date rollover. Actual next-day unattended operation cannot be verified before tonight's deadline; record that limitation. A replay proves neither freshness nor scheduler operation.
5. **Exercise failure.** Test unavailable sources, malformed/empty model output and PDF failure. Display truthful partial/unavailable status; keep the last successful edition dated. Completion: no fabricated filler, mislabeled stale edition or endless spinner. Set concrete timeouts/retry/candidate/token limits when selecting the stack.
6. **Measure before promising.** Record observed generation duration, retrieved/selected counts and provider usage. Label estimated cost and its assumptions. Test whether a reader can identify three useful takeaways; present this as a proposed usability measure, not demonstrated retention or an official score.

For public-source ingestion, choose a small tested source set with suitable reuse terms; retain attribution and avoid paywall bypass. Treat fetched text as evidence, not executable instructions. If arbitrary URL fetching is added, restrict destinations and redirects to prevent access to local/private services. Keep keys server-side and profiles isolated. These are delivery safeguards, not evidence of sponsor-specific security requirements.

## Demonstration

Use two contrasting readers, such as an AI product builder and a sports/science reader. Avoid making all content about the sponsor. Suggested five-minute sequence:

| Time | Show |
| --- | --- |
| 0:00–0:40 | Reader goal, short onboarding and persisted preferences. |
| 0:40–1:40 | One edition answering a concrete reader need; one useful takeaway checked against its source. |
| 1:40–2:30 | Original link, PDF download and prior edition. |
| 2:30–3:40 | Contrasting reader; explicit feedback and changed saved editions on controlled candidates. |
| 3:40–5:00 | Architecture and explicit limits; concise failure evidence if time permits. |

Label live generation, prepared editions and simulated dates. Keep detailed failure/usage evidence in the repository if it crowds out reading value. Select the next task from the unproven criteria in `spec.md`.

**Open decisions:** exact rubric/judge identity, source access and reuse, delivery trigger/timezone, empty-source behavior, profile isolation and numerical resource budgets. Resolve implementation-dependent items during the first runnable slice. A future sponsor conversation could establish internal use; public portfolio research cannot.
