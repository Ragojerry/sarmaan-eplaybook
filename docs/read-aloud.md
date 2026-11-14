# Read aloud (module reader)

App 0.1.21. The reader's **Read aloud** bar reads the module with the phone's own
text-to-speech engine (`flutter_tts`). English only for now. It works offline once
the phone has an English voice installed. No audio files, no backend or admin
changes, and no change to training rules: listening never counts as reading time
or completes anything (the 3-minute rule applies as before).

## How it works

| Part | File |
|---|---|
| What is said | `mobile/lib/services/narration_builder.dart` (`LocalNarrationBuilder`) |
| Speaking, voice, speed, pause, focus | `mobile/lib/services/read_aloud_service.dart` (`ReadAloudService`) |
| Player bar and section highlight | `mobile/lib/widgets/read_aloud_bar.dart` |
| Audio focus, voice settings shortcut | `MainActivity.kt` (channels `.../audio`, `.../device`) |

Screens never call `flutter_tts` directly; only `FlutterTtsEngine` in the service does.

### Narration

One chunk per content section, in reader order, built from the same (English)
sections the reader shows:

- **Read:** module title and description; HEADING; TEXT; LIST (its title only when
  it is not the heading just above it, then the items); IMAGE caption; WARNING
  ("Warning." + title if different from the heading + heading + text); CALLOUT and
  JOB_AID (title if different + heading + text); TABLE, one sentence per row:
  `<first cell>. <header>: <value>.` with "No mark" read as "No".
- **Skipped:** image alt text, VIDEO and AUDIO sections, flipbook notes in brackets
  ("(marked with a red X)", "(transcribed from image…)").
- **Quiz:** an inline True/False block is a *quiz stop*: reading pauses there and
  Play continues after it.
- **Clean-up:** "Step —" / "In the field —" lead-ins removed; NOT, CANNOT, DO,
  NEVER, ONLY, MUST lowered; "1-59" → "1 to 59"; "secs" → "seconds".
- **Slashes** (differs from the brief, on purpose): "/" becomes " or " only between
  two words ("Yes/No" → "Yes or No"). The content also has door-marking codes such
  as `AZM/26/3/56708/021/3/3/C` (read with "slash"), blank dates `_/_/202_` (read
  "date") and a reporting web address (left as is). A blanket " or " would have
  read these as "A-Z-M or 26 or 3 …".
- **Pronunciation** (const map `kPronunciations`): AZM → A-Z-M, SAM → S-A-M,
  MAM → M-A-M, CDD → C-D-D, CDDs → C-D-Ds, SBC → S-B-C, IPC → I-P-C, ANC → A-N-C.
- **Length:** a chunk longer than the engine's maximum input (Android
  `getMaxSpeechInputLength`, capped at 3,500; 3,500 when unknown) is split at
  sentence ends, never losing text. Two identical chunks in a row are read once.

`NarrationSource` is the seam for server-written narration (planned
server-generated audio): implement it and pass it to `ReadAloudBar`; the UI does
not change. `mobile/test/narration_vectors.json` is this builder's output for
HFW-01, HFW-04 and CDD-02, for a server builder to match. Regenerate after a
deliberate change with `UPDATE_NARRATION_VECTORS=1 flutter test test/narration_builder_test.dart`.

### Voice selection

On first use the engine's voices are listed and one is chosen and saved in
`app_settings` (`read_aloud_voice`):

1. **Offline voices first** (Android reports `network_required`; names ending in
   `-local`), because the app is used in the field without data. A network-only
   voice is chosen only when the phone has no offline English voice.
2. Within that: **en-NG**, then **en-GB**, then any English voice.

The saved voice is kept while the phone still has it (installing a new voice later
does not change it). Without a speech engine or an English voice the bar says
"Your phone needs an English voice to read aloud" with **Open voice settings**
(Android `com.android.settings.TTS_SETTINGS`, falling back to Settings).

### Language rule

The bar is shown only when the content language (`selected_language_code`) is
English. With Hausa (or any other language) selected it is hidden entirely, even
where a module falls back to English text, so English is never read under another
language or the reverse.

### Player

Previous section, Play/Pause, Next section, Speed (0.75x / 1x / 1.25x, saved as
`read_aloud_speed`), Stop. The section being read is tinted with a gold bar in the
margin and kept in view; tapping a section while reading continues from it.

- **Pause** is stop + resume from the start of the current section (reliable on
  every Android version).
- **Speed** per platform: Android 0.375 / 0.5 / 0.625 (flutter_tts doubles these:
  exactly 0.75x / 1x / 1.25x); iOS 0.42 / 0.5 / 0.56 (AVSpeech's scale is not
  linear). Check by ear that they sound slow / normal / slightly fast.
- **Stops** when the learner leaves the reader or opens a test (the reader closes),
  when the app goes to the background (Play resumes that section), and when
  another app takes the audio, e.g. a phone call (Android audio focus with a
  listener in MainActivity; flutter_tts's own focus request has no listener).
- **One module at a time:** one shared service; starting another module stops the first.
- **iOS:** playback audio category (plays with the silent switch on), spoken-audio mode.

## Known limits

- The accent and quality depend on the phone's engine and installed voices; most
  phones have en-GB or en-US, few have en-NG.
- English only. Hausa needs a Hausa voice (rare on phones) or server audio.
- Pause restarts the current section, so a long section is heard again from its start.
- Analytics: `read_aloud_start` / `read_aloud_complete` are **not logged yet**. The
  server accepts only known event types (`AnalyticsEventType`), so new names would
  be rejected; adding them is a small backend change (enum value + migration),
  held back because this phase is mobile-only.
- A highlight follows chunks; inside one long section split into several chunks the
  whole section stays highlighted.

## Verifying locally

```
cd mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs   # no schema change; regenerates as usual
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=https://d1eortf8qang6z.cloudfront.net
```

Tests: `narration_builder_test.dart` (real HFW and CDD content), `read_aloud_service_test.dart`
(fake engine), `read_aloud_reader_test.dart` (real reader, English and Hausa).
