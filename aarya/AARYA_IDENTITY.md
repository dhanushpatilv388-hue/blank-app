# 🎭 AARYA — Identity Card

Canonical reference set (in `aarya/references/`), locked identity markers, and the exact
prompts pre-baked into the workflows. When output drifts, check the markers in order —
they are the cheapest tell-tales.

## Locked identity markers (QA checklist)

| # | Marker | Detail |
|---|---|---|
| 1 | **Bindi** | small round **black** bindi, centred between the brows |
| 2 | **Nose stud** | tiny **silver stud, left nostril** |
| 3 | **Hair** | jet-black, **centre part**, loose waves falling past the chest |
| 4 | **Eyes** | dark-brown, almond-shaped, soft natural lashes |
| 5 | **Brows** | natural straight-ish dark brows, not over-shaped |
| 6 | **Lips** | nude-pink, medium-full, natural (no bold lipstick) |
| 7 | **Skin** | warm wheat-brown, even tone |
| 8 | **Build** | slim, graceful, ~5'4"–5'6" |

## Looks

| Look | Outfit | Source file |
|---|---|---|
| **A — signature** | bright orange cropped spaghetti-strap cami + blush-pink sequin skirt | `aarya_ref_front_bust.png` |
| **B — neutral base** | black spaghetti-strap bodysuit (the character-sheet look) | `aarya_charactersheet_01/02.jpeg` |

## Reference files → which node

| File | Resolution | Use it for |
|---|---|---|
| `aarya_ref_front_bust.png` | 1264×1200 | **WanAnimate2 `reference_image`** — default. Best for bust / 3-4-body driving videos. Highest-res identity source. |
| `aarya_ref_fullbody.png` | 183×488 (cropped from sheet 01) | WanAnimate2 `reference_image` when the driving video is **full-body** (framing match beats resolution). Low-res: expect slightly softer identity; raise `reference_image_strength` to ~1.3. |
| `aarya_face_direct.png` | 285×495 | **ReActor `source_image`** in the CPU stills workflow (face-swap source wants a clean frontal face). |
| `aarya_charactersheet_01/02.jpeg` | sheets | **Not for nodes.** Visual QA target + future LoRA training set. |

## Prompts (already patched into the workflows)

**Wan-Animate-2 character prompt** (`Motion Transfer` subgraph, `text_1`):

```text
Character Description: Aarya - a young Indian woman, ~23 years old, warm wheat-brown skin,
long jet-black wavy hair with a centre parting falling past her chest, a small round black
bindi between her brows, a tiny silver stud in her left nostril, dark brown almond eyes,
soft natural dark brows, nude-pink medium-full lips, slim graceful build; wearing a bright
orange cropped spaghetti-strap cami top and a blush-pink sequin skirt; photorealistic,
identical face in every frame.
Background description: <DESCRIBE SCENE, e.g. a sun-lit Mumbai seafront promenade at golden
hour, shallow depth of field>
```

> Looks only — never put motion words here. Motion lives in the pose prompt.
> For **Look B** swap the outfit clause to: `wearing a plain black spaghetti-strap bodysuit`.

**Wan-Animate-2 pose prompt** (`text_2`) — until you send the driving video:

```text
A person performing exactly the motion, hand gestures, head movement and camera framing
of the driving video
```

**CPU stills positive prompt**:

```text
portrait photo of Aarya, a young Indian woman ~23, warm wheat-brown skin, long jet-black
wavy hair with a centre parting, small round black bindi on her forehead, tiny silver nose
stud in her left nostril, dark brown almond eyes, nude-pink lips, wearing a bright orange
cropped cami top and blush-pink sequin skirt, soft window light, 85mm, sharp focus,
detailed skin
```

## Drift first-aid

| What you see | First move |
|---|---|
| Bindi / nose stud missing | raise `reference_image_strength` to 1.3–1.5; check the ref framing matches the drive video |
| Face "cousin, not her" | stills: re-run with `aarya_face_direct.png`; video: switch ref to the matching-framing file |
| Hair part flipped / waves straightened | add `centre parting` emphasis; lower `pose_strength` to 0.9 |
| Skin tone washed out | negative prompt is doing too much; drop cfg a notch (video: sampler cfg 1 → 0.9) |
