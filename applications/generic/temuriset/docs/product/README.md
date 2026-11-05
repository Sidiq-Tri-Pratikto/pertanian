# Product sources

TemuRiset's product documents live under `docs/generic/temuriset/` at the pertanian repository root. This project links them instead of copying them, so there is one copy of each.

| Document | Authority |
|---|---|
| [PRD EN v1.1](../../../../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md) | Canonical for behaviour: FR01–FR24, AC01–AC72, domain, API, states, fixtures |
| [PRD ID v1.1](../../../../../docs/generic/temuriset/01_PRD_TemuRiset_Generic_ID.md) | Same requirements in Indonesian; resolve a discrepancy against the English edition |
| [Application handoff](../../../../../docs/generic/temuriset/02_Claude_Design_TemuRiset_EN.md) | Screens S01–S18, journeys J01–J05, copy, fixtures F01–F06, UX-01–UX-24 |
| [Design system](../../../../../docs/generic/temuriset/design-system/project/README.md) | TemuRiset Design System 1.0.0-draft, `window.TR`, tokens and component contracts |
| [Prototype handoff](../../../../../docs/generic/temuriset/app-prototype/DESIGN_HANDOFF.md) | Playable front-end simulation, route map, mock ledger and validation evidence |
| [Prototype domain](../../../../../docs/generic/temuriset/app-prototype/project/domain.js) | Oracle source for matching, scheduling and consent behaviour; never production code |
| [Prototype oracles](../../../../../docs/generic/temuriset/app-prototype/tools/domain.test.mjs) | 39 service-level checks to port into API tests |

Order of authority: the constitution, then `docs/roadmap/architecture.md` for how the system is built, then the PRD for what it does, then the handoff for screens and copy. The prototype is evidence of intended behaviour, not a contract: where it simplified (see section 12 of its handoff), the PRD wins.
