import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Completed: a white tick on a Forest Green disc.
class DoneMark extends StatelessWidget {
  final double size;
  const DoneMark({super.key, this.size = 18});

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: const BoxDecoration(color: AppColors.forest, shape: BoxShape.circle),
        child: Icon(Icons.check, size: size * 0.66, color: AppColors.onPrimary),
      );
}

/// A dashed rounded outline, painted over a locked module.
class DashedOutline extends CustomPainter {
  final Color color;
  final double radius;
  const DashedOutline({required this.color, required this.radius});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    final outline = Path()..addRRect(RRect.fromRectAndRadius(Offset.zero & size, Radius.circular(radius)).deflate(0.75));
    for (final metric in outline.computeMetrics()) {
      for (var d = 0.0; d < metric.length; d += 9) {
        canvas.drawPath(metric.extractPath(d, d + 5 < metric.length ? d + 5 : metric.length), paint);
      }
    }
  }

  @override
  bool shouldRepaint(DashedOutline old) => old.color != color || old.radius != radius;
}
