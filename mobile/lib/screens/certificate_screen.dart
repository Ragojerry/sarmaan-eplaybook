import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../l10n/l10n.dart';
import '../learning/certificate.dart';
import '../learning/certificate_pdf.dart';
import '../learning/learning_service.dart';
import '../services/auth_service.dart';
import '../services/file_saver.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';

/// Congratulations after passing the General post-test (90% or more), with the
/// training completion certificate as a PDF the learner saves on the phone.
/// Everything works offline; the certificate number can be checked in the admin
/// portal once the phone has synced.
class CertificateScreen extends ConsumerStatefulWidget {
  const CertificateScreen({super.key});

  @override
  ConsumerState<CertificateScreen> createState() => _CertificateScreenState();
}

class _CertificateScreenState extends ConsumerState<CertificateScreen> {
  bool _saving = false;

  Future<void> _download(CertificateData data) async {
    setState(() => _saving = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final bytes = await buildCertificatePdf(data);
      final uri = await FileSaver.save('SARMAAN-II-certificate-${data.number}.pdf', bytes);
      if (uri == null) return; // cancelled
      messenger.showSnackBar(SnackBar(
        content: Text(L10n.t('cert.saved')),
        duration: const Duration(seconds: 8),
        action: SnackBarAction(
          label: L10n.t('cert.open'),
          onPressed: () async {
            if (!await FileSaver.open(uri)) messenger.showSnackBar(SnackBar(content: Text(L10n.t('cert.noViewer'))));
          },
        ),
      ));
    } on PlatformException catch (_) {
      messenger.showSnackBar(SnackBar(content: Text(L10n.t('cert.saveFailed'))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;
    final learning = ref.watch(learningProvider).valueOrNull;
    final data = (learning == null || user == null)
        ? null
        : CertificateData.of(learning.general, userId: user.id, name: '${user.firstName} ${user.lastName}'.trim());

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(context.t('cert.screenTitle')),
        leading: BackButton(onPressed: () => context.go('/modules')),
      ),
      body: learning == null
          ? const Center(child: CircularProgressIndicator())
          : data == null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(context.t('cert.notEarned'), textAlign: TextAlign.center),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.fromLTRB(22, 28, 22, 28),
                  children: [
                    const Icon(Icons.emoji_events_outlined, size: 64, color: AppColors.primary),
                    const SizedBox(height: 14),
                    Text(
                      context.t('cert.congratulations', {'name': data.name}),
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppColors.primary),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      context.t('cert.passedBody', {'correct': data.correct, 'total': data.total, 'percent': data.percent}),
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 14, height: 1.5, color: AppColors.textStrong),
                    ),
                    const SizedBox(height: 22),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.white,
                        borderRadius: BorderRadius.circular(AppRadius.standard),
                        border: Border.all(color: AppColors.primary, width: 1.5),
                      ),
                      child: Column(
                        children: [
                          const PartnerLogoRow(placement: 'tabHeader'),
                          Text(context.t('cert.title'),
                              textAlign: TextAlign.center,
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.primary)),
                          const SizedBox(height: 8),
                          Text(data.name,
                              textAlign: TextAlign.center,
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textStrong)),
                          const SizedBox(height: 4),
                          Text(context.t('cert.trainingName'), textAlign: TextAlign.center, style: const TextStyle(fontSize: 12.5)),
                          const SizedBox(height: 10),
                          Text(context.t('cert.numberShort', {'number': data.number}),
                              textAlign: TextAlign.center, style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    FilledButton.icon(
                      onPressed: _saving ? null : () => _download(data),
                      icon: _saving
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(AppColors.onPrimary)))
                          : const Icon(Icons.download_rounded),
                      label: Text(context.t('cert.download')),
                    ),
                    const SizedBox(height: 10),
                    Text(context.t('cert.downloadHint'),
                        textAlign: TextAlign.center, style: const TextStyle(fontSize: 11.5, color: AppColors.textMuted)),
                  ],
                ),
    );
  }
}
