import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../learning/curriculum_notice.dart';
import '../offline/content_sync_service.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import 'analytics_recorder.dart';
import 'release_installer.dart';

/// What the user sees (master prompt §55).
enum SyncStatus { offline, online, syncing, syncError, updateAvailable, upToDate }

class SyncSnapshot {
  final SyncStatus status;
  final int pendingCount; // changes waiting to upload
  final DateTime? lastSyncedAt;
  final String? installedReleaseCode;
  final String? installedVersion;
  final ReleaseInfo? availableRelease;
  final String? message;
  final bool installing;
  final InstallStage? installStage;
  final double installFraction;

  /// Bumped whenever the local content changed, so screens can reload.
  final int contentRevision;

  const SyncSnapshot({
    this.status = SyncStatus.online,
    this.pendingCount = 0,
    this.lastSyncedAt,
    this.installedReleaseCode,
    this.installedVersion,
    this.availableRelease,
    this.message,
    this.installing = false,
    this.installStage,
    this.installFraction = 0,
    this.contentRevision = 0,
  });

  SyncSnapshot copyWith({
    SyncStatus? status,
    int? pendingCount,
    DateTime? lastSyncedAt,
    String? installedReleaseCode,
    String? installedVersion,
    ReleaseInfo? availableRelease,
    bool clearAvailable = false,
    String? message,
    bool clearMessage = false,
    bool? installing,
    InstallStage? installStage,
    double? installFraction,
    int? contentRevision,
  }) {
    return SyncSnapshot(
      status: status ?? this.status,
      pendingCount: pendingCount ?? this.pendingCount,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      installedReleaseCode: installedReleaseCode ?? this.installedReleaseCode,
      installedVersion: installedVersion ?? this.installedVersion,
      availableRelease: clearAvailable ? null : (availableRelease ?? this.availableRelease),
      message: clearMessage ? null : (message ?? this.message),
      installing: installing ?? this.installing,
      installStage: installStage ?? this.installStage,
      installFraction: installFraction ?? this.installFraction,
      contentRevision: contentRevision ?? this.contentRevision,
    );
  }
}

final syncEngineProvider = StateNotifierProvider<SyncEngine, SyncSnapshot>((ref) => SyncEngine(ref));

/// Setting keys (app_settings table).
const kDeviceIdKey = 'device_id';

/// The one place that talks to /sync/*. Offline-first contract:
///  * nothing here is ever required for the app to work — screens read the
///    local database; this only moves data when the backend is reachable;
///  * queued data is NEVER deleted until the server confirms it (ok /
///    duplicate / rejected). Transient failures leave it queued and retry with
///    exponential backoff (30s, 60s, 2m ... capped at 30m);
///  * uploads are idempotent (client_id per item), so a retry after a lost
///    response cannot double-count;
///  * a failed or corrupt update leaves the installed release untouched.
class SyncEngine extends StateNotifier<SyncSnapshot> {
  final Ref _ref;
  Future<void>? _inFlight; // the sync/install currently running, if any
  int _failures = 0;
  DateTime? _nextAttempt;

  SyncEngine(this._ref) : super(const SyncSnapshot());

  ApiClient get _api => _ref.read(apiClientProvider);
  LocalDatabase get _db => _ref.read(localDatabaseProvider);

  // ---------- device + reachability ----------

