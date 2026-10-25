#!/usr/bin/env python3
"""
Structural validator for the Aarya workflow pack (ComfyUI UI-format JSON).

Checks, per workflow file:
  * every link endpoint exists, slot indices in range, socket types match
  * node.inputs[i].link / node.outputs[j].links agree with the links table
  * subgraph-typed nodes resolve to definitions.subgraphs and match their IO arity
  * subgraph-internal links resolve inside the subgraph
  * widget counts match a per-node-type table (catches mis-ordered widgets_values)
  * Aarya assets are wired (aarya_ref.png / aarya_drive.mp4 where applicable)

Exit code 0 = all files pass.
"""
import json
import sys
import os

WIDGET_COUNTS = {
    "LoadImage": 2,
    "LoadVideo": 2,
    "MarkdownNote": 1,
    "PrimitiveStringMultiline": 1,
    "CheckpointLoaderSimple": 1,
    "LoraLoader": 3,
    "CLIPTextEncode": 1,
    "EmptyLatentImage": 3,
    "KSampler": 7,
    "VAEDecode": 0,
    "SaveImage": 1,
    "ReActorFaceSwap": 11,
}


def norm_link(lk):
    if isinstance(lk, dict):  # subgraph-internal object format
        return (lk["id"], lk["origin_id"], lk["origin_slot"],
                lk["target_id"], lk["target_slot"], lk.get("type", "*"))
    return tuple(lk)  # top-level array format


def check_links(nodes, links, scope, errors, boundary=None, warnings=None):
    warnings = warnings if warnings is not None else errors
    by_id = {n["id"]: n for n in nodes}
    if boundary:  # (subgraph_inputs, subgraph_outputs) -> pseudo boundary nodes -10 / -20
        gin, gout = boundary
        by_id[-10] = {"id": -10, "type": "__subgraph_in__", "inputs": [],
                      "outputs": [{"name": i["name"], "type": i["type"], "links": None} for i in gin]}
        by_id[-20] = {"id": -20, "type": "__subgraph_out__",
                      "inputs": [{"name": o["name"], "type": o["type"], "link": None} for o in gout],
                      "outputs": []}
    seen = set()
    for lk in links:
        lid, fn, fs, tn, ts, ttype = norm_link(lk)
        if lid in seen:
            errors.append(f"{scope}: duplicate link id {lid}")
        seen.add(lid)
        a, b = by_id.get(fn), by_id.get(tn)
        if a is None or b is None:
            errors.append(f"{scope}: link {lid} endpoint missing ({fn}->{tn})")
            continue
        if fs >= len(a.get("outputs", [])):
            errors.append(f"{scope}: link {lid} from-slot {fs} out of range on {a['type']}#{fn}")
            continue
        if ts >= len(b.get("inputs", [])):
            errors.append(f"{scope}: link {lid} to-slot {ts} out of range on {b['type']}#{tn}")
            continue
        ot = a["outputs"][fs]["type"]
        it = b["inputs"][ts]["type"]
        # union sockets are comma-joined in the frontend format ("IMAGE,MASK")
        ok_types = (set(ot.split(",")) & set(it.split(","))) or "*" in ot or "*" in it
        if not ok_types:
            errors.append(f"{scope}: link {lid} type mismatch {ot} -> {it}")
        if tn not in (-20,) and b["inputs"][ts].get("link") != lid:
            warnings.append(f"{scope}: node {tn} input {ts} does not reference link {lid}")
        if fn not in (-10,) and (a["outputs"][fs].get("links") is None or lid not in a["outputs"][fs]["links"]):
            warnings.append(f"{scope}: node {fn} output {fs} does not list link {lid}")
    # every declared input link must exist in the table
    lids = {norm_link(lk)[0] for lk in links}
    for n in nodes:
        for i, ip in enumerate(n.get("inputs", [])):
            if ip.get("link") is not None and ip["link"] not in lids:
                warnings.append(f"{scope}: node {n['id']} input {i} references dangling link {ip['link']}")
        for o, op in enumerate(n.get("outputs", [])):
            for lid in (op.get("links") or []):
                if lid not in lids:
                    warnings.append(f"{scope}: node {n['id']} output {o} lists dangling link {lid} (ignored by frontend)")


def validate(path):
    errors = []
    warns = []
    doc = json.load(open(path))
    nodes = doc.get("nodes", [])
    links = doc.get("links", []) or []
    check_links(nodes, links, os.path.basename(path), errors)

    subgraphs = {sg["id"]: sg for sg in doc.get("definitions", {}).get("subgraphs", [])}
    for n in nodes:
        t = n["type"]
        if t in subgraphs:
            sg = subgraphs[t]
            sg_in_names = {i["name"] for i in sg.get("inputs", [])}
            for ip in n.get("inputs", []):
                if ip["name"] not in sg_in_names:
                    errors.append(f"subgraph node {n['id']}: input '{ip['name']}' not in subgraph '{sg['name']}'")
            if len(n.get("outputs", [])) != len(sg.get("outputs", [])):
                errors.append(f"subgraph node {n['id']}: output arity mismatch")
        wv = n.get("widgets_values")
        if t in WIDGET_COUNTS and isinstance(wv, list):
            if len(wv) != WIDGET_COUNTS[t]:
                errors.append(f"node {n['id']} ({t}): {len(wv)} widgets, expected {WIDGET_COUNTS[t]}")
        named = n.get("widgets_values_named")
        if named and isinstance(wv, list) and len(named) != len(wv):
            errors.append(f"node {n['id']} ({t}): named widgets {len(named)} != positional {len(wv)}")

    for sg in subgraphs.values():
        check_links(sg.get("nodes", []), sg.get("links", []) or [],
                    f"{os.path.basename(path)}/{sg['name']}", errors,
                    boundary=(sg.get("inputs", []), sg.get("outputs", [])),
                    warnings=warns)

    blob = json.dumps(doc)
    if "ReActorFaceSwap" in blob:
        if "aarya_ref.png" not in blob:
            errors.append("stills workflow: aarya_ref.png not wired")
    if "WanAnimate2ToVideo" in blob:
        for asset in ("aarya_ref.png", "aarya_drive.mp4"):
            if asset not in blob:
                errors.append(f"video workflow: {asset} not wired")
    return errors, warns


def main():
    ok = True
    for path in sys.argv[1:]:
        errs, warns = validate(path)
        if errs:
            ok = False
            print(f"FAIL {path}")
            for e in errs:
                print("   -", e)
        else:
            d = json.load(open(path))
            print(f"PASS {path}  ({len(d['nodes'])} top nodes, {len(d.get('links') or [])} links, "
                  f"{len(d.get('definitions', {}).get('subgraphs', []))} subgraphs"
                  + (f", {len(warns)} warnings" if warns else "") + ")")
            for w in dict.fromkeys(warns):
                print("   ~", w)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
