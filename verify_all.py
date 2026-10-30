"""Verify published ARC3 source packages without model or game execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def pin(raw):
    return {"bytes":len(raw), "sha256":hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publisher-zip", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    actual = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if path.is_symlink():
            raise ValueError("Unexpected symlink")
        if path.is_file() and rel.as_posix() != "SOURCE_MANIFEST.json":
            actual[rel.as_posix()] = pin(path.read_bytes())
    expected = json.loads((root / "SOURCE_MANIFEST.json").read_text())["files"]
    if actual != expected:
        raise ValueError("Release inventory/hash mismatch")
    results = {}
    for name, script in [("selected-control-v3", "verify_selected_source.py"),
                         ("official-v4", "verify_public_source.py"),
                         ("official-v4", "verify_contribution_map.py")]:
        result = subprocess.run([sys.executable, "-B", str(root/name/script),
                                 "--publisher-zip", str(args.publisher_zip.resolve())],
                                cwd=root/name, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"{name}/{script} failed: {result.stderr}")
        results[f"{name}/{script}"] = json.loads(result.stdout)
    print(json.dumps({"competition":"ARC-AGI-3", "all_release_files_verified":len(actual)+1,
                      "results":results,"official_scores_reproduced":False},indent=2))


if __name__ == "__main__":
    main()
