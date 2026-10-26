# ☁️ Runpod setup for the Aarya pack

Setup performed 2026-10-26 by following the official agent onboarding guide at
`https://agents.runpod.io/` (verified published there, mirror `docs.runpod.io/agent-setup.md`).

## Result banner

```
┌─ Runpod Agent Setup ─────────────────────────────────────────────┐
│ ✓ Runpod skills router + lane + journey skills                   │
│     (16 skills in ~/.agents/skills, verified: skills list --global)│
│ ✗ runpod MCP (https://mcp.runpod.io/) — unreachable from this    │
│     sandbox: egress allowlist covers only github.com,            │
│     codeload.github.com, api.github.com, registry.npmjs.org,     │
│     pypi.org, files.pythonhosted.org (probe: HTTP 000).          │
│     Arena also has no Runpod connector (status: unsupported),    │
│     so no OAuth sign-in surface exists here.                     │
│ ✗ RUNPOD_API_KEY not set — reported missing, not requested,      │
│     not printed, not written to any file (per guide).            │
│                                                                  │
│ ⚡ Skills are on disk and readable; reload/reattach an agent      │
│    with Runpod egress to use them live.                          │
└──────────────────────────────────────────────────────────────────┘
```

Next actions for every non-✓ line:
- **MCP / auth:** run the runbook below on a machine with normal internet (your laptop),
  or re-run this setup in an environment whose egress includes `mcp.runpod.io` /
  `api.runpod.io`, or connect a Runpod app in Arena if/when one appears.
- **API key:** create it yourself at Runpod console → *Settings → API Keys* (user step;
  the guide forbids the agent from asking for, printing or storing it).

Guide feedback could not be submitted: `docs.runpod.io` is outside this sandbox's egress
allowlist and no POST-capable tool with other network access was available.

---

## Aarya pod runbook (run on YOUR machine, ~10 min, ≈ $0.02–0.06 per 81-frame clip)

Follows the installed `pod-deploy` / `runpod-templates` skill rules: stock read before
create, cost stated before create, image resolved from a catalog read (never from memory),
only the needed port exposed, models on a network volume so they outlive the pod.

```bash
# 0) key (user step) — export in YOUR shell only
export RUNPOD_API_KEY=***      # console → Settings → API Keys

# 1) runpodctl (the companion CLI; skills install it on demand)
#    macOS: brew install runpod/runpod/runpodctl   |   linux: see `runpodctl` repo releases

# 2) resolve the OFFICIAL ComfyUI pod template (isRunpod: true) — cite what you read
runpodctl template search comfyui
runpodctl template get <template-id>        # note: exact image tag, ports (8188),
                                            #       allowedCudaVersions, disk sizes

# 3) stock read for a 24 GB class (RTX 4090 / A40 / L40S) in your data center
#    (MCP get-gpu-availability include:["AVAILABILITY"] product:["POD"], or console)

# 4) network volume >= 60 GB in the SAME data center (models ~24 GB + headroom)
#    mount path: /workspace          ← models + outputs survive stop/terminate

# 5) create the pod — state the hourly rate first (4090 ≈ $0.34–0.69/h)
#    image  = tag read in step 2     gpu.minCudaVersion = template's CUDA floor
#    ports  = 8188/http ONLY         mounts = volume → /workspace
#    poll get-pod until RUNNING *and* runtime.ports populated (image pull takes minutes)

# 6) connect:  https://<podId>-8188.proxy.runpod.net
#    (public + unauthenticated by default — don't put anything sensitive behind it)
```

Inside the pod (console web terminal):

```bash
cd /workspace   # the network volume
# models (sizes/links: ../README.md § Models) → /workspace/ComfyUI/models/...
# then in the ComfyUI web UI: drag in aarya_video_wan_animate2_gpu.json,
# upload aarya/references/aarya_ref_front_bust.png as input/aarya_ref.png
# and your driving video as input/aarya_drive.mp4, set the two prompts, Queue.
```

Aarya-specific settings once it runs: `WanAnimate2Cache` device `cpu` (pre-set),
480×832, `reference_image_strength` 1.3 with the low-res fullbody ref.

**Billing:** stop (not terminate) when done → GPU billing ends, volume disk bills at the
stopped rate until terminate; a network volume bills from creation until deleted.
Terminate deletes the volume disk (your models) — only terminate intentionally.

## Why not provisioned from the sandbox

`api.runpod.io`, `mcp.runpod.io`, `docs.runpod.io` all probe HTTP 000 from here (egress
allowlist), so no stock read, create call or boot-log read could be made truthfully —
and the `pod-deploy` skill forbids creating without a stock read or handing back URLs
without a read-back. Everything that needs no network (skills, playbooks, this runbook)
is done.
