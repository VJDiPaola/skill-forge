---
name: cloudflare-deploy
description: Deploy applications to Cloudflare Workers, Pages, and related platform services. Use when the user wants to deploy to Cloudflare Workers or Pages, wire up wrangler, or debug a Cloudflare deployment.
---

# Cloudflare Deploy

Decision trees for picking a Cloudflare product, then official docs for the details. This skill is not a docs mirror and does not replace `developers.cloudflare.com`.

## Prerequisites

- When sandboxing blocks the deployment network calls, rerun with `sandbox_permissions=require_escalated`.
- The deployment might take a few minutes. Use appropriate timeout values.

## Authentication (Required Before Deploy)

Verify auth before `wrangler deploy`, `wrangler pages deploy`, or `npm run deploy`:

```bash
npx wrangler whoami    # Shows account if authenticated
```

Not authenticated?
- Interactive/local: `npx wrangler login` ([wrangler login](https://developers.cloudflare.com/workers/wrangler/commands/login/))
- CI/CD: set `CLOUDFLARE_API_TOKEN` ([API tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/))

After deploy, verify with `npx wrangler deployments list` or by hitting the returned URL. Do not treat a successful CLI exit as proof the new version is live.

## Quick Decision Trees

### "I need to run code"

```
Need to run code?
├─ Serverless functions at the edge → Workers
├─ Full-stack web app with Git deploys → Pages
├─ Stateful coordination/real-time → Durable Objects
├─ Long-running multi-step jobs → Workflows
├─ Run containers → Containers
├─ Multi-tenant (customers deploy code) → Workers for Platforms
├─ Scheduled tasks (cron) → Cron Triggers
├─ Lightweight edge logic (modify HTTP) → Snippets
├─ Process Worker execution events (logs/observability) → Tail Workers
└─ Optimize latency to backend infrastructure → Smart Placement
```

### "I need to store data"

```
Need storage?
├─ Key-value (config, sessions, cache) → KV
├─ Relational SQL → D1 (SQLite) or Hyperdrive (existing Postgres/MySQL)
├─ Object/file storage (S3-compatible) → R2
├─ Message queue (async processing) → Queues
├─ Vector embeddings (AI/semantic search) → Vectorize
├─ Strongly-consistent per-entity state → Durable Objects storage
└─ Secrets management → Secrets Store
```

### "I need AI/ML"

```
Need AI?
├─ Run inference (LLMs, embeddings, images) → Workers AI
├─ Vector database for RAG/search → Vectorize
├─ Build stateful AI agents → Agents SDK
└─ Gateway for any AI provider (caching, routing) → AI Gateway
```

### "I need security"

```
Need security?
├─ Web Application Firewall → WAF
├─ DDoS protection → DDoS
├─ Bot detection/management → Bot Management
├─ API protection → API Shield
└─ CAPTCHA alternative → Turnstile
```

## Official docs

Load the matching page. Do not invent API shapes from memory.

### Compute & runtime

| Product | Docs |
|---------|------|
| Workers | https://developers.cloudflare.com/workers/ |
| Pages | https://developers.cloudflare.com/pages/ |
| Durable Objects | https://developers.cloudflare.com/durable-objects/ |
| Workflows | https://developers.cloudflare.com/workflows/ |
| Containers | https://developers.cloudflare.com/containers/ |
| Workers for Platforms | https://developers.cloudflare.com/cloudflare-for-platforms/workers-for-platforms/ |
| Cron Triggers | https://developers.cloudflare.com/workers/configuration/cron-triggers/ |
| Wrangler | https://developers.cloudflare.com/workers/wrangler/ |

### Storage & data

| Product | Docs |
|---------|------|
| KV | https://developers.cloudflare.com/kv/ |
| D1 | https://developers.cloudflare.com/d1/ |
| R2 | https://developers.cloudflare.com/r2/ |
| Queues | https://developers.cloudflare.com/queues/ |
| Hyperdrive | https://developers.cloudflare.com/hyperdrive/ |
| Vectorize | https://developers.cloudflare.com/vectorize/ |
| Secrets Store | https://developers.cloudflare.com/secrets-store/ |

### AI & security

| Product | Docs |
|---------|------|
| Workers AI | https://developers.cloudflare.com/workers-ai/ |
| Agents SDK | https://developers.cloudflare.com/agents/ |
| AI Gateway | https://developers.cloudflare.com/ai-gateway/ |
| WAF | https://developers.cloudflare.com/waf/ |
| Turnstile | https://developers.cloudflare.com/turnstile/ |
| Tunnel | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ |

## Troubleshooting

If deployment fails due to network issues (timeouts, DNS errors, connection resets), rerun the deploy with escalated permissions (`sandbox_permissions=require_escalated`). The deploy needs outbound access when sandbox networking blocks requests.

Example guidance to the user:

```
The deploy needs escalated network access to deploy to Cloudflare. I can rerun the command with escalated permissions—want me to proceed?
```
