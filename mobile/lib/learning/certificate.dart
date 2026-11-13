import 'dart:convert';

import 'package:crypto/crypto.dart';

import '../quiz/quiz_grader.dart';
import 'learning_rules.dart';

/// The training completion certificate: earned with a General post-test that passed
/// its stored pass mark (since 2026-11-13: CDD 60%, others 80%), or 90% for older
/// attempts stored without one (never re-graded). Works offline.
///
/// The number is derived, not stored, so the phone can print it before it syncs
/// and the admin portal can still check it (backend/app/learning/certificate.py
/// holds the same rule): SII-<year taken, UTC>-<first 10 hex digits of
/// sha256("<user id>:<attempt client id>"), upper case>.
String certificateNumber(String userId, String clientId, DateTime takenAt) {
  final digest = sha256.convert(utf8.encode('$userId:$clientId')).toString().substring(0, 10).toUpperCase();
  return 'SII-${takenAt.toUtc().year}-$digest';
}

/// Whether [general] holds a passing post-test.
bool hasCertificate(GeneralLearning general) {
  final post = general.post;
  if (post == null) return false;
  return post.passMark == null ? quizPassed(post.correct, post.total) : generalPasses(post.correct, post.total, post.passMark!);
}

/// What the certificate shows.
class CertificateData {
  final String name;
  final String number;
  final DateTime completedAt;
  final int correct;
  final int total;

  const CertificateData({required this.name, required this.number, required this.completedAt, required this.correct, required this.total});

  int get percent => quizScorePercent(correct, total);

  /// The certificate for [general], or null when the post-test was not passed.
  static CertificateData? of(GeneralLearning general, {required String userId, required String name}) {
    final post = general.post;
    if (post == null || !hasCertificate(general)) return null;
    return CertificateData(
      name: name,
      number: certificateNumber(userId, post.clientId, post.takenAt),
      completedAt: post.takenAt,
      correct: post.correct,
      total: post.total,
    );
  }
}
