import 'package:flutter/services.dart';

/// Saves a file the learner keeps through Android's "Save as" screen (opens in
/// Downloads; MainActivity.kt), and opens a saved file in the phone's viewer.
class FileSaver {
  static const _channel = MethodChannel('org.malariaconsortium.sarmaan/files');

  /// The saved file's address, or null when the learner cancelled.
  /// Throws a [PlatformException] when the file could not be written.
  static Future<String?> save(String name, Uint8List bytes, {String mime = 'application/pdf'}) =>
      _channel.invokeMethod<String>('save', {'name': name, 'mime': mime, 'bytes': bytes});

  /// False when no app on the phone can open this type of file.
  static Future<bool> open(String uri, {String mime = 'application/pdf'}) async =>
      await _channel.invokeMethod<bool>('open', {'uri': uri, 'mime': mime}) ?? false;
}