  /// Random id generated once and kept in the local database. Not derived from
  /// hardware identifiers, so it says nothing about the person or the phone.
  Future<String> deviceId() async {
    var id = await _db.getSetting(kDeviceIdKey);
    if (id == null || id.length < 16) {
      final r = Random.secure();
      id = List.generate(16, (_) => r.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
      await _db.setSetting(kDeviceIdKey, id);
    }
    return id;
  }

  /// "Connected to a network" is not the same as "can reach our server"
  /// (captive portals, dead mobile data), so the real test is a /health call.
  /// The connectivity check only short-circuits the obvious airplane-mode case.
  Future<bool> isBackendReachable() async {
    try {
      final c = await Connectivity().checkConnectivity();
      if (c.every((r) => r == ConnectivityResult.none)) return false;
    } catch (_) {
      // plugin problem: fall through to the real test
    }
    try {
      final probe = Dio(BaseOptions(
        baseUrl: _api.dio.options.baseUrl,
        connectTimeout: const Duration(seconds: 4),
        receiveTimeout: const Duration(seconds: 4),
      ));
      final r = await probe.get('/health');
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ---------- local status ----------

  Future<void> refreshLocalInfo() async {
    final installed = await _db.getCurrentRelease();
    final consent = (await _db.getSetting(kAnalyticsConsentKey)) == 'true';
    final queued = await _db.countPending(entityTypes: ['ai_question', if (consent) 'analytics']);
    final progress = (await _db.getUnsyncedProgress()).length + (await _db.getUnsyncedQuizAttempts()).length;
    if (!mounted) return;
    state = state.copyWith(
      pendingCount: queued + progress,
      installedReleaseCode: installed?.releaseCode,
      installedVersion: installed?.version,
    );
  }

  // ---------- main entry point ----------

  /// Safe to call at any time and as often as you like: a call made while a
  /// sync is already running simply waits for that one (no duplicate work), and
  /// automatic (non-manual) calls respect the retry backoff.
  /// Tells open screens (Home, module lists) to re-read local data.
  void notifyContentChanged() => state = state.copyWith(contentRevision: state.contentRevision + 1);

  Future<void> syncNow({bool manual = false}) => _single(() => _syncNow(manual));

  Future<void> _single(Future<void> Function() job) {
    final running = _inFlight;
    if (running != null) return running;
    final f = job().whenComplete(() => _inFlight = null);
    _inFlight = f;
    return f;
  }

  Future<void> _syncNow(bool manual) async {
    final user = _ref.read(authProvider).user;
    if (user == null) return; // nothing to sync before sign-in
    if (!manual && _nextAttempt != null && DateTime.now().isBefore(_nextAttempt!)) return;

    state = state.copyWith(status: SyncStatus.syncing, clearMessage: true);
    try {
      await refreshLocalInfo();
      if (!await isBackendReachable()) {
        state = state.copyWith(status: SyncStatus.offline);
        return;
      }
      state = state.copyWith(status: SyncStatus.online);

      final device = await deviceId();
      await _maybeHeartbeat();

      // Uploads first, so a slow or failing update can never block them.
      Object? uploadError;
      // A restart goes first: everything after it belongs to the new attempt.
      // Progress goes before test attempts: the server accepts a post-test
      // only once it knows reading was finished, and then completes the
      // module itself (so the order of a backlog after days offline is safe).
      for (final step in [_uploadRestart, _uploadProgress, _uploadQuizAttempts, _uploadAiQuestions, _uploadAnalytics]) {
        try {
          await step(device);
        } catch (e) {
          uploadError ??= e;
        }
      }

      // A learner-role change (made by an administrator) changes which
      // modules this account may see; the release check below then replaces
      // the content. Progress is never deleted.
      var roleChanged = false;
      try {
        roleChanged = await _ref.read(authProvider.notifier).refreshProfile();
      } catch (_) {}

      try {
        // Never restore server progress while our own restart is still waiting
        // to upload - it would bring the replaced attempt straight back.
        if (await _db.countPending(entityTypes: ['training_restart']) == 0) {
          await _applyServerRestart();
          await _pullLearning();
          await _pullProgress();
        }
      } catch (_) {
        // Restoring is best-effort; local progress keeps working regardless.
      }

      await _checkRelease(forceInstall: roleChanged);
      await _removeHiddenVideos();

      await _db.purgeSyncedQueue();
      if (uploadError != null) throw uploadError;

      _failures = 0;
      _nextAttempt = null;
      state = state.copyWith(lastSyncedAt: DateTime.now());
    } catch (e) {
      _failures++;
      final secs = min(30 * pow(2, _failures - 1).toInt(), 1800);
      _nextAttempt = DateTime.now().add(Duration(seconds: secs));
      state = state.copyWith(status: SyncStatus.syncError, message: _friendly(e));
      if (_failures == 1) {
        // One event per failure streak, not one per retry.
        try {
          await recordAnalyticsEvent(_db, 'SYNC_FAILED', payload: {'reason': e.runtimeType.toString()});
        } catch (_) {}
      }
    } finally {
      if (mounted) await refreshLocalInfo();
    }
  }

  String _friendly(Object e) {
    if (e is InstallException) return '$e Your current content is unchanged.';
    if (e is DioException) {
      if (e.response?.statusCode == 401) return 'Please sign in again to sync.';
      return 'Could not reach the server. Will retry automatically.';
    }
    return 'Sync did not complete. Will retry automatically.';
  }

  /// Brings down the progress this ACCOUNT already has on the server (new
  /// phone, reinstall, other device) so the learner resumes where they stopped.
  /// Local changes that have not uploaded yet are never overwritten.
  Future<void> _pullProgress() async {
    final resp = await _api.dio.get('/sync/progress');
    for (final r in (resp.data as List).cast<Map<String, dynamic>>()) {
      await _db.restoreProgressFromServer(
        moduleId: r['module_id'] as String,
        progressPercent: (r['progress_percent'] as num).toInt(),
        completed: r['completed'] as bool,
        lastSection: r['last_section'] as String?,
        lastOpenedAt: r['last_opened_at'] == null ? null : DateTime.parse(r['last_opened_at'] as String),
        completedAt: r['completed_at'] == null ? null : DateTime.parse(r['completed_at'] as String),
        readingCompletedAt:
            r['reading_completed_at'] == null ? null : DateTime.parse(r['reading_completed_at'] as String),
      );
    }
    state = state.copyWith(contentRevision: state.contentRevision + 1);
  }

  /// Downloaded videos of modules this account may no longer see are deleted
  /// (only once the module list was refreshed for the current learner role).
  Future<void> _removeHiddenVideos() async {
    try {
      for (final path in await _db.removeVideosOfHiddenModules()) {
        final f = File(path);
        if (await f.exists()) await f.delete();
      }
    } catch (_) {}
  }

  /// Pre-/post-test history the server holds for this account (so a new
  /// phone keeps the pre-test baseline) and the auto-approval threshold for
  /// 100% pre-tests.
  Future<void> _pullLearning() async {
    final resp = await _api.dio.get('/sync/learning');
    final data = resp.data as Map<String, dynamic>;
    for (final a in (data['attempts'] as List).cast<Map<String, dynamic>>()) {
      await _db.restoreAttemptFromServer(
        clientId: a['client_id'] as String,
        moduleId: a['module_id'] as String,
        testType: a['test_type'] as String,
        correct: (a['correct_count'] as num).toInt(),
        total: (a['total_count'] as num).toInt(),
        scorePercent: (a['score_percent'] as num).toInt(),
        passed: a['passed'] as bool,
        valid: a['valid'] as bool,
        invalidReason: a['invalid_reason'] as String?,
        takenAt: DateTime.parse(a['taken_at'] as String).toLocal(),
      );
    }
    // Lowest app version the server allows; older apps show "please update the app".
    await _db.setSetting(kMinAppVersionKey, (data['min_app_version'] as String?) ?? '');
    final threshold = data['auto_approve_percent'];
    if (threshold is num) await _db.setAutoApprovePercent(threshold.toInt());
  }

  /// One DEVICE_HEARTBEAT per UTC day (opt-in devices only) so the admin
  /// portal can count active devices even on days nobody opens a module.
  Future<void> _maybeHeartbeat() async {
    final today = DateTime.now().toUtc().toIso8601String().substring(0, 10);
    if ((await _db.getSetting('last_heartbeat_date')) == today) return;
    await recordAnalyticsEvent(_db, 'DEVICE_HEARTBEAT', payload: {'release_code': state.installedReleaseCode});
    await _db.setSetting('last_heartbeat_date', today);
  }

  // ---------- uploads ----------

  static String _utc(String? iso) {
    final parsed = iso == null ? null : DateTime.tryParse(iso);
    return (parsed ?? DateTime.now()).toUtc().toIso8601String();
  }

  List<Map<String, dynamic>> _results(Response<dynamic> resp) =>
      ((resp.data as Map<String, dynamic>)['results'] as List).cast<Map<String, dynamic>>();

  static bool _final(String status) => status == 'ok' || status == 'duplicate' || status == 'rejected';

  Future<void> _uploadRestart(String device) async {
    final rows = await _db.getPendingByType('training_restart', limit: 20);
    if (rows.isEmpty) return;
    final items = [for (final r in rows) jsonDecode(r.payloadJson) as Map<String, dynamic>];
    final resp = await _api.dio.post('/sync/training-restart', data: {'device_id': device, 'items': items});
    final done = <int>[];
    for (final res in _results(resp)) {
      if (_final(res['status'] as String)) {
        for (var i = 0; i < items.length; i++) {
          if (items[i]['client_id'] == res['key']) done.add(rows[i].id);
        }
      }
    }
    await _db.markSyncItemsDone(done);
  }

  /// A restart done elsewhere (an admin, or this account on another phone)
  /// replaces what this phone holds, so the old attempt cannot be re-uploaded.
  Future<void> _applyServerRestart() async {
    final resp = await _api.dio.get('/sync/training');
    final raw = (resp.data as Map<String, dynamic>)['restarted_at'] as String?;
    if (raw == null) return;
    final server = DateTime.parse(raw).toUtc();
    final local = await _db.lastTrainingRestart();
    if (local == null || server.isAfter(local.toUtc())) {
      if (local == null) {
        await _db.adoptServerRestart(server);
      } else {
        await _db.restartTraining(at: server, enqueue: false);
      }
      state = state.copyWith(contentRevision: state.contentRevision + 1);
    }
  }

  Future<void> _uploadQuizAttempts(String device) async {
    final rows = await _db.getUnsyncedQuizAttempts();
    for (var i = 0; i < rows.length; i += 50) {
      final batch = rows.sublist(i, min(i + 50, rows.length));
      final resp = await _api.dio.post('/sync/quiz-attempts', data: {
        'device_id': device,
        'items': [
          for (final r in batch)
            {
              'client_id': r.clientId,
              'module_id': r.moduleId,
              'correct_count': r.correctCount,
              'total_count': r.totalCount,
              'taken_at': r.takenAt.toUtc().toIso8601String(),
              'results': jsonDecode(r.resultsJson),
              // Attempts from before pre/post tests go without a type: kept as history only.
              if (r.testType != 'LEGACY') 'test_type': r.testType,
            },
        ],
      });
      for (final res in _results(resp)) {
        final status = res['status'] as String;
        if (!_final(status)) continue;
        // ok + a detail other than "completed" = stored but does not count.
        final detail = res['detail'] as String?;
        final counts = status == 'duplicate' ? null : (status == 'ok' && (detail == null || detail == 'completed'));
        await _db.markQuizAttemptSynced(res['key'] as String, valid: counts, reason: counts == false ? detail : null);
      }
    }
  }

  Future<void> _uploadProgress(String device) async {
    final rows = await _db.getUnsyncedProgress();
    final markers = await _db.getPendingByType('progress', limit: 1000);
    var allLanded = true;

    for (var i = 0; i < rows.length; i += 100) {
      final batch = rows.sublist(i, min(i + 100, rows.length));
      final resp = await _api.dio.post('/sync/progress', data: {
        'device_id': device,
        'items': [
          for (final r in batch)
            {
              'module_id': r.moduleId,
              'progress_percent': r.progressPercent,
              'completed': r.completed,
              'last_section': r.lastSection,
              'last_opened_at': r.lastOpenedAt?.toUtc().toIso8601String(),
              'completed_at': r.completedAt?.toUtc().toIso8601String(),
              'reading_completed_at': r.readingCompletedAt?.toUtc().toIso8601String(),
            },
        ],
      });
      for (final res in _results(resp)) {
        if (!_final(res['status'] as String)) {
          allLanded = false;
          continue;
        }
        final row = batch.where((r) => r.moduleId == res['key']).firstOrNull;
        if (row != null) await _db.markProgressSynced(row.moduleId, row.lastOpenedAt);
      }
    }
    // Queue rows for progress are only "something changed" markers; the rows
    // above are the source of truth, so the markers are done once they landed.
    if (allLanded) await _db.markSyncItemsDone([for (final m in markers) m.id]);
  }

  Future<void> _uploadAiQuestions(String device) => _drainQueue(
        device: device,
        entityType: 'ai_question',
        endpoint: '/sync/ai-questions',
        toItem: (clientId, p) => {
          'client_id': clientId,
          'question': p['question'],
          'answer': p['answer'],
          'matched': p['matched'] ?? false,
          'language': p['language'] ?? 'en',
          'asked_at': _utc(p['asked_at'] as String?),
        },
      );

  Future<void> _uploadAnalytics(String device) async {
    // Usage statistics leave the phone only if the person opted in (consent screen / Sync screen).
    if ((await _db.getSetting(kAnalyticsConsentKey)) != 'true') return;
    await _drainQueue(
      device: device,
      entityType: 'analytics',
      endpoint: '/sync/analytics',
      toItem: (clientId, p) => {
        'client_id': clientId,
        'event_type': p['event_type'],
        'module_id': p['module_id'],
        'video_id': p['video_id'],
        'language': p['language'],
        'payload': p['payload'] ?? <String, dynamic>{},
        'occurred_at': _utc(p['occurred_at'] as String?),
      },
    );
  }

  /// Uploads queued rows of one type, oldest first, 100 at a time. Rows are
  /// marked done only when the server reports ok / duplicate / rejected; a
  /// transport error or a per-item 'error' leaves them queued for the next run.
  Future<void> _drainQueue({
    required String device,
    required String entityType,
    required String endpoint,
    required Map<String, dynamic> Function(String clientId, Map<String, dynamic> payload) toItem,
  }) async {
    for (var round = 0; round < 50; round++) {
      final rows = await _db.getPendingByType(entityType, limit: 100);
      if (rows.isEmpty) return;

      final done = <int>[];
      final items = <Map<String, dynamic>>[];
      final rowByKey = <String, PendingSyncRow>{};
      for (final row in rows) {
        try {
          final payload = jsonDecode(row.payloadJson) as Map<String, dynamic>;
          final clientId = '$device-${row.id}'; // stable across retries => idempotent
          items.add(toItem(clientId, payload));
          rowByKey[clientId] = row;
        } catch (_) {
          done.add(row.id); // unreadable payload can never succeed: drop it
        }
      }

      var progressed = done.isNotEmpty;
      if (items.isNotEmpty) {
        final resp = await _api.dio.post(endpoint, data: {'device_id': device, 'items': items});
        for (final res in _results(resp)) {
          final row = rowByKey[res['key']];
          if (row != null && _final(res['status'] as String)) {
            done.add(row.id);
            progressed = true;
          }
        }
      }
      await _db.markSyncItemsDone(done);
      if (!progressed) return; // nothing could be confirmed: stop, retry later
    }
  }

  // ---------- releases ----------

  Future<void> _checkRelease({bool forceInstall = false}) async {
    try {
      await _checkReleaseCore(forceInstall: forceInstall);
    } finally {
      // Quizzes and the chosen language refresh on every sync, whether or not a
      // release update is pending, and after any install (which can rewrite
      // module text). Both helpers swallow their own errors.
      final content = _ref.read(contentSyncServiceProvider);
      await content.syncQuizzes();
      final code = await _db.getSetting('selected_language_code');
      if (code != null && code != 'en') await content.syncTranslations(code);
      state = state.copyWith(contentRevision: state.contentRevision + 1);
    }
  }

  Future<void> _checkReleaseCore({bool forceInstall = false}) async {
    final installed = await _db.getCurrentRelease();
    // "unknown" (installed by an app before 0.1.8) makes the server send this
    // account's role-filtered copy once.
    final variant = await _db.getSetting(kInstalledVariantKey);
    final resp = await _api.dio.get(
      '/sync/release/current',
      queryParameters: {
        if (installed != null) 'installed': installed.releaseCode,
        if (installed != null) 'installed_variant': (variant == null || variant.isEmpty) ? 'unknown' : variant,
      },
    );
    final data = resp.data as Map<String, dynamic>;
    final relJson = data['release'] as Map<String, dynamic>?;
    final hasContent = await _db.hasCachedContent();

    if (relJson == null) {
      // The server has not published a packaged release yet (development
      // setups). Fall back to the direct content download so a first-time
      // user is never left with an empty app.
      if (!hasContent) {
        await _ref.read(contentSyncServiceProvider).syncAll();
        state = state.copyWith(contentRevision: state.contentRevision + 1);
      }
      state = state.copyWith(status: SyncStatus.upToDate, clearAvailable: true);
      return;
    }

    final release = ReleaseInfo.fromJson(relJson);
    if (data['update_available'] != true) {
      state = state.copyWith(status: SyncStatus.upToDate, clearAvailable: true);
      return;
    }
    // First install and mandatory updates go ahead automatically; optional
    // updates wait for the person to choose a good moment (data costs money).
    // The same release in a different variant (the learner role changed, or
    // a module's audience did) is installed at once: it is small, and it
    // removes modules this account may no longer see.
    final sameReleaseNewVariant = installed?.releaseCode == release.releaseCode;
    if (release.mandatory || !hasContent || sameReleaseNewVariant || forceInstall) {
      await _install(release);
    } else {
      state = state.copyWith(status: SyncStatus.updateAvailable, availableRelease: release);
    }
  }

  /// Called by the "Install update" button.
  Future<void> installAvailableUpdate() => _single(() async {
        final release = state.availableRelease;
        if (release == null) return;
        try {
          await _install(release);
        } catch (e) {
          state = state.copyWith(status: SyncStatus.syncError, message: _friendly(e), installing: false);
          try {
            await recordAnalyticsEvent(_db, 'SYNC_FAILED', payload: {'stage': 'install', 'release': release.releaseCode});
          } catch (_) {}
        } finally {
          if (mounted) await refreshLocalInfo();
        }
      });

  Future<void> _install(ReleaseInfo release) async {
    state = state.copyWith(installing: true, installFraction: 0, status: SyncStatus.syncing);
    try {
      await ReleaseInstaller(_api, _db).install(release, onProgress: (stage, f) {
        if (mounted) state = state.copyWith(installStage: stage, installFraction: f);
      });
    } finally {
      if (mounted) state = state.copyWith(installing: false);
    }
    await recordAnalyticsEvent(
      _db,
      'UPDATE_INSTALLED',
      payload: {'release_code': release.releaseCode, 'version': release.version},
    );
    state = state.copyWith(
      status: SyncStatus.upToDate,
      clearAvailable: true,
      contentRevision: state.contentRevision + 1,
      lastSyncedAt: DateTime.now(),
    );
  }
}
