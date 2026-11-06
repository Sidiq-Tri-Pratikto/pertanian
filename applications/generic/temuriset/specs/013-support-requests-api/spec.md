# Feature Specification: Support requests and project budgets

**Feature Branch**: `013-support-requests-api`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M3 Needs and funding
**Depends on**: 009
**Size**: M
**Covers**: FR06, AC16, AC17, AC18
**Flips**: none

## User Scenarios & Testing

### User Story 1 - State what support is needed and at what cost (Priority: P1)

An invention can have several support requests for distinct outcomes. Each names its invention version, support forms, relationship form, scope, months, region, partial and non-cash acceptance, and an optional versioned project budget.

**Why this priority**: FR06; matching and pitches use one specific request.

**Independent Test**: Create the F01 request and budget through the API.

**Acceptance Scenarios**:

1. **Given** F01, **When** a request "Validasi prototipe enam bulan" with budget USD 20000–30000 for "biaya pilot enam bulan" over six months is saved, **Then** amounts are stored as decimals and returned as strings `"20000.0000"`.
2. **Given** a budget with min `-1` or max below min, **When** saved, **Then** `VALIDATION_FAILED` names the field in Indonesian and the request keeps its previous values (AC16).
3. **Given** a non-cash validation request with unknown money, **When** saved and read, **Then** min and max are `null` with reason `not_determined`, never zero (AC17).
4. **Given** a zero amount on a financial scope, **When** saved, **Then** it is refused unless the request is explicitly non-financial.
5. **Given** one monthly and one six-month amount in the same currency, **When** compatibility is asked, **Then** no direct comparison is produced without a confirmed equivalent basis (AC18; the comparison lives in 019, the basis fields here).

### User Story 2 - Lines add up or explain why not (Priority: P2)

**Acceptance Scenarios**:

1. **Given** budget lines, **When** saved, **Then** each line total is quantity × unit cost in decimal, and a range that differs from the lines' sum requires an explanation such as "cakupan sebagian".

### Edge Cases

- Activating a request needs its support forms and outcome; a draft can be incomplete.
- Editing an active request creates a new version; submissions keep theirs.
- Status moves `DRAFT` → `ACTIVE` ↔ `PAUSED` → `CLOSED`, plus `EXPIRED` at a deadline.

## Requirements

### Functional Requirements

- **FR-001**: Support forms and relationship form (`PROJECT`, `LICENSE`) MUST be stored separately and never inferred from each other.
- **FR-002**: Budgets MUST carry min, max, currency, period, scope, estimate date and assumptions, versioned with the request.
- **FR-003**: Validation MUST enforce min ≥ 0 and max ≥ min in the service and with database checks.
- **FR-004**: Changes MUST emit `support_request.changed` for the search projection and matching cache.

### Key Entities

- **SupportRequest**, **ProjectBudget**, **ProjectBudgetLine**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC16–AC17 pass; money never passes through float anywhere in the code path (a test with `"0.1"` + `"0.2"` lines asserts `"0.3000"`).
