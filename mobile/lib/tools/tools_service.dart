import 'package:drift/drift.dart' show Value;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart' show localDatabaseProvider;
import '../services/api_client.dart';
import '../services/auth_service.dart' show apiClientProvider;
import '../sync/sync_engine.dart';

/// What a Tools link points to (decides the icon; the type is also written out).
enum ToolType { document, spreadsheet, presentation, pdf, image, videoLink, website, form, other }

ToolType toolTypeFrom(String raw) => switch (raw) {
      'DOCUMENT' => ToolType.document,
      'SPREADSHEET' => ToolType.spreadsheet,
      'PRESENTATION' => ToolType.presentation,
      'PDF' => ToolType.pdf,
      'IMAGE' => ToolType.image,
      'VIDEO_LINK' => ToolType.videoLink,
      'WEBSITE' => ToolType.website,
      'FORM' => ToolType.form,
      _ => ToolType.other, // a type added on the server later still shows
    };

class ToolLink {
  final String id;
  final String moduleId;
  final String title;
  final String? description;
  final ToolType type;
  final String url;
  final String? host;
  final String? category;
  final String? languages;

  const ToolLink({
    required this.id,
    required this.moduleId,
    required this.title,
    required this.type,
    required this.url,
    this.description,
    this.host,
    this.category,
    this.languages,
  });

  /// Only https links are ever opened (the server accepts nothing else either).
  Uri? get uri {
    final u = Uri.tryParse(url);
    return u != null && u.scheme == 'https' && u.host.isNotEmpty ? u : null;
  }

  static ToolLink fromRow(CachedToolItemRow r) => ToolLink(
        id: r.id,
        moduleId: r.toolModuleId,
        title: r.title,
        description: r.description,
        type: toolTypeFrom(r.type),
        url: r.url,
        host: r.host,
        category: r.category,
        languages: r.languages,
      );
}

class ToolSection {
  final String id;
  final String title;
  final String? description;
  final List<ToolLink> links;

  const ToolSection(this.id, this.title, this.description, this.links);
}

/// The Tools repository as cached on the phone: modules that have links, in order.
class ToolsData {
  final List<ToolSection> sections;

  const ToolsData(this.sections);

  static const empty = ToolsData([]);

  bool get isEmpty => sections.isEmpty;
  int get linkCount => sections.fold(0, (n, s) => n + s.links.length);
  List<String> get categories =>
      ({for (final s in sections) for (final l in s.links) if (l.category != null && l.category!.isNotEmpty) l.category!}.toList()..sort());
}

/// Setting keys (app_settings table).
const kToolsSinceKey = 'tools_since';
const kToolsAudienceKey = 'tools_audience';

final toolsServiceProvider = Provider<ToolsService>((ref) => ToolsService(ref.read(apiClientProvider), ref.read(localDatabaseProvider)));

/// The cached Tools repository (works offline); re-read after every sync.
final toolsProvider = FutureProvider<ToolsData>((ref) async {
  ref.watch(syncEngineProvider.select((s) => s.contentRevision));
  return ref.read(toolsServiceProvider).load();
});

/// Keeps the Tools repository list on the phone: titles, descriptions and links
/// only (never the files). Downloads only the changes since the last download;
/// everything the first time or when the account's audience changed.
class ToolsService {
  final ApiClient _api;
  final LocalDatabase _db;

  ToolsService(this._api, this._db);

  Future<ToolsData> load() async {
    final items = (await _db.getToolItems()).map(ToolLink.fromRow).toList();
    return ToolsData([
      for (final m in await _db.getToolModules())
        if (items.any((i) => i.moduleId == m.id))
          ToolSection(m.id, m.title, m.description, [for (final i in items) if (i.moduleId == m.id) i]),
    ]);
  }

  /// [audience] names whose links these are (learner role, or staff). Never
  /// throws; an older server without the endpoint leaves the cache as it is.
  Future<void> sync(String audience) async {
    try {
      final sameAudience = (await _db.getSetting(kToolsAudienceKey)) == audience;
      final since = sameAudience ? await _db.getSetting(kToolsSinceKey) : null;
      final resp = await _api.dio.get('/sync/tools', queryParameters: {
        if (since != null && since.isNotEmpty) 'since': since,
      });
      final data = resp.data as Map<String, dynamic>;
      await _db.applyTools(
        [
          for (final m in (data['modules'] as List).cast<Map<String, dynamic>>())
            CachedToolModulesCompanion.insert(
              id: m['id'] as String,
              title: m['title'] as String,
              description: Value(m['description'] as String?),
              displayOrder: Value((m['display_order'] as num?)?.toInt() ?? 0),
            ),
        ],
        [
          for (final i in (data['items'] as List).cast<Map<String, dynamic>>())
            CachedToolItemsCompanion.insert(
              id: i['id'] as String,
              toolModuleId: i['tool_module_id'] as String,
              title: i['title'] as String,
              description: Value(i['description'] as String?),
              type: i['type'] as String,
              url: i['url'] as String,
              host: Value(i['host'] as String?),
              category: Value(i['category'] as String?),
              languages: Value(i['languages'] as String?),
              displayOrder: Value((i['display_order'] as num?)?.toInt() ?? 0),
            ),
        ],
        (data['removed'] as List? ?? const []).cast<String>(),
        replaceAll: data['full'] == true,
      );
      await _db.setSetting(kToolsAudienceKey, audience);
      await _db.setSetting(kToolsSinceKey, data['server_time'] as String);
    } catch (_) {
      // Offline, or a server without the endpoint: keep what is cached.
    }
  }
}
