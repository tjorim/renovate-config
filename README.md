# renovate-config

Shared [Renovate](https://docs.renovatebot.com) presets for the tjorim repos (bordertax, champagnefestival,
daynest, travel, worktime). It replaces five hand-synced `dependabot.yml` files with one set of presets.

**Status: published (private), not active anywhere.** Nothing here affects a repo until the Renovate app has access
to this repo and a repo adds a `renovate.json` that extends it.

## Layout

| File | Purpose |
|---|---|
| `default.json` | Base: Friday 18:00 UTC window, labels, `deps:` commit style, 3-day `minimumReleaseAge`, GitHub Actions, Docker, compose, `codeql` group |
| `js.json` | npm/pnpm groups shared by the frontends, `rangeStrategy: bump`, weekly `lockFileMaintenance` |
| `python.json` | uv groups shared by the backends |
| `android.json` | `android-build` group (AGP + Kotlin + KSP) |
| `python-lib.json` | `testing` and `linting` groups for the small Python libs and HA integrations |
| `astro.json` | `astro` group and a weekly `package-lock.json` refresh for the Astro sites |
| `rust.json` | cargo: `rust` label and a weekly `Cargo.lock` refresh |
| `submodules.json` | turns on Renovate's git-submodule manager (off by default) |
| `repos/<repo>.json` | Draft `renovate.json` for each repo: the `extends` list plus repo-only groups and directory labels/prefixes |

A repo's `renovate.json` is just `repos/<repo>.json`.

## Differences from the Dependabot setup

- **Group priority is reversed.** Dependabot gives a package to the *first* matching group; Renovate uses the *last*
  matching rule. Repo files come after the presets, so repo rules win. Overlapping patterns need care (see the
  `!@types/...` exclusions in `repos/bordertax.json`).
- **Renovate's built-in monorepo groups are switched off** (`ignorePresets` in `default.json`). Left on, they
  override these groups: `tailwindcss`, `vitest`, `oxlint` and `lucide-react` came out as `*-monorepo` branches.
- **`lockFileMaintenance` replaces the transitive-package groups** (`babel`, `transitive`) and the `allow: all`
  workaround. Transitive packages move in one lockfile PR instead of one PR each.
- **`minimumReleaseAge: 3 days` is native.** Renovate proposes the newest release that is old enough. With
  `internalChecksFilter: strict` it does not open a PR for a younger one. This is what the Dependabot `cooldown`
  was approximating.
- **Major updates get their own PR** (Renovate's default), even inside a group (`major-i18n`).
- **Not carried over:** the single-package `async` group in daynest's `custom_components`; Dependabot never
  bumped `packageManager` or `.node-version`, so those are disabled here for parity (Dockerfiles pin pnpm/node too).
- **`android-build` matches differently.** Gradle plugins are named `group:artifact`, and the pattern deliberately
  excludes `org.jetbrains.kotlinx:*`, which the Dependabot pattern `org.jetbrains.kotlin*` also matched.
- **Only the managers Dependabot covered are enabled** (`enabledManagers` in `default.json`: npm, pep621/uv, cargo,
  gradle, gradle-wrapper, dockerfile, docker-compose, github-actions, git-submodules). Left on, Renovate also bumps
  `.nvmrc`, `.python-version`, devcontainers, ansible-galaxy requirements, `engines` and `[build-system].requires`,
  which produced extra branches in the dry-runs. They are opt-in once the move is trusted.
- **`ha-mygrid-core` has the Python manager disabled**, because Dependabot never tracked its uv/pip
  dependencies. Remove the rule in `repos/<repo>.json` to start tracking them.
- **`windows` crates group** in `ElevenClock-rs` matches `windows` and `windows-*`; Dependabot's pattern
  `windows-*` missed the `windows` crate itself.
- **Security updates are not configured here.** Keep Dependabot security updates / alerts on in each repo.

## Checked

- `renovate-config-validator --strict` passes for every preset and for each merged per-repo config.
- Local dry-runs (`renovate --platform=local --dry-run=lookup`, Renovate 42.99.0) against bordertax,
  champagnefestival, pyrail, scat, ElevenClock-rs and ha-mygrid-modbus: managers detected (npm, pep621/uv, gradle, gradle-wrapper, dockerfile, docker-compose,
  github-actions, nodenv), groups form with these names, and `minimumReleaseAge` picks the newest old-enough version.

## Not checked

- Anything involving a GitHub token: label application, PR creation, `lockFileMaintenance` PR contents, the
  dependency dashboard, GitHub Actions lookups (the dry-runs hit the API rate limit).
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
