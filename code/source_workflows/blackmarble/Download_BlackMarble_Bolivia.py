from huggingface_hub import HfApi, hf_hub_download
from pathlib import Path
import json

REPO = "faviolc/BlackMarble"
PREFIX = "bolivia339/daily_raw/"
ROOT = Path(r"X:\Agentic Tasks\Bolivia\Inputs\Satellites\NASA_BlackMarble_Daily")
INPUTS = ROOT / "Inputs"
DEST = INPUTS / "daily_raw"
DEST.mkdir(parents=True, exist_ok=True)

api = HfApi()

files = [
    f for f in api.list_repo_files(
        repo_id=REPO,
        repo_type="dataset"
    )
    if f.startswith(PREFIX)
]

if not files:
    raise RuntimeError(
        "No files found. Check Hugging Face authentication."
    )

print(f"Found {len(files)} files.")

records = []

for i, remote in enumerate(files, 1):
    print(f"[{i}/{len(files)}] {remote}", flush=True)

    downloaded = hf_hub_download(
        repo_id=REPO,
        repo_type="dataset",
        filename=remote,
        local_dir=INPUTS / "_hf_download"
    )

    source = Path(downloaded)
    relative = Path(remote[len(PREFIX):])
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)

    # Preserve the source and destination content.
    import shutil
    shutil.copy2(source, target)

    records.append({
        "source": remote,
        "local": str(target),
        "bytes": target.stat().st_size
    })

report = {
    "repository": REPO,
    "source_directory": PREFIX,
    "files": len(records),
    "total_bytes": sum(x["bytes"] for x in records),
    "details": records
}

report_path = INPUTS / "BlackMarble_Download_Inventory.json"
report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\nDOWNLOAD COMPLETED")
print("Files:", len(records))
print("Bytes:", report["total_bytes"])
print("Destination:", DEST)
print("Inventory:", report_path)
