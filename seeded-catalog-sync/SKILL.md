---
name: seeded-catalog-sync
description: "Keep static content catalogs, seed scripts, and API reads aligned across multiple sources. Use when static content catalogs, seed scripts, and API reads must stay aligned."
---

# Seeded Catalog Sync

Use this workflow when curated content is stored in files but served through a seeded database or API.

## Map The Source Of Truth

1. Locate the base content files.
2. Locate any aggregated module that layers additional records on top.
3. Locate the server seed path, runtime routes, and tests that import the catalog.
4. Decide which module is the effective runtime source of truth.

## Sync Rules

- Point UI, tests, and seed code at the same effective catalog.
- If content is layered across files, prefer importing the aggregated module in the seed path.
- Keep IDs unique across base and additive layers.
- Do not leave the UI reading one file while the server seeds another.

## Seed Strategy

1. Keep the seed idempotent with `onConflictDoNothing` or equivalent upsert behavior.
2. Backfill missing rows when current DB count is less than catalog length.
3. Do not seed only on `count === 0` if new records need to appear in existing local databases.
4. Avoid destructive rewrites unless the user explicitly asks to reset seeded data.

## Validation

1. Compare expected catalog length to what the DB or API returns.
2. Run `npm.cmd run test`.
3. Run `npm.cmd run check`.
4. Verify that list and detail routes resolve records from the same dataset the UI imports in tests.
