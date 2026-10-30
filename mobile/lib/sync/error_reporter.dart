import 'dart:ui' show PlatformDispatcher;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../offline/content_sync_service.dart' show localDatabaseProvider;
import 'analytics_recorder.dart';

/// Turns uncaught app errors into APPLICATION_ERROR events (only if the person
/// opted in). Records the error TYPE only — never the message or stack, which
/// can contain personal data or file paths — and at most one event per type
/// per 10 minutes so a crash loop cannot flood the queue.
class ErrorReporter {
  static final Map<String, DateTime> _lastByType = {};
  static bool _reporting = false;

  static void install(ProviderContainer container) {
    final previousFlutter = FlutterError.onError;
    FlutterError.onError = (details) {
      previousFlutter?.call(details);
      _report(container, details.exception);
    };
    final previousPlatform = PlatformDispatcher.instance.onError;
    PlatformDispatcher.instance.onError = (error, stack) {
      _report(container, error);
      return previousPlatform?.call(error, stack) ?? false;
    };
  }

  static Future<void> _report(ProviderContainer container, Object error) async {
    if (_reporting) return; // never recurse if recording itself fails
    final type = error.runtimeType.toString();
    final last = _lastByType[type];
    final now = DateTime.now();
    if (last != null && now.difference(last) < const Duration(minutes: 10)) {
      return;
    }
    _lastByType[type] = now;
    _reporting = true;
    try {
      await recordAnalyticsEvent(container.read(localDatabaseProvider), 'APPLICATION_ERROR', payload: {'type': type});
    } catch (_) {
    } finally {
      _reporting = false;
    }
  }
}
