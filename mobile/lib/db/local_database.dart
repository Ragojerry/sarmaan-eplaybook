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
}

@DataClassName('PendingSyncRow')
class PendingSync extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get entityType => text()(); // 'progress' | 'ai_question' | 'analytics' — grows as later phases add sync payload types
  TextColumn get payloadJson => text()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get syncedAt => dateTime().nullable()();
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

/// Defined per master prompt §19 but unused until Phase 10/11 (offline AI).
@DataClassName('LocalAiQuestionRow')
class LocalAiQuestions extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get question => text()();
  TextColumn get answer => text().nullable()();
  BoolColumn get matched => boolean().withDefault(const Constant(false))();
  DateTimeColumn get askedAt => dateTime()();
  BoolColumn get synced => boolean().withDefault(const Constant(false))();
}

/// Defined per master prompt §19 but unused until Phase 10/11 (offline RAG).
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
  ],
)
class LocalDatabase extends _$LocalDatabase {
  LocalDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;

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

  Future<void> replaceSectionsForModule(String moduleId, List<CachedSectionsCompanion> rows) async {
    await batch((batch) {
      batch.deleteWhere(cachedSections, (s) => s.moduleId.equals(moduleId));
      batch.insertAll(cachedSections, rows);
    });
  }

  Future<List<CachedModuleRow>> getAllModules() => (select(cachedModules)..orderBy([(t) => OrderingTerm(expression: t.sortOrder)])).get();

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
      (select(localProgress)..where((p) => p.moduleId.equals(moduleId))).getSingleOrNull();

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
        ),
      );
    } else {
      await (update(localProgress)..where((p) => p.moduleId.equals(moduleId))).write(
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

  Future<List<LocalProgressRow>> getAllProgress() => select(localProgress).get();

  // ---------- Pending sync queue (Phase 12 drains this — Phase 8 only
  // populates it) ----------

  Future<void> enqueueSync(String entityType, String payloadJson) async {
    await into(pendingSync).insert(
      PendingSyncCompanion.insert(entityType: entityType, payloadJson: payloadJson, createdAt: DateTime.now()),
    );
  }

  Future<List<PendingSyncRow>> getUnsyncedItems() =>
      (select(pendingSync)..where((s) => s.syncedAt.isNull())).get();

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

  Future<InstalledReleaseRow?> getCurrentRelease() =>
      (select(installedReleases)..orderBy([(r) => OrderingTerm.desc(r.installedAt)])).getSingleOrNull();

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
