import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/auth_service.dart';
import 'sync_engine.dart';

/// Decides WHEN to sync: right after sign-in, when the app returns to the
/// foreground, when a network comes back, and every 5 minutes while open.
/// The engine itself guards against overlap and applies retry backoff, so
/// firing too often is harmless.
class SyncLifecycle extends ConsumerStatefulWidget {
  final Widget child;
  const SyncLifecycle({super.key, required this.child});

  @override
  ConsumerState<SyncLifecycle> createState() => _SyncLifecycleState();
}

class _SyncLifecycleState extends ConsumerState<SyncLifecycle> with WidgetsBindingObserver {
  Timer? _timer;
  StreamSubscription<List<ConnectivityResult>>? _connectivity;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _timer = Timer.periodic(const Duration(minutes: 5), (_) => _kick());
    try {
      _connectivity = Connectivity().onConnectivityChanged.listen(
        (results) {
          if (results.any((r) => r != ConnectivityResult.none)) _kick(manual: true);
        },
        onError: (_) {}, // no plugin (tests) or platform error: timer + resume hooks still work
      );
    } catch (_) {
      // No connectivity plugin (e.g. in tests): the timer and resume hooks still work.
    }
  }

  void _kick({bool manual = false}) {
    if (!mounted) return;
    ref.read(syncEngineProvider.notifier).syncNow(manual: manual);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _kick();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    _connectivity?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AuthState>(authProvider, (prev, next) {
      if (prev?.user == null && next.user != null) _kick(manual: true);
    });
    return widget.child;
  }
}
