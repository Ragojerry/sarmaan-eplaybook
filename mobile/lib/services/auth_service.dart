import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import 'api_client.dart';
import 'device_identity.dart';
import '../models/api_models.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class AuthState {
  final UserProfile? user;
  final bool loading;

  /// The server deactivated the account: the person was signed out and the sign-in
  /// screen explains why (cleared at the next sign-in attempt).
  final bool deactivated;

  const AuthState({this.user, this.loading = true, this.deactivated = false});

  bool get isLoggedIn => user != null;

  AuthState copyWith({UserProfile? user, bool? loading, bool clearUser = false, bool? deactivated}) => AuthState(
      user: clearUser ? null : (user ?? this.user), loading: loading ?? this.loading, deactivated: deactivated ?? this.deactivated);
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _api;
  final LocalDatabase _db;

  AuthNotifier(this._api, this._db) : super(const AuthState(loading: true)) {
    _restoreSession();
  }

  Future<void> _restoreSession() async {
    try {
      final token = await _api.getAccessToken();
      if (token == null) {
        state = state.copyWith(loading: false, clearUser: true);
        return;
      }
      final resp = await _api.dio.get('/auth/me');
      await _setUser(UserProfile.fromJson(resp.data));
    } catch (_) {
      // Covers both a genuinely invalid/expired token (server rejected
      // /auth/me, refresh also failed) AND a storage-layer failure reading
      // the token in the first place (e.g. secure storage unavailable) —
      // either way, the safe fallback is "treat as logged out", not crash.
      try {
        await _api.clearTokens();
      } catch (_) {
        // If even clearing tokens fails, there's nothing more this method
        // can do — state still gets set to logged-out below.
      }
      state = state.copyWith(loading: false, clearUser: true);
    }
  }

  /// Throws a DioException on failure — screens should catch it and show
  /// `error.response?.data['detail']` per FastAPI's error shape.
  Future<void> login(String username, String password) async {
    if (state.deactivated) state = state.copyWith(deactivated: false);
    Map<String, dynamic>? device;
    try {
      device = await deviceInfoPayload(_db);
    } catch (_) {}
    final resp = await _api.dio.post('/auth/login', data: {
      'username': username,
      'password': password,
      if (device != null) 'device': device, // device registry; older servers ignore it
    });
    await _api.saveTokens(accessToken: resp.data['access_token'], refreshToken: resp.data['refresh_token']);
    final meResp = await _api.dio.get('/auth/me');
    await _setUser(UserProfile.fromJson(meResp.data));
  }

  /// Points the local database at THIS user before the signed-in state is
  /// published, so no screen can read the previous person's progress.
  Future<void> _setUser(UserProfile user) async {
    _db.setActiveUser(user.id, learnerRole: user.learnerRole, staff: !user.isLearner);
    await _db.adoptAnonymousAnalytics();
    state = AuthState(user: user, loading: false);
  }

  /// Re-reads the account from the server (called by sync). Returns true when
  /// the learner role changed, so the caller can fetch the matching content.
  Future<bool> refreshProfile() async {
    final current = state.user;
    if (current == null) return false;
    final resp = await _api.dio.get('/auth/me');
    final fresh = UserProfile.fromJson(resp.data as Map<String, dynamic>);
    if (fresh.id != current.id) return false;
    final changed = fresh.learnerRole != current.learnerRole || fresh.role != current.role;
    if (changed) {
      _db.setActiveUser(fresh.id, learnerRole: fresh.learnerRole, staff: !fresh.isLearner);
    }
    state = AuthState(user: fresh, loading: false);
    return changed;
  }

  /// The server deactivated this account (api_client.dart): sign out locally, keep
  /// every local record, and let the sign-in screen say why. Never loops.
  void accountDeactivated() {
    if (state.user == null && state.deactivated) return;
    _db.setActiveUser(null);
    state = const AuthState(loading: false, deactivated: true);
  }

  Future<void> logout() async {
    final refreshToken = await _api.getRefreshToken();
    try {
      if (refreshToken != null) {
        await _api.dio.post('/auth/logout', data: {'refresh_token': refreshToken});
      }
    } catch (_) {
      // Best-effort server-side revocation — proceed with local logout
      // regardless, so a network blip never traps the user in a logged-in
      // UI they can't get out of.
    } finally {
      await _api.clearTokens();
      _db.setActiveUser(null);
      state = state.copyWith(loading: false, clearUser: true);
    }
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final api = ref.read(apiClientProvider);
  final notifier = AuthNotifier(api, ref.read(localDatabaseProvider));
  api.onAccountDeactivated = notifier.accountDeactivated;
  return notifier;
});
