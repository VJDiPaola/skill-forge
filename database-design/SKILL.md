---
name: "database-design"
description: "Design database schemas, write and review SQL, plan migrations, and diagnose slow queries. Use when the user asks to model a domain in tables, add or change a schema, write a migration, pick indexes, review a query for performance, or choose between SQL and other storage. Trigger on schema design, migration, index, N+1, EXPLAIN, foreign key, or normalize."
---

# Database Design

Schema design, SQL review, migrations, and query performance. Applies to Postgres, MySQL, and SQLite; call out dialect differences when they matter.

## Not in scope

ORM-specific API questions (look up the ORM's docs), NoSQL data modeling, data warehousing/analytics pipeline design, and DBA operations (replication, backups, tuning server config). For app-level security review of queries, see the security skills.

## Schema design ground rules

- Start from the queries, not the entities. List the top 5 reads and writes the app will do, then shape tables so those are cheap.
- Normalize until it hurts, denormalize where a measured read pattern justifies it. Record the justification in a comment or migration note.
- Every table gets: a primary key (prefer surrogate `id` unless a natural key is truly stable), `created_at`, and `updated_at` where rows mutate.
- Foreign keys ON by default. If someone wants them off for "performance," ask for the benchmark.
- Prefer `text` + check constraints over enums in Postgres when values will change; enums need a migration per value.
- Timestamps in UTC (`timestamptz` in Postgres). Convert at the edge.
- Money as integer cents or `numeric`, never float.
- Soft deletes (`deleted_at`) only when the product needs undo or audit; they complicate every query and unique constraint. Partial unique indexes (`WHERE deleted_at IS NULL`) fix the constraint side.

## Migration rules

- Migrations are append-only and each one must be runnable against production data, not just an empty dev database.
- Split risky changes into deploy-safe steps: add nullable column, backfill in batches, add constraint `NOT VALID` then `VALIDATE`, then flip application code. Never `ALTER TABLE ... SET NOT NULL` on a large hot table in one step.
- Adding an index on a big table: `CREATE INDEX CONCURRENTLY` (Postgres) outside a transaction.
- Renames are two migrations plus an app deploy in between (add new, dual-write or view, drop old). A bare `RENAME COLUMN` breaks the running old code during deploy.
- Every migration states its rollback. If it's irreversible (dropped data), say so loudly in the file.

## Query review checklist

1. Run `EXPLAIN (ANALYZE, BUFFERS)` (Postgres) or `EXPLAIN` (MySQL) before guessing.
2. Seq scan on a large table filtered by a selective column: missing or unusable index. Check for functions on the indexed column (`WHERE lower(email) = ...` needs an expression index).
3. N+1: loops issuing one query per row. Fix with a join, `IN` list, or the ORM's eager loading.
4. `OFFSET` pagination degrades linearly; use keyset pagination (`WHERE (created_at, id) < (?, ?) ORDER BY ... LIMIT ?`) for deep pages.
5. `SELECT *` in application code hides schema coupling and bloats the wire; select the columns used.
6. Watch for implicit type casts killing index use (text column compared to integer).
7. Composite index column order: equality columns first, then the range/sort column. An index on `(a, b)` serves `WHERE a = ?` but not `WHERE b = ?`.

## Index heuristics

- Index foreign key columns; most databases don't do it automatically and unindexed FKs make deletes on the parent table slow.
- One composite index that serves several queries beats three overlapping single-column indexes.
- Don't index low-cardinality columns alone (booleans, small enums) unless combined into a composite or partial index.
- Each index taxes every write. On write-heavy tables, justify each one with a query it serves.

## When asked "SQL or something else"

Default to Postgres unless there's a concrete reason not to. Redis for caches and queues alongside it, not instead of it. Reach for a document store only when the data is truly schemaless AND query patterns are key-based. "We might need to scale" is not a reason; "we measured and write volume exceeds X" is.
