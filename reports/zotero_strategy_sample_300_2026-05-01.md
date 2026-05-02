# Zotero Strategy for Sample 300

## Current state

- Current codebook-shaped sample: 300 `source_result` rows.
- Evidence levels now stand at: 88 level 6, 167 level 5, 37 level 4, and 8 level 2.
- That leaves 45 rows below strict level 5 after the Zotero storage re-ingest.
- The first Zotero automated pass targeted 15 `needs_manual_capture` rows and logged 45 attempts. It produced no immediate accepted full-article objects.
- The follow-up Zotero storage re-ingest saw 2 Zotero storage PDFs and promoted both after the normal identity gate:
  - `sr_266b83deab6b` -> `data/cache/full_article_text_acquisition/sample_300/sr_266b83deab6b__zotero_storage_reingest__c2420a86a334.pdf`
  - `sr_4dbf0cd7b50e` -> `data/cache/full_article_text_acquisition/sample_300/sr_4dbf0cd7b50e__zotero_storage_reingest__8d5693ca5170.pdf`

## Decision

Use Zotero Desktop as a lawful local full-text harvester, not as provenance authority. The authoritative promotion step remains the repository identity gate in `resolve_full_article_text_candidates_pilot.py`, which writes `source_file`, `source_access`, `source_access_attempt`, and related codebook TSV rows.

The practical loop is:

1. Run the automated Zotero pass against unresolved manual-capture rows.
2. Wait briefly for Zotero's late attachment downloads.
3. Run storage re-ingest over `.local/zotero-oa-data/storage`.
4. Promote only files accepted by DOI/title identity checks.
5. Treat all nonaccepted Zotero files as acquisition attempts or manual leads, not source objects.

## Commands

Start translation-server only when using the translation-assisted automated pass:

```bash
cd data/cache/zotero_translation_server
npm start
```

Start the dedicated Zotero profile:

```bash
xvfb-run -a zotero --profile "$PWD/.local/zotero-oa-profile" --no-remote --new-instance -ZoteroDebugText
```

Run the automated pass and then re-ingest late downloads:

```bash
.venv/bin/python scripts/run_zotero_automated_fulltext_pilot.py
.venv/bin/python scripts/ingest_zotero_storage_fulltext_pilot.py
```

## Bridge status

`tools/zotero-oa-bridge/` is still experimental. The source proxy installer now follows Zotero's documented development-profile rescan step by removing `extensions.lastAppBuildId` and `extensions.lastAppVersion` from the dedicated profile prefs, and it removes stale local XPI copies before writing the proxy file.

However, in the current dedicated profile, `POST http://127.0.0.1:23119/oa-pipeline/find-files` still returned `No endpoint found`, and `.local/zotero-oa-profile/extensions.json` still showed an empty add-on list. Do not rely on the bridge path until the plugin appears in `extensions.json` and that endpoint returns JSON.

Reference: Zotero's plugin-development docs describe source proxy files and the required profile prefs rescan: https://www.zotero.org/support/dev/client_coding/plugin_development

## Crash recovery rule

The automated Zotero script now checkpoints its attempt TSV after each target row and skips rows whose represented source already has an accepted full-article source file. If the process crashes again, re-run storage re-ingest first; then rerun the automated pass only for rows still lacking a full-article source object.
