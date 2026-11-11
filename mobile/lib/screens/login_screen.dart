import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/partner_logo_row.dart';

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
      setState(() => _error = e.response?.data?['detail']?.toString() ?? 'Login failed. Check your connection.');
    } catch (_) {
      setState(() => _error = 'Something went wrong. Please try again.');
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
                // The SARMAAN-II logo replaces the old "S" mark. Shown unmodified on white, and
                // never larger than the supplied file's own pixels (it is only 118 x 50 px).
                const Align(alignment: Alignment.centerLeft, child: SarmaanLogoMark()),
                const SizedBox(height: 16),
                Text('SARMAAN e-Playbook', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 4),
                Text(
                  'ADMIN & CDD SIGN IN',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(color: AppColors.textMuted),
                ),
                const SizedBox(height: 28),
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
                  decoration: const InputDecoration(labelText: 'Username'),
                  validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    suffixIcon: IconButton(
                      icon: Icon(_showPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                      tooltip: _showPassword ? 'Hide password' : 'Show password',
                      onPressed: () => setState(() => _showPassword = !_showPassword),
                    ),
                  ),
                  obscureText: !_showPassword,
                  enableSuggestions: false,
                  autocorrect: false,
                  validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
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
                      : const Text('Sign in'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
