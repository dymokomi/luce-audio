#!/usr/bin/env python3
"""Append node kinds to src/kinds.lucb and dispatch them in src/program.lucb.

    tools/add_kind.py spec.json

spec.json: a list of {"name", "constant", "category", "inputs", "outputs",
"doc", "call" (e.g. "models.sem"), "params": [{"name", "min", "max",
"initial", "units", "items"?, "log"?}]}. Indices and table sizes are kept
right; existing kinds never move."""
import json, re, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "src"
kinds_path = root / "kinds.lucb"
program_path = root / "program.lucb"
spec = json.loads(Path(sys.argv[1]).read_text())
k = kinds_path.read_text()
p = program_path.read_text()

params_size = int(re.search(r"pub let params: ParamSpec\[(\d+)\]", k).group(1))
kinds_size = int(re.search(r"pub let kinds: KindSpec\[(\d+)\]", k).group(1))
count = int(re.search(r"pub let count: u32 = (\d+)", k).group(1))
assert count == kinds_size

def lit(x):
    s = repr(float(x))
    return s if "e" not in s else f"{float(x):.10f}"

param_lines, kind_lines, constants, dispatch = [], [], [], []
for kind in spec:
    first = params_size
    param_lines.append(f"    # {first} {kind['name'].lower()}: {len(kind['params'])}")
    for q in kind["params"]:
        extra = ""
        if q.get("items"):
            extra += f', items = "{q["items"]}"'
        if q.get("log"):
            extra += ", logarithmic = true"
        param_lines.append(f'    ParamSpec(name = "{q["name"]}", minimum = {lit(q["min"])}, maximum = {lit(q["max"])}, initial = {lit(q["initial"])}, units = "{q.get("units", "")}"{extra}),')
    params_size += len(kind["params"])
    doc = kind["doc"].replace('"', "'")
    kind_lines.append(f'    KindSpec(name = "{kind["name"]}", category = "{kind["category"]}", inputs = "{kind["inputs"]}", outputs = "{kind["outputs"]}", first = {first}, count = {len(kind["params"])},\n             doc = "{doc}"),')
    constants.append(f"pub let {kind['constant']}: u32 = {count}")
    dispatch.append(f"        elif kind == kinds.{kind['constant']}: {kind['call']}(state, &ports)")
    count += 1

k = re.sub(r"pub let params: ParamSpec\[\d+\] = \[", f"pub let params: ParamSpec[{params_size}] = [", k)
k = re.sub(r"pub let kinds: KindSpec\[\d+\] = \[", f"pub let kinds: KindSpec[{count}] = [", k)
# the params table ends at the first "\n]\n" after its start
start = k.index("pub let params: ParamSpec[")
end = k.index("\n]\n", start)
k = k[:end] + "\n" + "\n".join(param_lines) + k[end:]
start = k.index("pub let kinds: KindSpec[")
end = k.index("\n]\n", start)
k = k[:end] + "\n" + "\n".join(kind_lines) + k[end:]
k = re.sub(r"pub let count: u32 = \d+", "\n".join(constants) + f"\npub let count: u32 = {count}", k)
kinds_path.write_text(k)

marker = "        elif kind == kinds.ladder: models.ladder(state, &ports)"
anchor = p.rindex("        elif kind == kinds.")
line_end = p.index("\n", anchor)
p = p[:line_end] + "\n" + "\n".join(dispatch) + p[line_end:]
program_path.write_text(p)
print(f"added {len(spec)} kinds; {count} in all, {params_size} parameters")
