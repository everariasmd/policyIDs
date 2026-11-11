---
name: greenscreen-reel-edit
description: >-
  Edit a creator's talking-head recording into a viral-style vertical green-screen Reel: the
  presenter cut out at the bottom of the frame, and behind them a background that changes with
  every point, showing the real evidence (the person in the news story, the study with its key
  line highlighted, the scan or specimen) or topic-specific B-roll with a bold headline, plus
  word-highlight captions, clean audio and no music. Covers Tella prep (cut-out layout,
  captions, Studio Sound, export), evidence capture, B-roll, the ffmpeg build and QA, and
  delivers the video plus an Instagram caption with CTA and sources. Use this whenever the user
  shares a Tella link or recording and asks to edit it, "green screen me", make it flow, add
  B-roll or studies or headlines behind them, or asks for a Reel / TikTok / Short "like the last
  one" or "in the same format", even if they don't say "green screen". Use it too when they want
  an earlier edit redone in this style or ask what visuals a script will need before recording.
---

# Green-screen Reel edit

This is the format a physician creator (weight loss for busy parents, evidence-based fitness)
landed on after several rounds of feedback, and it's the house style for their short-form
videos. The idea comes from the doctor and science reels that go viral: the creator is a small
cut-out at the bottom, "presenting" the evidence that fills the screen behind them, and the
evidence changes every time the point changes. The viewer is always looking at proof of what's
being said, not at a talking head in a room.

## What "done" looks like

Picture a 1080x1920 frame:

- **Bottom ~50%: the presenter**, cut out of their room (no background), feet off-frame. The
  caption sits over their chest: one line, word-by-word yellow highlight, opaque black pill.
- **Top ~45%: the evidence zone**, which changes with every point, every ~3–10 s:
  - **Real evidence first.** If the script names a person, show *that person* (news photo,
    headline). If it cites a study, show *that paper*: title, journal and year, and the one line
    that backs the claim, marker-highlighted. If it describes a scan, specimen or sign, show
    the real image (the MRI, the tea-colored urine, the ECG).
  - **Otherwise, B-roll that literally shows the thing:** curls for "muscle", a spin bike for
    the spin-class study, a blood draw for "get your labs checked", food for "carbs". Older
    adults lifting for an aging and strength video.
  - **Headline banner:** big heavy text, white plus a yellow punchline, black stroke, no box.
    It works as the headline of the point, at most 2 lines.
- Slow push-in on every background. Evidence cards pop in over a dimmed, blurred version of the
  B-roll, so the card reads and the motion stays.
- **Audio:** the voice only. Studio Sound high (removes room echo), loudness normalized to
  -14 LUFS, **no music**.
- **Cuts:** tight and clean. No pause longer than about a quarter-second, and no word clipped
  at a cut. The video ends the moment they stop talking.
- **No repeated visuals:** every scene gets its own clip or image. Reusing the same B-roll
  across scenes reads as lazy.

### What the creator rejected (don't bring these back)

Each of these came up as explicit negative feedback:

- **Text or graphics over the face.** Keep everything above roughly y=880.
- **A plain colour or a moving abstract background with nothing on it.** They found it
  distracting and empty.
- **A wall of text from a screenshot.** Show the article or study name, then only the finding,
  highlighted.
- **Boxed or coloured "info card" text panels**, like a purple box with white text. They said
  "I hate the box info cards". Use the stroked headline banners instead.
- **Generic visuals that don't match the sentence** (a random doctor, an X-ray for a muscle
  point, a water bottle).
- **Background music.**
- **A news story told without showing the person it's about.** Their face makes it real, and
  that's what the viral versions do.
