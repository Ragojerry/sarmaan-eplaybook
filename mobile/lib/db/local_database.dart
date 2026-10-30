import 'dart:convert';
import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'local_database.g.dart';

/// Phase 8: the full local database per master prompt §19 — all 11 tables,
/// exactly as named there. Not every table is actively used yet:
/// `LocalAiQuestions` and `RagMetadata` are defined now (so the schema is
/// stable and doesn't need another migration later) but stay empty until
/// Phase 10/11 actually populates them — same "schema now, logic later"
/// pattern used for `analytics_events` in the backend's Phase 5.
///
/// IMPORTANT — build step required: Drift generates `local_database.g.dart`
/// from this file via build_runner. That generated file does not exist in
/// this delivery (no Flutter/Dart SDK in the dev sandbox to run it) — run
/// this after `flutter pub get`, before anything using LocalDatabase will
/// compile:
///
///   dart run build_runner build --delete-conflicting-outputs
///
/// See docs/mobile-app.md for the full explanation.

/// Explicit @DataClassName on every table below: Drift infers a row-class
/// name from the table class by default (usually stripping a trailing "s"),
/// but that inference can't be verified here — no Dart/Flutter SDK in this
/// sandbox to actually run build_runner and see what it generates. Naming
/// every row class explicitly removes that entire class of risk; the names
/// used here match exactly what every method signature below expects.

@DataClassName('CachedModuleRow')
class CachedModules extends Table {
  TextColumn get id => text()(); // server UUID, used as-is
  TextColumn get moduleCode => text()();
  IntColumn get moduleNumber => integer()();
  TextColumn get title => text()();
  TextColumn get description => text().nullable()();
  TextColumn get status => text()();
  IntColumn get sortOrder => integer()();
  DateTimeColumn get cachedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('CachedTranslationRow')
class CachedTranslations extends Table {
  TextColumn get id => text()();
  TextColumn get moduleId => text()();
  TextColumn get languageId => text()();
  TextColumn get languageCode => text()(); // denormalized for offline filtering without a join
  TextColumn get title => text()();
  TextColumn get description => text().nullable()();
  TextColumn get body => text().nullable()();
  TextColumn get audioText => text().nullable()();
  TextColumn get status => text()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('CachedSectionRow')
class CachedSections extends Table {
  TextColumn get id => text()();
  TextColumn get moduleId => text()();
  IntColumn get sectionNumber => integer()();
  TextColumn get title => text().nullable()();
  TextColumn get contentType => text()();
  TextColumn get contentJson => text()(); // raw JSON of the `content` map — Drift/sqlite has no native JSON column
  IntColumn get sortOrder => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('CachedMediaRow')
class CachedMedia extends Table {
  TextColumn get id => text()(); // matches backend media_assets.id
  TextColumn get assetType => text()();
  TextColumn get filename => text()();
  TextColumn get localPath => text().nullable()(); // null until actually downloaded
  TextColumn get checksum => text()(); // sha256, verified against this after download
  IntColumn get sizeBytes => integer()();
  TextColumn get mimeType => text()();
  DateTimeColumn get downloadedAt => dateTime().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('CachedVideoRow')
class CachedVideos extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get description => text().nullable()();
  TextColumn get moduleId => text().nullable()();
  IntColumn get durationSeconds => integer().nullable()();
  TextColumn get language => text()();
  BoolColumn get offlineAvailable => boolean()();
  TextColumn get status => text()();
  BoolColumn get hasFile => boolean()();
  TextColumn get localPath => text().nullable()(); // populated in Phase 9 — always null for now

  @override
  Set<Column> get primaryKey => {id};
}

@DataClassName('LocalProgressRow')
class LocalProgress extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get moduleId => text()();
  IntColumn get progressPercent => integer().withDefault(const Constant(0))();
  BoolColumn get completed => boolean().withDefault(const Constant(false))();
  TextColumn get lastSection => text().nullable()();
  DateTimeColumn get lastOpenedAt => dateTime().nullable()();
  DateTimeColumn get completedAt => dateTime().nullable()();
  BoolColumn get synced => boolean().withDefault(const Constant(false))();

