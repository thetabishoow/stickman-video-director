# Mosquito: An Overreaction

A 25-second, 9:16 vertical slapstick short, directed and rendered end-to-end by the
skill's Style 4 (Cozy Storytelling) contract.

**`out/mosquito-vs-stickman.mp4`** — 1080×1920 · 30 fps · 25.00 s · H.264 + AAC · 13 MB

```
00:00-00:03  THE HOOK        He sleeps. A tiny black dot buzzes in, lands on his nose.
                             His eyes snap open, glowing vivid red.
00:03-00:10  THE ESCALATION  He slaps himself (miss), grabs a giant red flyswatter and
                             levels the bedroom. The mosquito dodges like a kung-fu master.
00:10-00:20  THE CLIMAX      Bazooka. Flamethrower. Then the big red button, and a giant
                             orbital laser stabs down the vertical frame. The house is gone.
00:20-00:25  THE PUNCHLINE   A crater, proud heavy breathing… and the mosquito flies back
                             onto the camera lens, unharmed. He faints.
```

## The finished short

`out/mosquito-vs-stickman.mp4`

| Track | What is in it |
|---|---|
| Picture | Four shots, 750 rendered frames, match-cut transitions, camera shake on impacts |
| Narrator | Dry British documentary voice, deadpan, five lines (en-GB) |
| Score | Sneaky pizzicato strings + walking bass in A minor, wood ticks, a heartbeat that accelerates into the strike, nervous quiet for the punchline |
| SFX | Snoring, an unhittable mosquito buzz, whiffs, a slap on the wrong person, splintering furniture, bazooka thump, flamethrower roar, safety-cover flip, button clunk, charge whine, laser shriek, one enormous boom and a long crater rumble |

## Reproduce it

```bash
pip install numpy pillow imageio imageio-ffmpeg      # ffmpeg comes bundled with imageio-ffmpeg
cd tools/mosquito-short
python3 audio.py                 # narrator placement + score + SFX -> audio/mix.wav
python3 render.py                # 750 frames streamed into ffmpeg -> out/mosquito-vs-stickman.mp4
python3 render.py --sheet        # storyboard proof sheets
python3 render.py --preview      # fast 540x960 pass
```

Narration text lives in `audio/vo*.mp3` and is re-timed with an ffmpeg `atempo` pass so
every line fits inside its scene.

## What is in this folder

| File | Role |
|---|---|
| `sticklib.py` | Style 4 character rig (the frozen protagonist anchor), camera transform, vector pen, particles, glow, vignette, grain |
| `props.py` | Night bedroom, progressive destruction states, flyswatter / bazooka / flamethrower / emergency console, crater environment |
| `fx.py` | Mosquito, dust & debris banks, fire cone, laser beam, blast, comic marks (anger cross, sweat, dizzy stars) |
| `shots.py` | The four-shot timeline: poses, cameras, impacts, cut windows, compositor |
| `audio.py` | Full 25 s soundtrack synthesis and mixdown |
| `render.py` | Frame streaming, H.264 encode, storyboard sheets |
| `PROMPTS.md` | The same film as a Gemini Omni Flash prompt package (3 × ~10 s clips), frozen voice profile and character anchor included |

## Continuity and acceptance notes

- One protagonist anchor, repeated verbatim in every shot; two arms and two legs, one
  current pose per limb. The face only ever changes its simple marks.
- The mosquito is one insect at a stable on-screen size; it is never harmed and never
  duplicated.
- Rooms change by destruction, then by annihilation: bedroom → wrecked bedroom → crater.
  Cut points are match-cut on the same prop or action (frozen swing → swing, flash → ash).
- No text, letters, numbers, captions or speech bubbles appear on screen at any frame.
- Regeneration is deterministic: frames are a pure function of time, with seeded particle
  systems and fixed grain, so re-running the pipeline reproduces the same film.
