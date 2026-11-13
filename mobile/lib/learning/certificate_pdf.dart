import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/services.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../theme/brand_identity.g.dart';
import '../l10n/l10n.dart';
import '../theme/app_theme.dart';
import 'certificate.dart';

/// The certificate as an A4 landscape PDF, made on the phone (no network).
/// Text is in the learner's language where translated (cert.* strings), set in
/// Arimo so names with ɓ ɗ ƙ ƴ print correctly. The partner logos come from
/// assets/brand/logos.json in the configured order, unmodified and never larger
/// than their own pixels.
Future<Uint8List> buildCertificatePdf(CertificateData data, {AssetBundle? bundle}) async {
  final assets = bundle ?? rootBundle;
  final regular = pw.Font.ttf(await assets.load('assets/fonts/Arimo-Regular.ttf'));
  final bold = pw.Font.ttf(await assets.load('assets/fonts/Arimo-Bold.ttf'));
  final logos = await _logos(assets);

  final forest = PdfColor.fromInt(AppColors.primary.toARGB32());
  final muted = PdfColor.fromInt(AppColors.textMuted.toARGB32());
  final date = '${data.completedAt.toLocal().day.toString().padLeft(2, '0')}/'
      '${data.completedAt.toLocal().month.toString().padLeft(2, '0')}/${data.completedAt.toLocal().year}';

  final doc = pw.Document(title: L10n.t('cert.title'), author: BrandIdentity.title);
  doc.addPage(pw.Page(
    pageFormat: PdfPageFormat.a4.landscape,
    margin: const pw.EdgeInsets.all(28),
    theme: pw.ThemeData.withFont(base: regular, bold: bold),
    build: (context) => pw.Container(
      decoration: pw.BoxDecoration(border: pw.Border.all(color: forest, width: 3)),
      padding: const pw.EdgeInsets.fromLTRB(40, 24, 40, 24),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.center,
        children: [
          // Logos on white with the IHS clear space between them.
          pw.Wrap(
            alignment: pw.WrapAlignment.center,
            crossAxisAlignment: pw.WrapCrossAlignment.center,
            spacing: 18,
            runSpacing: 10,
            children: [for (final l in logos) pw.Image(l.image, width: l.width, height: l.height)],
          ),
          pw.Spacer(),
          pw.Text(L10n.t('cert.title').toUpperCase(),
              style: pw.TextStyle(font: bold, fontSize: 30, color: forest, letterSpacing: 1.5), textAlign: pw.TextAlign.center),
          pw.SizedBox(height: 18),
          pw.Text(L10n.t('cert.certifies'), style: pw.TextStyle(fontSize: 14, color: muted), textAlign: pw.TextAlign.center),
          pw.SizedBox(height: 10),
          pw.Text(data.name, style: pw.TextStyle(font: bold, fontSize: 28), textAlign: pw.TextAlign.center),
          pw.Container(width: 320, height: 1, color: forest, margin: const pw.EdgeInsets.only(top: 6, bottom: 12)),
          pw.Text(L10n.t('cert.completed'), style: const pw.TextStyle(fontSize: 14), textAlign: pw.TextAlign.center),
          pw.SizedBox(height: 4),
          pw.Text(L10n.t('cert.trainingName'), style: pw.TextStyle(font: bold, fontSize: 18, color: forest), textAlign: pw.TextAlign.center),
          pw.Spacer(),
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            crossAxisAlignment: pw.CrossAxisAlignment.end,
            children: [
              _labelled(L10n.t('cert.dateLabel'), date, bold, muted),
              _labelled(L10n.t('cert.numberLabel'), data.number, bold, muted, end: true),
            ],
          ),
        ],
      ),
    ),
  ));
  return doc.save();
}

pw.Widget _labelled(String label, String value, pw.Font bold, PdfColor muted, {bool end = false}) => pw.Column(
      crossAxisAlignment: end ? pw.CrossAxisAlignment.end : pw.CrossAxisAlignment.start,
      children: [
        pw.Text(label, style: pw.TextStyle(fontSize: 10, color: muted)),
        pw.SizedBox(height: 2),
        pw.Text(value, style: pw.TextStyle(font: bold, fontSize: 13)),
      ],
    );

class _Logo {
  final pw.MemoryImage image;
  final double width;
  final double height;
  const _Logo(this.image, this.width, this.height);
}

/// The configured logos at a 54 pt row height (IHS 95 pt wide), each capped at its
/// own pixel size so a small file is never enlarged.
Future<List<_Logo>> _logos(AssetBundle assets) async {
  final config = jsonDecode(await assets.loadString('assets/brand/logos.json')) as Map<String, dynamic>;
  final logos = (config['logos'] as Map).cast<String, dynamic>();
  final out = <_Logo>[];
  for (final key in (config['order'] as List).cast<String>()) {
    final logo = (logos[key] as Map?)?.cast<String, dynamic>();
    if (logo == null) continue;
    final wPx = (logo['widthPx'] as num).toDouble();
    final hPx = (logo['heightPx'] as num).toDouble();
    final h = math.min(54.0, hPx);
    final bytes = (await assets.load('assets/brand/${logo['file']}')).buffer.asUint8List();
    out.add(_Logo(pw.MemoryImage(bytes), h * wPx / hPx, h));
  }
  return out;
}
