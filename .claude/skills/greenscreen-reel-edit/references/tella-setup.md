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

## 2. Clean the cuts

- `remove_fillers` and `remove_silences` handle ums and dead air.
- `cut_clip_by_transcript` with word indices from `view: "text"` removes retakes, false starts
  and anything after the final sentence. The creator wants it to end right when they stop
  talking.
- `update_transcript_words` fixes mistranscriptions (one earlier case: "7-year-old" should have
  been "70-year-old"). Captions are burned in, so a wrong word is a visible error.
- Re-read the sentences afterwards, because the times shift after cuts.

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
