/// Mirrors backend/app/schemas/* exactly — kept in lockstep manually since
/// there's no shared-schema codegen between FastAPI and Flutter in this
/// project. If a backend field changes, this file needs the matching edit.
library api_models;

class UserProfile {
  final String id;
  final String username;
  final String email;
  final String firstName;
  final String lastName;
  final String role;
  final String status;

  UserProfile({
    required this.id,
    required this.username,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.role,
    required this.status,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        id: json['id'] as String,
        username: json['username'] as String,
        email: json['email'] as String,
        firstName: json['first_name'] as String,
        lastName: json['last_name'] as String,
        role: json['role'] as String,
        status: json['status'] as String,
      );
}

class AppLanguage {
  final String id;
  final String code;
  final String name;
  final String nativeName;
  final String status;
  final bool isDefault;

  const AppLanguage({
    required this.id,
    required this.code,
    required this.name,
    required this.nativeName,
    required this.status,
    required this.isDefault,
  });

  factory AppLanguage.fromJson(Map<String, dynamic> json) => AppLanguage(
        id: json['id'] as String,
        code: json['code'] as String,
        name: json['name'] as String,
        nativeName: json['native_name'] as String,
        status: json['status'] as String,
        isDefault: json['is_default'] as bool,
      );
}

class TrainingModule {
  final String id;
  final String moduleCode;
  final int moduleNumber;
  final String title;
  final String? description;
  final String status;
  final int sortOrder;

  TrainingModule({
    required this.id,
    required this.moduleCode,
    required this.moduleNumber,
    required this.title,
    required this.description,
    required this.status,
    required this.sortOrder,
  });

  factory TrainingModule.fromJson(Map<String, dynamic> json) => TrainingModule(
        id: json['id'] as String,
        moduleCode: json['module_code'] as String,
        moduleNumber: json['module_number'] as int,
        title: json['title'] as String,
        description: json['description'] as String?,
        status: json['status'] as String,
        sortOrder: json['sort_order'] as int,
      );
}

class ModuleTranslation {
  final String id;
  final String moduleId;
  final String languageId;
  final String title;
  final String? description;
  final String? body;
  final String? audioText;
  final String status;

  ModuleTranslation({
    required this.id,
    required this.moduleId,
    required this.languageId,
    required this.title,
    required this.description,
    required this.body,
    required this.audioText,
    required this.status,
  });

  factory ModuleTranslation.fromJson(Map<String, dynamic> json) => ModuleTranslation(
        id: json['id'] as String,
        moduleId: json['module_id'] as String,
        languageId: json['language_id'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        body: json['body'] as String?,
        audioText: json['audio_text'] as String?,
        status: json['status'] as String,
      );
}

class ContentSection {
  final String id;
  final String moduleId;
  final int sectionNumber;
  final String? title;
  final String contentType;
  final Map<String, dynamic> content;
  final int sortOrder;

  ContentSection({
    required this.id,
    required this.moduleId,
    required this.sectionNumber,
    required this.title,
    required this.contentType,
    required this.content,
    required this.sortOrder,
  });

  factory ContentSection.fromJson(Map<String, dynamic> json) => ContentSection(
        id: json['id'] as String,
        moduleId: json['module_id'] as String,
        sectionNumber: json['section_number'] as int,
        title: json['title'] as String?,
        contentType: json['content_type'] as String,
        content: Map<String, dynamic>.from(json['content'] as Map),
        sortOrder: json['sort_order'] as int,
      );
}

class TrainingVideo {
  final String id;
  final String title;
  final String? description;
  final String? moduleId;
  final int? durationSeconds;
  final String language;
  final bool offlineAvailable;
  final bool requiredOffline;
  final String status;
  final bool hasFile;
  final int? fileSize;
  final String? checksum;

  TrainingVideo({
    required this.id,
    required this.title,
    required this.description,
    required this.moduleId,
    required this.durationSeconds,
    required this.language,
    required this.offlineAvailable,
    required this.requiredOffline,
    required this.status,
    required this.hasFile,
    required this.fileSize,
    required this.checksum,
  });

  factory TrainingVideo.fromJson(Map<String, dynamic> json) => TrainingVideo(
        id: json['id'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        moduleId: json['module_id'] as String?,
        durationSeconds: json['duration_seconds'] as int?,
        language: json['language'] as String,
        offlineAvailable: json['offline_available'] as bool,
        requiredOffline: json['required_offline'] as bool? ?? false,
        status: json['status'] as String,
        hasFile: json['has_file'] as bool,
        fileSize: json['file_size'] as int?,
        checksum: json['checksum'] as String?,
      );
}
