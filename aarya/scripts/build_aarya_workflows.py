#!/usr/bin/env python3
"""
Build the AARYA ComfyUI workflow pack.

Derives the two GPU video workflows from the OFFICIAL Comfy-Org workflow templates
(video_wan_animate2.json / video_wan_animate2_distilled.json, repo: Comfy-Org/workflow_templates)
and re-targets them at Aarya:

  * loader nodes renamed + pointed at aarya_ref.png / aarya_drive.mp4
  * prompts pre-filled with an Aarya character/motion template
  * WanAnimate2Cache moved to CPU (avoids VRAM spikes, per official tips)
  * an "AARYA PACK - START HERE" note added on the canvas
  * save prefixes set to video/aarya

Usage:
    python3 build_aarya_workflows.py /path/to/workflow_templates/templates /path/to/out_dir
"""
import json
import os
import sys

CHARACTER_PROMPT = (
    "Character Description: Aarya - a young Indian woman, ~23 years old, warm wheat-brown skin, "
    "long jet-black wavy hair with a centre parting falling past her chest, a small round black "
    "bindi between her brows, a tiny silver stud in her left nostril, dark brown almond eyes, "
    "soft natural dark brows, nude-pink medium-full lips, slim graceful build; wearing a bright "
    "orange cropped spaghetti-strap cami top and a blush-pink sequin skirt; photorealistic, "
    "identical face in every frame.\n"
    "Background description: <DESCRIBE SCENE, e.g. a sun-lit Mumbai seafront promenade at golden "
    "hour, shallow depth of field>"
)
POSE_PROMPT = (
    "A person performing exactly the motion, hand gestures, head movement and camera framing "
    "of the driving video"
)

AARYA_NOTE = """# AARYA PACK - START HERE

This workflow is pre-wired for **Aarya**: one reference image (WHO) + one driving video
(WHAT MOTION) = Aarya performing that motion, identity locked.

## Do this, in order
1. Update ComfyUI to **>= 0.42.0** (WanAnimate2 nodes are native; older builds will show red/missing nodes).
2. Download the models listed in the **Model Links** note (right side of canvas) into the folders it shows.
3. Copy your assets into `ComfyUI/input/`:
   - `aarya_ref.png`  - the single best photo of Aarya (front-facing, even light, face sharp)
   - `aarya_drive.mp4` - the video whose motion Aarya must perform (16-24 fps, one person, full body)
   Ready-made refs ship in this pack under `aarya/references/`: copy
   `aarya_ref_front_bust.png` (default) or `aarya_ref_fullbody.png` (full-body drive videos)
   to `ComfyUI/input/aarya_ref.png`. Identity markers + prompts: `aarya/AARYA_IDENTITY.md`.
4. On **AARYA - 1 Reference Image** and **AARYA - 2 Driving Video** nodes, click refresh/upload and pick those files.
5. Open the **Motion Transfer** subgraph (double-click it) and edit the two prompts:
   - character prompt: replace the `<DESCRIBE OUTFIT>` / `<DESCRIBE SCENE>` placeholders
   - pose prompt: describe the motion in your driving video in one sentence
6. Queue Prompt. Output lands in `ComfyUI/output/video/aarya_*.mp4`.

## Hardware reality check
- This workflow needs an **NVIDIA GPU with >= 16 GB VRAM** (24 GB comfortable), or a cloud GPU.
- On a laptop with Intel/AMD integrated graphics it will NOT run - use
  `aarya_stills_facelock_cpu.json` from this pack for CPU-only still images of Aarya,
  or rent a GPU (see aarya/README.md, "Run on a cloud GPU").

## Getting an EXACT likeness
- Framing match is everything: if the driving video is full-body, the reference photo should
  show Aarya full-body too (or at least the same crop level).
- One person in the driving video. Busy backgrounds in the drive video are ignored -
  the background comes from your prompt.
- Identity drift over long clips? Raise `reference_image_strength` to 1.2-1.5.
"""

ASSETS_NOTE = """

---

### Your Aarya assets (replace the sample files)
The links above are the *sample* assets used by the official template. For Aarya, put your
own files in `ComfyUI/input/` and select them on the two loader nodes:
- `aarya_ref.png` - best single reference photo of Aarya (clear front-facing face, good light)
- `aarya_drive.mp4` - the video whose motion Aarya should perform
"""


def set_named(node, key, value):
    """Set a widget value by its named key, keeping positional widgets_values in sync."""
    named = node.get("widgets_values_named")
    if named is not None and key in named:
        keys = list(named.keys())
        idx = keys.index(key)
        wv = node.get("widgets_values")
        if isinstance(wv, list) and idx < len(wv):
            wv[idx] = value
        named[key] = value
        return True
    wv = node.get("widgets_values")
    return False


