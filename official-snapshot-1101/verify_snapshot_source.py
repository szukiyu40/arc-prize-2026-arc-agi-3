"""Verify the submitted ARC3 snapshot repair as source data; no agent is imported."""
import ast
import hashlib
import json
from pathlib import Path

BASE_SHA = "d376294e112d04ee2b213e30aebf02472598be10adf53e323b97a7d28b0d28a9"
FIX_SHA = "94d0b3669bfbc3e25a55df6a568d64a96008c4c8099116d836227926cd5ae58f"
TARGET = "src/ARC3-Inference/inference/agent/tool_agent.py"
ANCHOR = ("    def _record_retained_functions(self, sandbox_result, payload) -> None:\n"
          "        if not _persistent_functions():\n"
          "            return\n")
GUARD = '        if isinstance(sandbox_result, dict) and "keepable_functions" not in sandbox_result:\n            return\n'


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def tree(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Unexpected symlink")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = pin(path.read_bytes())
    return result


def require(condition, label):
    if not condition:
        raise ValueError(label)


def sources(notebook):
    return [(cell["cell_type"], "".join(cell["source"])) for cell in notebook["cells"]]


def verify(root):
    parent = root.parent / "official-v4"
    contract = json.loads((root / "source_contract.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    actual = tree(root)
    actual.pop("manifest.json")
    require(actual == manifest["files"], "Snapshot package inventory mismatch")
    require(pin((parent / "manifest.json").read_bytes()) == contract["parent_manifest"],
            "Published V4 parent changed")
    parent_actual = tree(parent)
    parent_actual.pop("manifest.json")
    require(parent_actual == json.loads((parent / "manifest.json").read_text())["files"],
            "V4 parent inventory mismatch")
    base_contract = json.loads((parent / "source_contract.json").read_text())
    expected = base_contract["expected_effective_bundle"].copy()
    require(len(expected) == 79, "Unexpected base source inventory")
    text_files = tree(parent / "effective_source")
    external = {name for name in expected if name not in text_files}
    require(external == {"benchmark_initial.pkl", "deploy_target.pkl"}, "Unexpected external files")
    require(text_files == {name: value for name, value in expected.items() if name not in external},
            "Published parent effective source mismatch")
    before = (parent / "effective_source" / TARGET).read_bytes()
    require(pin(before)["sha256"] == BASE_SHA, "Wrong pre-repair agent")
    require(before.decode().count(ANCHOR) == 1, "Ambiguous snapshot anchor")
    after = before.decode().replace(ANCHOR, ANCHOR + GUARD, 1).encode()
    require(pin(after)["sha256"] == FIX_SHA, "Repair identity mismatch")
    require((root / "effective_source" / TARGET).read_bytes() == after,
            "Included repaired agent differs")
    change = json.loads((root / "snapshot_change.json").read_text())
    require(change["anchor"] == ANCHOR and change["inserted_text"] == GUARD,
            "Guard provenance mismatch")
    expected[TARGET] = pin(after)
    require(expected == contract["expected_effective_bundle"], "Final 79-file mapping mismatch")

    base_nb = json.loads((parent / "notebook/official_v4.ipynb").read_text())
    path = root / "notebook/arc3-official-snapshot-1101.ipynb"
    require(pin(path.read_bytes()) == contract["notebook"], "Submitted notebook identity mismatch")
    new_nb = json.loads(path.read_text())
    require(len(new_nb["cells"]) == 28 and len(base_nb["cells"]) == 27,
            "Wrong notebook cell inventory")
    require(all(not c.get("outputs") and c.get("execution_count") is None
                for c in new_nb["cells"] if c["cell_type"] == "code"), "Notebook contains run output")
    actual_sources = sources(new_nb)
    overlay = actual_sources.pop(8)[1]
    require(pin(overlay.encode()) == contract["overlay_cell"], "Overlay cell identity mismatch")
    require(ast.dump(ast.parse(overlay)).startswith("Module("), "Invalid overlay syntax")
    require(overlay.startswith("if ARC3_PACKAGE_OFFICIAL:\n"), "Save branch is not inert")
    base_sources = sources(base_nb)
    # These are exact, individually enumerated source edits, not broad whitespace normalization.
    actual_sources[0] = base_sources[0]
    cell1 = actual_sources[1][1]
    replacement = ("\"policy\": 'v4_snapshot_repair', \"expected_agent_sha256\": '" + FIX_SHA + "'")
    require(cell1.count(replacement) == 1, "Unexpected packaging receipt")
    actual_sources[1] = ("code", cell1.replace(replacement, "\"policy\": 'v4'", 1))
    cell2 = actual_sources[2][1]
    require(cell2.count("arc3-official-snapshot-1101") == 2, "Unexpected run identity occurrences")
    actual_sources[2] = ("code", cell2.replace("arc3-official-snapshot-1101", "arc3-official-v4-v2-1030"))
    require(actual_sources == base_sources, "Other submitted notebook source changed")
    meta_path = root / "notebook/original_kernel_metadata.json"
    require(pin(meta_path.read_bytes()) == contract["metadata"], "Original metadata changed")
    meta = json.loads(meta_path.read_text())
    base_meta = json.loads((parent / "notebook/original_kernel_metadata.json").read_text())
    for key in ["id", "title", "code_file"]:
        meta[key] = base_meta[key]
    # Enumerate the two omitted publisher/UI fields. Native readback separately
    # confirms the requested container digest and GPU.
    require(base_meta.get("keywords") == ["gpu"] and "keywords" not in meta,
            "Unexpected keywords difference")
    require(base_meta.get("docker_image_pinning_type") == "original"
            and "docker_image_pinning_type" not in meta, "Unexpected pinning-type difference")
    base_meta.pop("keywords")
    base_meta.pop("docker_image_pinning_type")
    require(meta == base_meta, "Runtime/input metadata differs from official V4")
    return {"competition": "ARC-AGI-3", "status": "SNAPSHOT_SOURCE_VERIFIED",
            "all79_effective_hashes": expected, "external_pickles_checked_as_bytes_by_parent_verifier": sorted(external),
            "parent_package_and77_source_files_verified": True, "only_agent_file_changed": TARGET,
            "agent_sha256": FIX_SHA, "all28_notebook_cells_pinned": True,
            "notebook_difference": "Markdown/receipt/run identity and one guarded overlay cell only",
            "metadata_omissions": ["keywords", "docker_image_pinning_type"],
            "model_game_notebook_or_pickle_executed": False,
            "official_score_or_eligibility_reproduced": False}


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent), indent=2))