  /// Owner of this row: every account on a shared phone keeps its own progress.
  TextColumn get userId => text().withDefault(const Constant(''))();
}

@DataClassName('PendingSyncRow')
class PendingSync extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get entityType => text()(); // 'progress' | 'ai_question' | 'analytics' — grows as later phases add sync payload types
  TextColumn get payloadJson => text()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get syncedAt => dateTime().nullable()();
  TextColumn get userId => text().withDefault(const Constant(''))();
}

@DataClassName('AppSettingRow')
class AppSettings extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

@DataClassName('InstalledReleaseRow')
class InstalledReleases extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get releaseCode => text()();
  TextColumn get version => text()();
  DateTimeColumn get installedAt => dateTime()();
  IntColumn get moduleCount => integer()();
  IntColumn get sectionCount => integer()();
}

/// Every question asked on the Ask screen (revised Phases 10/11): logged here
/// and queued in pending_sync for Phase 12 to upload to ai_question_log.
@DataClassName('LocalAiQuestionRow')
class LocalAiQuestions extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get question => text()();
  TextColumn get answer => text().nullable()();
  BoolColumn get matched => boolean().withDefault(const Constant(false))();
  DateTimeColumn get askedAt => dateTime()();
  BoolColumn get synced => boolean().withDefault(const Constant(false))();
  TextColumn get userId => text().withDefault(const Constant(''))();
}

/// RETIRED: reserved for an embedding-based retrieval design that the revised
/// Phases 10/11 replaced with ContentChunks + BM25. Unused; left in place so
/// existing installs need no destructive migration.
/// `embeddingJson` stores a JSON-encoded float array — sqlite has no native
/// vector type without an extension (master prompt §25 discusses this
/// choice explicitly as a later-phase decision, not Phase 8's).
@DataClassName('RagMetadataRow')
class RagMetadata extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get moduleId => text()();
  TextColumn get sectionId => text().nullable()();
  TextColumn get chunkText => text()();
  TextColumn get embeddingJson => text().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

/// Revised Phases 10/11: the passages the on-device Q&A engine searches.
/// Downloaded from GET /ai/chunks by ContentSyncService; one row per heading
/// group of a published module (same chunks the server uses, so answers match
/// online and offline). Plain table + the Dart BM25 in lib/qa/qa_engine.dart —
/// deliberately NOT an FTS5 virtual table (see docs/offline-qa.md).
@DataClassName('ContentChunkRow')
class ContentChunks extends Table {
  TextColumn get id => text()();
  TextColumn get moduleId => text()();
  TextColumn get moduleCode => text()();
  TextColumn get sectionId => text().nullable()();
  TextColumn get sectionTitle => text().nullable()();
  TextColumn get language => text()();
  TextColumn get sourceTitle => text()(); // the module's title
  TextColumn get chunkText => text()();

  @override
  Set<Column> get primaryKey => {id};
}

/// A module's quiz questions, delivered inside the release package. They include
/// the answers because grading happens on the phone, offline.
@DataClassName('CachedSectionTranslationRow')
class CachedSectionTranslations extends Table {
  TextColumn get sectionId => text()();
  TextColumn get moduleId => text()();
  TextColumn get languageCode => text()();
  TextColumn get title => text().nullable()();
  TextColumn get contentJson => text()();

  @override
  Set<Column> get primaryKey => {sectionId, languageCode};
}

@DataClassName('CachedQuizQuestionRow')
class CachedQuizQuestions extends Table {
  TextColumn get id => text()();
  TextColumn get moduleId => text()();
  TextColumn get questionType => text()();
  TextColumn get prompt => text()();
  TextColumn get contentJson => text()();
  TextColumn get explanation => text().nullable()();
  IntColumn get sortOrder => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

/// Every finished quiz attempt on this phone, per user. Uploaded to the server
/// (idempotent on clientId); the server re-checks the 90% rule.
@DataClassName('LocalQuizAttemptRow')
class LocalQuizAttempts extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get userId => text().withDefault(const Constant(''))();
  TextColumn get moduleId => text()();
  TextColumn get clientId => text().unique()();
  IntColumn get correctCount => integer()();
  IntColumn get totalCount => integer()();
  IntColumn get scorePercent => integer()();
  BoolColumn get passed => boolean()();
  TextColumn get resultsJson => text()(); // [{question_id, correct}]
  DateTimeColumn get takenAt => dateTime()();
  BoolColumn get synced => boolean().withDefault(const Constant(false))();
}

