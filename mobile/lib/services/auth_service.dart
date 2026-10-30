import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import 'api_client.dart';
import '../models/api_models.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class AuthState {
  final UserProfile? user;
  final bool loading;

  const AuthState({this.user, this.loading = true});

  bool get isLoggedIn => user != null;

  AuthState copyWith({UserProfile? user, bool? loading, bool clearUser = false}) =>
      AuthState(user: clearUser ? null : (user ?? this.user), loading: loading ?? this.loading);
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
    final resp = await _api.dio.post('/auth/login', data: {'username': username, 'password': password});
    await _api.saveTokens(accessToken: resp.data['access_token'], refreshToken: resp.data['refresh_token']);
    final meResp = await _api.dio.get('/auth/me');
    await _setUser(UserProfile.fromJson(meResp.data));
  }

  /// Points the local database at THIS user before the signed-in state is
  /// published, so no screen can read the previous person's progress.
  Future<void> _setUser(UserProfile user) async {
    _db.setActiveUser(user.id);
    await _db.adoptAnonymousAnalytics();
    state = AuthState(user: user, loading: false);
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

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.read(apiClientProvider), ref.read(localDatabaseProvider)),
);
