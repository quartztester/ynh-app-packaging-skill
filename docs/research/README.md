# Research corpus — the level-8 UX calibration

The UX doctrine in `references/ui-questions-panels-docs.md` (install questions, config panels, admin docs) is not opinion — it is calibrated against **199 catalog level-8 apps** studied in five rounds (2026-10-28). This directory holds the reusable research procedure, the per-round selections, and the aggregate stats, so anyone can run a round 6 and extend or challenge the doctrine.

## Method

1. **Pool**: fetch `apps.toml` from YunoHost/apps master, keep `level == 8` apps with GitHub repos under `YunoHost-Apps/`.
2. **Select** category-stratified (round-robin over categories, smallest pools first) so no category dominates and hand-picking bias stays out. Rounds 1–2 were hand-picked (popularity / user-named examples); rounds 3–5 are stratified: 30, 50, 100 apps.
3. **Fetch** `manifest.toml`, `config_panel.toml`, `README.md`, `README_fr.md`, `doc/ADMIN.md`, `doc/PRE_INSTALL.md`, `doc/POST_INSTALL.md`, `DESCRIPTION.md` from the default branch (master, fallback main). 100 apps fetch in ~10 s.
4. **Analyze**: question counts/ids/types/ask-lengths/defaults/optionals, panel option/bind/button/visible/services usage, ADMIN.md line counts, doc-file presence rates. Scripts: `ui-research/0*.py` and `1*.py`, one pair per round (select → fetch → analyze).
5. **Fold**: only findings that contradict or materially sharpen the doctrine get merged into `references/ui-questions-panels-docs.md` — a round that changes nothing is a PASS. Anecdotes that don't generalize stay out.

## Round selections

`ui-research/round{3,4,5}_selection.json` records exactly which apps each stratified round studied (rounds 1–2 app lists are hardcoded in `01_levels.py` / `06_fetch2.py`). Raw fetched files are NOT vendored — they are other projects' GPL/AGPL content and re-fetch in seconds via the scripts; the selections are the provenance.

## Per-round stats (all from real runs; N = apps parsed)

| round | N | questions median | range | no `path` | `is_public` bool | panels | ADMIN.md |
|---|---|---|---|---|---|---|---|
| 1 | 9 | 4 | 1–5 | — | 0 | 2/9 | 6–78 lines |
| 2 | 10 | 4.5 | 2–5 | — | 0 | 2/10 | 1–86 (peertube 1) |
| 3 | 30 | 3 | 1–8 | 13 (43%) | 1 (fediverse) | 3/30 | 4–124 (adguardhome 124) |
| 4 | 50 | 3.0 | 1–7 | 22 (44%) | 0 | 7/50, 1–11 opts | 24/50, median 4.5, max 41 |
| 5 | 100 | 3.0 | 0–10 | 58 (58%) | 0 | 22/100, bind 94/141 opts, `services` key 13/22 | 40/100, median 10.5, max 111 |

Stable across all rounds: standard types (`domain`/`path`/`user`/`group`) ship ask-less; `init_main_permission` near-universal, default `visitors` (96%); zero apps asking ports/DB credentials; every optional carries a default; packaging_format 2 everywhere; DESCRIPTION.md and README_fr.md near-zero presence; README.md bot-generated (`apps_tools/readme_generator`).

Notable single-round facts: round 4 — all 11 password-asking apps declare `sso != true` (zero SSO-first violations; ~14% of level-8 apps can SSO at all); round 5 — gemserv/opensearch ship ZERO install questions, loops tops at 10 (ActivityPub bootstrap), newer panels pair `bind = "settings"` with the section `services` key.

## Running a new round

```bash
cd research/ui-research
python3 11_select4.py   # or a copy with the cumulative excluded list updated
python3 12_fetch4.py    # -> data<round>/<app>/{manifest.toml,config_panel.toml,...}
python3 13_analyze4.py
```

Copy the select/fetch/analyze trio, extend the excluded set with the previous rounds' selections (cumulative — never restudy an app), update the data directory suffix, run, then compare against `references/ui-questions-panels-docs.md` and fold only what contradicts or materially sharpens it.
