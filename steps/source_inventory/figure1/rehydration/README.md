# Figure 1 Source Artifact Rehydration

This directory records how to repull Figure 1 source-family artifacts without
committing large files under `data/raw/`.

Build the URL ledger and manifest:

```sh
make figure1-rehydration-manifest
```

Repull supported artifacts:

```sh
make figure1-rehydrate-source-artifacts
```

Tracked files:

- `figure1-working-urls.tsv`: URL evidence found in successful download
  sidecars, mirror status rows, and provider inventories.
- `figure1-rehydration-manifest.tsv`: supported repull routes with target
  repo-relative paths and expected checksums when available.
- `figure1-rehydrate-run-status.tsv`: most recent rehydrate verification run.
- `access_events/*.json`: successful rehydrate access events for URLs fetched
  by the rehydration script.
- `figure1-rehydration-gaps.tsv`: local-only artifacts that still need an
  upstream route, unpack step, generated-metadata rebuild, or manual recovery.

Raw downloads remain ignored by Git. The manifest and access events are the
tracked state needed to reconstruct them.
