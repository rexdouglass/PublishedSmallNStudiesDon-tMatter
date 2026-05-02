# Wayback Manual-Task Lead Pass

- Sample rows: 300
- Open manual tasks with candidate URLs: 260
- Manual tasks queried in this polite pilot pass: 20
- URL variants queried: 39
- URL variants with at least one Wayback capture: 2
- Manual tasks with at least one capture lead: 2

## Interpretation

- These rows are acquisition leads only. A Wayback capture must still be mirrored, checksummed, byte-classified, and inspected before it changes any evidence level.
- A landing-page or abstract capture remains level 3/4 unless the exact value-bearing D/N text is present in the archived bytes.
- The target timestamp in this pilot is the manual task opening date, not the original corpus extraction date; source-version work still needs true corpus as-of dates.

## First Capture Leads

- `mtask_1de1792cc064` `clinicaltrials` captures=1; closest `20210413184757` http://web.archive.org/web/20210413184757/https://clinicaltrials.gov/ct2/show/NCT00511342
- `mtask_722d8ec6541a` `clinicaltrials` captures=1; closest `20230426202011` http://web.archive.org/web/20230426202011/https://www.clinicaltrials.gov/ct2/show/NCT01610700

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/wayback_cdx_manual_task_attempts_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/wayback_cdx_manual_task_attempts_summary_sample_300.tsv`
