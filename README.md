# 🎭 Aarya Studio — ComfyUI Identity Pack

A Streamlit studio + a ready-to-run **ComfyUI workflow pack** for **Aarya**:
feed it *one reference image* (who Aarya is) + *one driving video* (what motion to perform)
and get videos / stills of Aarya herself, identity locked.

- **`aarya/`** — the pack: 3 validated workflow JSONs (Wan-Animate-2 video ×2, CPU face-lock
  stills ×1), build scripts, structural validator, and the full setup guide
  ([`aarya/README.md`](aarya/README.md)).
- **`streamlit_app.py`** — this studio: hardware-aware workflow picker, model checklist,
  prep guide, cloud-run recipe.

### Run the studio

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Run the workflows

Open ComfyUI (≥ 0.42), drag in `aarya/workflows/aarya_video_wan_animate2_gpu.json`
(NVIDIA ≥ 16 GB / cloud) or `aarya_stills_facelock_cpu.json` (CPU laptops).
Models, folders, sources and tuning knobs: [`aarya/README.md`](aarya/README.md).
