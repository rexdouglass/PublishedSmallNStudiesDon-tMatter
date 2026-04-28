# FORRT FReD Freshness Check - 2026-04-27

## Source Links Checked

- Live OSF project: https://osf.io/9r62x/
- Current clean export on OSF: `/0 Data/FReD.xlsx`, download shortlink `https://osf.io/download/2tbvd/`
- Current FLORA metadata export on OSF: `/0 Data/flora.csv`, download shortlink `https://osf.io/download/t4j8f/`
- Current codebook on OSF: `/0 Data/fred_codebook.xlsx`, download shortlink `https://osf.io/download/g7r9z/`
- Data-paper reported-analysis file: `https://osf.io/download/qtkzy/`
- Paper-era most-recent shortlink: `https://osf.io/download/z5u9b/`
- Latest archived workbook found in the OSF manifest: `/0 Data/Archive/FReD_2.4.1.xlsx`, download shortlink `https://osf.io/download/9pjvy/`

## Local Files Checked

- `data/raw/corpus_candidates/fred/FReD.xlsx`
- `data/raw/corpus_candidates/fred/flora.csv`
- `data/raw/corpus_candidates/fred/fred_codebook.xlsx`
- `data/raw/replication_projects/fred/FReD.xlsx`
- `data/raw/replication_projects/fred/fred_codebook.xlsx`

Freshness-check downloads and API metadata are stored under:

- `data/raw/corpus_candidates/fred/freshness_check_2026-04-27/`

## Freshness Result

The current live OSF clean export files are byte-for-byte identical to the local canonical files:

| File | Local bytes | Live bytes | SHA-256 match |
|---|---:|---:|---|
| `FReD.xlsx` | 1,083,820 | 1,083,820 | yes |
| `flora.csv` | 5,637,223 | 5,637,223 | yes |
| `fred_codebook.xlsx` | 8,863 | 8,863 | yes |

OSF metadata for the current clean `FReD.xlsx` reports `date_modified = 2026-02-01T13:19:26.349386` and size `1,083,820` bytes. The local copy is current as of this check.

## Row-Unit Reconciliation

The apparent mismatch with the Röseler et al. data-paper abstract is a row-unit/version issue, not a missing local download.

- The data paper describes a platform with 1,239 original findings paired with replication findings.
- The reported-analysis OSF file at `qtkzy` is a CSV with 1,239 rows and 70 columns.
- The current OSF clean export `FReD.xlsx` has 2,164 effect-level rows and 56 columns.
- The current clean export contains 1,116 unique `fred_id` values, 786 unique original DOIs, and 320 unique replication DOIs.
- The local parser yields 1,969 original-claim D/N rows across 762 original-paper DOI units for the published-endpoint corpus.
- The replication-pair parser yields 843 usable pair rows from the clean export, of which 685 pass the current D/N and size gates.

So the current build uses the current clean OSF export, not the older reported-analysis snapshot.

## Archive Workbook Check

The OSF project also includes larger archived/workflow workbooks, including `FReD_2.4.1.xlsx` and the `z5u9b` paper-era workbook now named `FReD - legacy v1.xlsx`. These are not drop-in replacements for the current clean export.

`FReD_2.4.1.xlsx` has 20 sheets and 4,661 rows on `Data`, but it mixes documentation/header rows, pending rows, excluded rows, duplicate/workflow rows, and partially coded submissions. A conservative scan of the archive `Data` sheet found:

- 4,005 rows after dropping obvious header rows and explicit exclusions.
- 1,203 rows with converted original and replication effect sizes plus original and replication Ns.
- 425 rows that are both validated as `1` or `2` and complete on converted effects plus Ns.
- 343 converted/N-complete rows whose DOI pair is absent from the current clean export. These are mostly from ML1, RRR, OSF Registries, Boyce et al. 2023, individual submissions, and OpenMKT-like sources.

Decision: keep the archive workbook as provenance and a possible future rescue queue, but do not promote it into the live FReD parser automatically. It is an archival/workflow artifact, whereas the current OSF `FReD.xlsx` is the clean current export. Any archive rescue should be a separate curated source with duplicate handling against existing direct-project rows.

## Current Documentation Decision

FReD should be documented as:

- Source type: living replication-target database, not a random journal-paper sample.
- Local freshness: current clean OSF export verified byte-for-byte on 2026-04-27.
- Row unit: effect-level rows in the current clean export; paper-abstract count refers to an older/frozen finding-level snapshot.
- Live usage: included in both the replication-pair corpus and the published-original endpoint corpus.
- Caveat: the archival workbook contains additional potentially usable rows, but those require a separate duplicate-aware archive-rescue pass.
