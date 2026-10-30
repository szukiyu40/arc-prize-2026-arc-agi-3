"""Check ARC3 contribution maps by replaying their text edits as data.

No Python source-transform helper, notebook, pickle, model or game is executed.
The known inherited source patch is applied by Git in temporary storage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from verify_public_source import pin, require, tree, load_original


def verify(root, archive):
    manifest = json.loads((root / "manifest.json").read_text())
    actual = tree(root)
    actual.pop("manifest.json")
    require(actual == manifest["files"], "Package inventory mismatch")
    contract = json.loads((root / "source_contract.json").read_text())
    mapping = json.loads((root / "provenance/source_layer_map.json").read_text())
    edits = json.loads((root / "provenance/submitter_hunk_map.json").read_text())
    require(pin((root / "recipe/harness-changes.patch").read_bytes()) == contract["patch"], "Patch identity mismatch")
    require(len(mapping["files"]) == 79 and len({x["path"] for x in mapping["files"]}) == 79, "Layer inventory mismatch")
    expected = lambda stage: {x["path"]:x["states"][stage] for x in mapping["files"] if x["states"][stage] is not None}
    require(expected("publisher") == contract["original_bundle"], "Original layer mismatch")
    require(expected("local_deadline_propagation") == contract["expected_effective_bundle"], "Final layer mismatch")
    stages = ["inherited_patch", "local_overlay", "local_telemetry", "local_deadline_propagation"]
    require(all((x["from_stage"],x["to_stage"]) in list(zip(stages,stages[1:])) for x in edits["file_edits"]), "Unexpected edit stage")
    require(len({(x["from_stage"],x["to_stage"],x["path"]) for x in edits["file_edits"]}) == len(edits["file_edits"]), "Duplicate file edit")
    total_hunks = 0
    with tempfile.TemporaryDirectory(prefix="arc3-contribution-replay-") as temp:
        destination = Path(temp) / "source_bundle"
        load_original(archive, destination, contract)
        result = subprocess.run(["git","apply","--include=ARC3-Inference/*",str((root / "recipe/harness-changes.patch").resolve())],
            cwd=destination / "src",capture_output=True,text=True,timeout=30)
        require(result.returncode == 0, "Inherited patch failed")
        require(tree(destination) == expected("inherited_patch"), "Inherited layer mismatch")
        for before_stage, after_stage in zip(stages,stages[1:]):
            for edit in edits["file_edits"]:
                if (edit["from_stage"],edit["to_stage"]) != (before_stage,after_stage):
                    continue
                name = edit["path"]
                require(name in expected(before_stage), "Unknown edited path")
                target = destination / name
                raw = target.read_bytes()
                require(pin(raw) == edit["before"], "Before-file identity mismatch")
                lines = raw.decode().splitlines(keepends=True)
                result_lines = []
                cursor = 0
                for hunk in edit["hunks"]:
                    start,end = hunk["before_zero_based_half_open"]
                    require(0 <= cursor <= start <= end <= len(lines), "Invalid or overlapping hunk range")
                    removed = "".join(lines[start:end]).encode()
                    require(pin(removed) == hunk["removed"], "Removed text hash mismatch")
                    require(pin(hunk["added_text"].encode()) == hunk["added"], "Added text hash mismatch")
                    result_lines.extend(lines[cursor:start])
                    after_start = len(result_lines)
                    inserted = hunk["added_text"].splitlines(keepends=True)
                    result_lines.extend(inserted)
                    require([after_start,len(result_lines)] == hunk["after_zero_based_half_open"], "After range mismatch")
                    cursor = end
                    total_hunks += 1
                result_lines.extend(lines[cursor:])
                after = "".join(result_lines).encode()
                require(pin(after) == edit["after"], "After-file identity mismatch")
                target.write_bytes(after)
            require(tree(destination) == expected(after_stage), "Intermediate layer mismatch: " + after_stage)
        final = tree(destination)
        require(final == contract["expected_effective_bundle"], "Official source mismatch")
    return {"competition":"ARC-AGI-3","status":"CONTRIBUTION_MAP_REPLAY_VERIFIED",
        "file_edits":len(edits["file_edits"]),"distinct_files":len({x["path"] for x in edits["file_edits"]}),
        "hunks":total_hunks,"all79_generated_hashes":final,"python_source_transform_helpers_executed":False,
        "notebook_model_game_or_pickle_executed":False,"legal_authorship_or_eligibility_proven":False}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--publisher-zip", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent, args.publisher_zip), indent=2))
