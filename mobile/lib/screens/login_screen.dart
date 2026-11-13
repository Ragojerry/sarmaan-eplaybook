import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/api_client.dart';
import '../widgets/brand_mark.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';
import '../l10n/l10n.dart';

/// New in Phase 7 — the prototype had no login at all (docs/prototype-analysis.md
/// §1), so there's no prototype CSS to match here. Styled to sit consistently
/// alongside the other screens: brand colours and font from the global theme
/// (theme/app_theme.dart), and the partner logos at the bottom (logos.json).
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  String? _error;
  bool _submitting = false;
  bool _showPassword = false;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _error = null;
      _submitting = true;
    });
    try {
      await ref.read(authProvider.notifier).login(_usernameController.text.trim(), _passwordController.text);
      if (mounted) context.go('/home');
    } on DioException catch (e) {
      setState(() => _error = ApiClient.isDeactivated(e.response)
          ? L10n.t('auth.deactivated')
          : e.response?.data?['detail']?.toString() ?? L10n.t('login.failed'));
    } catch (_) {
      setState(() => _error = L10n.t('common.somethingWrong'));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // The logos sit on white at the bottom, full width so the row fits on one line.
      bottomNavigationBar: const SafeArea(top: false, child: PartnerLogoRow(placement: 'login')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // The app logo and title (brand/brand.json); the title wraps on small phones.
                const Align(alignment: Alignment.centerLeft, child: BrandLogo()),
                const SizedBox(height: 16),
                const BrandTitle(),
                const SizedBox(height: 4),
                Text(
                  context.t('login.eyebrow'),
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(color: AppColors.textMuted),
                ),
                const SizedBox(height: 28),
                if (_error == null && ref.watch(authProvider.select((a) => a.deactivated))) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.warningSurface,
                      borderRadius: BorderRadius.circular(AppRadius.small),
                      border: const Border(left: BorderSide(color: AppColors.warning, width: 3)),
                    ),
                    child: Semantics(
                      liveRegion: true,
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.info_outline_rounded, size: 18, color: AppColors.warningText),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(context.t('auth.deactivated'), style: const TextStyle(color: AppColors.warningText, fontSize: 13, height: 1.4)),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                if (_error != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.errorSurface,
                      borderRadius: BorderRadius.circular(AppRadius.small),
                      border: const Border(left: BorderSide(color: AppColors.error, width: 3)),
                    ),
                    child: Text(_error!, style: const TextStyle(color: AppColors.errorText, fontSize: 12)),
                  ),
                  const SizedBox(height: 16),
                ],
                TextFormField(
                  controller: _usernameController,
                  decoration: InputDecoration(labelText: context.t('login.username')),
                  validator: (v) => (v == null || v.isEmpty) ? context.t('common.required') : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    labelText: context.t('login.password'),
                    suffixIcon: IconButton(
                      icon: Icon(_showPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                      tooltip: _showPassword ? context.t('login.hidePassword') : context.t('login.showPassword'),
                      onPressed: () => setState(() => _showPassword = !_showPassword),
                    ),
                  ),
                  obscureText: !_showPassword,
                  enableSuggestions: false,
                  autocorrect: false,
                  validator: (v) => (v == null || v.isEmpty) ? context.t('common.required') : null,
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, valueColor: AlwaysStoppedAnimation(AppColors.onPrimary)),
                        )
                      : Text(context.t('login.signIn')),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
