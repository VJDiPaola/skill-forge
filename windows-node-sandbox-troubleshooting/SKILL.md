---
name: windows-node-sandbox-troubleshooting
description: "Troubleshoot Windows-specific Node/npm issues in Codex or sandboxed agent sessions. Use when Node or npm misbehaves inside Codex or sandboxed agent sessions on Windows."
---

# Windows Node Sandbox Troubleshooting

Use this workflow for Windows execution issues in automated or sandboxed Node workflows.

## Known Patterns And Fixes

### 1) `npm` blocked by PowerShell execution policy

Symptom:
- `npm.ps1 cannot be loaded because running scripts is disabled`

Fix:
- Use `npm.cmd ...` instead of `npm ...`.

### 2) UNC workdir fallback to `C:\Windows`

Symptom:
- `CMD.EXE was started with the above path as the current directory. UNC paths are not supported. Defaulting to Windows directory.`
- `npm ERR! enoent Could not read package.json ... C:\Windows\package.json`

Fix:
- Use a normal drive-letter path for `workdir`, such as `C:\Users\...\repo`, not `\\?\...`.
- This matters even if the visible current directory was supplied to the agent as a UNC-style path.

### 3) `spawn EPERM` during test or build

Symptom:
- esbuild, vite, next, or worker process startup fails with `spawn EPERM`

Fix:
- Re-run the command with the tool's elevated or unrestricted execution mode.

### 4) BOM corruption in JSON or TS config

Symptom:
- `Unexpected token '﻿'` in `package.json` or another config file

Fix:
- Rewrite the file as UTF-8 without BOM.
- In PowerShell, use `System.Text.UTF8Encoding($false)` with `WriteAllText`.

## Recovery Order

1. Switch to `npm.cmd`.
2. Replace UNC `workdir` values with a normal `C:\...` path.
3. Retry with elevated execution if worker startup fails.
4. Strip BOM from recently edited config files if parsing errors remain.
5. Re-run `npm.cmd run test`, `npm.cmd run lint`, and `npm.cmd run build`.
