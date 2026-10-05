# Mobile Application — Phase 7

## 1. Scope, exactly per master prompt

Phase 7's screen list: splash, language, consent, login, home, modules, reader, videos, about.
That's it — no more. Specifically **not** in this phase, even though earlier scaffolding had stub
files for them: offline content download/`/downloading` (Phase 8/9), release/`/updates` (Phase 12),
and the AI assistant/`/ai` (Phase 10/11). Routing to those now would mean either broken destinations
or fresh fake stubs — the exact problem this whole project replaces. Their screen files still exist
under `lib/screens/` for when those phases actually build them out; they're just not wired into
`app_router.dart` or the bottom nav yet.

## 2. A new screen: Login

The prototype never had one — it had no backend, so nothing to authenticate against
(`docs/prototype-analysis.md` §1). The real backend requires it (`POST /auth/login`, master prompt
§52), so Phase 7 adds `lib/screens/login_screen.dart`: a real form calling the real endpoint, storing
tokens via `flutter_secure_storage`, with real error messages surfaced from the backend's actual
`detail` response field — not a generic "login failed."

## 3. Real networking, mirroring the admin portal's pattern exactly

`lib/services/api_client.dart` is the Flutter equivalent of `admin/src/services/api.ts`: a Dio client
that attaches the stored access token to every request, and on a 401, automatically tries the stored
refresh token once, retries the original request, and falls back to clearing tokens (forcing re-login)
if that also fails. Both clients — web and mobile — behave identically against the same backend
contract, which matters since they're built by different people/at different times but need to agree
on the same session semantics.

## 4. Real content rendering — no raw HTML, matching the admin portal's own model

`lib/screens/reader_screen.dart` renders the exact same `ContentType` enum the backend and admin
portal use (`HEADING`, `TEXT`, `LIST`, `IMAGE`, `CALLOUT`, `WARNING`, `JOB_AID`, `TABLE`, `VIDEO`) —
native Flutter widgets per type, never a WebView or raw HTML string. `IMAGE` sections fetch through
`AuthenticatedImage` (see §5); `VIDEO` sections navigate to the video detail screen; `TABLE` sections
render as a real `DataTable`.

Real on-device text-to-speech via `flutter_tts`, reading the module translation's `audio_text` field
— replacing the prototype's browser-only `speechSynthesis` call, which only ever worked in a desktop
browser preview, never on an actual Android device (`docs/prototype-analysis.md` §1).

## 5. `AuthenticatedImage` — and a bug caught before it shipped

A bare `Image.network(url)` can't attach the Bearer token `GET /media/{id}/file` requires (media is
deliberately not public — training content shouldn't be servable to anyone with a guessed URL). Built
`lib/widgets/authenticated_image.dart` to fetch bytes through the authenticated Dio client instead —
the exact same reasoning as `admin/src/components/AuthenticatedImage.tsx`.

**Caught during review, not left in**: the first version used a `ConsumerWidget` with
`FutureBuilder(future: api.dio.get(...))` directly in `build()`. That's a real, easy-to-miss Flutter
bug — the future gets created fresh on every rebuild, silently re-fetching the image and re-showing
the loading spinner any time a parent widget rebuilds for any reason. Fixed by converting to a
`ConsumerStatefulWidget` and creating the future exactly once, in `initState()`.

## 6. `/languages` had to become a public endpoint — a real, fixed bug

Master prompt Phase 7's screen order (splash → **language** → consent → **login** → home) means the
language picker must work *before* the user has logged in. The endpoint from Phase 5 required
authentication. Caught this while writing `language_screen.dart` — not left as a "known gap," fixed at
the source: `GET /languages` is now public (no auth dependency) in
`backend/app/routers/languages.py`, since a language list isn't sensitive data and gating it behind a
login a first-time user hasn't completed yet would just break the first-run flow. Verified: full
regression (16 existing backend tests) still passes with this change, and a fresh unauthenticated
`curl` confirms the endpoint works with zero token.

## 7. A second real backend gap, closed: `/videos`

Nothing could list videos before this phase — Phase 5's admin scope explicitly didn't include video
management (`docs/admin-portal.md` §7). Added `GET /videos` and `GET /videos/{id}` (read-only,
authenticated), and a `GET /media/{id}` + `GET /media/{id}/file` pairing already existed from Phase 6.
Every video currently reports `has_file: false` — verified honestly, not hidden: no real footage exists
anywhere in the source materials, and the mobile video screens show this plainly ("Video not yet
available") rather than pretending otherwise.

## 8. What's intentionally NOT here yet

- **"Mark as complete"** on the reader screen is a disabled button with a label explaining why. Real
  progress tracking needs the local (Drift) database Phase 8 builds — implementing an online-only
  version now would just get thrown away and rebuilt once offline storage exists.
- **Continue-reading card on Home** — same reason; the prototype's hardcoded 62% is gone, replaced
  with nothing rather than a different fake number, because there's no real progress data source yet
  (`docs/prototype-analysis.md` §8's exact concern).
- **Video playback** — every video is metadata-only; real playback needs real footage plus Phase 9's
  download/checksum/local-file mechanism.
- **The AI assistant tab** — removed from the bottom nav entirely rather than left pointing at
  nothing; returns in Phase 10/11.

## 9. Verified — and what could NOT be verified here

**Verified in this environment:**
- `GET /videos` and `GET /videos/{id}` — real data returned, 401 without a token, confirmed against
  the live database populated in Phase 6.
- `GET /languages` — confirmed public (200 with zero auth headers), full 16-test backend regression
  still passes after the change.
- All new/changed Dart files — brace/paren balance checked across all 18 files (mechanical sanity
  check, not a substitute for real compilation).

**NOT verified here — no Flutter SDK in this sandbox** (same limitation as Phase 2): `flutter pub get`,
`flutter analyze`, `flutter test`, and `flutter run` were not run against this code. The two new
dependencies (`shared_preferences`, `package_info_plus`) need fetching; `flutter test` should be run
against the updated `test/widget_test.dart` (which now mocks `SharedPreferences.setMockInitialValues`
— required because `SplashScreen` reads local settings in a post-frame callback, and a real platform
channel doesn't exist in the widget-test environment). Please run all four locally and report back
what comes up — that loop caught real, fixable bugs during Phase 2 and would likely do so again here.

## 10. Robustness fix worth flagging

`AuthNotifier._restoreSession()` originally called `_api.getAccessToken()` (a secure-storage read)
*outside* its try/catch block — meaning a storage-layer failure (not just an invalid/expired token)
would throw unhandled on every app launch. Fixed to wrap the entire method: any failure — expired
token, server rejection, or a storage read error — now falls back to a clean "treat as logged out"
state rather than crashing. This matters for real devices too, not just tests: secure storage can
legitimately fail (corrupted keystore, first-run timing issues on some Android versions), and the app
should degrade to a login screen in that case, not crash on launch.
