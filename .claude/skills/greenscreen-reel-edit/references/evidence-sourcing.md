# Sourcing evidence and B-roll

The background is only as good as how specific it is. Get the real thing first, then fall back
to B-roll that shows the action, then to a headline banner.

## Capturing any web page

```
import_from_url {url, videoId: <the Tella video>, video: false}   # 1920x1080 above-the-fold PNG
get_source_thumbnail {sourceId, width: 1920, format: "png"}       # saves it locally (path in result)
cp <tool-results path> ev/<name>.png
```

Read the 960-px thumbnail first to judge the page, then fetch the full-resolution version.
Coordinates for `evidence.py` are in that 1920x1080 space. Only the area above the fold is
captured. Pass `scroll: true` for a scrolling video instead, but that's rarely needed.

## Studies

- Use **Europe PMC**: `https://europepmc.org/article/MED/<PMID>`. PubMed returns a CAPTCHA to
  the capture service.
- Look up the PMID with a web search, then **check that the captured title is the study you
  meant**. An earlier lookup returned a PMID that was a different 1990 JAMA paper.
- Layout of a Europe PMC capture: title ≈ y 280–400, authors below it, journal and date line
  ≈ y 450–580 (lower when there are many authors or comment boxes), abstract from ≈ y 640.
  Only the top of the abstract fits, so if the key sentence is lower down, show the title and
  journal line and put the number in a banner.
- Card recipe: title highlighted, journal and year highlighted, plus 1–3 rows from the
  abstract with exactly the words that back the claim highlighted. Build it with
  `evidence.py stitch` and split rows at the gaps that `evidence.py gaps` reports.
- Confirm the on-screen number in the captured text: "Strength gains averaged 174%",
  "Mid-thigh muscle area… did not decline with age".

Citations verified in past videos (reuse freely):

| Claim | Paper |
|---|---|
| Masters athletes aged 40–81 kept thigh muscle; decline reflects disuse | Wroblewski et al., *Phys Sportsmed* 2011 (PMID 22030953) |
| −5 kg grip strength ≈ +16% all-cause mortality; ~140k people, 17 countries | Leong et al., PURE, *Lancet* 2015 (PMID 25982160) |
| 30–60 min/week of muscle-strengthening = largest risk reduction | Momma et al., *Br J Sports Med* 2022 (PMID 35228201) |
| Nonagenarians +174% strength in 8 weeks | Fiatarone et al., *JAMA* 1990 (PMID 2342214) |
| Spin-class (exertional) rhabdomyolysis case series | Cureus 2021, captured via Europe PMC |
| Marathon cardiac arrest ≈ 1 in 185,000 runners | Kim et al., *NEJM* 2012 |

## People in news stories

- Capture several outlets and keep the cleanest. Local TV affiliates (ABC7, NBC NY) and
  memorial pages usually work. Daily Beast and Fox News showed paywall or ad-block popups over
  the photo.
- A good hook pairs a headline card on top with the person's photo underneath (the `stack`
  kind), or the photo full-bleed with a name banner (the `img` kind).
- Remove a video play-button over a face by blurring a small circle there. In PIL, composite a
  Gaussian-blurred copy through a feathered ellipse mask.
- Crop away site chrome such as profile-avatar circles and share bars.
- Be respectful: say it's per the family or the news report, use "official cause under
  investigation" where true, and leave out private details.

## Medical images

- Wikipedia article captures put the infobox image on the right (≈ x 1130–1430). Rhabdomyolysis
  shows tea-colored urine; Hyperkalemia shows ECGs with peaked T waves. `File:` pages fail to
  capture.
- Watch for Wikipedia fundraising banners covering the top of the capture.
- User-supplied images (e.g. MRI scans) are already Tella sources: `get_source_thumbnail` them.
  Label them literally (age and status from the source).
- When no image shows the mechanism, generate one (e.g. `ecg_strip.py`) instead of using a
  generic stand-in.

## B-roll

- Reuse the local `broll/` library first. Past clips: older adults lifting (gym1, gym2,
  gymmembers, trainer), a spin bike with a coach (bike), curls, a family walking (walk), a
  marathon crowd, food and oatmeal, a blood draw, a sweaty head-in-hands shot (sweat), water,
  a doctor, and an X-ray.
- New clips: `vidiq_generate_broll` (Pexels, ~1 credit). Check `vidiq_balance` first; credits
  have run to zero before.
- Write specific queries ("woman doing dumbbell bicep curls", "indoor cycling class") and avoid
  generic ones ("fitness").
- The sandbox can't reach `pexels.com` directly. Rehost with `vidiq_video_upload {url}` (free;
  any public MP4 up to 299 MB), then curl the `storage.googleapis.com` URL.
- Tella `list_library {scope: "vintage", query}` has public-domain archive footage.
- Clips from other creators' social posts can count as fair use when the video reacts to or
  comments on them (the creator's own guidance). Credit them on screen if used.

## Environment limits seen so far (re-check; they change)

- The sandbox network blocked pexels, pubmed, many news sites and wikimedia, and allowed
  storage.googleapis.com and S3. Route captures through Tella `import_from_url`, and downloads
  through `vidiq_video_upload`.
- Tella trial: no video source uploads and no AI generation, which is why the background is
  built locally.
- Google Drive links were not directly downloadable; ask for a Tella upload instead.
