# 🎭 AARYA — ComfyUI Identity Pack

Give ComfyUI **one reference image of Aarya** + **one driving video**, and get videos/stills of
*Aarya herself* performing that motion — face, hair, outfit and all.

Built against **ComfyUI ≥ 0.42.0** (node schemas verified from `Comfy-Org/ComfyUI@fe298e4` and
`Gourieff/ComfyUI-ReActor`). The two video workflows are derived from the **official**
`Comfy-Org/workflow_templates` Wan-Animate-2 templates and re-targeted at Aarya
(loaders renamed, prompts pre-filled, cache on CPU, save prefix `video/aarya`, START-HERE note added).

---

## What's in the pack

| File | Runs on | What it does |
|---|---|---|
| `workflows/aarya_video_wan_animate2_gpu.json` | NVIDIA ≥ 16 GB VRAM (24 GB comfy) or cloud GPU | **Aarya performs your video's motion.** Wan-Animate-2 (14B, int8) + LightX2V distill LoRA, 6 steps, context-windowed, auto-extends long videos in 81-frame chunks. |
| `workflows/aarya_video_wan_animate2_distilled_gpu.json` | NVIDIA ≥ 12 GB VRAM or cloud GPU | Same, distilled 4-step-style variant (10 steps, no LoRA slot) — faster, slightly less detail. Includes a ready-made 2nd segment for longer clips. |
| `workflows/aarya_stills_facelock_cpu.json` | **CPU / integrated graphics (your laptop)** | Face-locked still portraits of Aarya: SD1.5 + LCM LoRA (6 steps @ 512×768) → ReActor inswapper face-swap → CodeFormer restore. ~1–3 min/image on CPU. |
| `scripts/build_aarya_workflows.py` | any | Re-generates the two GPU workflows from the official templates (idempotent). |
| `scripts/build_stills_workflow.py` | any | Emits the CPU stills workflow. |
| `scripts/validate_workflows.py` | any | Structural validator: link/slot/type graph, subgraph IO, widget ordering. Run it after editing anything. |

```
reference image (WHO)  ──VAE+CLIP-vision──┐
                                         ├─▶ Wan-Animate-2 DiT ─▶ frames ─▶ aarya_*.mp4
driving video (MOTION) ──VAE pose branch─┘        ▲
                                        text prompt (looks + scene)
```

Wan-Animate-2 needs **no pose extraction** — it consumes the raw driving video directly and keeps
the identity of the reference image. The background comes from your prompt, not from either input.

---

## ⚠️ Hardware reality check (your machine)

Your laptop: **Intel UHD integrated graphics, ~16 GB RAM, no CUDA GPU.**

- The two **video** workflows need an NVIDIA GPU with ≥ 16 GB VRAM (the 14B int8 model alone is
  ~15.5 GB). They will *not* run on Intel UHD — not slowly, not at all.
- On this laptop use **`aarya_stills_facelock_cpu.json`** (CPU mode: launch ComfyUI with `--cpu`).
- For videos, rent a GPU for an hour (see *Run on a cloud GPU* below) — a 24 GB card renders
  ~3.4 s of video (81 frames) in roughly 2–6 minutes with this workflow.

---

## Quick start

### 0. Update ComfyUI
Wan-Animate-2 nodes (`WanAnimate2ToVideo`, `WanAnimate2Cache`, native `LoadVideo`/`SaveVideo`)
ship with ComfyUI **0.42+**. Update first (`git pull` / Desktop update), otherwise nodes show red.

### 1. Models

