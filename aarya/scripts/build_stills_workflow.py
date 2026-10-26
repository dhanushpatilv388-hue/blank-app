#!/usr/bin/env python3
"""
Emit aarya_stills_facelock_cpu.json - a CPU-only (no GPU needed) still-image workflow
that generates a portrait and face-locks it to Aarya with ReActor (inswapper + CodeFormer).

Runs on integrated graphics / CPU-only machines (e.g. Intel UHD + 16 GB RAM laptops):
SD1.5 + LCM LoRA = 6 sampling steps at 512x768, then face swap + restore.

Node schemas verified against:
  - ComfyUI 0.42 nodes.py (CheckpointLoaderSimple, CLIPTextEncode, EmptyLatentImage,
    KSampler, VAEDecode, SaveImage, LoadImage, LoraLoader)
  - Gourieff/ComfyUI-ReActor nodes.py (ReActorFaceSwap)
"""
import json
import os
import sys

POS = ("portrait photo of Aarya, a young Indian woman ~23, warm wheat-brown skin, long "
       "jet-black wavy hair with a centre parting, small round black bindi on her forehead, "
       "tiny silver nose stud in her left nostril, dark brown almond eyes, nude-pink lips, "
       "wearing a bright orange cropped cami top and blush-pink sequin skirt, soft window "
       "light, 85mm, sharp focus, detailed skin")

NEG = ("worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, "
       "poorly drawn face, mutation, deformed, bad anatomy, bad proportions, extra limbs, "
       "disfigured, gross proportions, malformed limbs, missing arms, cross-eyed, blurry")


def node(nid, ntype, pos, size, inputs, outputs, widgets=None, named=None, title=None, order=0):
    n = {
        "id": nid, "type": ntype, "pos": list(pos), "size": list(size),
        "flags": {}, "order": order, "mode": 0,
        "inputs": inputs, "outputs": outputs, "properties": {"Node name for S&R": ntype},
    }
    if title:
        n["title"] = title
    if widgets is not None:
        n["widgets_values"] = widgets
    if named is not None:
        n["widgets_values_named"] = named
    return n


def inp(name, ntype, link=None):
    return {"name": name, "type": ntype, "link": link}


def out(name, ntype, links):
    return {"name": name, "type": ntype, "links": links}