@DriftDatabase(
  tables: [
    CachedModules,
    CachedTranslations,
    CachedSections,
    CachedMedia,
    CachedVideos,
    LocalProgress,
    PendingSync,
    AppSettings,
    InstalledReleases,
    LocalAiQuestions,
    RagMetadata,
    ContentChunks,
    CachedQuizQuestions,
    LocalQuizAttempts,
    CachedSectionTranslations,
  ],
)
class LocalDatabase extends _$LocalDatabase {
  LocalDatabase() : super(_openConnection());

  // v2 (Phases 10/11 revised): added ContentChunks. Devices already on v1
  // (every install since Phase 8) get the table via onUpgrade — without this,
  // the Ask screen would crash with "no such table: content_chunks".
  // v4: quiz questions + attempts.
  // v3: progress, the upload queue and the question log are per user
  // (user_id), so a second account on the same phone starts fresh and each
  // person resumes exactly where they stopped.
  @override
  int get schemaVersion => 5;

  String? _activeUserId;

  /// Whose data every progress/queue/question query below reads and writes.
  /// Set synchronously by the sign-in code BEFORE the signed-in state is
  /// published, so no screen ever reads the previous person's rows.
  String get _uid => _activeUserId ?? '';

  void setActiveUser(String? userId) {
    _activeUserId = userId;
  }

