/// Manages the downloaded content package on-device: verifying the release
/// manifest, checking content hashes (master prompt §72), and performing the
/// atomic swap-in of a new release (master prompt §56) so the app is never
/// left with a half-updated, inconsistent content set.
///
/// Phase 2 scope: interface only. Real implementation lands once
/// scripts/build_release.py (server-side) produces a real manifest to
/// validate against (Phase 6/9).
library offline_package_manager;
