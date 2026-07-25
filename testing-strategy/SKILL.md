---
name: "testing-strategy"
description: "Decide what to test, at which level, and how much. Use when the user asks what tests to write for a feature, whether coverage is adequate, why the test suite is slow or flaky, how to test something hard (time, randomness, external APIs), or to review an existing suite. Trigger on test strategy, what should I test, unit vs integration, flaky test, mocking, coverage, or TDD."
---

# Testing Strategy

What to test, at which level, and when to stop. Framework-agnostic; complements `react-query-test-harness-fixer` (which fixes specific React/Vitest failures).

## Not in scope

Load/performance testing, formal verification, and CI pipeline configuration (see `gh-fix-ci` for failing checks). This skill decides and structures; it doesn't debug one specific red test unless asked.

## The only question that matters

A test earns its keep by failing when the code is wrong and staying green when the code is right but different. Judge every test and every layer by that: tests that break on refactors (asserting internals, mock call counts, snapshot noise) are negative-value; tests that can't fail (tautologies, testing the mock) are dead weight.

## Choosing the level

Test at the lowest level that can actually catch the bug.

- **Unit** (pure logic, no I/O): business rules, calculations, parsers, edge cases. Fast, deterministic, most of the count lives here.
- **Integration** (real collaborators, real database when feasible): repository/query code against a real or containerized DB, route handlers through the framework, serialization boundaries. This layer catches what unit tests structurally can't: SQL that doesn't match the schema, wiring mistakes, contract drift.
- **End-to-end** (whole system through the UI or public API): a handful of critical paths only (sign up, pay, the core loop). Expensive and flaky-prone; every E2E test must justify why a lower level couldn't catch its bug.

Distribution follows from that rule, not from a dogmatic pyramid ratio. CRUD-heavy apps need proportionally more integration tests; algorithm-heavy code more unit tests.

## What to test for a new feature

1. The happy path through the public interface.
2. Each boundary: empty input, max size, zero, one, many, unicode, already-exists, not-found, unauthorized.
3. Each error the code deliberately handles (and that the error surfaces correctly, not just "doesn't crash").
4. Anything that has ever broken in this area before: regressions get a named test.
5. Skip: getters, framework behavior, third-party libraries, private functions (test through the public surface; wanting to test a private function means it wants to be its own module).

## Test doubles: rules of engagement

- Mock at ownership boundaries you don't control (HTTP APIs, clock, randomness, payment providers), not between your own classes.
- Prefer fakes (in-memory implementation) over mocks with scripted expectations; assert on outcomes, not on which methods got called.
- Never mock what you're testing, and never assert "function X was called with Y" when you could assert the observable result.
- Time and randomness are injected dependencies (clock param, seeded RNG). A `sleep` in a test is a bug.
- Contract drift check: anything mocked in many tests needs at least one integration test against the real thing.

## Flakiness triage

Flaky tests are ordered by root-cause frequency: (1) shared mutable state between tests (fix: isolate, reset DB per test, no test order dependence), (2) time (fix: fake clock), (3) async race (fix: await the actual condition, never a fixed timeout), (4) external network (fix: fake it; real-network tests run in a separate, non-blocking suite). Quarantine a flake the day it appears (skip with a ticket) rather than training the team to re-run red builds.

## Coverage

Use coverage to find untested regions, never as a target. 100% on trivial code and 60% on the money path is worse than the reverse. Diff coverage (new code in this PR is covered) is the useful gate; repo-wide percentage is vanity. Mutation testing (Stryker, mutmut) is the honest audit when it matters: it tells you whether tests would notice the code being wrong.

## Reviewing an existing suite

1. Run it twice, then in random order; note flakes and order dependence.
2. Time it: name the 10 slowest tests, check they earn their runtime.
3. Sample 10 tests: for each, what bug would it catch? Delete or rewrite the ones with no answer.
4. Grep for `sleep`, retries in tests, and skipped/commented tests with no ticket.
5. Check the critical user paths have any test at all; gaps there outrank everything above.
