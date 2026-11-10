import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';
import 'package:sarmaan_eplaybook/services/api_client.dart';
import 'package:sarmaan_eplaybook/sync/release_installer.dart';

/// Serves release packages and images to the real ReleaseInstaller with no
/// network. Uses only APIs that exist in app 0.1.9 as well, so the same tests
/// also run against the 0.1.9 code (see content/hfw_flipbook/offline_and_app_version_tests.md).
class FakeServer implements HttpClientAdapter {
  final Map<String, List<int>> files = {};

  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final body = files[options.path];
    if (body == null) return ResponseBody.fromString('not found', 404);
    return ResponseBody.fromBytes(body, 200, headers: {
      Headers.contentTypeHeader: ['application/octet-stream'],
    });
  }

  @override
  void close({bool force = false}) {}
}

class TempDocs extends PathProviderPlatform with MockPlatformInterfaceMixin {
  final String root;
  TempDocs(this.root);
  @override
  Future<String?> getApplicationDocumentsPath() async => root;
  @override
  Future<String?> getTemporaryPath() async => root;
  @override
  Future<String?> getApplicationSupportPath() async => root;
}

/// An API client whose requests go to [server].
ApiClient fakeApi(FakeServer server) {
  FlutterSecureStorage.setMockInitialValues({});
  final api = ApiClient();
  api.dio.httpClientAdapter = server;
  return api;
}

List<int> imageBytes(String seed) => utf8.encode('fake-png-$seed');

Map<String, dynamic> module(String id, String code, int order, {String audience = 'GENERAL', List<String> roles = const [], String? imageId}) => {
      'id': id,
      'module_code': code,
      'module_number': order,
      'title': 'Module $code',
      'description': null,
      'status': 'PUBLISHED',
      'sort_order': order,
      'audience': audience,
      'learner_roles': roles,
      'translations': [
        {'id': 'tr-$id', 'language_id': 'en-id', 'language_code': 'en', 'title': 'Module $code', 'description': null,
         'body': null, 'audio_text': null, 'status': 'PUBLISHED'},
      ],
      'quiz_questions': [
        {'id': 'q-$id', 'question_type': 'TRUE_FALSE', 'prompt': 'Q?', 'content': {'correct': true},
         'explanation': null, 'sort_order': 1, 'usage': 'BOTH'},
      ],
      'sections': [
        {'id': 's1-$id', 'section_number': 1, 'title': null, 'content_type': 'TEXT', 'content': {'text': 'Lesson of $code'}, 'sort_order': 1},
        if (imageId != null)
          {'id': 's2-$id', 'section_number': 2, 'title': null, 'content_type': 'IMAGE',
           'content': {'media_asset_id': imageId, 'caption': 'Picture of $code', 'alt': 'Alt of $code'}, 'sort_order': 2},
      ],
      'section_translations': [],
    };

/// Puts a package (and its images) on the fake server; returns what /sync/release/current would offer.
ReleaseInfo publish(FakeServer server, String code, List<Map<String, dynamic>> modules, {String? curriculum}) {
  final media = <Map<String, dynamic>>[];
  for (final m in modules) {
    for (final s in (m['sections'] as List).cast<Map<String, dynamic>>()) {
      final type = s['content_type'];
      if (type != 'IMAGE' && type != 'AUDIO') continue;
      final id = s['content']['media_asset_id'] as String;
      final bytes = server.files['/media/$id/file'] ?? imageBytes(id);
      server.files['/media/$id/file'] = bytes;
      final audio = type == 'AUDIO';
      media.add({'id': id, 'asset_type': type, 'filename': audio ? '$id.mp3' : '$id.png',
                 'mime_type': audio ? 'audio/mpeg' : 'image/png',
                 'size_bytes': bytes.length, 'checksum': sha256.convert(bytes).toString()});
    }
  }
  final pkg = {
    'schema_version': 1,
    if (curriculum != null) 'curriculum': curriculum,
    'release': {'release_code': code, 'version': code, 'mandatory': true},
    'quiz_pass_mark': 90,
    'languages': ['en'],
    'modules': modules,
    'media': media,
    'chunks': [],
    'counts': {
      'modules': modules.length,
      'sections': modules.fold<int>(0, (n, m) => n + (m['sections'] as List).length),
      'media': media.length,
      'chunks': 0,
      'quiz_questions': modules.length,
    },
  };
  final bytes = utf8.encode(jsonEncode(pkg));
  server.files['/sync/release/$code/package'] = bytes;
  return ReleaseInfo(releaseCode: code, version: code, mandatory: true, packageSize: bytes.length,
      checksum: sha256.convert(bytes).toString());
}

Future<Directory> tempDocs() async {
  final dir = await Directory.systemTemp.createTemp('sarmaan-test-');
  PathProviderPlatform.instance = TempDocs(dir.path);
  return dir;
}