  /// Analytics queued before anyone signed in belong to the device, not to a
  /// person; the first account to sign in adopts them.
  Future<void> adoptAnonymousAnalytics() async {
    final id = _activeUserId;
    if (id == null) return;
    await (update(pendingSync)..where((s) => s.userId.equals('') & s.entityType.equals('analytics')))
        .write(PendingSyncCompanion(userId: Value(id)));
  }

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) async => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.createTable(contentChunks);
          }
          if (from < 4) {
            await m.createTable(cachedQuizQuestions);
            await m.createTable(localQuizAttempts);
          }
          if (from < 5) {
            await m.createTable(cachedSectionTranslations);
          }
          if (from < 3) {
            await m.addColumn(localProgress, localProgress.userId);
            await m.addColumn(pendingSync, pendingSync.userId);
            await m.addColumn(localAiQuestions, localAiQuestions.userId);
            // Existing rows belong to whoever last used the phone (recorded by
            // the old sync engine); without a recorded owner they stay
            // unowned and are never uploaded or shown to anyone.
            final owner = await customSelect(
              "SELECT value FROM app_settings WHERE key = 'queue_owner_user_id'",
            ).getSingleOrNull();
            final ownerId = owner?.read<String>('value');
            if (ownerId != null) {
              for (final table in ['local_progress', 'pending_sync', 'local_ai_questions']) {
                await customStatement('UPDATE $table SET user_id = ?', [ownerId]);
              }
            }
          }
        },
      );

  // ---------- Content cache ----------

  Future<void> replaceModules(List<CachedModulesCompanion> rows) async {
    await batch((batch) {
      batch.deleteAll(cachedModules);
      batch.insertAll(cachedModules, rows);
    });
  }

  Future<void> replaceTranslationsForModule(String moduleId, List<CachedTranslationsCompanion> rows) async {
    await batch((batch) {
      batch.deleteWhere(cachedTranslations, (t) => t.moduleId.equals(moduleId));
      batch.insertAll(cachedTranslations, rows);
    });
  }

  /// Replaces ONE language's cached translations (module text + sections) for
  /// the given modules. Other languages, and English, are left alone.
  Future<void> replaceLanguageTranslations(
    String languageCode,
    Iterable<String> moduleIds,
    List<CachedTranslationsCompanion> modules,
    List<CachedSectionTranslationsCompanion> sections,
  ) async {
    final ids = moduleIds.toList();
    await batch((batch) {
      batch.deleteWhere(cachedTranslations, (t) => t.languageCode.equals(languageCode) & t.moduleId.isIn(ids));
      batch.deleteWhere(cachedSectionTranslations, (t) => t.languageCode.equals(languageCode) & t.moduleId.isIn(ids));
      batch.insertAll(cachedTranslations, modules);
      batch.insertAll(cachedSectionTranslations, sections);
    });
  }

  Future<List<CachedSectionTranslationRow>> getSectionTranslations(String moduleId, String languageCode) =>
      (select(cachedSectionTranslations)
            ..where((t) => t.moduleId.equals(moduleId) & t.languageCode.equals(languageCode)))
          .get();

  Future<void> replaceQuizForModule(String moduleId, List<CachedQuizQuestionsCompanion> rows) async {
    await batch((batch) {
      batch.deleteWhere(cachedQuizQuestions, (q) => q.moduleId.equals(moduleId));
      batch.insertAll(cachedQuizQuestions, rows);
    });
  }

  Future<List<CachedQuizQuestionRow>> getQuizQuestions(String moduleId) => (select(cachedQuizQuestions)
        ..where((q) => q.moduleId.equals(moduleId))
        ..orderBy([(q) => OrderingTerm(expression: q.sortOrder)]))
      .get();

  Future<int> countQuizQuestions(String moduleId) async {
    final r = await (selectOnly(cachedQuizQuestions)
          ..addColumns([cachedQuizQuestions.id.count()])
          ..where(cachedQuizQuestions.moduleId.equals(moduleId)))
        .getSingle();
    return r.read(cachedQuizQuestions.id.count()) ?? 0;
  }

  // ---------- Quiz attempts (per user) ----------

  Future<void> insertQuizAttempt({
    required String moduleId,
    required String clientId,
    required int correct,
    required int total,
    required int scorePercent,
    required bool passed,
    required String resultsJson,
  }) async {
    await into(localQuizAttempts).insert(
      LocalQuizAttemptsCompanion.insert(
        userId: Value(_uid),
        moduleId: moduleId,
        clientId: clientId,
        correctCount: correct,
        totalCount: total,
        scorePercent: scorePercent,
        passed: passed,
        resultsJson: resultsJson,
        takenAt: DateTime.now(),
      ),
    );
  }

  /// Highest-scoring attempt by the signed-in user for this module.
  Future<LocalQuizAttemptRow?> getBestQuizAttempt(String moduleId) => (select(localQuizAttempts)
        ..where((a) => a.moduleId.equals(moduleId) & a.userId.equals(_uid))
        ..orderBy([(a) => OrderingTerm.desc(a.scorePercent)])
        ..limit(1))
      .getSingleOrNull();

  Future<bool> hasPassedQuiz(String moduleId) async {
    final r = await (select(localQuizAttempts)
          ..where((a) => a.moduleId.equals(moduleId) & a.userId.equals(_uid) & a.passed.equals(true))
          ..limit(1))
        .getSingleOrNull();
    return r != null;
  }

  Future<List<LocalQuizAttemptRow>> getUnsyncedQuizAttempts() =>
      (select(localQuizAttempts)..where((a) => a.synced.equals(false) & a.userId.equals(_uid))).get();

  Future<void> markQuizAttemptSynced(String clientId) => (update(localQuizAttempts)..where((a) => a.clientId.equals(clientId)))
      .write(const LocalQuizAttemptsCompanion(synced: Value(true)));

  Future<void> replaceSectionsForModule(String moduleId, List<CachedSectionsCompanion> rows) async {
    await batch((batch) {
      batch.deleteWhere(cachedSections, (s) => s.moduleId.equals(moduleId));
      batch.insertAll(cachedSections, rows);
    });
  }

  /// Modules in order, with title/description in the language the person
  /// chose when a published translation is cached (English otherwise).
  Future<List<CachedModuleRow>> getAllModules() async {
    final rows = await (select(cachedModules)..orderBy([(t) => OrderingTerm(expression: t.sortOrder)])).get();
    final code = await getSetting('selected_language_code');
    if (code == null || code == 'en') return rows;
    final tr = await (select(cachedTranslations)..where((t) => t.languageCode.equals(code))).get();
    final byModule = {for (final t in tr) t.moduleId: t};
    return [
      for (final r in rows)
        if (byModule[r.id] case final t?)
          r.copyWith(title: t.title, description: Value(t.description ?? r.description))
        else
          r,
    ];
  }

  Future<CachedModuleRow?> getModule(String id) =>
      (select(cachedModules)..where((t) => t.id.equals(id))).getSingleOrNull();

  Future<List<CachedSectionRow>> getSectionsForModule(String moduleId) =>
      (select(cachedSections)
            ..where((s) => s.moduleId.equals(moduleId))
            ..orderBy([(s) => OrderingTerm(expression: s.sortOrder)]))
          .get();

  Future<CachedTranslationRow?> getTranslationForModule(String moduleId, String languageCode) =>
      (select(cachedTranslations)
            ..where((t) => t.moduleId.equals(moduleId) & t.languageCode.equals(languageCode)))
          .getSingleOrNull();

  Future<bool> hasCachedContent() async {
    final count = await (selectOnly(cachedModules)..addColumns([cachedModules.id.count()])).getSingle();
    return (count.read(cachedModules.id.count()) ?? 0) > 0;
  }

  // ---------- Media cache ----------

  Future<void> upsertMedia(CachedMediaCompanion row) => into(cachedMedia).insertOnConflictUpdate(row);

  Future<CachedMediaRow?> getMedia(String id) =>
      (select(cachedMedia)..where((m) => m.id.equals(id))).getSingleOrNull();

  /// Sums the actual on-disk size of every downloaded training image —
  /// the "Training" figure in master prompt §24's storage-usage display
  /// (Videos / Training / AI / Total / Available). Checked live against
  /// the filesystem, same reasoning as totalDownloadedVideoBytes.
  Future<int> totalCachedMediaBytes() async {
    final rows = await (select(cachedMedia)..where((m) => m.localPath.isNotNull())).get();
    int total = 0;
    for (final row in rows) {
      if (row.localPath == null) continue;
      final file = File(row.localPath!);
      if (await file.exists()) total += await file.length();
    }
    return total;
  }

  // ---------- Local search (title + body/text substring match — no FTS
  // extension required for this phase's scope; §19 lists "local search" as
  // a requirement, not specifically full-text-search tooling) ----------

  Future<List<CachedModuleRow>> searchModules(String query) {
    final lower = '%${query.toLowerCase()}%';
    return (select(cachedModules)..where((m) => m.title.lower().like(lower))).get();
  }

  Future<List<CachedSectionRow>> searchSections(String query) {
    final lower = '%${query.toLowerCase()}%';
    return (select(cachedSections)..where((s) => s.contentJson.lower().like(lower))).get();
  }

  // ---------- Progress ----------

  Future<LocalProgressRow?> getProgressForModule(String moduleId) =>
      (select(localProgress)..where((p) => p.moduleId.equals(moduleId) & p.userId.equals(_uid))).getSingleOrNull();

  Future<void> upsertProgress({
    required String moduleId,
    int? progressPercent,
    bool? completed,
    String? lastSection,
  }) async {
    final existing = await getProgressForModule(moduleId);
    final now = DateTime.now();
    if (existing == null) {
      await into(localProgress).insert(
        LocalProgressCompanion.insert(
          moduleId: moduleId,
          progressPercent: Value(progressPercent ?? 0),
          completed: Value(completed ?? false),
          lastSection: Value(lastSection),
          lastOpenedAt: Value(now),
          completedAt: Value(completed == true ? now : null),
          synced: const Value(false),
          userId: Value(_uid),
        ),
      );
    } else {
      await (update(localProgress)..where((p) => p.moduleId.equals(moduleId) & p.userId.equals(_uid))).write(
        LocalProgressCompanion(
          progressPercent: Value(progressPercent ?? existing.progressPercent),
          completed: Value(completed ?? existing.completed),
          lastSection: Value(lastSection ?? existing.lastSection),
          lastOpenedAt: Value(now),
          completedAt: Value(completed == true ? now : existing.completedAt),
          synced: const Value(false), // any local change means it needs re-syncing
        ),
      );
    }
  }

  Future<List<LocalProgressRow>> getAllProgress() =>
      (select(localProgress)..where((p) => p.userId.equals(_uid))).get();

  /// Applies progress the SERVER holds for this account (new phone, reinstall,
  /// or work done on another device). Never overwrites local changes that have
  /// not been uploaded yet; those upload first and the server merges them.
  Future<void> restoreProgressFromServer({
    required String moduleId,
    required int progressPercent,
    required bool completed,
    String? lastSection,
    DateTime? lastOpenedAt,
    DateTime? completedAt,
  }) async {
    final local = await getProgressForModule(moduleId);
    if (local == null) {
      await into(localProgress).insert(
        LocalProgressCompanion.insert(
          moduleId: moduleId,
          progressPercent: Value(progressPercent),
          completed: Value(completed),
          lastSection: Value(lastSection),
          lastOpenedAt: Value(lastOpenedAt),
          completedAt: Value(completedAt),
          synced: const Value(true),
          userId: Value(_uid),
        ),
      );
      return;
    }
    if (!local.synced) return;
    final serverNewer = lastOpenedAt != null && (local.lastOpenedAt == null || lastOpenedAt.isAfter(local.lastOpenedAt!));
    if (serverNewer || (completed && !local.completed)) {
      await (update(localProgress)..where((p) => p.moduleId.equals(moduleId) & p.userId.equals(_uid))).write(
        LocalProgressCompanion(
          progressPercent: Value(completed ? 100 : progressPercent),
          completed: Value(completed || local.completed),
          lastSection: Value(lastSection ?? local.lastSection),
          lastOpenedAt: Value(lastOpenedAt ?? local.lastOpenedAt),
          completedAt: Value(completedAt ?? local.completedAt),
          synced: const Value(true),
        ),
      );
    }
  }

  // ---------- Training restart ----------

  /// Starts this account's training over: its progress and quiz attempts on
  /// this phone are replaced (deleted), and the restart is queued so the server
  /// replaces its copy too. [enqueue] is false when the restart came FROM the
  /// server (admin reset or another device) and only needs applying here.
  Future<void> restartTraining({DateTime? at, bool enqueue = true}) async {
    final when = (at ?? DateTime.now()).toUtc();
    await transaction(() async {
      await (delete(localProgress)..where((p) => p.userId.equals(_uid))).go();
      await (delete(localQuizAttempts)..where((a) => a.userId.equals(_uid))).go();
      // Queued progress markers belong to the attempt being replaced.
      await (update(pendingSync)
            ..where((s) => s.syncedAt.isNull() & s.userId.equals(_uid) & s.entityType.equals('progress')))
          .write(PendingSyncCompanion(syncedAt: Value(DateTime.now())));
      await setSetting('training_restarted_at_$_uid', when.toIso8601String());
      if (enqueue) {
        await enqueueSync(
          'training_restart',
          jsonEncode({'client_id': '$_uid-${when.microsecondsSinceEpoch}', 'restarted_at': when.toIso8601String()}),
        );
      }
    });
  }

  /// First time this phone hears of an earlier server-side restart: drop only
  /// what predates it, keeping anything done since (e.g. offline on a new phone).
  Future<void> adoptServerRestart(DateTime at) async {
    final cutoff = at.toUtc();
    await transaction(() async {
      await (delete(localProgress)
            ..where((p) => p.userId.equals(_uid) & (p.lastOpenedAt.isNull() | p.lastOpenedAt.isSmallerThanValue(cutoff))))
          .go();
      await (delete(localQuizAttempts)..where((a) => a.userId.equals(_uid) & a.takenAt.isSmallerThanValue(cutoff))).go();
      await setSetting('training_restarted_at_$_uid', cutoff.toIso8601String());
    });
  }

  Future<DateTime?> lastTrainingRestart() async {
    final v = await getSetting('training_restarted_at_$_uid');
    return v == null ? null : DateTime.tryParse(v);
  }

  // ---------- Pending sync queue (Phase 12 drains this — Phase 8 only
  // populates it) ----------

  Future<void> enqueueSync(String entityType, String payloadJson) async {
    await into(pendingSync).insert(
      PendingSyncCompanion.insert(
        entityType: entityType,
        payloadJson: payloadJson,
        createdAt: DateTime.now(),
        userId: Value(_uid),
      ),
    );
  }

  Future<List<PendingSyncRow>> getUnsyncedItems() =>
      (select(pendingSync)..where((s) => s.syncedAt.isNull() & s.userId.equals(_uid))).get();

  // ---------- Settings (replaces SharedPreferences — one local storage
  // technology, per master prompt §19 listing app_settings as a table) ----------

  Future<String?> getSetting(String key) async {
    final row = await (select(appSettings)..where((s) => s.key.equals(key))).getSingleOrNull();
    return row?.value;
  }

  Future<void> setSetting(String key, String value) async {
    await into(appSettings).insertOnConflictUpdate(AppSettingsCompanion.insert(key: key, value: value));
  }

  // ---------- Installed releases ----------

  Future<void> recordInstalledRelease({
    required String releaseCode,
    required String version,
    required int moduleCount,
    required int sectionCount,
  }) async {
    await into(installedReleases).insert(
      InstalledReleasesCompanion.insert(
        releaseCode: releaseCode,
        version: version,
        installedAt: DateTime.now(),
        moduleCount: moduleCount,
        sectionCount: sectionCount,
      ),
    );
  }

  /// Newest installed release. `limit(1)` matters: the table keeps history,
  /// and Drift's getSingleOrNull() throws if more than one row comes back.
  Future<InstalledReleaseRow?> getCurrentRelease() =>
      (select(installedReleases)
            ..orderBy([(r) => OrderingTerm.desc(r.installedAt), (r) => OrderingTerm.desc(r.id)])
            ..limit(1))
          .getSingleOrNull();

  // ---------- Q&A passages + question log (revised Phases 10/11) ----------

  Future<void> replaceChunks(String language, List<ContentChunksCompanion> rows) async {
    await batch((b) {
      b.deleteWhere(contentChunks, (c) => c.language.equals(language));
      b.insertAll(contentChunks, rows);
    });
  }

  Future<List<ContentChunkRow>> getChunks(String language) =>
      (select(contentChunks)..where((c) => c.language.equals(language))).get();

  Future<void> logQuestion({required String question, String? answer, required bool matched}) async {
    await into(localAiQuestions).insert(
      LocalAiQuestionsCompanion.insert(
        question: question,
        answer: Value(answer),
        matched: Value(matched),
        askedAt: DateTime.now(),
        userId: Value(_uid),
      ),
    );
  }

  // ---------- Phase 12: sync queue + release install helpers ----------

  /// Oldest-first, so uploads reach the server in the order things happened.
  Future<List<PendingSyncRow>> getPendingByType(String entityType, {int limit = 100}) =>
      (select(pendingSync)
            ..where((s) => s.syncedAt.isNull() & s.entityType.equals(entityType) & s.userId.equals(_uid))
            ..orderBy([(s) => OrderingTerm.asc(s.id)])
            ..limit(limit))
          .get();

  Future<int> countPending({List<String>? entityTypes}) async {
    final q = selectOnly(pendingSync)
      ..addColumns([pendingSync.id.count()])
      ..where(pendingSync.syncedAt.isNull() & pendingSync.userId.equals(_uid));
    if (entityTypes != null) q.where(pendingSync.entityType.isIn(entityTypes));
    final row = await q.getSingle();
    return row.read(pendingSync.id.count()) ?? 0;
  }

  Future<void> markSyncItemsDone(List<int> ids) async {
    if (ids.isEmpty) return;
    await (update(pendingSync)..where((s) => s.id.isIn(ids))).write(PendingSyncCompanion(syncedAt: Value(DateTime.now())));
  }

  /// Progress rows changed since the last successful upload.
  Future<List<LocalProgressRow>> getUnsyncedProgress() =>
      (select(localProgress)..where((p) => p.synced.equals(false) & p.userId.equals(_uid))).get();

  /// Marks a progress row uploaded ONLY if it has not changed since it was
  /// read for upload — otherwise a change made mid-upload would be hidden.
  Future<void> markProgressSynced(String moduleId, DateTime? lastOpenedAtSent) async {
    final current = await getProgressForModule(moduleId);
    if (current == null) return;
    final unchanged = current.lastOpenedAt == lastOpenedAtSent;
    if (unchanged) {
      await (update(localProgress)..where((p) => p.moduleId.equals(moduleId) & p.userId.equals(_uid))).write(
        const LocalProgressCompanion(synced: Value(true)),
      );
    }
  }

  /// Housekeeping: uploaded queue rows older than [age] are no longer needed.
  Future<void> purgeSyncedQueue({Duration age = const Duration(days: 7)}) async {
    final cutoff = DateTime.now().subtract(age);
    await (delete(pendingSync)..where((s) => s.syncedAt.isNotNull() & s.syncedAt.isSmallerThanValue(cutoff))).go();
  }

  /// Wipes EVERY account's local progress/queue/questions on this device.
  /// Not used by sign-in any more (data is per user now); kept for a future
  /// "reset this device" action.
  Future<void> clearUserData() async {
    await transaction(() async {
      await delete(pendingSync).go();
      await delete(localProgress).go();
      await delete(localAiQuestions).go();
      await delete(localQuizAttempts).go();
    });
  }

  Future<List<CachedMediaRow>> getAllMedia() => select(cachedMedia).get();

  Future<void> deleteMedia(String id) => (delete(cachedMedia)..where((m) => m.id.equals(id))).go();

  Future<int> countModules() async {
    final r = await (selectOnly(cachedModules)..addColumns([cachedModules.id.count()])).getSingle();
    return r.read(cachedModules.id.count()) ?? 0;
  }

  Future<int> countSections() async {
    final r = await (selectOnly(cachedSections)..addColumns([cachedSections.id.count()])).getSingle();
    return r.read(cachedSections.id.count()) ?? 0;
  }

  Future<int> countChunks() async {
    final r = await (selectOnly(contentChunks)..addColumns([contentChunks.id.count()])).getSingle();
    return r.read(contentChunks.id.count()) ?? 0;
  }

  /// Drops cached translations/sections/chunks of modules that are no longer
  /// part of the installed release (e.g. an unpublished module).
  Future<void> deleteContentOutside(Set<String> moduleIds, Set<String> languages) async {
    final ids = moduleIds.toList();
    await (delete(cachedTranslations)..where((t) => t.moduleId.isNotIn(ids))).go();
    await (delete(cachedSections)..where((s) => s.moduleId.isNotIn(ids))).go();
    await (delete(cachedQuizQuestions)..where((q) => q.moduleId.isNotIn(ids))).go();
    await (delete(cachedSectionTranslations)..where((t) => t.moduleId.isNotIn(ids))).go();
    await (delete(contentChunks)..where((c) => c.language.isNotIn(languages.toList()))).go();
  }

  // ---------- Videos (Phase 9: offline video) ----------

  Future<CachedVideoRow?> getVideo(String id) => (select(cachedVideos)..where((v) => v.id.equals(id))).getSingleOrNull();

  Future<void> markVideoDeleted(String id) async {
    await (update(cachedVideos)..where((v) => v.id.equals(id))).write(
      const CachedVideosCompanion(offlineAvailable: Value(false), hasFile: Value(false), localPath: Value(null)),
    );
  }

  /// Sums the actual on-disk size of every downloaded video file, checked
  /// live against the filesystem rather than trusting a possibly-stale
  /// stored byte count — backs the storage-usage display master prompt
  /// §24 specifies.
  Future<int> totalDownloadedVideoBytes() async {
    final rows = await (select(cachedVideos)..where((v) => v.localPath.isNotNull())).get();
    int total = 0;
    for (final row in rows) {
      if (row.localPath == null) continue;
      final file = File(row.localPath!);
      if (await file.exists()) total += await file.length();
    }
    return total;
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'sarmaan_eplaybook.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
