import json
import os

import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
WF_DIR = os.path.join(HERE, "aarya", "workflows")

st.set_page_config(page_title="Aarya Studio", page_icon="🎭", layout="wide")

st.title("🎭 Aarya Studio — ComfyUI Identity Pack")
st.caption(
    "Reference image (WHO) + driving video (MOTION) → Aarya performs it, identity locked. "
    "Workflows validated against ComfyUI 0.42 node schemas."
)

# ---------------------------------------------------------------- sidebar: hardware
st.sidebar.header("Your hardware")
hw = st.sidebar.radio(
    "Where will you run it?",
    [
        "This laptop (Intel UHD, no NVIDIA GPU)",
        "NVIDIA 12–16 GB VRAM",
        "NVIDIA 24 GB+ VRAM",
        "Cloud GPU (RunPod / vast.ai)",
    ],
    index=0,
)
VERDICT = {
    0: ("🟥 Video workflows will NOT run here (no CUDA GPU). Use the **CPU stills** workflow "
        "with `--cpu`, or rent a GPU for videos.", ["stills"]),
    1: ("🟨 Use the **distilled** video workflow (int8, cache on CPU) at 480×832, or the stills "
        "workflow locally.", ["distilled", "stills"]),
    2: ("🟩 Full pack available: **full** video workflow at 480×832–720p, plus stills.",
        ["full", "distilled", "stills"]),
    3: ("🟩 Full pack available on a 24 GB pod (RTX 4090/A40/L40S). ~$0.02–0.06 per 81-frame clip.",
        ["full", "distilled", "stills"]),
}
idx = ["This laptop (Intel UHD, no NVIDIA GPU)", "NVIDIA 12–16 GB VRAM",
       "NVIDIA 24 GB+ VRAM", "Cloud GPU (RunPod / vast.ai)"].index(hw)
st.sidebar.success(VERDICT[idx][0])
recommended = VERDICT[idx][1]

WORKFLOWS = [
    {
        "key": "full",
        "file": "aarya_video_wan_animate2_gpu.json",
        "name": "Aarya Video — Wan-Animate-2 (full)",
        "hw": "NVIDIA ≥ 16 GB VRAM / cloud",
        "desc": ("14B int8 DiT + LightX2V distill LoRA, 6 steps, context windows, auto-chunks long "
                 "driving videos in 81-frame segments with seamless continuation."),
        "models": ["wan_animate_2_int8_convrot.safetensors (~15.5 GB)",
                   "lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors (~704 MB)",
                   "umt5_xxl_fp8_e4m3fn_scaled.safetensors (~6.3 GB)",
                   "clip_vision_h.safetensors (~1.2 GB)",
                   "Wan2_1_VAE_bf16.safetensors (~242 MB)"],
    },
    {
        "key": "distilled",
        "file": "aarya_video_wan_animate2_distilled_gpu.json",
        "name": "Aarya Video — Wan-Animate-2 (distilled)",
        "hw": "NVIDIA ≥ 12 GB VRAM / cloud",
        "desc": ("Distilled 10-step variant, no LoRA slot, ships a pre-wired 2nd segment for longer "
                 "clips. Slightly softer detail, noticeably faster."),
        "models": ["wan_animate_2_distill_int8_convrot.safetensors (~15.5 GB)",
                   "umt5_xxl_fp8_e4m3fn_scaled.safetensors (~6.3 GB)",
                   "clip_vision_h.safetensors (~1.2 GB)",
                   "Wan2_1_VAE_bf16.safetensors (~242 MB)"],
    },
    {
        "key": "stills",
        "file": "aarya_stills_facelock_cpu.json",
        "name": "Aarya Stills — Face-Lock (CPU / your laptop)",
        "hw": "CPU / integrated graphics",
        "desc": ("SD1.5 + LCM LoRA (6 steps @ 512×768) → ReActor inswapper_128 face-swap → CodeFormer "
                 "restore. ~1–3 min per image on CPU. Needs the ComfyUI-ReActor custom node."),
        "models": ["v1-5-pruned-emaonly-fp16.safetensors (any SD1.5 ckpt)",
                   "lcm-lora-sdv1-5.safetensors (~134 MB)",
                   "inswapper_128.onnx (~500 MB)",
                   "codeformer-v0.1.0.pth (~360 MB)"],
    },
]

tabs = st.tabs(["🎭 Identity", "📦 Workflows", "🧰 Models checklist", "📸 Prep guide",
                "☁️ Cloud run", "📖 README"])

# ---------------------------------------------------------------- identity tab
with tabs[0]:
    st.subheader("Locked identity markers")
    refs = os.path.join(HERE, "aarya", "references")
    c1, c2, c3, c4 = st.columns(4)
    for col, fn, cap in [
        (c1, "aarya_ref_front_bust.png", "Look A — signature\n(WanAnimate2 reference_image)"),
        (c2, "aarya_face_direct.png", "Face lock\n(ReActor source_image)"),
        (c3, "aarya_ref_fullbody.png", "Full-body ref\n(full-body drive videos)"),
        (c4, "aarya_charactersheet_01.jpeg", "Character sheet 01\n(QA target / LoRA set)"),
    ]:
        p = os.path.join(refs, fn)
        if os.path.exists(p):
            col.image(p, caption=cap, use_container_width=True)
    st.markdown(
        "1. **Bindi** — small round black, centred between brows  ·  "
        "2. **Nose stud** — tiny silver, *left* nostril  ·  "
        "3. **Hair** — jet-black, centre part, waves past chest  ·  "
        "4. **Eyes** — dark brown almond  ·  "
        "5. **Brows** — natural dark  ·  "
        "6. **Lips** — nude-pink  ·  "
        "7. **Skin** — warm wheat-brown  ·  "
        "8. **Build** — slim, ~5'4\"–5'6\""
    )
    st.subheader("Character prompt (pre-baked into the video workflows)")
    st.code(
        "Character Description: Aarya - a young Indian woman, ~23 years old, warm wheat-brown "
        "skin, long jet-black wavy hair with a centre parting falling past her chest, a small "
        "round black bindi between her brows, a tiny silver stud in her left nostril, dark brown "
        "almond eyes, soft natural dark brows, nude-pink medium-full lips, slim graceful build; "
        "wearing a bright orange cropped spaghetti-strap cami top and a blush-pink sequin skirt; "
        "photorealistic, identical face in every frame.\n"
        "Background description: <DESCRIBE SCENE>",
        language="text",
    )
    st.info("Full identity card, look variants and drift first-aid: `aarya/AARYA_IDENTITY.md` "
            "(README tab → or the repo). Send the **driving video** next and I'll write the "
            "matching pose prompt.")

