from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download
import pyarrow as pa
import pyarrow.parquet as pq
import json
import re
import os

ROOT = Path(r"X:\Agentic Tasks\Bolivia\Inputs\Satellites\PM25_Satellite_Estimates")
INPUTS = ROOT / "Inputs"
RAW = INPUTS / "pm25_monthly"
RAW.mkdir(parents=True, exist_ok=True)

REPO = "faviolc/gdo4Bolivia"
PREFIX = "pm25_monthly/"
YEARS = list(range(1998, 2025))

OUTPUT = INPUTS / "Bolivia_PM25_Monthly_1998_2024.parquet"
REPORT = INPUTS / "Bolivia_PM25_Validation.json"

api = HfApi()
repo_files = api.list_repo_files(
    repo_id=REPO,
    repo_type="dataset"
)

pattern = re.compile(
    r"^pm25_monthly/SatPM_V6GL03_PM25_Bolivia_Municipality_Stats_(\d{4})\.parquet$"
)

found = {}
for filename in repo_files:
    match = pattern.fullmatch(filename)
    if match:
        year = int(match.group(1))
        if year in found:
            raise RuntimeError(f"Duplicate year: {year}")
        found[year] = filename

missing = sorted(set(YEARS) - set(found))
if missing:
    raise RuntimeError(f"Missing years in repository: {missing}")

print(f"Found {len(found)} annual Parquet files.")

tables = []
summary = []
reference_schema = None

for year in YEARS:
    remote = found[year]

    print(f"Downloading {year} ...", flush=True)

    local = hf_hub_download(
        repo_id=REPO,
        repo_type="dataset",
        filename=remote,
        local_dir=RAW,
    )

    table = pq.read_table(local)

    # Require identical schemas to avoid silent coercion.
    if reference_schema is None:
        reference_schema = table.schema
    elif not table.schema.equals(reference_schema):
        raise RuntimeError(
            f"Schema mismatch in {year}: "
            f"{table.schema} != {reference_schema}"
        )

    summary.append({
        "year": year,
        "rows": table.num_rows,
        "columns": table.num_columns,
        "file_bytes": Path(local).stat().st_size,
    })

    tables.append(table)

    print(
        f"  OK: {table.num_rows:,} rows",
        flush=True
    )

print("Combining annual datasets...", flush=True)

mega = pa.concat_tables(tables)

# Atomic output: prevent partial final files
temporary = OUTPUT.with_suffix(".parquet.tmp")

try:
    pq.write_table(
        mega,
        temporary,
        compression="zstd",
        row_group_size=100000
    )

    metadata = pq.read_metadata(temporary)

    expected_rows = sum(x["rows"] for x in summary)

    if metadata.num_rows != expected_rows:
        raise RuntimeError("Row count validation failed.")

    if metadata.num_columns != mega.num_columns:
        raise RuntimeError("Column count validation failed.")

    os.replace(temporary, OUTPUT)
finally:
    if temporary.exists():
        temporary.unlink()

report = {
    "source": REPO,
    "source_folder": PREFIX,
    "year_start": 1998,
    "year_end": 2024,
    "files": len(summary),
    "rows": mega.num_rows,
    "columns": mega.num_columns,
    "column_names": mega.column_names,
    "schema": str(mega.schema),
    "output": str(OUTPUT),
    "output_bytes": OUTPUT.stat().st_size,
    "annual_details": summary,
    "validation": {
        "all_expected_years_present": True,
        "identical_schemas": True,
        "row_count_matches": True,
        "output_metadata_readable": True
    }
}

REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\n================================")
print("MEGAPARQUET COMPLETED")
print("================================")
print(f"Years: {YEARS[0]}-{YEARS[-1]}")
print(f"Files: {len(summary)}")
print(f"Rows: {mega.num_rows:,}")
print(f"Columns: {mega.num_columns}")
print(f"Output: {OUTPUT}")
print(f"Validation: {REPORT}")
