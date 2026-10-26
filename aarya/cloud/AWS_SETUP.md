# ☁️ Aarya on AWS EC2 (Mumbai / ap-south-1)

Yes — AWS runs the full Aarya pack, including the Wan-Animate-2 motion-video workflow.
This is the "own a GPU box" route: most reliable, lowest latency from India, models persist on
EBS between sessions — and the most expensive per hour unless you have **AWS credits**.

## Pricing reality (verified Oct 2026, ap-south-1 Mumbai)

| Instance | GPU / VRAM | On-demand | Spot | Aarya fit |
|---|---|---|---|---|
| **g6.xlarge** | 1× L4, 24 GB | **$0.9664/h** | **from ~$0.42–0.53/h** | ✅ video + stills (recommended) |
| g5.xlarge | 1× A10G, 24 GB | $1.208/h | ~$0.47–0.63/h | ✅ video + stills (pricier L4 sibling) |
| g4dn.xlarge | 1× T4, 16 GB | ~$0.63/h | ~$0.3/h | ❌ video (16 GB), ✅ stills |

Per 81-frame clip (≈10–20 min on an L4): **~$0.10–0.18 spot / ~$0.20–0.33 on-demand** — vs
~$0.02–0.06 on a Runpod 4090. AWS wins on reliability/latency/persistence, not on price.
**The AWS free tier includes NO GPU instances** — GPU time is paid unless you hold credits
(AWS Activate / student / promo $100–300). Plus ~$8–12/month for the 100–150 GB gp3 disk while
stopped (that disk is what keeps your 24 GB of models alive).

## Console recipe (~15 min, one-time)

1. Region **ap-south-1 (Mumbai)**. EC2 → Launch instances.
2. AMI: **Deep Learning AMI (Ubuntu 22.04)** with PyTorch (driver+CUDA preinstalled) — or plain
   Ubuntu 24.04 (the bootstrap script installs the driver then asks for one reboot).
3. Instance type **g6.xlarge** (spot OK for experiments; on-demand for long renders — a spot
   interruption costs you only the in-flight 81-frame chunk, earlier chunks are saved).
4. Storage: **150 GB gp3** root (models ~24 GB + repo + outputs). This disk survives stop/start.
5. Key pair: create/download `.pem`. Security group: **SSH (22) from your IP only**.
   **Do NOT open 8188** — ComfyUI has no authentication.
6. Launch. Note the public IP.

## Bootstrap + connect

```bash
# from your laptop (one-time): put the pack on the box
scp -i key.pem -r aarya ubuntu@<ec2-ip>:~/aarya
ssh -i key.pem ubuntu@<ec2-ip> 'bash ~/aarya/cloud/aws_bootstrap.sh'

# every session: tunnel in (ComfyUI stays loopback-only)
ssh -i key.pem -L 8188:127.0.0.1:8188 ubuntu@<ec2-ip>
# browse http://localhost:8188 → drag in aarya_video_wan_animate2_gpu.json
#   reference_image: aarya_ref.png (already in ComfyUI/input/)
#   driving video:   upload yours via the Load Video node
```

The script (`aws_bootstrap.sh`) is idempotent: clones ComfyUI ≥0.42 + ReActor into a venv,
downloads the Wan-Animate-2 + stills model stacks with resume/skip, stages your workflows and
Aarya refs, and launches ComfyUI on loopback. Re-run after any stop/start — downloads skip.

## Billing rules (read once, save money)

- **Stop** (not terminate) when done: compute billing ends, EBS disk (models!) persists and bills
  ~$0.08/GB-month. **Terminate** deletes the disk = re-download 24 GB next time.
- Per-second billing; set a **billing alarm** ($5 threshold) in Billing → Budgets now.
- Spot interruption mid-render loses only the current chunk; the workflow's `continue_motion`
  chaining resumes from the last saved segment.
- Forgot to stop? The instance bills $0.97/h asleep-or-not — the alarm is your seatbelt.

## When AWS is the right call

- You have **credits** (then it's effectively free and the best option here).
- You want a **persistent Mumbai box** you tunnel into like a home server (models never move).
- You need enterprise knobs: VPC, IAM, snapshots of the model disk, auto-stop Lambdas.

Otherwise: Runpod/vast.ai per clip is 3–10× cheaper, and Kaggle/Colab free tiers cover stills.
Full comparison: [`../README.md`](../README.md) § *Every run option, compared*.
