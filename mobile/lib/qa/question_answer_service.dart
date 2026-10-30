import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../db/local_database.dart';
import '../offline/content_sync_service.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import 'qa_engine.dart';

final questionAnswerServiceProvider = Provider<QuestionAnswerService>(
  (ref) => QuestionAnswerService(ref.read(apiClientProvider), ref.read(localDatabaseProvider)),
);

const String kNothingDownloadedMessage =
    'No training content has been downloaded to this device yet. Connect to the internet and open Home to download it, then ask again.';

/// The single seam the Ask screen talks to — it never knows which engine
/// answered. Local-first (offline-first, master prompt §18): if this device
/// holds the training passages, the question is answered ON the device with
/// no network at all. Only a device with nothing downloaded yet tries the
/// server (same algorithm, same answers). This is also where an online
/// "enhanced" answer or a local LLM could later slot in without touching the
/// UI. Every question is logged locally and queued for Phase 12 to upload.
class QuestionAnswerService {
  final ApiClient _api;
  final LocalDatabase _db;

  QuestionAnswerService(this._api, this._db);

  Future<AnswerResult> ask(String question, {String language = 'en'}) async {
    final q = question.trim();
    final rows = await _db.getChunks(language);

    AnswerResult result;
    if (rows.isNotEmpty) {
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
    } else {
      result = await _askServer(q, language);
    }

    await _db.logQuestion(question: q, answer: result.matched ? result.answer : null, matched: result.matched);
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
    return result;
  }

  Future<AnswerResult> _askServer(String question, String language) async {
    try {
      final resp = await _api.dio.post('/ai/ask', data: {'question': question, 'language': language});
      return AnswerResult.fromJson(resp.data as Map<String, dynamic>);
    } catch (_) {
      return const AnswerResult(
        answer: kNothingDownloadedMessage,
        matched: false,
        confidence: 0,
        offline: true,
        sources: [],
        suggestions: [],
      );
    }
  }
}
