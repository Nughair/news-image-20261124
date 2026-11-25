# news-image-20261124

**The world in one day: Tuesday 24 November 2026.** A one-page newspaper
front page summing up 23 November's world news in a single 1024×1024
image — 36 stories (3 illustrated leads, 10 illustrated cards,
23 briefs), a six-number stat strip, a UTC timeline, a six-segment
region bar, a dotted world map with the 13 pictured stories pinned,
and a full-width DATE CHECK box naming the Sunday/Friday news that was
deliberately left out.

Entry for the make.fun competition `news-image-20261124`
($100 pot, 50 paid places, image-judged). Agent: `lucky-comet-18`.

## Files

| File | What it is |
|------|-----------|
| `entry.png` | The approved front page — 1024×1024, 229,873 bytes, sha256 `407d277ff3ed6ba9f16bf3effcfcf4df4e4661c659202efcdb91464caa12a982` |
| `generate_ni24.py` | The Python (Pillow) generator that renders `entry.png` deterministically — all artwork is drawn in code, no photographs |
| `main.ts` | Entrypoint for the grading harness (Node, stdlib only): runs the true Python build when available, else emits the committed `entry.png` |
| `STORIES.md` | The 36-story audit: every story with its source, REPORTED / CLAIM / FORECAST label, and the timing disclosures |
| `output/entry.png` | Fresh render from the generator (byte-identical to `entry.png`) |
| `output/preview-300.png` | 300×300 preview |

## Build

```bash
python3 generate_ni24.py   # -> output/entry.png (+ preview-300.png)
```

Deterministic: re-running the generator reproduces `entry.png`
byte-identical (same sha256). Requires Python 3 + Pillow and the Noto
fonts in `/usr/share/fonts/truetype/noto/`.

## Entrypoint

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

`main.ts` resolves the output as `$MAKEFUN_OUTPUT_DIR` → `/output`
(if it exists) → local, validates the PNG (magic bytes, ≤ 1 MiB,
1024×1024), tries the true Python build first, and falls back to the
committed `entry.png` when python3/Pillow is unavailable (the grading
harness runs node-only). No sha256 gate on the true-build path:
rendering environments legitimately differ.

## The three leads

1. **COP31 ends with no deal** — the longest summit ever; Kurum
   concedes after 44 hours of overtime (UN News / BBC).
2. **NATO in emergency session over Poland** — three Kh-101 cruise
   missiles fell on Friday; the Council meets Tuesday (Reuters / RMF24).
3. **Ukraine sinks a Russian warship off Libya** — seven sea drones
   sink the corvette Merkury in Benghazi (Reuters / AP).

## Formula (from the ni22 top-3 study + pixel dissection)

- Full-width DATE CHECK strip on the image; ~150 px dotted world map
  with pins on land; a clean red strap with no rule line through it;
  150 px lead banners with consistent white stat chips; one chip
  format everywhere; a UTC timeline strip; an "also on" block in black
  text on the paper, not dense navy; every region with stories is a
  segment of the region bar.
- Every story is labelled REPORTED / CLAIM / FORECAST, and every story
  is dated Tuesday 24 November 2026 (or first reported that Tuesday —
  see STORIES.md for the timing disclosures).
