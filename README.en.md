# Bolivia Satellites

[Espanol](README.md) | [Methods](public/docs/methods.md) | [Publication preparation](public/docs/publication.md)

A bilingual scientific application for seven products over the **exact 339
Bolivia Agriculture municipalities**, linked by `asdf_id`. Human review is
pending; preparing this repository does not constitute publication, scientific
certification or contractual acceptance.

## Current interface

One page with seven tabs, a fluid map, unboxed contextual statistics, municipal
history, synchronized Top 10 / Bottom 10 with names and values on the same row,
and progressive trajectories up to 339 series. The requested initial reference
is fixed at November 10, 2025, or November 2025 for monthly data. Effective dates,
gaps and visual point reduction are explicitly disclosed.

Colour midpoint = inverse of the full historical pool mean in the chosen
transformed space. Temperature stays linear; night lights default to
`ln(1000*x+1)`. The map's three informational means use original values.
Downloads always preserve original x. Black Marble exposes 23 numeric fields,
including municipal sum. EDGAR is excluded.

## Clean checkout

Node >=22 and Python >=3.10 are required; restoration uses Python's standard
library. No npm dependencies or CDN are needed. Large web arrays, scientific
masters, ZIP assets, `dist` and `Offline` are excluded from Git.

Place both versioned `BoliviaSatellites_webdata_partNN.zip` files in `Packages`:

```sh
python -B scripts/restore_webdata.py --packages ../Packages
node scripts/build.mjs
python -B scripts/serve_local.py --root dist --packages ../Packages --port 8768
```

Open `http://127.0.0.1:8768/`. Restoration verifies archive and member SHA-256,
sizes and paths against `distribution/webdata-manifest.json`. Complete data
ZIPs must also be in `Packages` for their download links to work.

**Known build limit:** `dist` is generated, but build exits 1 because its total
size exceeds the contractual 250 MiB budget. The limit is not silently raised.
The generated local site is reviewable; Netlify remains blocked pending size
and other validation requirements. Do not connect a source-only checkout to an
automatic deploy.

After a separately authorized Release exists, an explicit immutable URL can be used:

```sh
python -B scripts/restore_webdata.py --release-base-url https://github.com/Favioleiva/BoliviaSatellites/releases/download/APPROVED_TAG
```

The proposed tag is not a live Release. This restores existing web assets, not
new satellite observations, and never uses `latest` or browser credentials.

## Portable distribution

Extract all `BoliviaSatellites_portable_partNN.zip` files together, then open
`ABRIR_BOLIVIA_SATELLITES.html`. Keep `site`, `Offline` and `packages` together.
The portable includes code, all observations and scientific download packages.
It does not require internet. A restored checkout can generate its local
companion with `python -B scripts/build_offline.py`, then the normal Node build.

## Reproduction and limitations

[Reproduction guide](public/docs/reproducibility.md), [visual definitions](public/docs/visual-design.md).
`code/run.py` reconstructs from supplied municipal aggregates without new
extractions. `requirements.lock` records scientific dependencies. Source
workflows are reference code, never run automatically. Notebook source cells
are preserved while outputs, widgets and session metadata are removed from
publication copies; hashes are recorded in `provenance/notebook_sanitization.json`.

ERA5/GPM coverage >1 is retained with warnings. HKU includes upstream
reconstructed history. Burned-area QA, SatPM extremes/upstream traceability,
and Black Marble extraction, scale, QA and numeric discrepancies remain open.
No global scientific certification is claimed. Six source-code discrepancies
are retained; geography remains 339 municipalities, never replaced by 343.

Git carries code, tests, documentation, geography, catalogues and small manifests.
Release assets carry complete data, aggregate sources, webdata and portable parts.
Netlify would receive only a validated `dist`. Private evidence, contracts,
credentials and scientific masters are excluded from the Git candidate.

The new project-code license and redistribution selection await the supervisor's
decision. Existing third-party licenses and notices remain in `LICENSES` and
`THIRD_PARTY_NOTICES.txt`. No blanket open-data license is asserted. Nothing
is published automatically.