- **"The edit pauses and cuts me off."** Tella's `remove_silences` left 300–600 ms gaps, and
  cuts placed on transcript word times clipped word tails ("…-ause fat loss", "If- If you
  wanna"). Make the cuts from the audio with `recut.py` (step 1).
- **The same B-roll reused across scenes.** Give each scene its own visual.

## Workflow

Work in a scratch directory with `broll/`, `ev/` (evidence and banner PNGs) and `segs/`.
Scripts live in this skill's `scripts/` folder; run them with `python3`.

### 1. Read the recording and set it up in Tella

The user records in Tella and shares a link (`tella.tv/video/<slug>-<id-suffix>`). Find the
video with `list_videos` (or by its ID), then `get_transcript` with `view: "sentences"`. These
sentence times are the timeline you'll plan against.

Prepare it as described in `references/tella-setup.md`:

1. Clean up the cuts from the audio, not from word times. Note the transcript source times of
   the retakes and false starts you'll drop (`get_transcript` with `includeCut: true`). Then:
   save the clip's cuts, `update_clip {cuts: []}`, export once without subtitles, and download
   it. Run `recut.py uncut.mp4 --remove S-E ...` and apply its `cuts.json` with `update_clip`.
   It snaps each cut to the quietest point and trims every pause to a natural breath.
   - Fix any seam it reports as loud by hand (`--show T` prints the levels around T).
   - Hide (`hidden: true`) any word whose start falls just before a removed span, or it
     flashes in the captions.
   - Fix mistranscribed words, because they show in the burned-in captions.
   - Don't use `remove_silences` or `cut_clip_by_transcript` for the final cut.
2. Set the background to solid magenta `#FF00FF` and the base layout to a custom `cutout` at
   (110, 600), 860x1419.
3. Remove every old overlay.
4. Captions: highlight style with an *opaque* black background.
5. Turn on Studio Sound at `high`.
6. Export with subtitles, then download the export locally as `fg.mp4`.

### 2. Plan the segments

Go sentence by sentence and give each idea one visual. Write the plan as a table before
gathering anything, with columns for time, what's said, the visual and its source. This is
also exactly what the user wants to see if they ask what B-roll you'll use before they record.

Choosing the visual, in order of preference:

1. **The real thing named in the sentence:** the person, the paper, the image, the headline.
2. **B-roll that shows the action or object in the sentence.**
3. **A headline banner over on-topic B-roll.** This is the fallback for abstract points
   ("why this matters in your 30s").
4. **A generated visual** when the point is a mechanism no photo shows. For example, a heart
   monitor whose T waves grow taller and then flatline, for "potassium spikes and your heart
   stops" (`ecg_strip.py`).

The first 2–3 seconds are the hook and the thumbnail, so use the most striking real visual
there (the MRI, the person's face plus the headline). End on the CTA banner
(`COMMENT` / `"<KEYWORD>"`).

### 3. Gather evidence and B-roll

See `references/evidence-sourcing.md` for where each kind of evidence comes from and the
workarounds that have worked. In brief:

- **Pages:** Tella `import_from_url` (with `video: false` and the `videoId`) captures a
  1920x1080 screenshot. Then `get_source_thumbnail` with `width: 1920, format: png` saves it
  locally; copy it into `ev/`.
- **Studies:** use Europe PMC (`europepmc.org/article/MED/<PMID>`). Check that the captured
  title matches the study you meant, and read the abstract to confirm the number you'll put on
  screen.
- **B-roll:** plan one unique visual per scene, and never put the same clip in two scenes.
  1. Use `broll/` first.
  2. Then `vidiq_generate_broll` (1 credit for 4 clips, so check `vidiq_balance`) or Tella's
     free vintage library.
  3. Then photoreal AI stills from Higgsfield (`gpt_image_2_6`, 4:3, quality medium, about 0.5
     credits each; batch them in groups of 3 because larger batches hit rate limits). Make each
     still a moving clip with `still_to_clip.sh`. Prompts should describe the exact action or
     object in the sentence (a tape measure on a waist, a leg press, chicken on a food scale,
     a man sleeping), with "no text, no logos".
  4. AI stills are illustration only. Never use them for evidence (people in the news,
     studies, scans).

**Accuracy is part of the brand.** This is a doctor's account. Every number or claim on screen
must match the source it's shown with, and image labels must be literal: if the scan is of a
74-year-old, label it 74 even if the script says "a 70-year-old". If the script misstates a
study, tell the user rather than quietly showing something different. Name sources in the
summary and the caption.

**Real people in news stories:** use images published in the news coverage, as commentary.
Stay respectful, and frame it as education and prevention, not spectacle. Leave out private
details such as final texts. Mention in your summary that a family may see it.

### 4. Make the assets

- `evidence.py card SRC OUT --box x0,y0,x1,y1 --hl ...` crops a screenshot and highlights it.
  Highlight boxes use SRC pixel coordinates, the same space as the crop box.
- `evidence.py stitch SRC OUT --row ... --row ... --hl ...` joins title, journal line and
  finding into one compact card. Split long abstract lines into 2–3 shorter rows so the text
  is big on a phone. Find clean split points with
  `evidence.py gaps SRC --y y0,y1 --x x0,x1 --debug gaps.png`, so no row starts or ends
  mid-word.
- `banner.py OUT "LINE ONE" "LINE TWO" [--colors white,yellow]` makes a headline banner.
- `fullframe.py OUT --line "TEXT:color" ... --img A [--label ...] [--img B --label ...]` makes
  hook or comparison frames: one big image, or two side by side with coloured labels.
- `ecg_strip.py OUT` makes the scrolling heart-monitor strip.
- `still_to_clip.sh IMG OUT [SECONDS]` turns a still into a B-roll clip: the image sits above
  the presenter with a slow push-in, over a blurred copy of itself.
- `reframe_broll.sh SRC OUT Y0 H [TOP] [ZOOM]` lifts the action of a stock clip into the
  visible zone above the presenter's head. Most vertical clips put the subject (someone
  planking on the floor) mid-frame or lower, exactly where the cut-out covers it. Check a frame
  of every B-roll clip and reframe any whose action sits below y≈900.

Look at every card at reduced size (read the PNG) before building. Highlights that start
mid-word and text too small to read were the most common fixes.

### 5. Build, preview, render

1. Write `plan.tsv`. The columns and segment kinds are documented in the header of
   `scripts/build_bg.py`, and `assets/example_plan_strength.tsv` is a complete real example.
   Times come from the transcript, and segments must be contiguous to the end of the export.
2. Build the background:
   `build_bg.py plan.tsv --broll broll --assets ev --out bg.mp4`.
   Use `--only 3 7` to re-render just the segments you changed.
3. Preview:
   `preview.py --bg bg.mp4 --fg fg.mp4 --times <one per segment> --out sheet.png`. Read the
   sheet and fix anything over the face, unreadable text, a wrong visual or a bad highlight
   before rendering.
4. Render: `composite.sh bg.mp4 fg.mp4 Final.mp4`. A 2-minute video takes 10–15 minutes, so
   run it in the background with a long timeout. Add `-t 8` to the end of the command for a
   quick test.
5. QA the render: `preview.py --video Final.mp4 ...`, and check loudness with
   `ffmpeg -i Final.mp4 -af volumedetect -f null -`. A max around -1 dB is right. A garbled
   caption on a single frame is just Tella's caption transition; check a frame 0.3 s later.

### 6. Deliver

- Send the MP4 with `SendUserFile` (status `proactive` if it finishes while they're away).
- Reply with a short table: time, what they're saying, what's behind them. Follow it with the
  sources as links and anything you couldn't verify or that's sensitive.
- Offer an Instagram caption. The house style: a hook line, 3–5 short value lines, the CTA
  (`Comment "<KEYWORD>" and I'll send you <lead magnet>`), the sources, and a few hashtags.
  The usual lead magnet is a free 5-week resistance-training plan for busy parents, with the
  keyword `RESISTANCE TRAINING`. If the video's CTA differs, use what the creator says in it.

## Reference files

- `references/tella-setup.md`: exact Tella calls and settings, the export and download path,
  and Tella gotchas.
- `references/evidence-sourcing.md`: where to get news photos, papers, medical images and
  B-roll; capture workarounds; and environment limits such as blocked hosts and credits.
- `assets/example_plan_strength.tsv` and `assets/example_plan_planks.tsv`: full plans of two
  finished videos, with notes on why each visual was chosen. The planks plan shows the
  numbered-list pattern ("#1 CALORIE DEFICIT" … "#4 SLEEP") for advice segments.
