#!/usr/bin/env bash
# Aarya-on-AWS bootstrap. Run ON the EC2 instance (Ubuntu 22.04/24.04 or Deep Learning AMI):
#   scp -r aarya ubuntu@<ec2-ip>:~/aarya && ssh ubuntu@<ec2-ip> 'bash ~/aarya/cloud/aws_bootstrap.sh'
# Idempotent: safe to re-run after a stop/start or a failed download.
set -euo pipefail

HOME_DIR=${HOME:-/home/ubuntu}
COMFY="$HOME_DIR/ComfyUI"
AARYA="$HOME_DIR/aarya"

echo "== [1/6] GPU / driver =="
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "no nvidia-smi: installing driver (needs one reboot, then re-run this script)"
  sudo apt-get update -qq && sudo apt-get install -y -qq nvidia-driver-550-server >/dev/null
  echo "REBOOT NOW: sudo reboot   then re-run this script."
  exit 0
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

echo "== [2/6] ComfyUI =="
if [ ! -d "$COMFY" ]; then
  git clone --depth 1 https://github.com/Comfy-Org/ComfyUI.git "$COMFY"
fi
cd "$COMFY"
if [ ! -x "$HOME_DIR/aarya-venv/bin/python" ]; then
  python3 -m venv "$HOME_DIR/aarya-venv"
fi
"$HOME_DIR/aarya-venv/bin/pip" install -q --upgrade pip
"$HOME_DIR/aarya-venv/bin/pip" install -q -r requirements.txt

echo "== [3/6] ReActor (face-lock stills) =="
if [ ! -d "$COMFY/custom_nodes/ComfyUI-ReActor" ]; then
  git clone --depth 1 https://github.com/Gourieff/ComfyUI-ReActor.git "$COMFY/custom_nodes/ComfyUI-ReActor"
  "$HOME_DIR/aarya-venv/bin/pip" install -q -r "$COMFY/custom_nodes/ComfyUI-ReActor/requirements.txt"
fi

echo "== [4/6] models (Wan-Animate-2 stack, ~24 GB, resumable, skip-if-present) =="
dl() { # dl <dest> <url>
  if [ -f "$1" ] && [ "$(stat -c%s "$1")" -gt 10000000 ]; then echo "skip $(basename "$1")"; return; fi
  mkdir -p "$(dirname "$1")"
  wget -q -c -O "$1" "$2" && echo "ok $(basename "$1")" || echo "FAILED $2"
}
HF=https://huggingface.co/Comfy-Org/Wan-Animate-2/resolve/main
dl "$COMFY/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" "$HF/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
dl "$COMFY/models/clip_vision/clip_vision_h.safetensors"               "$HF/clip_vision/clip_vision_h.safetensors"
dl "$COMFY/models/vae/Wan2_1_VAE_bf16.safetensors"                     "$HF/vae/Wan2_1_VAE_bf16.safetensors"
dl "$COMFY/models/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" "$HF/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors"
dl "$COMFY/models/diffusion_models/wan_animate_2_int8_convrot.safetensors" "$HF/diffusion_models/wan_animate_2_int8_convrot.safetensors"
# stills stack
dl "$COMFY/models/loras/lcm-lora-sdv1-5.safetensors"  https://huggingface.co/latents/lcm-lora/resolve/main/lcm-lora-sdv1-5.safetensors
dl "$COMFY/models/inswapper/inswapper_128.onnx"       https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx
dl "$COMFY/models/facerestore_models/codeformer-v0.1.0.pth" https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer-v0.1.0.pth
if [ ! -f "$COMFY/models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors" ]; then
  dl "$COMFY/models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors" https://huggingface.co/Comfy-Org/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly-fp16.safetensors \
   || dl "$COMFY/models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors" https://huggingface.co/sd-legacy/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly-fp16.safetensors
fi

echo "== [5/6] Aarya pack: workflows + references =="
if [ -d "$AARYA/workflows" ]; then
  mkdir -p "$COMFY/input"
  cp -f "$AARYA"/workflows/*.json "$HOME_DIR/" 2>/dev/null || true
  [ -f "$AARYA/references/aarya_ref_front_bust.png" ] && cp -f "$AARYA/references/aarya_ref_front_bust.png" "$COMFY/input/aarya_ref.png"
  [ -f "$AARYA/references/aarya_ref_fullbody.png" ]   && cp -f "$AARYA/references/aarya_ref_fullbody.png"   "$COMFY/input/aarya_ref_fullbody.png"
  [ -f "$AARYA/references/aarya_face_direct.png" ]    && cp -f "$AARYA/references/aarya_face_direct.png"    "$COMFY/input/aarya_face_direct.png"
  echo "workflows in $HOME_DIR/*.json (drag into the UI) ; refs in $COMFY/input/"
else
  echo "WARNING: ~/aarya not found - scp the repo's aarya/ folder first for workflows/refs"
fi

echo "== [6/6] launch (loopback only - reach it through an SSH tunnel) =="
pkill -f "main.py --listen" 2>/dev/null || true
cd "$COMFY"
nohup "$HOME_DIR/aarya-venv/bin/python" main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch > "$HOME_DIR/comfy.log" 2>&1 &
sleep 5
echo "ComfyUI starting on 127.0.0.1:8188 (log: ~/comfy.log)"
cat <<'EOF'

FROM YOUR LAPTOP, open ComfyUI safely:
    ssh -L 8188:127.0.0.1:8188 ubuntu@<ec2-ip>
    then browse http://localhost:8188 and drag in aarya_video_wan_animate2_gpu.json

BILLING: stop the instance when done (EBS keeps models; compute billing ends):
    aws ec2 stop-instances --instance-ids <id>   (or console -> Instance state -> Stop)
NEVER open port 8188 in the security group - ComfyUI has no auth.
EOF
