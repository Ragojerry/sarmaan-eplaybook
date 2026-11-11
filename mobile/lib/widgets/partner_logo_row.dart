import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/app_theme.dart';

/// The partner logos for one placement (splash, login, about), as set in
/// assets/brand/logos.json (copied from brand/logos.json by scripts/brand_sync.py).
/// Order, row height and the partnership line all come from that file.
///
/// Logo rules (brand/logos.json, docs/brand/brand_compliance.md):
/// - files are shown exactly as supplied: same aspect ratio, no recolouring or effects;
/// - never larger than the file's own pixels (a small file stays smaller than the row);
/// - the IHS logo never narrower than its minimum width (95 dp);
/// - clear space on every side = the width of the "I" in IHS at the row height;
/// - always on white, the only approved background for the supplied full-colour files.
class PartnerLogoRow extends StatelessWidget {
  const PartnerLogoRow({super.key, required this.placement});

  final String placement;

  static Future<Map<String, dynamic>>? _config;
  static Future<Map<String, dynamic>> _load() => _config ??= rootBundle
      .loadString('assets/brand/logos.json')
      .then((s) => jsonDecode(s) as Map<String, dynamic>);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _load(),
      builder: (context, snap) {
        final config = snap.data;
        if (config == null) return const SizedBox.shrink();
        return _LogoRow(config: config, placement: placement);
      },
    );
  }
}

class _LogoRow extends StatelessWidget {
  const _LogoRow({required this.config, required this.placement});

  final Map<String, dynamic> config;
  final String placement;

  @override
  Widget build(BuildContext context) {
    final logos = (config['logos'] as Map).cast<String, dynamic>();
    final place = ((config['placements'] as Map)[placement] as Map?)
        ?.cast<String, dynamic>();
    if (place == null) return const SizedBox.shrink();
    final keys = place['logos'] == 'order'
        ? (config['order'] as List).cast<String>()
        : (place['logos'] as List).cast<String>();
    final rowHeight = (place['rowHeightDp'] as num).toDouble();
    final dpr = MediaQuery.devicePixelRatioOf(context);

    // Clear space: the IHS rule (width of its "I") at the row height, used for every logo.
    final ihs = (logos['ihs'] as Map?)?.cast<String, dynamic>();
    final clear = ihs == null
        ? rowHeight * 0.3
        : (ihs['clearSpaceRatio'] as num) *
            rowHeight *
            (ihs['widthPx'] as num) /
            (ihs['heightPx'] as num);

    final images = <Widget>[];
    for (final key in keys) {
      final logo = (logos[key] as Map?)?.cast<String, dynamic>();
      if (logo == null) continue;
      final wPx = (logo['widthPx'] as num).toDouble();
      final hPx = (logo['heightPx'] as num).toDouble();
      final maxH = hPx / dpr; // never upscale the file
      var h = math.min(rowHeight, maxH);
      final minW = (logo['minWidthDp'] as num?)?.toDouble();
      if (minW != null) h = math.min(math.max(h, minW * hPx / wPx), maxH);
      images.add(Image.asset(
        'assets/brand/${logo['file']}',
        width: h * wPx / hPx,
        height: h,
        fit: BoxFit.contain,
        filterQuality: FilterQuality.medium,
        semanticLabel: logo['label'] as String?,
      ));
    }

    final line = (config['partnershipLine'] as Map?)?['text'] as String?;
    return Container(
      color: AppColors.white,
      padding: EdgeInsets.all(clear),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (place['showPartnershipLine'] == true && line != null) ...[
            Text(line,
                textAlign: TextAlign.center,
                style: const TextStyle(
                    fontSize: 11.5, color: AppColors.textMuted)),
            SizedBox(height: clear * 0.6),
          ],
          // One row where it fits; on a narrow screen a second line rather than a logo below its minimum.
          Wrap(
            alignment: WrapAlignment.center,
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: clear,
            runSpacing: clear,
            children: images,
          ),
        ],
      ),
    );
  }
}
