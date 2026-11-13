import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Real networking client for the "online" half of the hybrid architecture.
/// Token attachment + auto-refresh-on-401 mirrors the same pattern used in
/// admin/src/services/api.ts, so both clients behave identically against
/// the same backend contract.
///
/// Base URL is a build-time value:
///   flutter build apk --dart-define=API_BASE_URL=https://d1eortf8qang6z.cloudfront.net
/// Without it, the default 10.0.2.2 is the Android emulator's alias for the
/// host machine's localhost, i.e. a local dev backend.
class ApiClient {
  static const String _baseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
  static const _accessTokenKey = 'sarmaan_access_token';
  static const _refreshTokenKey = 'sarmaan_refresh_token';

  final Dio dio;
  final FlutterSecureStorage _storage;
  Future<String?>? _refreshInFlight;

  /// Called once the server says this account was deactivated (header
  /// X-Account-Status: deactivated on any call or on the token refresh). The tokens
  /// are already cleared; the sign-in state signs the person out (auth_service.dart).
  void Function()? onAccountDeactivated;
  bool _refreshSaidDeactivated = false;

  static bool isDeactivated(Response<dynamic>? response) =>
      response?.headers.value('x-account-status')?.toLowerCase() == 'deactivated';

  Future<void> _deactivated() async {
    await clearTokens();
    onAccountDeactivated?.call();
  }

  ApiClient({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage(),
        dio = Dio(BaseOptions(baseUrl: _baseUrl, connectTimeout: const Duration(seconds: 10))) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: _accessTokenKey);
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          // Login answers 403 + the header; the sign-in screen shows its own message for it.
          if (isDeactivated(error.response) && error.requestOptions.path != '/auth/login') {
            await _deactivated();
            handler.next(error);
            return;
          }
          final isAuthError = error.response?.statusCode == 401;
          final alreadyRetried = error.requestOptions.extra['retried'] == true;
          if (!isAuthError || alreadyRetried) {
            handler.next(error);
            return;
          }

          final refreshToken = await _storage.read(key: _refreshTokenKey);
          if (refreshToken == null) {
            handler.next(error);
            return;
          }

          try {
            _refreshInFlight ??= _refreshAccessToken(refreshToken);
            final newAccessToken = await _refreshInFlight;
            _refreshInFlight = null;
            if (newAccessToken == null) {
              if (_refreshSaidDeactivated) {
                _refreshSaidDeactivated = false;
                await _deactivated();
              }
              handler.next(error);
              return;
            }

            final retryOptions = error.requestOptions;
            retryOptions.headers['Authorization'] = 'Bearer $newAccessToken';
            retryOptions.extra['retried'] = true;
            final response = await dio.fetch(retryOptions);
            handler.resolve(response);
          } catch (_) {
            _refreshInFlight = null;
            await clearTokens();
            handler.next(error);
          }
        },
      ),
    );
  }

  Future<String?> _refreshAccessToken(String refreshToken) async {
    try {
      final response = await Dio(BaseOptions(baseUrl: _baseUrl)).post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final newAccessToken = response.data['access_token'] as String;
      await _storage.write(key: _accessTokenKey, value: newAccessToken);
      return newAccessToken;
    } on DioException catch (e) {
      _refreshSaidDeactivated = isDeactivated(e.response);
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<String?> getAccessToken() => _storage.read(key: _accessTokenKey);
  Future<String?> getRefreshToken() => _storage.read(key: _refreshTokenKey);

  Future<void> clearTokens() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }
}
