---
name: "security-audit"
description: "Run a Windows supply-chain security audit across npm, pip, pnpm, and editor extensions. Use when the user asks for a supply-chain audit of npm, pip, pnpm packages or editor extensions on Windows."
---
Perform a comprehensive supply chain security audit on this Windows machine. Work through all phases and produce a severity-ranked markdown report saved to ~/security-audit-YYYY-MM-DD.md (using today's date).

## Phase 1: Software Inventory

Collect and list:
- Globally installed npm packages: `npm ls -g --depth=0`
- pip packages: `pip list`
- pnpm globals: `pnpm ls -g --depth=0`
- yarn globals: `yarn global list` (if installed)
- VS Code extensions: `code --list-extensions`
- Cursor extensions: `cursor --list-extensions`
- Node, Python, npm, pnpm, pip versions

## Phase 1b: Vulnerability Scanning

Run automated vulnerability scanners and include results in the report:
- `npm audit signatures` â€” verify provenance of installed npm packages
- `npm audit` â€” check for known vulnerabilities in global packages
- `pip-audit` â€” scan pip packages for known CVEs (install with `pip install pip-audit` if missing)
- `gh auth status` â€” verify GitHub token scopes are minimal (flag if `admin:org`, `delete_repo`, or other overly broad scopes are present)

## Phase 2: Known-Bad Package Check

Search the web for current IOC lists and cross-reference installed packages against:
- Shai-Hulud npm worm and its variants (check Datadog IOC repo, CISA alerts)
- Recent PyPI supply chain attacks (TeamPCP/litellm, typosquats)
- Compromised VS Code/Cursor extensions
- Axios supply chain attack versions
- Typosquat patterns for popular packages

Check specifically for:
- `setup_bun.js` or `bun_environment.js` in npm global node_modules (Shai-Hulud IOC)
- Suspicious preinstall/postinstall scripts in global packages
- TeamPCP persistence files: `~/.config/sysmon/sysmon.py`, `~/.config/systemd/user/sysmon.service`, `tpcp.tar.gz`
- Malicious `.pth` files in Python site-packages (inspect contents for obfuscated code)

## Phase 3: Secret Exposure

Check for credential files (report existence only, NEVER print secret values):
- `~/.npmrc` (check for auth tokens)
- `~/.aws/credentials`
- `~/.git-credentials`
- `~/.env`
- `.env` files in project directories under `~/Project_Codespaces` (max depth 3)

For each `.env` found:
- List the key names (not values)
- Check if the file is in `.gitignore`
- Check if it was ever committed to git history: `git log --all --diff-filter=A --name-only --format="" -- .env`

Check git config:
- `git config --global --list` for suspicious entries
- `git config --global core.hooksPath` for custom hook paths

## Phase 4: Persistence Mechanisms

Enumerate and assess:
- Scheduled tasks: `Get-ScheduledTask` â€” flag any non-Microsoft, non-standard-vendor tasks
- Startup entries: `Get-CimInstance Win32_StartupCommand`
- Recently modified files (last 90 days) in `%APPDATA%\npm` and `%LOCALAPPDATA%\Programs`

## Phase 5: Report Generation

Compile all findings into a markdown report at `~/security-audit-YYYY-MM-DD.md`:
- Executive summary (1-2 sentences)
- Severity-ranked findings: Critical / High / Medium / Info
- For each Critical or High finding, provide the exact remediation command
- Software inventory table
- Secret exposure summary table
- Persistence assessment table
- Threat intelligence references with links to sources consulted
- Recommendations summary ranked by priority

