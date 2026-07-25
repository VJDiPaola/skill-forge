---
name: "docker-debug"
description: "Review Dockerfiles and debug containers and docker-compose setups. Use when the user asks why a container won't start, exits immediately, can't reach another service, builds slowly, or produces a huge image, or wants a Dockerfile or compose file written or reviewed. Trigger on Dockerfile, docker compose, container exits, image size, layer caching, healthcheck, or works on my machine but not in Docker."
---

# Docker Debug

Dockerfile review, image size and build-speed fixes, and container/compose debugging.

## Not in scope

Kubernetes manifests and cluster debugging, registry/CI pipeline configuration, and container security scanning (see the security skills for supply-chain review). This skill covers local and single-host Docker.

## Debugging: look before guessing

Run these in order; each answers a specific question.

```bash
docker ps -a                       # is it running? exit code?
docker logs <c> --tail 100        # what did it say before dying?
docker inspect <c> --format '{{json .State}}'   # OOMKilled? exit code? restarting?
docker exec -it <c> sh            # poke around a live container
docker run --rm -it --entrypoint sh <image>     # poke around when it won't stay up
docker events --since 10m         # restarts, OOM kills, healthcheck failures
```

Common exit codes: `137` = OOM-killed or `docker stop` (check `.State.OOMKilled`), `126`/`127` = entrypoint not executable / not found (Windows line endings or missing shebang are the usual culprits), `1` immediately = read the logs, the app told you.

## The usual suspects

- **Exits immediately, no logs:** entrypoint runs a command that daemonizes or finishes. Containers live as long as PID 1; run the process in the foreground.
- **Can't reach another compose service:** use the service name as hostname, not `localhost`. `localhost` inside a container is the container.
- **Port published but unreachable:** app binds `127.0.0.1` inside the container; it must bind `0.0.0.0`.
- **Works locally, fails in container:** missing file from a `.dockerignore` overreach, env var set only in your shell, or an Alpine/glibc mismatch for native deps.
- **File changes not showing up:** bind mount path wrong, or the image copy is shadowing the mount. Check `docker inspect <c> --format '{{json .Mounts}}'`.
- **Compose "works after restart":** missing `depends_on` with `condition: service_healthy` plus a real `healthcheck` on the dependency. `depends_on` alone only orders startup, it doesn't wait for readiness.
- **Windows hosts:** CRLF line endings break shell entrypoints (`env: sh\r: not found`). Add `*.sh text eol=lf` to `.gitattributes`.

## Dockerfile review checklist

1. **Pin the base image** (`node:22-bookworm-slim`, not `node:latest`). Prefer slim/bookworm over Alpine when native modules are involved.
2. **Layer order = cache order.** Copy dependency manifests and install first, copy source last:
   ```dockerfile
   COPY package.json package-lock.json ./
   RUN npm ci
   COPY . .
   ```
   Any file change above a layer invalidates everything below it.
3. **Multi-stage builds** for compiled or bundled apps: build stage with the toolchain, final stage with only the artifact and runtime. This is the single biggest image-size lever.
4. **One `.dockerignore`** mirroring `.gitignore` plus `node_modules`, `.git`, build output. Its absence is why builds are slow and images are fat.
5. **Run as non-root** in the final stage (`USER node` or an added user).
6. **`ENTRYPOINT` vs `CMD`:** ENTRYPOINT is the executable, CMD the default args. Use exec form (JSON array) so signals reach the process and Ctrl+C works.
7. **No secrets in layers.** Build args and `COPY`ed credential files persist in history. Use BuildKit secret mounts (`RUN --mount=type=secret,...`) or runtime env.
8. **Healthcheck** for anything another service waits on.

## Image size triage

```bash
docker history <image> --no-trunc   # which layer is fat?
docker image ls                     # compare tags
```

Biggest wins in order: multi-stage build, slim base, `.dockerignore`, combining `apt-get update && apt-get install && rm -rf /var/lib/apt/lists/*` into one layer, `npm ci --omit=dev` / `pip install --no-cache-dir`.
