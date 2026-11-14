# SARMAAN II e-Playbook app: changelog

## 0.1.21 (build 22), 2026-11-14

**Read aloud in the module reader** (English only). See docs/read-aloud.md.

- New Read aloud bar in the reader: Play/Pause, previous and next section, speed
  0.75x / 1x / 1.25x (remembered), Stop. Uses the phone's own text-to-speech voice;
  works offline once an English voice is installed. No audio files are downloaded.
- The section being read is highlighted and kept on screen; tapping a section while
  reading continues from it. Reading pauses at an inline True/False quiz and Play
  continues after it.
- Voice: an offline English voice is chosen first (en-NG, then en-GB, then any
  English) and saved. A phone without an English voice gets a message and a button
  to its voice settings.
- Shown only when English is the content language (hidden for Hausa).
- Stops when leaving the reader, opening a test, going to the background, or when a
  phone call or another app takes the audio.
- Narration skips image descriptions (alt text), quiz statements, videos and
  flipbook notes; reads tables row by row; spells out AZM, SAM, MAM, CDD(s), SBC,
  IPC and ANC.
- Replaces the old audio bar, which read a module-level audio text only where one existed.
- Training rules are unchanged: listening does not count as reading time or complete anything.
- Not included: read-aloud analytics events (they need a small backend change).
- MIN_APP_VERSION unchanged.

## 0.1.20 (build 21), 2026-11-14

Videos on demand: videos download only when the learner asks, resume after
interruptions, are verified by SHA-256 and play offline. See docs/offline-video.md
and deploy/aws/README.md ("Training videos").
