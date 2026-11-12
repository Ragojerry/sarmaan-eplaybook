import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/learning/certificate.dart';
import 'package:sarmaan_eplaybook/learning/certificate_pdf.dart';
import 'package:sarmaan_eplaybook/learning/learning_rules.dart';

/// The training certificate: earned at 90% on the General post-test, numbered the
/// same way as the server (backend/tests/test_certificate.py checks the same vector).
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  GeneralLearning withPost(int correct, int total) => GeneralLearning(
        active: true,
        questions: total,
        pre: TestScore(clientId: 'pre-1', testType: 'PRE', correct: 10, total: total, takenAt: DateTime.utc(2026, 11, 1)),
        post: TestScore(
            clientId: 'general-post-1731405600000-0', testType: 'POST', correct: correct, total: total, takenAt: DateTime.utc(2026, 11, 12, 10)),
        modulesTotal: 6,
        modulesCompleted: 6,
      );

  test('the number matches the server rule', () {
    expect(certificateNumber('11111111-2222-3333-4444-555555555555', 'general-post-1731405600000-0', DateTime.utc(2026, 11, 12, 10)),
        'SII-2026-06E1A47048');
  });

  test('earned at 90% or more on the post-test only', () {
    expect(hasCertificate(withPost(23, 25)), isTrue, reason: '92%');
    expect(hasCertificate(withPost(22, 25)), isFalse, reason: '88%');
    expect(hasCertificate(withPost(25, 25).copyWithoutPost()), isFalse, reason: 'no post-test yet');
    final data = CertificateData.of(withPost(23, 25), userId: '11111111-2222-3333-4444-555555555555', name: 'Ɓello Ɗanjuma')!;
    expect(data.number, 'SII-2026-06E1A47048');
    expect(data.percent, 92);
    expect(CertificateData.of(withPost(22, 25), userId: 'u', name: 'x'), isNull);
  });

  test('the PDF builds offline from the bundled font and logos, with Hausa letters in the name', () async {
    final data = CertificateData.of(withPost(23, 25), userId: '11111111-2222-3333-4444-555555555555', name: 'Ɓello Ɗanjuma Ƙanƙara')!;
    final bytes = await buildCertificatePdf(data);
    expect(ascii.decode(bytes.sublist(0, 5)), '%PDF-');
    expect(bytes.length, greaterThan(20000), reason: 'font and logos embedded');
  });
}

extension on GeneralLearning {
  GeneralLearning copyWithoutPost() => GeneralLearning(
      active: active, questions: questions, pre: pre, post: null, modulesTotal: modulesTotal, modulesCompleted: modulesCompleted);
}
