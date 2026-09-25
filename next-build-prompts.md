# CampaignCrash — Next Build Prompts

Two builds, in order. Each is written for a coding agent working directly in
the `campaigncrash/` repo from the scaffold. Do the image-ad version first —
it's the input format most real ads will actually come in, and it reuses the
screenshot-upload pattern already used for the landing page. Video is a
separate, harder version and depends on nothing here except the platform
context work done in version 1.1.

---

## Version 1.1 — Single-image ad screenshots (Instagram / Facebook / YouTube thumbnail)

```
Right now CampaignInput.advertisement in backend/app/models.py only accepts
pasted ad copy as text. I need to also accept a screenshot of the actual ad
creative as it would appear in-feed — a single static image, the kind used
for Instagram feed/Stories, Facebook feed, or a YouTube thumbnail+title ad.
This is a separate input from the landing page screenshot already supported
— an ad screenshot and a landing page screenshot can both be present in the
same campaign.

Backend:
1. In models.py, add to CampaignInput:
   - advertisement_image: Optional[str] (base64, no data URI prefix)
   - advertisement_image_media_type: Optional[str]
   - ad_platform: Optional[Literal["instagram_feed", "instagram_story",
     "facebook_feed", "youtube_thumbnail", "other"]]
   Add a validator: exactly one of advertisement or advertisement_image must
   be provided. If advertisement_image is set, ad_platform is required —
   platform context is what makes the persona reactions realistic (feed
   scroll speed, thumbnail-plus-title-only visibility, Stories being
   full-screen and skippable in under a second, etc).
2. In personas.py, extend the Persona model with an optional
   platform_notes: dict[str, str] field keyed by ad_platform value, so each
   persona can have a platform-specific attention/behavior note (e.g. the
   "student" persona on instagram_story: "you'll tap through in under a
   second unless the first frame stops you"). Fill in notes for at least 2-3
   personas per platform — don't leave this as a generic passthrough, it's
   the thing that makes a screenshot reaction differ from a text reaction.
3. In prompts.py, add PERSONA_REACTION_IMAGE_SYSTEM (variant of the existing
   system prompt) that explicitly instructs the model to react as someone
   scrolling that platform, not someone reading an ad in isolation — name
   what's visible in the screenshot (headline, image, any visible price or
   badge) before reacting, and call out anything that would be illegible or
   easy to miss at normal scroll speed.
4. In engine.py's generate_reactions, when advertisement_image is set, build
   the Anthropic message content as [image block, text block] instead of a
   single text block — reuse whatever content-block-building helper you
   already have from the landing-page-screenshot work; don't duplicate that
   logic. Pass ad_platform and the matching platform_notes into the text
   block so they're visible to the model alongside the image.
5. Update _mock_reactions so mock mode produces a visibly different, platform-
   aware reaction when advertisement_image + ad_platform is set versus plain
   text — at minimum, vary the reaction and flags for 2-3 personas per
   platform so the demo shows the difference without needing a real API key.

Frontend:
1. In UploadForm.tsx, replace the single advertisement textarea with a toggle
   (same "Paste text" / "Upload screenshot" pattern already used for the
   landing page) and, when screenshot mode is selected, add a platform
   selector (Instagram Feed / Instagram Story / Facebook Feed / YouTube
   Thumbnail / Other) that's required before submit.
2. Update CampaignInput in types.ts to match the new backend fields.
3. Show a thumbnail preview of the uploaded ad screenshot, sized to roughly
   match the aspect ratio of the selected platform (square-ish for feed,
   9:16 for Stories) so the preview itself signals which format is being
   tested.
4. In PersonaCard.tsx, when a reaction includes a platform note in its flags
   (e.g. "illegible at scroll speed"), render that flag with a small visual
   distinction (e.g. a subtle icon or tag) so platform-specific issues are
   scannable separately from copy/messaging issues.

Keep the landing page input (text or screenshot, from the prior build)
completely unchanged — these are independent input paths.
```

---

## Version 2 — Video advertisements

