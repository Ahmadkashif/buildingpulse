# Testing — The Codebase Is Tests

Tests are not a safety net for implementation. Tests **are** the specification. The implementation exists to satisfy them.

## Core framing

- **Tests describe the system.** Reading the test suite must tell you what the system is and how it behaves, without reading implementation.
- **Every module has multiple tests, one per pillar.** A pillar is one true functionality the system guarantees. No pillar, no test. No test, no pillar.
- **Untested behavior does not exist.** If there's no test asserting it, the system does not promise it, and the implementation is free to remove it.

## What counts as a good test

All seven must hold. Any one missing, the test doesn't land.

1. **Names a behavior, not a function.** `rejects_year_built_before_1800`, not `test_predict`. The name reads as a sentence describing what the system does.
2. **One pillar per test.** If the name needs "and", split it.
3. **Asserts the contract, not the implementation.** Rewriting internals must not break the test. No asserts on private state. No mocks of your own code. No checks on *how* the result was produced — only *what* the result is.
4. **Failure paired with success.** Every happy path has its matching error path. Boundary values exact: min, min−1, max, max+1, empty, zero where relevant.
5. **Deterministic.** No wall clock, no randomness, no network, no ordering dependency. Time, IDs, randomness, and I/O are injected at the boundary so the test controls them.
6. **Fails for the right reason.** Breaking the behavior on purpose produces a failure message that points to what broke. Vague failure = wrong assertion.
7. **Adds information.** Deleting the test must shrink what the suite tells you about the system. Duplicates are dead weight.

## Workflow

1. **Design the pillars.** Before any test file exists, list the module's pillars — what behaviors the system must guarantee.
2. **Write tests red.** One test per pillar. Show the failing output.
3. **Implementation lands separately.** Implementation is a response to red tests. Tests and implementation never ship in the same commit.
4. **Tests go green.** Green means the system satisfies its pillars. Not "done."
5. **Mutation test.** CI introduces small bugs to the implementation; if tests don't catch them, the test was weak, not the implementation.

## What stops bad tests (ranked by actual signal)

1. **Mutation testing in CI** (Stryker / mutmut / cosmic-ray). The only objective signal for test quality. Coverage is a floor; mutation score is the measure.
2. **Rubric review.** Every test PR is reviewed against the seven rules above. Violations are rejected.
3. **Red-before-green in git history.** Tests commit separately and first. Implementation commits reference the test commit. Same-commit test+impl is disallowed.
4. **Shallow lint rules.** `vitest/expect-expect`, `no-disabled-tests`, `no-focused-tests`, pytest equivalents. Catch mechanical sloppiness (empty tests, `.only`, `.skip` in committed code) — not design flaws.

## Honest edge

Visual polish — "looks right" is not a pillar and does not get a test. For UI, pillars are structural (renders expected nodes), behavioral (click submits form), accessible (aria labels, keyboard nav), and integration (form → loading → result wires end-to-end). Spacing, color, animation feel remain human-reviewed. The test suite is not dishonest about what it captures.

## Rules for agents

- You write tests. You do not write implementation. Ever.
- Types, schemas, and interfaces are specifications, not implementation — you may write them alongside tests.
- Function bodies, class methods with logic, route handlers, component internals — all implementation. The human writes these.
- If a test requires implementation to run green, that is the human's work. Your job is complete when the pillar is expressed as a test and the test is red for the right reason.
