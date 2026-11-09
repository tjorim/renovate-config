# renovate-config

Shared [Renovate](https://docs.renovatebot.com) presets for the tjorim repos (bordertax, champagnefestival,
daynest, travel, worktime). It replaces five hand-synced `dependabot.yml` files with one set of presets.

**Status: public and being adopted.** A preset affects a repository only when its `renovate.json` extends it and the Renovate app has access to that repository.

## Layout

| File | Purpose |
|---|---|
| `default.json` | Base: Friday 18:00 UTC window, labels, `deps:` commit style, 3-day `minimumReleaseAge`, weekly lockfile maintenance, GitHub Actions, Docker, compose, `codeql` group |
| `js.json` | npm/pnpm groups shared by the frontends, `rangeStrategy: bump` |
| `python.json` | uv groups shared by the backends |
| `android.json` | `android-build` group (AGP + Kotlin + KSP) |
| `home-assistant.json` | Base + Python library groups; enables Python, GitHub Actions and HA manifest requirements for custom integrations |
| `python-library.json` | Standalone Python libraries: base + Python groups and lower-bound version bumps |
| `python-lib.json` | `testing` and `linting` groups for the small Python libs and HA integrations |
| `astro.json` | `astro` group for the Astro sites |
| `rust.json` | cargo: `rust` label |
| `submodules.json` | turns on Renovate's git-submodule manager (off by default) |
| `repos/<repo>.json` | Draft `renovate.json` for each repo: the `extends` list plus repo-only groups and directory labels/prefixes |

A repo's `renovate.json` is just `repos/<repo>.json`.

Custom Home Assistant integrations extend `github>tjorim/renovate-config:home-assistant`. This preset intentionally replaces the base manager allowlist with `pep621`, `github-actions`, `homeassistant-manifest`, `pyenv` and `devcontainer`. Keep library-specific grouping and HA compatibility rules in the consuming repository: each library group spans its runtime `manifest.json` requirement and development pin in `pyproject.toml`. CI should verify matching exact pins without hard-coding a particular library release.

For `ha-mygrid-modbus`, Home Assistant owns the shared transport versions. Its scoped Python rule prevents independent transport upgrades; CI compares the test pins against the installed HA Modbus manifest. Update those pins together with the HA test baseline.

## Differences from the Dependabot setup

- **Group priority is reversed.** Dependabot gives a package to the *first* matching group; Renovate uses the *last*
  matching rule. Repo files come after the presets, so repo rules win. Overlapping patterns need care (see the
  `!@types/...` exclusions in `repos/bordertax.json`).
- **Renovate's built-in monorepo groups are switched off** (`ignorePresets` in `default.json`). Left on, they
  override these groups: `tailwindcss`, `vitest`, `oxlint` and `lucide-react` came out as `*-monorepo` branches.