def iter_all_nodes(doc):
    for n in doc.get("nodes", []):
        yield n
    for sg in doc.get("definitions", {}).get("subgraphs", []):
        for n in sg.get("nodes", []):
            yield n


def patch(doc, variant):
    subgraph_ids = {sg["id"]: sg["name"] for sg in doc.get("definitions", {}).get("subgraphs", [])}
    load_image = load_video = None
    for n in doc.get("nodes", []):
        t = n["type"]
        if t == "LoadImage":
            load_image = n
            n["title"] = "AARYA - 1 Reference Image (WHO)"
            set_named(n, "image", "aarya_ref.png")
        elif t == "LoadVideo":
            load_video = n
            n["title"] = "AARYA - 2 Driving Video (MOTION)"
            set_named(n, "file", "aarya_drive.mp4")
        elif t == "SaveVideo":
            set_named(n, "filename_prefix", "video/aarya")
        elif t == "MarkdownNote":
            title = n.get("title", "")
            if title == "Model Links":
                txt = n["widgets_values_named"].get("text") or n["widgets_values"][0]
                if ASSETS_NOTE.strip()[:40] not in txt:
                    txt = txt + ASSETS_NOTE
                    set_named(n, "text", txt)
        elif t in subgraph_ids and "Motion Transfer" in subgraph_ids[t]:
            # prompt widgets exposed on the subgraph node itself
            if variant == "full":
                set_named(n, "text_1", CHARACTER_PROMPT)
                set_named(n, "text_2", POSE_PROMPT)
            else:
                set_named(n, "text", CHARACTER_PROMPT)
                set_named(n, "text_4", POSE_PROMPT)
        elif t == "PrimitiveStringMultiline":
            title = n.get("title", "")
            if "Character Prompt" in title:
                set_named(n, "value", CHARACTER_PROMPT)
            elif "Post Prompt" in title:
                set_named(n, "value", POSE_PROMPT)

    # cache on system RAM instead of VRAM (official tip, avoids VRAM spikes)
    for n in iter_all_nodes(doc):
        if n["type"] == "WanAnimate2Cache":
            wv = n.get("widgets_values")
            if isinstance(wv, list) and wv:
                wv[0] = "cpu"
            for k in ("device", "device_1"):
                set_named(n, k, "cpu")

    # add (or refresh) the START HERE note next to the reference-image loader
    if load_image is not None:
        existing = next((x for x in doc["nodes"]
                         if x["type"] == "MarkdownNote"
                         and x.get("title") == "AARYA PACK - START HERE"), None)
        if existing is not None:
            existing["widgets_values"] = [AARYA_NOTE]
            existing.setdefault("widgets_values_named", {})["text"] = AARYA_NOTE
            return doc
        note = {
            "id": doc["last_node_id"] + 1,
            "type": "MarkdownNote",
            "pos": [load_image["pos"][0] - 700, load_image["pos"][1]],
            "size": [640, 1000],
            "flags": {},
            "order": max((x.get("order", 0) for x in doc["nodes"]), default=0) + 1,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "title": "AARYA PACK - START HERE",
            "properties": {},
            "widgets_values": [AARYA_NOTE],
            "widgets_values_named": {"text": AARYA_NOTE},
            "color": "#233",
            "bgcolor": "#012",
        }
        doc["nodes"].append(note)
        doc["last_node_id"] = note["id"]
    return doc


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    tpl_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    jobs = [
        ("video_wan_animate2.json", "aarya_video_wan_animate2_gpu.json", "full"),
        ("video_wan_animate2_distilled.json", "aarya_video_wan_animate2_distilled_gpu.json", "distilled"),
    ]
    for src, dst, variant in jobs:
        src_path = os.path.join(tpl_dir, src)
        if not os.path.exists(src_path):  # self-contained re-patch of our own output
            src_path = os.path.join(out_dir, dst)
            if not os.path.exists(src_path):
                raise SystemExit(f"neither template nor existing output found: {src_path}")
            print(f"note: official template missing, re-patching {src_path} in place")
        with open(src_path) as f:
            doc = json.load(f)
        doc = patch(doc, variant)
        doc.setdefault("extra", {})["aarya_pack"] = {
            "derived_from": f"Comfy-Org/workflow_templates/{src}",
            "variant": variant,
            "reference_image": "input/aarya_ref.png",
            "driving_video": "input/aarya_drive.mp4",
        }
        with open(os.path.join(out_dir, dst), "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        print("wrote", os.path.join(out_dir, dst), f"({len(doc['nodes'])} top-level nodes)")


if __name__ == "__main__":
    main()
