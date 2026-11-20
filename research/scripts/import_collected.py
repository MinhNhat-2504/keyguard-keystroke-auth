"""Nhập snapshot JSONL đã ẩn danh từ commit Git có sẵn tại local, không đổi dữ liệu."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "44a610bd120b09e2838e76073cb164c3ce6cac36"


def main():
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", SOURCE,
                                     "data/collected/"], cwd=ROOT, text=True).splitlines()
    entries = []
    for name in names:
        if not name.endswith(".jsonl"):
            continue
        data = subprocess.check_output(["git", "show", f"{SOURCE}:{name}"], cwd=ROOT)
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f"Không ghi đè file khác snapshot: {name}")
        target.write_bytes(data)
        entries.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                        "rows": sum(bool(line.strip()) for line in data.splitlines())})
    manifest = {"source_repo": "https://github.com/MinhNhat-2504/keyguard-keystroke-auth",
                "source_commit": SOURCE, "files": entries, "raw_rows": sum(e["rows"] for e in entries),
                "note": "Bản sao nguyên byte từ nhánh thu-branch; chưa chỉnh sửa/đánh số lại mẫu gốc."}
    (ROOT / "data/collected_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Imported {len(entries)} files, {manifest['raw_rows']} raw rows from {SOURCE}")


if __name__ == "__main__":
    main()
