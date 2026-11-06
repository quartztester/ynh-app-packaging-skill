# Publish, transfer, catalog, announce — the production path

Green CI is the halfway point. A package becomes a catalog app only after it has a
public repo, a human who installed it, an org transfer, two green org-CI jobs and a
merged entry in `YunoHost/apps`. Each stage has one gate — do not move forward because
the previous stage "looks fine".

`local green` → `public repo` → `human verify` → `transfer` → `org CI` → `catalog PR` → `announce`

## Credentials — ask once, before the stage that needs them
| what | needed for | how to get it |
|---|---|---|
| GitHub | push, transfer, PRs, CI comments | `gh auth status`; if unauthenticated run `gh auth login` device flow and ask the human to finish it |
| YunoHost forum | the announcement topic | ask for their forum account (they post; you hand them the exact text) or a Discourse API key for `POST /posts.json` |
| Lemmy / Mastodon | the fediverse announcement | ask for instance URL + access token |

Ask in plain language, never assume an account exists, never write a token into the repo, a
commit or this skill, and never echo one back. Session-scoped env vars only.

## 1. Public repo — gate: local package_check green
Repo `$GH_ACCOUNT/<upstream-name>_ynh`, tag `v<version>-ynh<N>`, sources as release assets.
Every tag gets a matching GitHub release — a tag with no release is a half-published version.

## 2. Human verification — gate: the human installed it
The human reads the diff and installs the package on their own machine for testing. That is a
real gate, not a formality: present the evidence and stop. The standard they judge by is
`PHILOSOPHY.md` and `STRATEGY.md` in this skill's repo — read them, never paraphrase them back.

## 3. Transfer — gate: YunoHost-Apps membership
```bash
gh api orgs/YunoHost-Apps/memberships/$GH_ACCOUNT        # 404 = not a member yet
gh api repos/$GH_ACCOUNT/<app>_ynh/transfer -f new_owner=YunoHost-Apps
```
Transfer needs admin on the repo **and** membership of the `YunoHost-Apps` org. Without
membership, do not stall: open the catalog PR first and mark the package `(pending org
transfer)` — that is the accepted shape for a first contribution and how a newcomer gets
noticed. Ask for an invite in the forum's Contribute Room, then transfer and continue at step 4.
After transfer the repo has no fork link, so PRs are same-repo branches (`--head <branch>`, not
`<you>:<branch>`).

## 4. Org CI — acceptance is two jobs, one warning each
In the org repo: open the PR against `testing`, then comment `!testme` as its **own** comment.
The bot posts two matrices — **bookworm (Debian 12)** and **trixie (Debian 13)**.

Both jobs are passes when each ends green with **exactly one package_linter warning**:

```
not in YunoHost's application catalog
```

That warning is structural — the app cannot be checked against a catalog it is not in yet. Any
*other* ✘/⚠ line is a defect: read the per-test log, fix in the repo, re-push, re-comment.
Judge the completed per-test summary; a run still in progress, a timeout, or the first SUCCESS
banner in the log is not a verdict.

## 5. Catalog PR — gate: catalog_linter exit 0
PR to [YunoHost/apps](https://github.com/YunoHost/apps). Three files in the normal case:
- `apps.toml` — entry inserted at its **alphabetic** slot: `branch`, `category` (from
  `categories.toml`), `state = "working"`, `url` = the `YunoHost-Apps` URL.
- `logos/<id>.png` — the app's logo, 512px square PNG with transparency.
- `wishlist.toml` — delete the app's block if it exists; `graveyard.toml` — delete the entry
  when refreshing a dead app. Neither present → the PR touches two files.

Category comes from the catalog itself, not from the app's marketing: grep similar catalog
apps' `category` lines (`office` for note/wiki apps — joplin, trilium, memos, silverbullet).
Validate before pushing: `tomllib.loads()` the patched `apps.toml`, and run the catalog's own
`catalog_linter.py` (exit 0 required, and prove it saw your entry). Mechanics and the
false-pass traps: references/repo-hygiene.md §Catalog submission.

**PR title:** `add <app name>`

**PR body — exactly this, nothing else:**
```
Package: https://github.com/YunoHost-Apps/<app>_ynh
Upstream: <upstream repo URL>
Category: `<category>` (matching <two or three similar catalog apps>)

CI: App has passed CI — <link to the app repo PR whose `!testme` run was green>

Review by me and installed on my machine for testing. There is a fully determined human behind this PR with LLM assistance.
Please let me know if not up to any quality or standards. See my Philosophy and Strategy.md for my why to packaging.
I will maintain this repo.
```
The app logo ships in the same PR as `logos/<app>.png`. Real example of the accepted shape:
[YunoHost/apps#3689](https://github.com/YunoHost/apps/pull/3689) — match it, add no other text.
While the transfer is pending, the Package line reads
`Package (pending org transfer): https://github.com/$GH_ACCOUNT/<app>_ynh`.
The CI link must point at a real green run — never ship the PR with a placeholder in it.

## 6. Announce — forum, then fediverse
Forum topic in the Contribute Room (https://forum.yunohost.org/c/contribute-room), following
the existing `[<app>] <one-line description>` topic titles: what the app does, the catalog PR
link, the package link, and the tested YunoHost version. Use the human's forum account.
Then the same text shortened to a fediverse post on their Lemmy/Mastodon account, linking the
catalog PR. Announce only after the catalog PR is open — the links are the point.

## Rehearse on a fork
Dry-run the whole catalog diff against `$GH_ACCOUNT/apps` (a fork of `YunoHost/apps`) instead
of the real repo: branch off `upstream/main`, apply the three files, open the PR there, read
the rendered body. Only after it reads correctly does the same branch go to `YunoHost/apps`.
