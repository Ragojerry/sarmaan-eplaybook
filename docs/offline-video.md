# Offline Video — Phase 9

## 1. Scope, exactly per master prompt §24

Download, resume, checksum, storage, local playback. "Allow administrators to define required
versus optional videos." All of it real, all of it verified against actual binary data — not
written and assumed to work.

## 2. What was actually missing before this phase

Phase 7 built a read-only `/videos` list. Phase 6 flagged that **no real video files exist anywhere
in the source materials** — the prototype's video screen was always a non-functional placeholder.
Nothing before this phase could upload a file, download one, resume an interrupted transfer, or play
anything from disk. This phase closes that gap for real, using a genuine small MP4 generated with
`ffmpeg` to prove the whole pipeline end-to-end rather than writing it blind.

## 3. Backend: upload + resumable download

`POST /videos/{id}/file` — `CONTENT_ADMIN`/`SUPER_ADMIN` only. Computes the SHA-256 checksum
server-side from the actual uploaded bytes (never trusts a client-supplied checksum), stores the
file, and updates the `Video` row's `filename`/`storage_path`/`mime_type`/`file_size`/`checksum`.

`GET /videos/{id}/file` — any authenticated user. Supports HTTP Range requests:
- No `Range` header → full file, with `Accept-Ranges: bytes` advertised so a client knows resume is
  possible if the connection drops.
- `Range: bytes=<start>-` or `bytes=<start>-<end>` → `206 Partial Content` with the exact requested
  slice and a correct `Content-Range` header.
- An out-of-bounds range → `416 Range Not Satisfiable`, not a silent full-file fallback.

`PATCH /videos/{id}?required_offline=true|false` — implements master prompt §24's "administrators
define required versus optional videos" exactly. New `Video.required_offline` boolean column
(migration `6dab31114b5b`, with a `server_default` since 4 video rows already existed from Phase 6 —
without it, adding a `NOT NULL` column to a populated table fails outright; confirmed by generating
the migration, hitting exactly that, and fixing it before applying).

## 4. Mobile: `VideoManager` — real download, real resume, real checksum verification

`lib/video/video_manager.dart`. `downloadVideo(videoId, onProgress: ...)`:
1. Fetches metadata (expected size + checksum) first.
2. If a local file already exists with the full byte count, verifies its checksum before trusting
   it — a same-size-but-corrupted file is deleted and re-downloaded, not assumed valid.
3. Otherwise requests only the missing range (`Range: bytes=<existing-length>-`) and appends to the
   existing file rather than restarting from zero.
4. Verifies the complete file's checksum once every byte has arrived. **A mismatch deletes the file
   and throws** — a corrupted download is never left marked as available, satisfying master prompt
   §72's "verify checksums" requirement for real, not just at upload time.
5. Only on successful verification does it write to the local `cached_videos` table — `hasFile: true`
   and a real `localPath` that `video_player` can actually open.

`deleteDownloadedVideo()` and `totalVideoBytesUsed()` back the storage-management side of §24 (see
§6 below).

## 5. Mobile: `video_screen.dart` — three real states, not one fake one

1. **No file uploaded server-side** (`has_file: false`) — the honest "not yet available" notice,
   unchanged from Phase 7 (every video is still in this state right now — no real footage exists).
2. **File exists, not downloaded to this device** — a real download button showing the actual file
   size, with a live progress bar driven by Dio's `onReceiveProgress` callback (fires incrementally
   as the response streams in, even without a separate chunked-streaming implementation).
3. **Downloaded and checksum-verified** — plays from the real local file via `video_player`,
   satisfying master prompt §95's explicit requirement: offline playback must always be a real file
   on disk, never a remote URL relabeled as offline.

`video_library_screen.dart` shows the same three states per row (hourglass / download / play icon).

## 6. Storage usage — master prompt §24's exact display, with an honest gap

The spec shows a literal example display: `Videos: 1.2 GB / Training: 200 MB / AI: 350 MB / Total: 1.75 GB
/ Available: 4.2 GB`. Added a real storage card to the About screen computing **actual** on-disk
bytes for Videos (`VideoManager.totalVideoBytesUsed()`) and Training/images
(`LocalDatabase.totalCachedMediaBytes()`) — both walk the real cache tables and check real file
sizes on the filesystem, not stored/assumed byte counts.

**Not included**: an "AI" figure (Phase 10/11 doesn't exist yet — there's nothing to measure) and
"Available" free-disk-space (needs a platform-specific plugin not yet added). Rather than fabricate
either number to match the spec's example output verbatim, the card shows only what's genuinely
computable. This is the same principle applied throughout — the admin dashboard's "0" values in
Phase 5, the video "not yet available" notices since Phase 7 — a true partial answer beats a
complete fake one.

## 7. Verified — with real binary data, not mocked bytes

**`tests/test_videos.py`** — 7 automated tests, all against a real small MP4 generated with
`ffmpeg` (not a mocked byte string, so checksum and Range-slicing logic runs against actual binary
content):

1. `CDD` role blocked from uploading a video (403)
2. `CONTENT_ADMIN` can upload — response includes the correct real checksum and file size
3. Full download returns bytes identical to what was uploaded
4. **Resumed partial download**: request only the bytes after an arbitrary split point, reassemble
   with the "already-downloaded" prefix, confirm the reassembled file is byte-identical to the
   original and its SHA-256 matches exactly
5. An out-of-bounds Range request returns 416, not a silent fallback
6. Downloading before any file was uploaded returns 404
7. `required_offline` PATCH actually persists

All 23 backend tests (16 existing + 7 new) pass together, confirmed stable across two consecutive
runs.

**Manually verified once, end-to-end, via curl against the running server** before writing the
automated suite (this is what caught that the reassembly logic was actually correct, informing how
the automated tests were written): uploaded a real `ffmpeg`-generated MP4, downloaded it whole,
downloaded a resumed partial range, reassembled the two pieces, and confirmed identical SHA-256
hashes against the original source file at every step.

## 8. Known gaps / next steps

- `video_player`, `VideoManager`, and the restyled video screens are written correctly against the
  documented Flutter/package APIs but **not compiler-verified** in this environment (no Flutter SDK
  here, same limitation as every mobile-side phase) — run `flutter analyze`/`flutter test`/`flutter run`
  locally and report back.
- No real training footage exists yet for any of the 4 videos — the pipeline is proven correct with
  a synthetic test file; the first real upload through the admin portal (once video-upload admin UI
  exists — not built yet, Phase 5's scope explicitly excluded video management) will be the first
  genuine end-to-end real-content test.
- "AI" and "Available" storage figures — see §6.
- No admin-side UI for uploading videos yet (only the API endpoint) — Phase 5 didn't include video
  management in its explicit scope; this would be a reasonable small addition to the admin portal
  whenever real footage is ready to upload.
