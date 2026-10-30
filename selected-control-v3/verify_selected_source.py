"""Check the selected ARC3 source candidate without executing notebook code.

Run with --publisher-zip PATH. No network, installation, inference or unpickling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import zipfile

BEST_SHA = "318aa89a1b62dbf9a331dc9ac1273dacb9a23757de034b68f835c37ee33998ad"
UPSTREAM_SHA = "88a379f17c3a4ba8c98715fc23155346ccd6eb289bdafebadfc61a3178f9d9bd"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pin(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def tree(root):
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Symlink in package")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = pin(path.read_bytes())
    return result


def cell_source(cell):
    value = cell["source"]
    return value if isinstance(value, str) else "".join(value)


def replay(before, changes):
    """Rebuild text using explicit original coordinates; do not execute edits."""
    lines = before.splitlines(keepends=True)
    result, cursor = [], 0
    for change in changes:
        start, stop = change["old_range"]
        require(cursor <= start <= stop <= len(lines), "Invalid/overlapping edit range")
        require(lines[start:stop] == change["old_lines"], "Edit context mismatch")
        result.extend(lines[cursor:start])
        result.extend(change["new_lines"])
        cursor = stop
    result.extend(lines[cursor:])
    return "".join(result)


def verify(root, publisher):
    root, publisher = Path(root).resolve(), Path(publisher).resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    actual = tree(root)
    actual.pop("manifest.json")
    require(actual == manifest["files"], "Package inventory/hash mismatch")
    contract = json.loads((root / "source_contract.json").read_text())
    require(contract["official_submission"]["id"] == 57034274, "Wrong submission")
    require(contract["official_submission"]["script_version_id"] == 356741836, "Wrong script version")
    raw = (root / "notebook/arc3-control-v3-356741836.ipynb").read_bytes()
    upstream_raw = (root / "provenance/upstream_notebook.ipynb").read_bytes()
    require(pin(raw)["sha256"] == BEST_SHA, "Wrong selected notebook")
    require(pin(upstream_raw)["sha256"] == UPSTREAM_SHA, "Wrong upstream notebook")
    require(pin(raw) == contract["notebook"], "Notebook contract mismatch")
    nb, up = json.loads(raw), json.loads(upstream_raw)
    require(len(nb["cells"]) == 26 and len(up["cells"]) == 23, "Wrong cell count")
    for notebook in (nb, up):
        require(all(not c.get("outputs") and c.get("execution_count") is None
                    for c in notebook["cells"] if c["cell_type"] == "code"), "Notebook has outputs")
    patch_header, separator, body = cell_source(nb["cells"][4]).partition("\n")
    require(patch_header == "%%writefile /kaggle/harness-changes.patch" and separator, "Wrong patch cell")
    require(cell_source(nb["cells"][4]) == cell_source(up["cells"][2]), "Inherited patch changed")
    patch = (body + "\n").encode()
    require((root / "recipe/harness-changes.patch").read_bytes() == patch, "Patch bytes differ")
    require(pin(patch) == contract["patch"], "Patch contract mismatch")

    mapping = json.loads((root / "provenance/notebook_cell_map.json").read_text())
    require(len(mapping["inherited_cells"]) == 23, "Missing cell mapping")
    require(mapping["inserted_cells"] == [0, 1, 25], "Wrong added cells")
    changed = []
    for index, row in enumerate(mapping["inherited_cells"]):
        require(row["upstream_index"] == index and row["selected_index"] == index + 2, "Wrong cell join")
        a, b = up["cells"][index], nb["cells"][index + 2]
        require(a["cell_type"] == b["cell_type"] == row["cell_type"], "Cell type differs")
        before, after = cell_source(a), cell_source(b)
        require(row["upstream"] == pin(before.encode()) and row["selected"] == pin(after.encode()), "Cell pin differs")
        require(row["source_equal"] == (before == after), "Wrong equality claim")
        require(replay(before, row["edits"]) == after, "Cell edit replay differs")
        if before != after:
            changed.append(index + 2)
    require(changed == [18, 22], "Unexpected adapted cells")
    for index in mapping["inserted_cells"]:
        require((root / f"recipe/added_cell_{index}.txt").read_text() == cell_source(nb["cells"][index]),
                "Extracted added cell differs")
    metadata = json.loads((root / "notebook/native_metadata_observed_20261025.json").read_text())
    require(metadata["id"] == 137867577 and metadata["ref"] == "szukiyu/arc3-control-v3"
            and metadata["currentVersionNumber"] == 1, "Wrong native notebook metadata")

    require(pin(publisher.read_bytes()) == contract["publisher_archive"], "Wrong publisher archive")
    with tempfile.TemporaryDirectory(prefix="arc3-selected-source-") as tmp:
        dest = Path(tmp) / "source_bundle"
        with zipfile.ZipFile(publisher) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)) == 73, "Duplicate or missing publisher members")
            require(set(names) == set(contract["original_bundle"]), "Wrong publisher members")
            for name in names:
                rel = PurePosixPath(name)
                require(not rel.is_absolute() and ".." not in rel.parts and "\\" not in name, "Unsafe member")
                data = archive.read(name)
                require(pin(data) == contract["original_bundle"][name], "Publisher member changed")
                path = dest / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        result = subprocess.run(["git", "apply", "--include=ARC3-Inference/*",
                                 str(root / "recipe/harness-changes.patch")],
                                cwd=dest / "src", capture_output=True, text=True, timeout=30)
        require(result.returncode == 0, "Patch failed: " + result.stderr)
        generated = tree(dest)
        require(len(generated) == 79 and generated == contract["expected_effective_bundle"], "Reconstruction differs")
        require(tree(root / "effective_source") == {k:v for k,v in generated.items() if not k.endswith(".pkl")},
                "Published source differs")
    layers = json.loads((root / "provenance/source_layers.json").read_text())
    require(set(layers) == set(generated), "Source layer coverage differs")
    for name, row in layers.items():
        original = contract["original_bundle"].get(name)
        require(row["publisher"] == original and row["selected"] == generated[name], "Source layer pin differs")
        require(row["changed_by_inherited_patch"] == (original != generated[name]), "Wrong layer change flag")
    scopes = json.loads((root / "LICENSE_SCOPE.json").read_text())["files"]
    require(set(scopes) == set(actual) - {"LICENSE_SCOPE.json"}, "License scope coverage differs")
    return {"competition":"ARC-AGI-3", "passed":True, "submission_id":57034274,
            "script_version_id":356741836, "package_members":len(actual)+1,
            "selected_notebook_cells":26, "inherited_cells_unchanged":21,
            "adapted_cells":changed, "inserted_cells":[0,1,25],
            "original_files":73, "reconstructed_files":79, "published_text_files":77,
            "all_generated_hashes":generated, "target_code_executed":False,
            "pickle_deserialized":False, "historical_runtime_identity_proven":False,
            "official_score_reproduced":False, "prize_eligibility_confirmed":False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publisher-zip", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent, args.publisher_zip), indent=2))
