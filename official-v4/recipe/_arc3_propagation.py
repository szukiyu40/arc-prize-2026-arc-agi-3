"""ARC3 source-only overlay: propagate the existing deadline to the solver.

No input/runtime execution is performed by this module. Apply only after the
existing deadline and telemetry overlays; original frozen files stay unchanged.
"""
import ast
import hashlib
from pathlib import Path

EXPECTED = {
    'baseline': '4ee68c6bd053e91b86635b5f9153d3f7a151988f339a59cdb5952d0ed1311e01',
    'disclosure': 'c4235d52e42d83613234125b8e64e25927cd823acdd28ca54ceff6028b38cb6a',
}
ANCHOR = (
    '        except requests.RequestException as exc:\n'
    '            if _is_read_timeout(exc) and _yield_on_timeout_enabled():\n'
)
INSERT = (
    '        except DeadlineReached:\n'
    '            # Preserve completed usage/history in finally and let the solver\n'
    '            # classify its existing deadline signal as cancellation.\n'
    '            raise\n'
)


def patch_source(source_bytes, variant):
    expected = EXPECTED[variant]
    if hashlib.sha256(source_bytes).hexdigest() != expected:
        raise ValueError('Unrecognized frozen analyzer source: ' + variant)
    text = source_bytes.decode('utf-8')
    if text.count(ANCHOR) != 1:
        raise ValueError('Deadline handler anchor is not unique')
    changed = text.replace(ANCHOR, INSERT + ANCHOR, 1)
    before, after = ast.parse(text), ast.parse(changed)
    old_class, = [n for n in before.body if isinstance(n, ast.ClassDef) and n.name == 'ToolAgent']
    new_class, = [n for n in after.body if isinstance(n, ast.ClassDef) and n.name == 'ToolAgent']
    old_method, = [n for n in old_class.body if isinstance(n, ast.FunctionDef) and n.name == 'analyze']
    new_method, = [n for n in new_class.body if isinstance(n, ast.FunctionDef) and n.name == 'analyze']
    matches = [n for n in ast.walk(new_method) if isinstance(n, ast.Try)
               and n.handlers and isinstance(n.handlers[0].type, ast.Name)
               and n.handlers[0].type.id == 'DeadlineReached']
    handler, = matches
    added = handler.handlers.pop(0)
    if (len(added.body) != 1 or not isinstance(added.body[0], ast.Raise)
            or added.body[0].exc is not None or added.body[0].cause is not None):
        raise ValueError('Expected only a bare re-raise')
    if ast.dump(before, include_attributes=False) != ast.dump(after, include_attributes=False):
        raise ValueError('Changes beyond the single deadline handler')
    return changed.encode('utf-8')


def apply(path, variant):
    path = Path(path)
    original = path.read_bytes()
    changed = patch_source(original, variant)
    path.write_bytes(changed)
    return dict(variant=variant, input_sha256=hashlib.sha256(original).hexdigest(),
                output_sha256=hashlib.sha256(changed).hexdigest(), bytes=len(changed))
