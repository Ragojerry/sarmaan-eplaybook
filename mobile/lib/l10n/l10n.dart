import 'package:flutter/widgets.dart';

import 'app_strings_en.g.dart';

/// The app's interface text (buttons, labels, messages) in the learner's language.
///
/// English is compiled into the app (app_strings_en.g.dart, generated from
/// mobile/l10n/app_strings.json by scripts/l10n_sync.py), so a fresh install works
/// fully offline. Published translations for the chosen language come from the
/// admin portal (GET /sync/app-strings), are cached in the local database, and
/// replace English string by string. Anything missing, empty or unsafe falls back
/// to the English text, so the screen never shows a key or a blank.
///
/// Plural strings are stored as two entries: `key` (the "other" form) and
/// `key#one`. Placeholders are written `{name}` and filled from the arguments.
class L10n extends ChangeNotifier {
  L10n._();

  static final L10n instance = L10n._();

  String _code = 'en';
  Map<String, String> _strings = const {};

  /// The language the interface is shown in (the same setting as content).
  String get code => _code;

  /// Shows [strings] (published translations for [code]) from now on.
  void apply(String code, Map<String, String> strings) {
    _code = code;
    _strings = code == 'en' ? const {} : Map.unmodifiable(strings);
    notifyListeners();
  }

  /// [key] in the current language, with `{placeholders}` filled from [args].
  static String t(String key, [Map<String, Object?> args = const {}]) => instance._lookup(key, args);

  /// The plural form of [key] for [count]; `{count}` is filled in too.
  static String n(String key, int count, [Map<String, Object?> args = const {}]) {
    final all = {...args, 'count': count};
    final one = pluralFormOf(instance._code, count) == 'one';
    if (one && kEnglishStrings.containsKey('$key#one')) return instance._lookup('$key#one', all);
    return instance._lookup(key, all);
  }

  /// CLDR cardinal rules for the app's languages, reduced to one/other. Fulfulde
  /// (ff) treats 0 and 1 as singular; English, Hausa and Kanuri only 1 (Kanuri
  /// confirmed by a Kanuri speaker, 2026-11-12).
  static String pluralFormOf(String code, int count) {
    if (code == 'ff') return (count == 0 || count == 1) ? 'one' : 'other';
    return count == 1 ? 'one' : 'other';
  }

  static final _placeholder = RegExp(r'\{(\w+)\}');

  static Set<String> placeholdersOf(String text) => {for (final m in _placeholder.allMatches(text)) m.group(1)!};

  String _lookup(String key, Map<String, Object?> args) {
    final english = kEnglishStrings[key];
    final translated = _strings[key];
    // A translation is used only if it is non-empty and every placeholder in it is
    // one the English text also has (a renamed or mistyped {name} would otherwise
    // show on screen as literal braces).
    final usable = translated != null &&
        translated.trim().isNotEmpty &&
        (english == null || placeholdersOf(english).containsAll(placeholdersOf(translated)));
    final text = usable ? translated : english;
    // scripts/l10n_sync.py --check guarantees every key the code uses exists in
    // English, so this last resort is unreachable in a checked build.
    if (text == null) {
      assert(false, 'Missing English text for "$key" (run scripts/l10n_sync.py)');
      return '';
    }
    return _format(text, args);
  }

  static String _format(String text, Map<String, Object?> args) {
    if (args.isEmpty) return text;
    return text.replaceAllMapped(_placeholder, (m) {
      final name = m.group(1)!;
      return args.containsKey(name) ? '${args[name] ?? ''}' : m.group(0)!;
    });
  }
}

/// Rebuilds every widget that reads text through [BuildContext.t] when the
/// language or its downloaded strings change. Sits above the app's screens.
class L10nScope extends InheritedNotifier<L10n> {
  L10nScope({super.key, required super.child}) : super(notifier: L10n.instance);
}

extension L10nContext on BuildContext {
  /// [key] in the learner's language; rebuilds this widget when the language changes.
  String t(String key, [Map<String, Object?> args = const {}]) {
    dependOnInheritedWidgetOfExactType<L10nScope>();
    return L10n.t(key, args);
  }

  /// The plural form of [key] for [count] ({count} is filled in).
  String tn(String key, int count, [Map<String, Object?> args = const {}]) {
    dependOnInheritedWidgetOfExactType<L10nScope>();
    return L10n.n(key, count, args);
  }
}
