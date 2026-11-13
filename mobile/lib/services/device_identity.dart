import 'dart:io';
import 'dart:math';

import 'package:flutter/services.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../db/local_database.dart';

/// app_settings key of this install's random id.
const kDeviceIdKey = 'device_id';

const _deviceChannel = MethodChannel('org.malariaconsortium.sarmaan/device');

/// Random id generated once per install and kept in the local database. Not derived
/// from hardware identifiers, so it says nothing about the person or the phone.
Future<String> installId(LocalDatabase db) async {
  var id = await db.getSetting(kDeviceIdKey);
  if (id == null || id.length < 16) {
    final r = Random.secure();
    id = List.generate(16, (_) => r.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
    await db.setSetting(kDeviceIdKey, id);
  }
  return id;
}

/// What the device registry receives at login and on every sync (POST /sync/device):
/// the random install id, the OS and its version, and the app version. No phone
/// model, IMEI, advertising id or phone number (decision 2026-11-13).
Future<Map<String, dynamic>> deviceInfoPayload(LocalDatabase db) async {
  String? osVersion;
  try {
    osVersion = await _deviceChannel.invokeMethod<String>('osVersion');
  } catch (_) {
    osVersion = null; // not Android, or a test: the OS name is still sent
  }
  String? appVersion;
  try {
    appVersion = (await PackageInfo.fromPlatform()).version;
  } catch (_) {}
  return {
    'install_id': await installId(db),
    'os': Platform.operatingSystem,
    if (osVersion != null) 'os_version': osVersion,
    if (appVersion != null) 'app_version': appVersion,
  };
}