# ---------------------------------------------------------------- workflows tab
with tabs[1]:
    for wf in WORKFLOWS:
        path = os.path.join(WF_DIR, wf["file"])
        is_rec = wf["key"] in recommended
        with st.expander(f"{'✅ ' if is_rec else ''}{wf['name']}  —  {wf['hw']}", expanded=is_rec):
            st.write(wf["desc"])
            if os.path.exists(path):
                doc = json.load(open(path))
                c1, c2, c3 = st.columns(3)
                c1.metric("top-level nodes", len(doc["nodes"]))
                c2.metric("subgraphs", len(doc.get("definitions", {}).get("subgraphs", [])))
                c3.metric("links", len(doc.get("links") or []))
                st.download_button(
                    f"Download {wf['file']}",
                    data=open(path, "rb").read(),
                    file_name=wf["file"],
                    mime="application/json",
                    key=wf["key"],
                )
                st.code(f"inputs:  input/aarya_ref.png   +   input/aarya_drive.mp4\n"
                        f"outputs: output/video/aarya_*.mp4  (or output/aarya/still_*.png)",
                        language="text")
            else:
                st.error(f"missing {path}")

# ---------------------------------------------------------------- models tab
with tabs[2]:
    st.markdown("Tick what you already have. Sizes are download sizes.")
    rows = []
    for wf in WORKFLOWS:
        for m in wf["models"]:
            rows.append({"workflow": wf["key"], "model": m, "have": False})
    for wf in WORKFLOWS:
        st.subheader(wf["name"])
        for m in wf["models"]:
            st.checkbox(f"{m}", key=f"chk_{wf['key']}_{m[:40]}")
    st.info("Full download list with folders + sources: aarya/README.md § Models, or the README tab.")

# ---------------------------------------------------------------- prep tab
with tabs[3]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Reference image (WHO)")
        st.markdown(
            "- One person, front-facing, face **sharp**, even light\n"
            "- No sunglasses / hands over face\n"
            "- **Match the framing** of the driving video (full-body ⇒ full-body)\n"
            "- Background irrelevant — output background comes from the prompt\n"
            "- From a video? Extract the sharpest front-facing frame with ffmpeg"
        )
    with c2:
        st.subheader("Driving video (MOTION)")
        st.markdown(
            "- One person performing the motion\n"
            "- 16–24 fps (60 fps phone clips play in slow-mo — resample!)\n"
            "- 2–10 s per segment; longer auto-chunks\n"
            "- Keep hands + body visible (gestures are copied)\n"
            "- Busy backgrounds are ignored"
        )
    st.subheader("Dial-in knobs")
    st.markdown(
        "| Symptom | Fix |\n|---|---|\n"
        "| Face drifts / almost her | `reference_image_strength` 1.2 → 1.5 |\n"
        "| Motion too loose | `pose_strength` 1.1 → 1.3 |\n"
        "| Motion rigid, mushy detail | `pose_end_percent` 0.7 |\n"
        "| VRAM spikes / OOM | `WanAnimate2Cache` device = `cpu` (pre-set), 480×832 |\n"
        "| 1-frame hiccup at seams | drop `trim_image` frames of the new segment |\n"
        "| Stills: mask-like swap | `face_restore_visibility` 0.8, `codeformer_weight` 0.6 |"
    )

# ---------------------------------------------------------------- cloud tab
with tabs[4]:
    st.subheader("Rent a GPU for the video workflows (~$0.02–0.06 per 81-frame clip)")
    st.code(
        "# RunPod: community cloud, template runpod/comfyui, GPU = RTX 4090 / A40 / L40S (24 GB)\n"
        "cd /workspace/ComfyUI && git pull            # ComfyUI >= 0.42 required\n"
        "# upload models into models/{diffusion_models,loras,text_encoders,clip_vision,vae}\n"
        "# upload aarya_ref.png + aarya_drive.mp4 into input/\n"
        "# open Web UI (RunPod Connect), drag aarya_video_wan_animate2_gpu.json in, Queue Prompt\n"
        "# STOP THE POD when done!",
        language="bash",
    )
    st.warning("Your laptop (Intel UHD, 16 GB RAM) can run the stills workflow only — "
               "launch ComfyUI with the `--cpu` flag there.")

# ---------------------------------------------------------------- readme tab
with tabs[5]:
    readme = os.path.join(HERE, "aarya", "README.md")
    if os.path.exists(readme):
        st.markdown(open(readme, encoding="utf-8").read())
    else:
        st.error("aarya/README.md not found")

st.divider()
st.caption(
    "Validation: `python3 aarya/scripts/validate_workflows.py aarya/workflows/*.json` — "
    "link/slot/type graph, subgraph IO and widget ordering checked against ComfyUI 0.42 schemas."
)
