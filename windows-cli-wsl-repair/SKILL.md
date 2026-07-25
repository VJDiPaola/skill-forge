---
name: windows-cli-wsl-repair
description: Diagnose and repair Windows developer CLI, npm global package, PATH shim, PowerShell, Codex sandbox, and WSL Ubuntu package or default-user issues. Use when the user asks to figure out what is wrong with a local Windows tool install/update, a broken command on PATH, npm postinstall/native binary behavior, WSL package health, Ubuntu launch/user errors, or misleading sandbox output.
---

# Windows CLI And WSL Repair

Use this skill to separate real machine state from Codex sandbox artifacts before changing local tooling. Diagnose first, then make the smallest repair supported by evidence.

## Workflow

1. Identify the active command path.
   - Use `Get-Command <name>` and `where.exe <name>`.
   - Inspect wrappers such as `.bat`, `.cmd`, `.ps1`, or tiny `.exe` stubs before assuming the package itself is broken.
   - Compare the active PATH command to any known native binary under the tool's own install directory.

2. Separate sandbox behavior from normal-user behavior.
   - If a command fails only in Codex sandbox, run a narrow normal-user probe with escalation when needed.
   - Prefer no-profile PowerShell for diagnostics if profile-loaded shells hang.
   - Do not treat sandbox-only WSL inventory output as truth.

3. Check package-manager and postinstall state.
   - For npm tools, inspect `npm.cmd config get ignore-scripts`.
   - If global npm install leaves a tiny native launcher stub, inspect package metadata and optional native dependency folders.
   - If the package has an install script, rerun only that package's postinstall in the package directory after confirming it is the intended repair.

4. Repair PATH carefully.
   - Prefer the official current shim when it works.
   - Back up stale wrapper files before replacing them.
   - Point legacy wrappers to the known-good native executable only after direct version checks pass.

5. Repair WSL package state only after inventory is trusted.
   - Use unsandboxed `wsl.exe --status` and `wsl.exe -l -v` when sandbox output says no distro exists but other evidence suggests WSL is running.
   - Check `/etc/passwd`, `/etc/wsl.conf`, `id`, `whoami`, and `pwd` before reading sensitive files.
   - Use the maintenance sequence: `dpkg --configure -a`, `apt-get -f install -y`, `apt-get update`, `apt-get upgrade -y`, `apt-get autoremove -y`, `apt-get autoclean`, then `apt-get check`.

6. Fix WSL default-user drift when proven.
   - If plain `wsl.exe -d <distro>` falls back to root with `getpwuid(1000) failed`, compare the Linux user's UID to Windows-side `DefaultUid`.
   - If the registry `DefaultUid` is stale, update only that distro value, then run `wsl.exe --terminate <distro>` and retest.

## Guardrails

- Do not read `.env`, tokens, private keys, cookies, or `/etc/shadow`.
- Do not change registry values until the exact distro GUID and intended UID are proven.
- Do not disable global security settings like `ignore-scripts=true` unless the user explicitly asks.
- Do not run broad reinstall or cleanup commands before proving the narrower failure layer.

## Verification

Report the final state with:

- Active command path and version for the repaired CLI.
- Any wrapper files backed up or changed.
- WSL distro/version, launch user, `apt-get check`, `dpkg --audit`, and remaining upgradable package count.
- Settings intentionally left unchanged, especially security-sensitive npm config.
