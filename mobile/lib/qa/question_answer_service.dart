import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart';
import '../services/auth_service.dart';
import 'qa_engine.dart';

final questionAnswerServiceProvider = Provider<QuestionAnswerService>((ref) {
  final api = ref.read(apiClientProvider);
  return QuestionAnswerService(ref.read(localDatabaseProvider), (question, language) async {
    final resp = await api.dio.post('/ai/ask', data: {'question': question, 'language': language});
    return resp.data as Map<String, dynamic>;
  });
});

const String kNothingDownloadedMessage =
    'No training content has been downloaded to this device yet. Connect to the internet and open Home to download it, then ask again.';

/// POST /ai/ask; throws when the server can't be reached.
typedef ServerAsk = Future<Map<String, dynamic>> Function(String question, String language);

/// The single seam the Ask screen talks to — it never knows which engine
/// answered. Online first: the server searches by meaning and also holds the
/// approved reference library, so it understands reworded questions the
/// on-device keyword engine misses. When the server can't answer quickly
/// (no signal, dead mobile data), a device holding the training passages
/// answers ON the device with no network at all (offline-first, master
/// prompt §18), so a CDD in the field always gets an answer.
///
/// The server logs the questions it answers; questions answered on the
/// device are logged locally and queued for upload (Phase 12).
class QuestionAnswerService {
  final LocalDatabase _db;
  final ServerAsk _askServer;
  final Future<bool> Function() _maybeOnline;

  /// How long to wait for the server before answering on the device. A phone
  /// with nothing downloaded has no fallback, so it waits longer.
  final Duration serverTimeout;
  final Duration serverTimeoutWithoutContent;

  QuestionAnswerService(
    this._db,
    this._askServer, {
    Future<bool> Function()? maybeOnline,
    this.serverTimeout = const Duration(seconds: 8),
    this.serverTimeoutWithoutContent = const Duration(seconds: 20),
  }) : _maybeOnline = maybeOnline ?? _hasNetwork;

  /// Skips the server in airplane mode; anything else is decided by trying.
  static Future<bool> _hasNetwork() async {
    try {
      final c = await Connectivity().checkConnectivity();
      return !c.every((r) => r == ConnectivityResult.none);
    } catch (_) {
      return true; // plugin problem: let the request decide
    }
  }

  Future<AnswerResult> ask(String question, {String language = 'en'}) async {
    final q = question.trim();
    final rows = await _db.getChunks(language);

    var result = await _tryServer(q, language, hasLocalContent: rows.isNotEmpty);
    final answeredOnline = result != null;
    if (result == null && rows.isNotEmpty) {
      final chunks = [
        for (final r in rows)
          QaChunk(
            id: r.id,
            moduleId: r.moduleId,
            sectionId: r.sectionId,
            moduleCode: r.moduleCode,
            sourceTitle: r.sourceTitle,
            sectionTitle: r.sectionTitle,
            chunkText: r.chunkText,
          ),
      ];
      result = answerQuestion(q, chunks).copyWith(offline: true);
    }
    result ??= const AnswerResult(
      answer: kNothingDownloadedMessage,
      matched: false,
      confidence: 0,
      offline: true,
      sources: [],
      suggestions: [],
    );

    await _db.logQuestion(question: q, answer: result.matched ? result.answer : null, matched: result.matched);
    if (!answeredOnline) {
      await _db.enqueueSync(
        'ai_question',
        jsonEncode({
          'question': q,
          'matched': result.matched,
          'answer': result.matched ? result.answer : null,
          'language': language,
          'asked_at': DateTime.now().toUtc().toIso8601String(),
        }),
      );
    }
    return result;
  }

  Future<AnswerResult?> _tryServer(String question, String language, {required bool hasLocalContent}) async {
    if (!await _maybeOnline()) return null;
    try {
      final json = await _askServer(question, language)
          .timeout(hasLocalContent ? serverTimeout : serverTimeoutWithoutContent);
      return AnswerResult.fromJson(json);
    } catch (_) {
      return null;
    }
  }
}