- **`lockFileMaintenance` replaces the transitive-package groups** (`babel`, `transitive`) and the `allow: all`
  workaround. Transitive packages move in one lockfile PR instead of one PR each. It is enabled in `default.json`, so
  it applies to every manager with a lockfile (pnpm, npm, uv, cargo, gradle), including Python-only repos. Its schedule
  is **before 4am UTC on Monday**: lockfile maintenance has its own schedule (Renovate's default), which the base Friday
  window does not override. It does not apply the 3-day release-age wait; pnpm's own `minimumReleaseAge` still limits
  npm, but `uv lock --upgrade` has no age limit.
- **`minimumReleaseAge: 3 days` is native.** Renovate proposes the newest release that is old enough. With
  `internalChecksFilter: strict` it does not open a PR for a younger one. This is what the Dependabot `cooldown`
  was approximating.
- **Major updates get their own PR** (Renovate's default), even inside a group (`major-i18n`).
- **Toolchain pins are tracked.** `packageManager`, exact `engines` versions, `.node-version`, `.nvmrc`, `.python-version` and devcontainers receive reviewed updates. Supported `engines` ranges and `requires-python` remain manual policy. Python version files receive patch updates within the selected minor.
- **Coordinated tools:** Node pins are grouped across version files, exact engines, actions and Docker images. pnpm pins are grouped across package manifests and hard-coded `npm install -g pnpm@…` Dockerfile commands, detected by the shared regex manager. `Dockerfile` and `Dockerfile.*` are supported. No consumer changes are needed for existing inherited presets.
- **`android-build` matches differently.** Gradle plugins are named `group:artifact`, and the pattern deliberately
  excludes `org.jetbrains.kotlinx:*`, which the Dependabot pattern `org.jetbrains.kotlin*` also matched.
- **Manager coverage:** the base enables the existing application managers plus `nvm`, `pyenv`, `devcontainer` and a narrowly scoped Dockerfile pnpm regex manager. Managers without matching files have no effect. The HA preset also enables Python version files and devcontainers despite its narrower manager allowlist.
- **Python build tools are tracked.** `[build-system].requires` dependencies such as Hatchling, hatch-vcs and setuptools receive ordinary reviewed updates through `pep621`, with the shared release-age and scheduling policy. `requires-python` remains disabled because changing the support floor is a policy decision.
- **`ha-mygrid-core` has the Python manager disabled**, because Dependabot never tracked its uv/pip
  dependencies. Remove the rule in `repos/<repo>.json` to start tracking them.
- **`windows` crates group** in `ElevenClock-rs` matches `windows` and `windows-*`; Dependabot's pattern
  `windows-*` missed the `windows` crate itself.
- **GitHub Actions are pinned by commit hash with the exact version as a comment** (`helpers:pinGitHubActionDigestsToSemver`
  in `default.json`), e.g. `actions/checkout@<sha> # v7.0.1`, matching the repos that already do this by hand. In a repo
  that still uses tags like `@v7`, the first run converts them: one update PR per action that moves a major tag to the
  exact version and its hash, plus one `pin-dependencies` PR for actions already on an exact version. After that
  Renovate keeps the hashes and version comments updated.
- **Submodule pointers skip the release-age wait** (`submodules.json` sets `minimumReleaseAge: 0 days` for the
  `git-submodules` manager). They follow the tips of repos you already reviewed and merged, and a 3-day wait would
  miss a Monday-only window for anything merged after Friday night.
- **Security updates are not configured here.** Keep Dependabot security updates / alerts on in each repo.

## Checked

- `renovate-config-validator --strict` passes for every preset and for each merged per-repo config.
- Local dry-runs (`renovate --platform=local --dry-run=lookup`, Renovate 42.99.0) against bordertax,
  champagnefestival, pyrail, scat, ElevenClock-rs and ha-mygrid-modbus: managers detected (npm, pep621/uv, gradle, gradle-wrapper, dockerfile, docker-compose,
  github-actions, nodenv), groups form with these names, and `minimumReleaseAge` picks the newest old-enough version.

## Not checked

- Anything the dry-runs cannot do: label application, real PR creation, `lockFileMaintenance` PR contents and the
  dependency dashboard.
- GitHub Actions digest lookups were only exercised for `scat`, using a GitHub token; the other dry-runs ran without
  one and were rate-limited.
- Dry-runs for daynest, travel, worktime, custom-mygrid, python-mygrid-*, ha-mygrid-voltbridge, ha-mygrid-core.
- Submodule updates (`submodules.json`) in a real run: with a token, the app needs access to the submodule repos if they are private.
- `ha-mygrid-modbus` produced no update branches in its dry-run (rate-limited), so its `ignoreDeps` is unexercised.
- Whether a `renovate/*` branch passes each repo's CI.

## Adopting it

1. Publish this repo as `tjorim/renovate-config` (public is simplest; a private repo needs the Renovate app
   to have access to it).
2. Install the Renovate GitHub app on one repo first (bordertax is the smallest).
3. In that repo, merge `repos/<repo>.json` as `renovate.json`. Committing the config first avoids the onboarding PR.
4. Running both tools duplicates PRs. When Renovate is trusted, delete `.github/dependabot.yml` (this stops
   Dependabot *version* updates; security updates stay on via the repo setting) and close the leftover Dependabot PRs.
5. Roll out to the other four repos.

## Automated validation and drift checks

Pull requests and main run strict validation of every preset/example with the Renovate version pinned in `renovate-version.txt`, plus representative HA, Python library, and Rust/Astro extraction fixtures. Extraction resolves the candidate commit, rather than silently testing only the published main configuration. Inherited preset references retain their declared refs. Fork PRs may need a maintainer branch because the candidate commit must be readable in this repository.

A separate weekly/manual workflow compares examples with consumers’ default-branch configs. It fails on semantic differences but ignores JSON formatting and object key order; rule order remains significant. It does not change repositories or open issues. Unadopted/inaccessible repositories returning 404 are reported as skipped. Temporary drift is expected while a shared preset PR and its dependent consumer PRs merge; re-run the check afterwards.

Standalone libraries can extend `github>tjorim/renovate-config:python-library` to share the existing `pep621` lower-bound bump policy. HA integrations retain exact pins and continue using the Home Assistant preset.

## Self-maintenance

This repository’s `renovate.json` opts into the shared base but restricts updates to GitHub Actions workflows and `renovate-version.txt`. The version file is the single Renovate CLI pin used by both strict validation and extraction checks, so a CLI update is tested with the proposed version throughout CI. Preset definitions, repo examples and embedded fixture dependencies are not update targets. Updates retain the shared review, release-age and scheduling policy.
