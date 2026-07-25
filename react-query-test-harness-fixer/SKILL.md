---
name: react-query-test-harness-fixer
description: "Fix React/Vitest test failures for TanStack React Query components and jsdom side effects. Use when React Query component tests fail under Vitest or jsdom with hangs, act warnings, or side-effect leaks."
---

# React Query Test Harness Fixer

Use this workflow when test setup has fallen behind the app's React Query and browser dependencies.

## Read First

- The failing test file
- The page or component under test
- Shared test setup such as `client/tests/setup.ts`
- Any route or data modules the component depends on

## Workflow

1. Identify every `useQuery`, `useMutation`, and route dependency used by the rendered component.
2. Wrap the render path in a fresh `QueryClientProvider`.
3. Create a new `QueryClient` per helper or per test and set `retry: false` for deterministic failures.
4. Stub network calls at the boundary the component actually uses. Return stable list and detail responses.
5. Recreate routing context with the same router the app uses, such as `memoryLocation` for `wouter`.
6. Wait for async UI with `findBy...` or `waitFor` after the query resolves.
7. Neutralize browser-only side effects.

## Browser API Rules

- Mock `navigator.clipboard` in the test when copy behavior is asserted.
- Put durable browser shims in shared test setup for `matchMedia` and `HTMLCanvasElement.getContext`.
- Mock side-effect libraries such as `canvas-confetti` directly when the animation is not part of the assertion.
- Clear `localStorage` and reset globals after each test.

## Anti-Patterns

- Do not share one `QueryClient` across unrelated tests.
- Do not assert on post-query UI before the fetch promise has resolved.
- Do not leave broad fetch mocks or global state behind between tests.

## Validation

1. Run the targeted test file first.
2. Run `npm.cmd run test`.
3. Run `npm.cmd run check`.