def build():
    nodes, links = [], []

    def L(lid, fn, fs, tn, ts, ttype):
        links.append([lid, fn, fs, tn, ts, ttype])

    # 1 - Aarya source face
    nodes.append(node(1, "LoadImage", [-1200, 200], [400, 500], [],
                      [out("IMAGE", "IMAGE", [21]), out("MASK", "MASK", None)],
                      widgets=["aarya_ref.png", "image"],
                      named={"image": "aarya_ref.png", "upload": "image"},
                      title="AARYA - Source Face (swap target identity)", order=0))
    # 2 - checkpoint
    nodes.append(node(2, "CheckpointLoaderSimple", [-1200, -350], [400, 100], [],
                      [out("MODEL", "MODEL", [10]), out("CLIP", "CLIP", [11]), out("VAE", "VAE", [12])],
                      widgets=["v1-5-pruned-emaonly-fp16.safetensors"],
                      named={"ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"}, order=1))
    # 6 - LCM lora (few steps => CPU-feasible)
    nodes.append(node(6, "LoraLoader", [-760, -350], [400, 130],
                      [inp("model", "MODEL", 10), inp("clip", "CLIP", 11)],
                      [out("MODEL", "MODEL", [13]), out("CLIP", "CLIP", [14, 15])],
                      widgets=["lcm-lora-sdv1-5.safetensors", 1.0, 1.0],
                      named={"lora_name": "lcm-lora-sdv1-5.safetensors",
                             "strength_model": 1.0, "strength_clip": 1.0}, order=2))
    # 3 - positive prompt
    nodes.append(node(3, "CLIPTextEncode", [-320, -450], [420, 180], [inp("clip", "CLIP", 14)],
                      [out("CONDITIONING", "CONDITIONING", [16])],
                      widgets=[POS], named={"text": POS},
                      title="CLIP Text Encode (Aarya scene prompt)", order=3))
    # 4 - negative prompt
    nodes.append(node(4, "CLIPTextEncode", [-320, -220], [420, 160], [inp("clip", "CLIP", 15)],
                      [out("CONDITIONING", "CONDITIONING", [17])],
                      widgets=[NEG], named={"text": NEG},
                      title="CLIP Text Encode (Negative)", order=4))
    # 5 - empty latent
    nodes.append(node(5, "EmptyLatentImage", [-320, 0], [400, 110], [],
                      [out("LATENT", "LATENT", [18])],
                      widgets=[512, 768, 1],
                      named={"width": 512, "height": 768, "batch_size": 1}, order=5))
    # 7 - ksampler (LCM: 6 steps, cfg 1.5)
    nodes.append(node(7, "KSampler", [150, -300], [320, 260],
                      [inp("model", "MODEL", 13), inp("positive", "CONDITIONING", 16),
                       inp("negative", "CONDITIONING", 17), inp("latent_image", "LATENT", 18)],
                      [out("LATENT", "LATENT", [19])],
                      widgets=[88123412, "randomize", 6, 1.5, "lcm", "sgm_uniform", 1.0],
                      named={"seed": 88123412, "control_after_generate": "randomize",
                             "steps": 6, "cfg": 1.5, "sampler_name": "lcm",
                             "scheduler": "sgm_uniform", "denoise": 1.0}, order=6))
    # 8 - vae decode
    nodes.append(node(8, "VAEDecode", [520, -300], [220, 60],
                      [inp("samples", "LATENT", 19), inp("vae", "VAE", 12)],
                      [out("IMAGE", "IMAGE", [20])], order=7))
    # 9 - reactor face swap
    nodes.append(node(9, "ReActorFaceSwap", [520, 100], [420, 330],
                      [inp("input_image", "IMAGE", 20), inp("source_image", "IMAGE", 21),
                       inp("face_model", "FACE_MODEL", None), inp("face_boost", "FACE_BOOST", None)],
                      [out("SWAPPED_IMAGE", "IMAGE", [22]), out("FACE_MODEL", "FACE_MODEL", None),
                       out("ORIGINAL_IMAGE", "IMAGE", None)],
                      widgets=[True, "inswapper_128.onnx", "retinaface_resnet50",
                               "codeformer-v0.1.0.pth", 1.0, 0.5, "no", "no", "0", "0", 1],
                      named={"enabled": True, "swap_model": "inswapper_128.onnx",
                             "facedetection": "retinaface_resnet50",
                             "face_restore_model": "codeformer-v0.1.0.pth",
                             "face_restore_visibility": 1.0, "codeformer_weight": 0.5,
                             "detect_gender_input": "no", "detect_gender_source": "no",
                             "input_faces_index": "0", "source_faces_index": "0",
                             "console_log_level": 1},
                      title="ReActor - Face-Lock to AARYA", order=8))
    # 10 - save
    nodes.append(node(10, "SaveImage", [1000, 100], [400, 400], [inp("images", "IMAGE", 22)],
                      [], widgets=["aarya/still"], named={"filename_prefix": "aarya/still"},
                      title="Save Aarya Still", order=9))

    L(10, 2, 0, 6, 0, "MODEL")
    L(11, 2, 1, 6, 1, "CLIP")
    L(12, 2, 2, 8, 1, "VAE")
    L(13, 6, 0, 7, 0, "MODEL")
    L(14, 6, 1, 3, 0, "CLIP")
    L(15, 6, 1, 4, 0, "CLIP")
    L(16, 3, 0, 7, 1, "CONDITIONING")
    L(17, 4, 0, 7, 2, "CONDITIONING")
    L(18, 5, 0, 7, 3, "LATENT")
    L(19, 7, 0, 8, 0, "LATENT")
    L(20, 8, 0, 9, 0, "IMAGE")
    L(21, 1, 0, 9, 1, "IMAGE")
    L(22, 9, 0, 10, 0, "IMAGE")

    doc = {
        "id": "aarya-stills-facelock-cpu",
        "revision": 0,
        "last_node_id": 10,
        "last_link_id": 22,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "definitions": {"subgraphs": []},
        "config": {},
        "extra": {
            "aarya_pack": {
                "purpose": "CPU-only face-locked stills of Aarya (SD1.5 + LCM + ReActor)",
                "reference_image": "input/aarya_ref.png",
                "needs_custom_node": "ComfyUI-ReActor (Gourieff/ComfyUI-ReActor)",
            }
        },
        "version": 0.4,
    }
    return doc


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "aarya_stills_facelock_cpu.json")
    with open(path, "w") as f:
        json.dump(build(), f, indent=2)
    print("wrote", path)