**Video workflows** → into `ComfyUI/models/…` (all from
[HF: Comfy-Org/Wan-Animate-2](https://huggingface.co/Comfy-Org/Wan-Animate-2)):

| Folder | File | Size | Needed by |
|---|---|---|---|
| `diffusion_models/` | `wan_animate_2_int8_convrot.safetensors` | ~15.5 GB | full |
| `diffusion_models/` | `wan_animate_2_distill_int8_convrot.safetensors` | ~15.5 GB | distilled |
| `loras/` | `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` | ~704 MB | full |
| `text_encoders/` | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | ~6.3 GB | both |
| `clip_vision/` | `clip_vision_h.safetensors` | ~1.2 GB | both |
| `vae/` | `Wan2_1_VAE_bf16.safetensors` | ~242 MB | both |

**Stills workflow** → plus the custom node
[ComfyUI-ReActor](https://github.com/Gourieff/ComfyUI-ReActor)
(`git clone` into `custom_nodes/`, then `pip install -r custom_nodes/ComfyUI-ReActor/requirements.txt`):

| Folder | File | Source |
|---|---|---|
| `checkpoints/` | `v1-5-pruned-emaonly-fp16.safetensors` (any SD1.5 ckpt works) | Hugging Face, search *v1-5-pruned-emaonly-fp16* |
| `loras/` | `lcm-lora-sdv1-5.safetensors` | [HF: latents/lcm-lora](https://huggingface.co/latents/lcm-lora) |
| `inswapper/` | `inswapper_128.onnx` | [HF mirror: ezioruan/inswapper_128.onnx](https://huggingface.co/ezioruan/inswapper_128.onnx) |
| `facerestore_models/` | `codeformer-v0.1.0.pth` | [CodeFormer releases](https://github.com/sczhou/CodeFormer/releases) |

(ReActor also auto-downloads InsightFace detection weights on first run — needs internet once.)

### 2. Your Aarya assets
Copy into `ComfyUI/input/`:
- **`aarya_ref.png`** — the single best photo of Aarya (see *Prep guide*)
- **`aarya_drive.mp4`** — the video whose motion Aarya should perform

Then on the nodes **AARYA - 1 Reference Image** / **AARYA - 2 Driving Video** hit refresh and select them.

### 3. Prompts (video workflows)
Inside the **Motion Transfer** subgraph:
- **Character prompt** — already pre-filled with an Aarya template; replace the
  `<DESCRIBE OUTFIT>` / `<DESCRIBE SCENE>` placeholders. Describe *looks only*, no motion words.
- **Pose prompt** — one sentence describing the motion in your driving video.

### 4. Queue
`Queue Prompt`. Videos land in `ComfyUI/output/video/aarya_*.mp4`; the canvas also shows a
side-by-side comparison against the driving video. Stills go to `output/aarya/still_*.png`.

---

## Prep guide — getting an *exact* Aarya

**Reference image**
- One person, front-facing, face sharp and evenly lit (no harsh shadows/sunglasses/hands on face).
- Match the **framing level** of your driving video: full-body drive video ⇒ full-body (or 3/4) ref.
  Framing mismatch is the #1 cause of "that's not her".
- Plain background is fine — the output background comes from the prompt anyway.
- From a video? Extract the sharpest frame where she faces camera (`ffmpeg -i vid.mp4 -vf "select=eq(n\,123)" -vframes 1 aarya_ref.png`).

**Driving video**
- One person performing the motion; 16–24 fps; 2–10 s per segment (the workflow auto-chunks longer ones).
- Frames are read 1:1 (no fps resampling) — a 60 fps phone clip will play in slow motion; resample first:
  `ffmpeg -i src.mp4 -r 24 -vf scale=-2:832 aarya_drive.mp4`
- Busy backgrounds are ignored; keep the *body* visible (hands included — gestures are copied).

**Dial-in knobs (video)**
| Symptom | Fix |
|---|---|
| Face drifts / "almost her" | `reference_image_strength` 1.2 → 1.5 |
| Motion too loose / floaty | `pose_strength` 1.1 → 1.3 |
| Motion too rigid, details mushy | `pose_end_percent` 0.7 |
| VRAM spikes / OOM | `WanAnimate2Cache` device = `cpu` (already set), lower width/height to 480×832 |
| 1-frame hiccup at chunk seams | drop `trim_image` frames of the new segment (node is pre-wired) |

**Dial-in knobs (stills)**
| Symptom | Fix |
|---|---|
| Swap looks mask-like | `face_restore_visibility` 0.8, `codeformer_weight` 0.6 |
| Wrong face picked (2 people) | `source_faces_index` / `input_faces_index` |
| Too soft | raise KSampler steps to 8, or render 768×1024 |

---

## Run on a cloud GPU (for the video workflows)

Cheapest sane option: **RunPod** (or vast.ai / TensorDock) with any **RTX 4090 / A40 / L40S (24 GB)**.

1. RunPod → Community Cloud → template **"runpod/comfyui"** (or official ComfyUI docker image).
2. In the container terminal:
   ```bash
   cd /workspace/ComfyUI && git pull          # ensure >= 0.42
   # upload the 5 model files into models/... (RunPod web UI → Upload, or `cd models && wget <hf-url>`)
   ```
3. Upload `aarya_ref.png` + `aarya_drive.mp4` to `input/`, and this pack's workflow JSON to `/workspace/`.
4. Open the ComfyUI web UI (RunPod "Connect" button), drag the JSON in, Queue.
5. **Cost ball-park:** 4090 ≈ $0.34–0.69/h → one 81-frame clip ≈ $0.02–0.06. Stop the pod when done.

No-cloud alternative: any friend's PC with an NVIDIA ≥ 16 GB card — copy the whole `ComfyUI` folder
(models included) or just re-download models there.

---

## Run on Google Colab (no local GPU needed)

**[`aarya/cloud/aarya_comfy_colab.ipynb`](cloud/aarya_comfy_colab.ipynb)** — upload to Colab and run
cells top to bottom. It mounts Drive (models download **once** into `Drive/MyDrive/aarya/models`,
reused every session), installs ComfyUI + ReActor, symlinks model dirs, fetches the right model
stack for your GPU, and prints a public tunnel URL to the ComfyUI UI.

| Colab tier | GPU | Aarya stills | Aarya motion video |
|---|---|---|---|
| Free | T4 ~15 GB | ✅ | ❌ (14B int8 won't fit / Turing-slow) |
| Pro (~$10/mo) | T4 / **L4 24 GB** / A100 draws | ✅ | ✅ on L4/A100 draws |
| Pro+ (~$50/mo) | A100 40 GB | ✅ | ✅ comfortable |

Cell 1 auto-detects VRAM and picks the tier (≥ 20 GB ⇒ Wan-Animate-2 stack, else stills stack).
Keep the tab focused (idle-kick), and run the last cell to copy outputs to Drive before the
session recycles. See also [`cloud/RUNPOD_SETUP.md`](cloud/RUNPOD_SETUP.md) for the pay-per-use
alternative (≈ $0.02–0.06 per clip, deterministic 4090).

---

## Every run option, compared (verified Oct 2026)

| Option | GPU you get | Aarya stills | Aarya motion video | Cost | Notes |
|---|---|---|---|---|---|
| Your laptop | Intel UHD | ✅ slow (CPU) | ❌ | free | `--cpu` flag |
| **Kaggle** [`aarya_comfy_kaggle.ipynb`](cloud/aarya_comfy_kaggle.ipynb) | 2× T4 16 GB (free, ~30 h/wk, 12 h session; P100 sunset Sep 2026) | ✅ | ❌ (16 GB/GPU; 2nd T4 not turnkey-usable) | free | fixed weekly quota (no Colab roulette); models persist as **private datasets**; phone verification; idle burns quota |
| **Colab** [`aarya_comfy_colab.ipynb`](cloud/aarya_comfy_colab.ipynb) | Free T4 15 GB · Pro L4/A100 draws · Pro+ A100 | ✅ | ✅ on Pro L4/A100 draws | free / ~$10 / ~$50 mo | Drive-persistent models; GPU lottery on Pro |
| **Runpod** [`cloud/RUNPOD_SETUP.md`](cloud/RUNPOD_SETUP.md) | pick it: 4090/A40/L40S 24 GB | ✅ | ✅ deterministic | ~$0.34–0.69/h ⇒ $0.02–0.06/clip | pay-per-use; volume keeps models; skills installed in this repo's setup |
| **vast.ai** | marketplace 4090-class 24 GB | ✅ | ✅ | ~$0.25–0.45/h | cheapest video hours; quality varies by host |
| HF Spaces | always-on ComfyUI space, A10G-class 24 GB | ✅ | ✅ | cents/h while on | your private persistent ComfyUI *site*; shareable URL |
| fal.ai / Replicate | hosted Wan-Animate APIs | – | ✅ zero setup | per-video | no infra at all; upload ref+drive video, get clip back |

**Bottom line:** free tiers (Kaggle/Colab) = Aarya *images* today. Aarya *motion video* needs a
≥ 20 GB single GPU: cheapest = vast.ai/Runpod per clip; most convenient subscription = Colab Pro
on an L4/A100 draw; zero-ops = fal/Replicate per-video billing.

---

## Repo layout & maintenance

```
aarya/
├── README.md                      ← you are here
├── workflows/
│   ├── aarya_video_wan_animate2_gpu.json
│   ├── aarya_video_wan_animate2_distilled_gpu.json
│   └── aarya_stills_facelock_cpu.json
└── scripts/
    ├── build_aarya_workflows.py   ← templates dir + out dir as argv
    ├── build_stills_workflow.py
    └── validate_workflows.py      ← python3 validate_workflows.py ../workflows/*.json
```

After editing any workflow JSON, run:

```bash
python3 aarya/scripts/validate_workflows.py aarya/workflows/*.json
```

It checks link/slot/type integrity, subgraph input names, widget ordering and that the Aarya
assets are still wired. Known-benign warning: one dangling link id inside the official
Motion-Transfer subgraph (present upstream, ignored by the frontend).

---

## Send me next (and I'll finish the tuning for you)

1. Your **reference images + driving video** of Aarya — I'll pick/prepare the best ref frame and
   write the exact character + pose prompts for her.
2. **Your existing workflow file** (if you have one) — I'll merge the Aarya identity branch into it
   instead of replacing it.
3. Which output matters most: talking-head lip-sync (adds Wan InfiniteTalk), or full-body motion
   (current pack).
