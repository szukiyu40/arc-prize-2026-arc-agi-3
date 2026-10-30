"""Verify the ARC3 V4 draft from an external, pinned publisher ZIP.

Usage: python3 -B verify_public_source.py --publisher-zip /path/to/archive.zip
No network, package installation, notebook/model/game execution or unpickling.
Only reviewed source-transform helpers execute after all package hashes pass.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tempfile
import zipfile


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def tree(root):
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Symlink in package")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = pin(path.read_bytes())
    return result


def load_original(archive, destination, contract):
    raw = archive.read_bytes()
    require(pin(raw) == contract["publisher_archive"], "Wrong publisher ZIP")
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), "Duplicate archive members")
        require(set(names) == set(contract["original_bundle"]), "Unexpected archive paths")
        for name in names:
            rel = PurePosixPath(name)
            require(not rel.is_absolute() and ".." not in rel.parts and "\\" not in name,
                    "Unsafe archive path")
            data = z.read(name)
            require(pin(data) == contract["original_bundle"][name], "Changed original: " + name)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return tree(destination)


def extract(notebook):
    patch_calls = [n for n in ast.walk(ast.parse("".join(notebook["cells"][5]["source"])))
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "write_text"]
    require(len(patch_calls) == 1, "Ambiguous notebook patch")
    patch = ast.literal_eval(patch_calls[0].args[0]).encode()
    names = {"_arc3_overlay_namespace", "_arc3_legacy_telemetry",
             "_arc3_minimal_telemetry", "_arc3_propagation"}
    helpers = {}
    for node in ast.walk(ast.parse("".join(notebook["cells"][7]["source"]))):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "exec" and len(node.args) == 2
                and isinstance(node.args[1], ast.Name) and node.args[1].id in names):
            name = node.args[1].id
            require(name not in helpers, "Duplicate transform")
            helpers[name] = ast.literal_eval(node.args[0]).encode()
    require(set(helpers) == names, "Missing transforms")
    return patch, helpers


def verify(root, archive):
    manifest = json.loads((root / "manifest.json").read_text())
    actual = tree(root)
    actual.pop("manifest.json")
    require(actual == manifest["files"], "Package inventory or hash mismatch")
    c = json.loads((root / "source_contract.json").read_text())
    nb_raw = (root / "notebook/official_v4.ipynb").read_bytes()
    require(pin(nb_raw) == c["notebook"], "Notebook hash mismatch")
    notebook = json.loads(nb_raw)
    require(len(notebook["cells"]) == 27, "Wrong notebook cell count")
    require(all(not cell.get("outputs") and cell.get("execution_count") is None
                for cell in notebook["cells"] if cell["cell_type"] == "code"),
            "Notebook carries execution output")
    patch, helpers = extract(notebook)
    require(pin(patch) == c["patch"] and (root / "recipe/harness-changes.patch").read_bytes() == patch,
            "Patch mismatch")
    require({name: pin(data) for name, data in helpers.items()} == c["helpers"], "Helper mismatch")
    for name, data in helpers.items():
        require((root / "recipe" / (name + ".py")).read_bytes() == data, "Extracted helper mismatch")
    support_targets = {"_arc3_deadline_file": "arc3_deadline.py", "_path": "arc3_ready.py"}
    support = {}
    for node in ast.walk(ast.parse("".join(notebook["cells"][2]["source"]))):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "write_text" and isinstance(node.func.value, ast.Name)
                and node.func.value.id in support_targets):
            name = support_targets[node.func.value.id]
            require(name not in support, "Duplicate support module")
            support[name] = ast.literal_eval(node.args[0]).encode()
    require(set(support) == set(support_targets.values()), "Missing support module")
    for name, data in support.items():
        require((root / "notebook_support" / name).read_bytes() == data, "Support module mismatch")
    with tempfile.TemporaryDirectory(prefix="arc3-public-source-") as temporary:
        destination = Path(temporary) / "source_bundle"
        original = load_original(archive, destination, c)
        command = subprocess.run(["git", "apply", "--include=ARC3-Inference/*",
                                  str((root / "recipe/harness-changes.patch").resolve())],
                                 cwd=destination / "src", capture_output=True, text=True, timeout=30)
        require(command.returncode == 0, "Patch failed: " + command.stderr)
        modules = {}
        for name, data in helpers.items():
            namespace = {"__name__": "source_only_reproduction"}
            exec(compile(data, name, "exec"), namespace)
            modules[name] = namespace
        pins = modules["_arc3_overlay_namespace"]["apply_overlay"](destination / "src")
        modules["_arc3_minimal_telemetry"]["patch_runtime"](
            destination / "src", pins, modules["_arc3_legacy_telemetry"])
        modules["_arc3_propagation"]["apply"](
            destination / "src/ARC3-Inference/inference/agent/tool_agent.py", "baseline")
        generated = tree(destination)
        require(generated == c["expected_effective_bundle"], "Effective source hash mismatch")
        text_files = {k: v for k, v in generated.items() if not k.endswith(".pkl")}
        require(tree(root / "effective_source") == text_files, "Published text differs")
    return {"competition": "ARC-AGI-3", "status": "SOURCE_RECONSTRUCTION_VERIFIED",
            "python": sys.version, "implementation": platform.python_implementation(),
            "git": subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
            "package_file_count": len(actual), "original_file_count": len(original),
            "effective_file_count": len(generated), "published_effective_text_count": len(text_files),
            "notebook_support_modules_matched": len(support),
            "all_generated_hashes": generated, "source_transform_helpers_executed": True,
            "notebook_model_game_executed": False, "pickle_deserialized": False,
            "official_score_reproduced": False, "prize_eligibility_confirmed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publisher-zip", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent, args.publisher_zip), indent=2))
