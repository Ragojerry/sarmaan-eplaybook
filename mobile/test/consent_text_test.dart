import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sarmaan_eplaybook/db/local_database.dart';
import 'package:sarmaan_eplaybook/models/consent_text.dart';
import 'package:sarmaan_eplaybook/services/settings_service.dart';

ConsentText _t(String language, String title, int version) => ConsentText(
      language: language,
      title: title,
      body: 'Body in $language',
      usageLabel: 'Usage',
      buttonLabel: 'OK',
      version: version,
    );

void main() {
  test('shows the chosen language, else English, else the built-in copy', () {
    final texts = [_t('en', 'Before you start', 2), _t('ha', 'Kafin ka fara', 1)];
    expect(pickConsent(texts, 'ha').title, 'Kafin ka fara');
    expect(pickConsent(texts, 'ff').title, 'Before you start', reason: 'no Fulfulde translation yet');
    expect(pickConsent(texts, null).language, 'en');
    expect(pickConsent(null, 'ha'), same(kBundledConsent), reason: 'never online');
    expect(pickConsent([_t('ha', 'Kafin ka fara', 1)], 'kr'), same(kBundledConsent), reason: 'no English row cached');
  });

  test('cached texts and the accepted version survive storage', () async {
    final db = LocalDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final settings = SettingsService(db);
    expect(await settings.getCachedConsent(), isNull);

    await settings.setCachedConsent([_t('en', 'Before you start', 2), _t('ha', 'Kafin ka fara', 1)]);
    final cached = await settings.getCachedConsent();
    expect(cached!.map((t) => t.language), ['en', 'ha']);
    expect(cached.last.body, 'Body in ha');

    await settings.recordAcceptedConsent(pickConsent(cached, 'ha'));
    expect(await settings.getAcceptedConsent(), 'ha:1');
  });
}