Do this after 1.1 is working end to end. Video is meaningfully harder: Claude
doesn't accept raw video, so this needs a frame-sampling + transcript
pipeline before anything reaches the model. Treat this as a new pipeline
stage inserted before persona reactions, not a tweak to the existing one.

```
Add support for video advertisements (Reels, TikTok-style vertical video,
YouTube pre-roll/in-stream) as a third advertisement input type, alongside
the existing text and image-screenshot paths.

Backend — video processing pipeline:
1. Add a new endpoint POST /api/campaigns/upload-video that accepts a
   multipart file upload (not base64 in the JSON body — video files are too
   large for that). Save the file to a temp directory, return an
   upload_id the frontend then references in the main crash-test request.
2. Add a new module backend/app/video.py with:
   - extract_frames(video_path, interval_seconds=1.0) -> list[bytes]: use
     ffmpeg (add ffmpeg-python to requirements.txt) to pull one frame every
     interval_seconds, plus always include the very first frame at 0s and
     one at 3s specifically — the first 3 seconds is the make-or-break hook
     window on every platform this targets, so it needs guaranteed coverage
     even if the interval would otherwise skip it.
   - transcribe_audio(video_path) -> str: extract the audio track and run it
     through a speech-to-text step. Stub this out behind an interface
     (TranscriptionProvider) with a mock implementation that returns a
     placeholder transcript, so the rest of the pipeline can be built and
     tested without wiring a real transcription service yet.
   - get_video_metadata(video_path) -> dict: duration, resolution, aspect
     ratio (needed to infer platform — vertical video reads as
     Reels/Stories/TikTok-style, horizontal reads as YouTube in-stream).
3. In models.py, add VideoAdInput (upload_id, platform) and extend
   CampaignInput so advertisement_video: Optional[VideoAdInput] is a third
   alternative alongside advertisement and advertisement_image — update the
   validator so exactly one of the three is set.
4. In prompts.py, add PERSONA_REACTION_VIDEO_SYSTEM: instruct the model it's
   reviewing a sequence of frames (labeled with timestamps) plus a
   transcript, standing in for a video. Explicitly ask it to evaluate: does
   the first 3 seconds (first 2-3 frames) give a reason to keep watching;
   would this work with sound off and captions only (a large share of feed
   video is watched muted — factor the transcript-as-captions case into the
   reaction, not just the audio case); does the pacing lose the viewer
   anywhere.
5. In engine.py's generate_reactions, when advertisement_video is set: call
   extract_frames + transcribe_audio + get_video_metadata, build the message
   content as an interleaved sequence of [image, text-timestamp-label]
   blocks for each sampled frame followed by a text block with the full
   transcript and platform context. Keep this behind the same generate_
   reactions entry point — branch on which of the three advertisement_*
   fields is set, don't fork into a separate pipeline function.
6. Update _mock_reactions to handle mock video input: return a canned
   reaction set that explicitly references a "first 3 seconds" hook
   assessment and a "watched muted" assessment for at least 2 personas, so
   the mock-mode demo shows the video-specific reasoning even without ffmpeg
   or a transcription service configured.

Frontend:
1. Add a third UploadForm.tsx tab ("Upload video") alongside text/screenshot,
   with a file input accepting video/*, a progress indicator during the
   /api/campaigns/upload-video call, and a native <video> preview once
   uploaded.
2. Add a platform selector scoped to video (Reels, TikTok-style, YouTube
   in-stream) — reuse the ad_platform pattern from 1.1 rather than inventing
   a parallel field.
3. In PersonaCard.tsx, when the reaction came from a video ad, surface the
   hook assessment (first-3-seconds verdict) and the muted-viewing verdict as
   their own labeled lines in the card, not buried in the general reaction
   quote — these are the two questions unique to video and worth being
   scannable at a glance.

Scope note: don't build multi-video (e.g. A/B creative comparison) or
per-frame click-to-jump scrubbing in this pass — single video in, one set of
persona reactions out, same as the image and text paths. Those are
reasonable v2.1 additions once this baseline works.
```
