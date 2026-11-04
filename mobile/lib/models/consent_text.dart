/// The first-launch consent screen's text in one language, edited and
/// translated in the admin portal (GET /consent, public). The phone caches
/// every language and shows the chosen one, else English, else
/// [kBundledConsent] (a fresh install that has never been online).
class ConsentText {
  final String language;
  final String title;
  final String body;
  final String usageLabel;
  final String buttonLabel;

  /// 0 for the copy built into the app; the server's version otherwise.
  final int version;

  const ConsentText({
    required this.language,
    required this.title,
    required this.body,
    required this.usageLabel,
    required this.buttonLabel,
    required this.version,
  });

  factory ConsentText.fromJson(Map<String, dynamic> j) => ConsentText(
        language: j['language'] as String,
        title: j['title'] as String,
        body: j['body'] as String,
        usageLabel: j['usage_label'] as String,
        buttonLabel: j['button_label'] as String,
        version: j['version'] as int,
      );

  Map<String, dynamic> toJson() => {
        'language': language,
        'title': title,
        'body': body,
        'usage_label': usageLabel,
        'button_label': buttonLabel,
        'version': version,
      };
}

const kBundledConsent = ConsentText(
  language: 'en',
  title: 'Before you start',
  body: 'This app is used to deliver AZM training content to Community Drug Distributors. '
      'Your training progress and the questions you ask in the app are linked to your account and '
      'uploaded when you are online, so your supervisor and the programme team can support you. '
      'Module content is downloaded to this device so you can keep working without an internet connection.',
  usageLabel: 'Also share anonymous usage statistics (optional)',
  buttonLabel: 'Agree and continue',
  version: 0,
);

/// The text to show for [language]: its translation, else English, else the
/// built-in copy.
ConsentText pickConsent(List<ConsentText>? texts, String? language) {
  final all = texts ?? const <ConsentText>[];
  for (final code in [language, 'en']) {
    for (final t in all) {
      if (t.language == code) return t;
    }
  }
  return kBundledConsent;
}
