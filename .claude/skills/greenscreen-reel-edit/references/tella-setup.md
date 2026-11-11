# Tella setup for the green-screen Reel

Tella hosts the creator's recording. We use it for the edits it does well: transcript-based
cuts, cutting out the presenter, Studio Sound and burned-in captions. It exports the presenter
alone on solid magenta, and everything behind them is built locally with ffmpeg. That route
avoids Tella plan limits (a trial can't upload video sources or generate media) and gives full
control of the background.

Tool names below are from the Tella MCP server. Load them with ToolSearch (`select:...`)
before calling.

## 1. Find the video and read it

- The share link looks like `tella.tv/video/<slug>-<last 8 chars of id>`. Use `list_videos`
  (or `search_videos`) to get `vid_...`, then `get_video` for `clipIds`. These videos are
  usually one clip.
- `get_transcript {videoId, clipId, view: "sentences"}` gives sentence start and end times in
  ms on the playback timeline, which is also the exported video's timeline. Use these for
  `plan.tsv`.
- If a recording is still "transcribing" or stuck, ask the user to re-upload rather than
  waiting indefinitely.

## 2. Clean the cuts (from the audio)

The transcript's word times are often 60–160 ms off. Cutting on them (with
`cut_clip_by_transcript`, or `update_clip` using word times) clips the tail of a kept word or
leaves a fragment of a removed one. `remove_silences` (even in `fast` mode) leaves 300–600 ms
gaps. The creator called the result "pauses and cuts me off". Do this instead:

1. `get_transcript {includeCut: true}`: note the source start and end ms of every retake or
   false start to drop. Each one is a whole phrase that you'll replace with its later, clean
   take. If two takes run together with no gap ("…was they lost fat…"), it's often cleaner to
   drop the whole sentence when the next one still reads naturally.
2. Save the clip's current cuts. Run `update_clip {cuts: []}`, export without subtitles, then
   download it (rehost through `vidiq_video_upload` if needed). This is the uncut audio. Raw
   exports need a paid plan, which is why it's done this way.
3. `scripts/recut.py uncut.mp4 --remove S-E --remove S-E … --out cuts.json`. Fix any loud seam
   it reports (`--show T`), then `update_clip {cuts: <cuts.json>}`.
4. Hide (`update_transcript_words` with `hidden: true`) any word whose start lies just before a
   removed span (e.g. the first "tested" of "tested tested"). Tella counts it as kept, and it
   would flash in the captions.
5. Fix mistranscriptions with `update_transcript_words` (e.g. "7-year-old" should have been
   "70-year-old"). Fix capitals where a cut now starts a sentence ("they" becomes "They").
6. Re-read `view: "sentences"`: these are the times for `plan.tsv`. Check the export with
   `ffmpeg -af silencedetect=noise=-38dB:d=0.3`. Only the final tail should show up.

## 3. Cut-out presenter on magenta

A freshly uploaded recording often arrives with `autoRatio: true` and an odd canvas, such as
97:160 (1164x1920). Pin it first with `update_video {videoId, dimensions: {width: 1080,
height: 1920}}`, then apply the layout. Changing dimensions resets custom layouts, so do it
before the layout, not after.

```
update_clip   {videoId, clipId, background: {type: "solid", color: "#FF00FF"}}
update_layout {videoId, clipId, layoutId: "base",
               layout: {kind: "custom",
                        subject: {point: {x: 110, y: 600}, dimensions: {width: 860, height: 1419},
                                  shape: "cutout", corners: "none", order: 0, hidden: false}}}
```

Tella keeps the camera's aspect ratio, so the width may snap (e.g. to 798). That's fine.
Sections with `followsBase: true` follow automatically; `list_layouts` shows them.

Remove every existing overlay. `list_overlays` and `list_text_overlays` list them;
`remove_overlay` and `remove_text_overlay` delete them. Anything left over would be keyed or
would cover the evidence zone. Double-check the IDs: one mistyped ID fails silently in a batch
and leaves a card behind. Re-list afterwards to confirm both lists are empty.

## 4. Captions and audio

```
update_video {videoId,
  captionsEnabled: true, subtitlesEnabled: true,
  captionStyle: {name: "highlight", backgroundColor: "#000000FF", backgroundEnabled: true,
                 primaryTextColor: "#FFFFFFFF", secondaryTextColor: "#FFFFFFB3",
                 highlightColor: "#FACC15FF", wordLevelHighlights: true, textCase: "original"},
  captionFontFamily: "Inter", captionFontWeight: 500, captionFontSize: 80,
  captionGrouping: "chunked", captionLinesPerBlock: 1, captionPosition: {x: 0.5, y: 0.9},
  studioSoundLevel: "high"}
```

- **The caption background must be fully opaque** (`...FF`). A translucent black pill over
  magenta becomes purple and gets partly keyed out, or leaves a magenta fringe.
- For the same reason, any Tella overlay animation must not fade opacity over the magenta.
  Better still, have no Tella overlays at all.
- `studioSoundLevel: "high"` fixed a noticeable room echo, taking the noise floor from about
  -58 dB to about -87 dB.

## 5. Export and download

```
export_video {videoId, subtitles: true}
get_export_status {videoId, exportId}   # poll every ~10 s until completed; read downloadUrl
```

Download `downloadUrl` to `fg.mp4`. If a direct `curl` from the sandbox is blocked, rehost it
with `vidiq_video_upload {url: downloadUrl}` (free; it returns a `storage.googleapis.com`
`videoUrl`) and curl that instead.

Check the file: 1080x1920, magenta everywhere except the presenter and the caption. Grab 3–4
frames with `ffmpeg -ss T -i fg.mp4 -frames:v 1` and look at them.

## Useful extras

- `get_source_thumbnail {sourceId, width: 1920, format: "png"}` returns the image *and* saves a
  full-resolution file under `~/.claude/projects/<project>/tool-results/`. This is how page
  captures and user-supplied images become local files.
- `list_library {scope: "video", videoId}` lists what was already imported for this video, so
  you don't import the same thing twice.
- A redo of an older video in this style: strip its old overlays (step 3), apply this layout
  and captions, then re-export. Tella keeps the cuts.
