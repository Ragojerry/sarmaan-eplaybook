// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'local_database.dart';

// ignore_for_file: type=lint
class $CachedModulesTable extends CachedModules
    with TableInfo<$CachedModulesTable, CachedModuleRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedModulesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleCodeMeta =
      const VerificationMeta('moduleCode');
  @override
  late final GeneratedColumn<String> moduleCode = GeneratedColumn<String>(
      'module_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleNumberMeta =
      const VerificationMeta('moduleNumber');
  @override
  late final GeneratedColumn<int> moduleNumber = GeneratedColumn<int>(
      'module_number', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sortOrderMeta =
      const VerificationMeta('sortOrder');
  @override
  late final GeneratedColumn<int> sortOrder = GeneratedColumn<int>(
      'sort_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _cachedAtMeta =
      const VerificationMeta('cachedAt');
  @override
  late final GeneratedColumn<DateTime> cachedAt = GeneratedColumn<DateTime>(
      'cached_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _audienceMeta =
      const VerificationMeta('audience');
  @override
  late final GeneratedColumn<String> audience = GeneratedColumn<String>(
      'audience', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('GENERAL'));
  static const VerificationMeta _learnerRolesJsonMeta =
      const VerificationMeta('learnerRolesJson');
  @override
  late final GeneratedColumn<String> learnerRolesJson = GeneratedColumn<String>(
      'learner_roles_json', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('[]'));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        moduleCode,
        moduleNumber,
        title,
        description,
        status,
        sortOrder,
        cachedAt,
        audience,
        learnerRolesJson
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_modules';
  @override
  VerificationContext validateIntegrity(Insertable<CachedModuleRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('module_code')) {
      context.handle(
          _moduleCodeMeta,
          moduleCode.isAcceptableOrUnknown(
              data['module_code']!, _moduleCodeMeta));
    } else if (isInserting) {
      context.missing(_moduleCodeMeta);
    }
    if (data.containsKey('module_number')) {
      context.handle(
          _moduleNumberMeta,
          moduleNumber.isAcceptableOrUnknown(
              data['module_number']!, _moduleNumberMeta));
    } else if (isInserting) {
      context.missing(_moduleNumberMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('sort_order')) {
      context.handle(_sortOrderMeta,
          sortOrder.isAcceptableOrUnknown(data['sort_order']!, _sortOrderMeta));
    } else if (isInserting) {
      context.missing(_sortOrderMeta);
    }
    if (data.containsKey('cached_at')) {
      context.handle(_cachedAtMeta,
          cachedAt.isAcceptableOrUnknown(data['cached_at']!, _cachedAtMeta));
    } else if (isInserting) {
      context.missing(_cachedAtMeta);
    }
    if (data.containsKey('audience')) {
      context.handle(_audienceMeta,
          audience.isAcceptableOrUnknown(data['audience']!, _audienceMeta));
    }
    if (data.containsKey('learner_roles_json')) {
      context.handle(
          _learnerRolesJsonMeta,
          learnerRolesJson.isAcceptableOrUnknown(
              data['learner_roles_json']!, _learnerRolesJsonMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedModuleRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedModuleRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      moduleCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_code'])!,
      moduleNumber: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}module_number'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description']),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      sortOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}sort_order'])!,
      cachedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}cached_at'])!,
      audience: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}audience'])!,
      learnerRolesJson: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}learner_roles_json'])!,
    );
  }

  @override
  $CachedModulesTable createAlias(String alias) {
    return $CachedModulesTable(attachedDatabase, alias);
  }
}

class CachedModuleRow extends DataClass implements Insertable<CachedModuleRow> {
  final String id;
  final String moduleCode;
  final int moduleNumber;
  final String title;
  final String? description;
  final String status;
  final int sortOrder;
  final DateTime cachedAt;
  final String audience;
  final String learnerRolesJson;
  const CachedModuleRow(
      {required this.id,
      required this.moduleCode,
      required this.moduleNumber,
      required this.title,
      this.description,
      required this.status,
      required this.sortOrder,
      required this.cachedAt,
      required this.audience,
      required this.learnerRolesJson});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['module_code'] = Variable<String>(moduleCode);
    map['module_number'] = Variable<int>(moduleNumber);
    map['title'] = Variable<String>(title);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    map['status'] = Variable<String>(status);
    map['sort_order'] = Variable<int>(sortOrder);
    map['cached_at'] = Variable<DateTime>(cachedAt);
    map['audience'] = Variable<String>(audience);
    map['learner_roles_json'] = Variable<String>(learnerRolesJson);
    return map;
  }

  CachedModulesCompanion toCompanion(bool nullToAbsent) {
    return CachedModulesCompanion(
      id: Value(id),
      moduleCode: Value(moduleCode),
      moduleNumber: Value(moduleNumber),
      title: Value(title),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      status: Value(status),
      sortOrder: Value(sortOrder),
      cachedAt: Value(cachedAt),
      audience: Value(audience),
      learnerRolesJson: Value(learnerRolesJson),
    );
  }

  factory CachedModuleRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedModuleRow(
      id: serializer.fromJson<String>(json['id']),
      moduleCode: serializer.fromJson<String>(json['moduleCode']),
      moduleNumber: serializer.fromJson<int>(json['moduleNumber']),
      title: serializer.fromJson<String>(json['title']),
      description: serializer.fromJson<String?>(json['description']),
      status: serializer.fromJson<String>(json['status']),
      sortOrder: serializer.fromJson<int>(json['sortOrder']),
      cachedAt: serializer.fromJson<DateTime>(json['cachedAt']),
      audience: serializer.fromJson<String>(json['audience']),
      learnerRolesJson: serializer.fromJson<String>(json['learnerRolesJson']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'moduleCode': serializer.toJson<String>(moduleCode),
      'moduleNumber': serializer.toJson<int>(moduleNumber),
      'title': serializer.toJson<String>(title),
      'description': serializer.toJson<String?>(description),
      'status': serializer.toJson<String>(status),
      'sortOrder': serializer.toJson<int>(sortOrder),
      'cachedAt': serializer.toJson<DateTime>(cachedAt),
      'audience': serializer.toJson<String>(audience),
      'learnerRolesJson': serializer.toJson<String>(learnerRolesJson),
    };
  }

  CachedModuleRow copyWith(
          {String? id,
          String? moduleCode,
          int? moduleNumber,
          String? title,
          Value<String?> description = const Value.absent(),
          String? status,
          int? sortOrder,
          DateTime? cachedAt,
          String? audience,
          String? learnerRolesJson}) =>
      CachedModuleRow(
        id: id ?? this.id,
        moduleCode: moduleCode ?? this.moduleCode,
        moduleNumber: moduleNumber ?? this.moduleNumber,
        title: title ?? this.title,
        description: description.present ? description.value : this.description,
        status: status ?? this.status,
        sortOrder: sortOrder ?? this.sortOrder,
        cachedAt: cachedAt ?? this.cachedAt,
        audience: audience ?? this.audience,
        learnerRolesJson: learnerRolesJson ?? this.learnerRolesJson,
      );
  CachedModuleRow copyWithCompanion(CachedModulesCompanion data) {
    return CachedModuleRow(
      id: data.id.present ? data.id.value : this.id,
      moduleCode:
          data.moduleCode.present ? data.moduleCode.value : this.moduleCode,
      moduleNumber: data.moduleNumber.present
          ? data.moduleNumber.value
          : this.moduleNumber,
      title: data.title.present ? data.title.value : this.title,
      description:
          data.description.present ? data.description.value : this.description,
      status: data.status.present ? data.status.value : this.status,
      sortOrder: data.sortOrder.present ? data.sortOrder.value : this.sortOrder,
      cachedAt: data.cachedAt.present ? data.cachedAt.value : this.cachedAt,
      audience: data.audience.present ? data.audience.value : this.audience,
      learnerRolesJson: data.learnerRolesJson.present
          ? data.learnerRolesJson.value
          : this.learnerRolesJson,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedModuleRow(')
          ..write('id: $id, ')
          ..write('moduleCode: $moduleCode, ')
          ..write('moduleNumber: $moduleNumber, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('status: $status, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('audience: $audience, ')
          ..write('learnerRolesJson: $learnerRolesJson')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, moduleCode, moduleNumber, title,
      description, status, sortOrder, cachedAt, audience, learnerRolesJson);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedModuleRow &&
          other.id == this.id &&
          other.moduleCode == this.moduleCode &&
          other.moduleNumber == this.moduleNumber &&
          other.title == this.title &&
          other.description == this.description &&
          other.status == this.status &&
          other.sortOrder == this.sortOrder &&
          other.cachedAt == this.cachedAt &&
          other.audience == this.audience &&
          other.learnerRolesJson == this.learnerRolesJson);
}

class CachedModulesCompanion extends UpdateCompanion<CachedModuleRow> {
  final Value<String> id;
  final Value<String> moduleCode;
  final Value<int> moduleNumber;
  final Value<String> title;
  final Value<String?> description;
  final Value<String> status;
  final Value<int> sortOrder;
  final Value<DateTime> cachedAt;
  final Value<String> audience;
  final Value<String> learnerRolesJson;
  final Value<int> rowid;
  const CachedModulesCompanion({
    this.id = const Value.absent(),
    this.moduleCode = const Value.absent(),
    this.moduleNumber = const Value.absent(),
    this.title = const Value.absent(),
    this.description = const Value.absent(),
    this.status = const Value.absent(),
    this.sortOrder = const Value.absent(),
    this.cachedAt = const Value.absent(),
    this.audience = const Value.absent(),
    this.learnerRolesJson = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedModulesCompanion.insert({
    required String id,
    required String moduleCode,
    required int moduleNumber,
    required String title,
    this.description = const Value.absent(),
    required String status,
    required int sortOrder,
    required DateTime cachedAt,
    this.audience = const Value.absent(),
    this.learnerRolesJson = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        moduleCode = Value(moduleCode),
        moduleNumber = Value(moduleNumber),
        title = Value(title),
        status = Value(status),
        sortOrder = Value(sortOrder),
        cachedAt = Value(cachedAt);
  static Insertable<CachedModuleRow> custom({
    Expression<String>? id,
    Expression<String>? moduleCode,
    Expression<int>? moduleNumber,
    Expression<String>? title,
    Expression<String>? description,
    Expression<String>? status,
    Expression<int>? sortOrder,
    Expression<DateTime>? cachedAt,
    Expression<String>? audience,
    Expression<String>? learnerRolesJson,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleCode != null) 'module_code': moduleCode,
      if (moduleNumber != null) 'module_number': moduleNumber,
      if (title != null) 'title': title,
      if (description != null) 'description': description,
      if (status != null) 'status': status,
      if (sortOrder != null) 'sort_order': sortOrder,
      if (cachedAt != null) 'cached_at': cachedAt,
      if (audience != null) 'audience': audience,
      if (learnerRolesJson != null) 'learner_roles_json': learnerRolesJson,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedModulesCompanion copyWith(
      {Value<String>? id,
      Value<String>? moduleCode,
      Value<int>? moduleNumber,
      Value<String>? title,
      Value<String?>? description,
      Value<String>? status,
      Value<int>? sortOrder,
      Value<DateTime>? cachedAt,
      Value<String>? audience,
      Value<String>? learnerRolesJson,
      Value<int>? rowid}) {
    return CachedModulesCompanion(
      id: id ?? this.id,
      moduleCode: moduleCode ?? this.moduleCode,
      moduleNumber: moduleNumber ?? this.moduleNumber,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      sortOrder: sortOrder ?? this.sortOrder,
      cachedAt: cachedAt ?? this.cachedAt,
      audience: audience ?? this.audience,
      learnerRolesJson: learnerRolesJson ?? this.learnerRolesJson,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (moduleCode.present) {
      map['module_code'] = Variable<String>(moduleCode.value);
    }
    if (moduleNumber.present) {
      map['module_number'] = Variable<int>(moduleNumber.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (sortOrder.present) {
      map['sort_order'] = Variable<int>(sortOrder.value);
    }
    if (cachedAt.present) {
      map['cached_at'] = Variable<DateTime>(cachedAt.value);
    }
    if (audience.present) {
      map['audience'] = Variable<String>(audience.value);
    }
    if (learnerRolesJson.present) {
      map['learner_roles_json'] = Variable<String>(learnerRolesJson.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedModulesCompanion(')
          ..write('id: $id, ')
          ..write('moduleCode: $moduleCode, ')
          ..write('moduleNumber: $moduleNumber, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('status: $status, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('cachedAt: $cachedAt, ')
          ..write('audience: $audience, ')
          ..write('learnerRolesJson: $learnerRolesJson, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedTranslationsTable extends CachedTranslations
    with TableInfo<$CachedTranslationsTable, CachedTranslationRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedTranslationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _languageIdMeta =
      const VerificationMeta('languageId');
  @override
  late final GeneratedColumn<String> languageId = GeneratedColumn<String>(
      'language_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _languageCodeMeta =
      const VerificationMeta('languageCode');
  @override
  late final GeneratedColumn<String> languageCode = GeneratedColumn<String>(
      'language_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _bodyMeta = const VerificationMeta('body');
  @override
  late final GeneratedColumn<String> body = GeneratedColumn<String>(
      'body', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _audioTextMeta =
      const VerificationMeta('audioText');
  @override
  late final GeneratedColumn<String> audioText = GeneratedColumn<String>(
      'audio_text', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        moduleId,
        languageId,
        languageCode,
        title,
        description,
        body,
        audioText,
        status
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_translations';
  @override
  VerificationContext validateIntegrity(
      Insertable<CachedTranslationRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('language_id')) {
      context.handle(
          _languageIdMeta,
          languageId.isAcceptableOrUnknown(
              data['language_id']!, _languageIdMeta));
    } else if (isInserting) {
      context.missing(_languageIdMeta);
    }
    if (data.containsKey('language_code')) {
      context.handle(
          _languageCodeMeta,
          languageCode.isAcceptableOrUnknown(
              data['language_code']!, _languageCodeMeta));
    } else if (isInserting) {
      context.missing(_languageCodeMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('body')) {
      context.handle(
          _bodyMeta, body.isAcceptableOrUnknown(data['body']!, _bodyMeta));
    }
    if (data.containsKey('audio_text')) {
      context.handle(_audioTextMeta,
          audioText.isAcceptableOrUnknown(data['audio_text']!, _audioTextMeta));
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedTranslationRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedTranslationRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      languageId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}language_id'])!,
      languageCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}language_code'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description']),
      body: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}body']),
      audioText: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}audio_text']),
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
    );
  }

  @override
  $CachedTranslationsTable createAlias(String alias) {
    return $CachedTranslationsTable(attachedDatabase, alias);
  }
}

class CachedTranslationRow extends DataClass
    implements Insertable<CachedTranslationRow> {
  final String id;
  final String moduleId;
  final String languageId;
  final String languageCode;
  final String title;
  final String? description;
  final String? body;
  final String? audioText;
  final String status;
  const CachedTranslationRow(
      {required this.id,
      required this.moduleId,
      required this.languageId,
      required this.languageCode,
      required this.title,
      this.description,
      this.body,
      this.audioText,
      required this.status});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['module_id'] = Variable<String>(moduleId);
    map['language_id'] = Variable<String>(languageId);
    map['language_code'] = Variable<String>(languageCode);
    map['title'] = Variable<String>(title);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    if (!nullToAbsent || body != null) {
      map['body'] = Variable<String>(body);
    }
    if (!nullToAbsent || audioText != null) {
      map['audio_text'] = Variable<String>(audioText);
    }
    map['status'] = Variable<String>(status);
    return map;
  }

  CachedTranslationsCompanion toCompanion(bool nullToAbsent) {
    return CachedTranslationsCompanion(
      id: Value(id),
      moduleId: Value(moduleId),
      languageId: Value(languageId),
      languageCode: Value(languageCode),
      title: Value(title),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      body: body == null && nullToAbsent ? const Value.absent() : Value(body),
      audioText: audioText == null && nullToAbsent
          ? const Value.absent()
          : Value(audioText),
      status: Value(status),
    );
  }

  factory CachedTranslationRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedTranslationRow(
      id: serializer.fromJson<String>(json['id']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      languageId: serializer.fromJson<String>(json['languageId']),
      languageCode: serializer.fromJson<String>(json['languageCode']),
      title: serializer.fromJson<String>(json['title']),
      description: serializer.fromJson<String?>(json['description']),
      body: serializer.fromJson<String?>(json['body']),
      audioText: serializer.fromJson<String?>(json['audioText']),
      status: serializer.fromJson<String>(json['status']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'moduleId': serializer.toJson<String>(moduleId),
      'languageId': serializer.toJson<String>(languageId),
      'languageCode': serializer.toJson<String>(languageCode),
      'title': serializer.toJson<String>(title),
      'description': serializer.toJson<String?>(description),
      'body': serializer.toJson<String?>(body),
      'audioText': serializer.toJson<String?>(audioText),
      'status': serializer.toJson<String>(status),
    };
  }

  CachedTranslationRow copyWith(
          {String? id,
          String? moduleId,
          String? languageId,
          String? languageCode,
          String? title,
          Value<String?> description = const Value.absent(),
          Value<String?> body = const Value.absent(),
          Value<String?> audioText = const Value.absent(),
          String? status}) =>
      CachedTranslationRow(
        id: id ?? this.id,
        moduleId: moduleId ?? this.moduleId,
        languageId: languageId ?? this.languageId,
        languageCode: languageCode ?? this.languageCode,
        title: title ?? this.title,
        description: description.present ? description.value : this.description,
        body: body.present ? body.value : this.body,
        audioText: audioText.present ? audioText.value : this.audioText,
        status: status ?? this.status,
      );
  CachedTranslationRow copyWithCompanion(CachedTranslationsCompanion data) {
    return CachedTranslationRow(
      id: data.id.present ? data.id.value : this.id,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      languageId:
          data.languageId.present ? data.languageId.value : this.languageId,
      languageCode: data.languageCode.present
          ? data.languageCode.value
          : this.languageCode,
      title: data.title.present ? data.title.value : this.title,
      description:
          data.description.present ? data.description.value : this.description,
      body: data.body.present ? data.body.value : this.body,
      audioText: data.audioText.present ? data.audioText.value : this.audioText,
      status: data.status.present ? data.status.value : this.status,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedTranslationRow(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('languageId: $languageId, ')
          ..write('languageCode: $languageCode, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('body: $body, ')
          ..write('audioText: $audioText, ')
          ..write('status: $status')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, moduleId, languageId, languageCode, title,
      description, body, audioText, status);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedTranslationRow &&
          other.id == this.id &&
          other.moduleId == this.moduleId &&
          other.languageId == this.languageId &&
          other.languageCode == this.languageCode &&
          other.title == this.title &&
          other.description == this.description &&
          other.body == this.body &&
          other.audioText == this.audioText &&
          other.status == this.status);
}

class CachedTranslationsCompanion
    extends UpdateCompanion<CachedTranslationRow> {
  final Value<String> id;
  final Value<String> moduleId;
  final Value<String> languageId;
  final Value<String> languageCode;
  final Value<String> title;
  final Value<String?> description;
  final Value<String?> body;
  final Value<String?> audioText;
  final Value<String> status;
  final Value<int> rowid;
  const CachedTranslationsCompanion({
    this.id = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.languageId = const Value.absent(),
    this.languageCode = const Value.absent(),
    this.title = const Value.absent(),
    this.description = const Value.absent(),
    this.body = const Value.absent(),
    this.audioText = const Value.absent(),
    this.status = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedTranslationsCompanion.insert({
    required String id,
    required String moduleId,
    required String languageId,
    required String languageCode,
    required String title,
    this.description = const Value.absent(),
    this.body = const Value.absent(),
    this.audioText = const Value.absent(),
    required String status,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        moduleId = Value(moduleId),
        languageId = Value(languageId),
        languageCode = Value(languageCode),
        title = Value(title),
        status = Value(status);
  static Insertable<CachedTranslationRow> custom({
    Expression<String>? id,
    Expression<String>? moduleId,
    Expression<String>? languageId,
    Expression<String>? languageCode,
    Expression<String>? title,
    Expression<String>? description,
    Expression<String>? body,
    Expression<String>? audioText,
    Expression<String>? status,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleId != null) 'module_id': moduleId,
      if (languageId != null) 'language_id': languageId,
      if (languageCode != null) 'language_code': languageCode,
      if (title != null) 'title': title,
      if (description != null) 'description': description,
      if (body != null) 'body': body,
      if (audioText != null) 'audio_text': audioText,
      if (status != null) 'status': status,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedTranslationsCompanion copyWith(
      {Value<String>? id,
      Value<String>? moduleId,
      Value<String>? languageId,
      Value<String>? languageCode,
      Value<String>? title,
      Value<String?>? description,
      Value<String?>? body,
      Value<String?>? audioText,
      Value<String>? status,
      Value<int>? rowid}) {
    return CachedTranslationsCompanion(
      id: id ?? this.id,
      moduleId: moduleId ?? this.moduleId,
      languageId: languageId ?? this.languageId,
      languageCode: languageCode ?? this.languageCode,
      title: title ?? this.title,
      description: description ?? this.description,
      body: body ?? this.body,
      audioText: audioText ?? this.audioText,
      status: status ?? this.status,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (languageId.present) {
      map['language_id'] = Variable<String>(languageId.value);
    }
    if (languageCode.present) {
      map['language_code'] = Variable<String>(languageCode.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (body.present) {
      map['body'] = Variable<String>(body.value);
    }
    if (audioText.present) {
      map['audio_text'] = Variable<String>(audioText.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedTranslationsCompanion(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('languageId: $languageId, ')
          ..write('languageCode: $languageCode, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('body: $body, ')
          ..write('audioText: $audioText, ')
          ..write('status: $status, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedSectionsTable extends CachedSections
    with TableInfo<$CachedSectionsTable, CachedSectionRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedSectionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sectionNumberMeta =
      const VerificationMeta('sectionNumber');
  @override
  late final GeneratedColumn<int> sectionNumber = GeneratedColumn<int>(
      'section_number', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _contentTypeMeta =
      const VerificationMeta('contentType');
  @override
  late final GeneratedColumn<String> contentType = GeneratedColumn<String>(
      'content_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _contentJsonMeta =
      const VerificationMeta('contentJson');
  @override
  late final GeneratedColumn<String> contentJson = GeneratedColumn<String>(
      'content_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sortOrderMeta =
      const VerificationMeta('sortOrder');
  @override
  late final GeneratedColumn<int> sortOrder = GeneratedColumn<int>(
      'sort_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns =>
      [id, moduleId, sectionNumber, title, contentType, contentJson, sortOrder];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_sections';
  @override
  VerificationContext validateIntegrity(Insertable<CachedSectionRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('section_number')) {
      context.handle(
          _sectionNumberMeta,
          sectionNumber.isAcceptableOrUnknown(
              data['section_number']!, _sectionNumberMeta));
    } else if (isInserting) {
      context.missing(_sectionNumberMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    }
    if (data.containsKey('content_type')) {
      context.handle(
          _contentTypeMeta,
          contentType.isAcceptableOrUnknown(
              data['content_type']!, _contentTypeMeta));
    } else if (isInserting) {
      context.missing(_contentTypeMeta);
    }
    if (data.containsKey('content_json')) {
      context.handle(
          _contentJsonMeta,
          contentJson.isAcceptableOrUnknown(
              data['content_json']!, _contentJsonMeta));
    } else if (isInserting) {
      context.missing(_contentJsonMeta);
    }
    if (data.containsKey('sort_order')) {
      context.handle(_sortOrderMeta,
          sortOrder.isAcceptableOrUnknown(data['sort_order']!, _sortOrderMeta));
    } else if (isInserting) {
      context.missing(_sortOrderMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedSectionRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedSectionRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      sectionNumber: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}section_number'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title']),
      contentType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}content_type'])!,
      contentJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}content_json'])!,
      sortOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}sort_order'])!,
    );
  }

  @override
  $CachedSectionsTable createAlias(String alias) {
    return $CachedSectionsTable(attachedDatabase, alias);
  }
}

class CachedSectionRow extends DataClass
    implements Insertable<CachedSectionRow> {
  final String id;
  final String moduleId;
  final int sectionNumber;
  final String? title;
  final String contentType;
  final String contentJson;
  final int sortOrder;
  const CachedSectionRow(
      {required this.id,
      required this.moduleId,
      required this.sectionNumber,
      this.title,
      required this.contentType,
      required this.contentJson,
      required this.sortOrder});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['module_id'] = Variable<String>(moduleId);
    map['section_number'] = Variable<int>(sectionNumber);
    if (!nullToAbsent || title != null) {
      map['title'] = Variable<String>(title);
    }
    map['content_type'] = Variable<String>(contentType);
    map['content_json'] = Variable<String>(contentJson);
    map['sort_order'] = Variable<int>(sortOrder);
    return map;
  }

  CachedSectionsCompanion toCompanion(bool nullToAbsent) {
    return CachedSectionsCompanion(
      id: Value(id),
      moduleId: Value(moduleId),
      sectionNumber: Value(sectionNumber),
      title:
          title == null && nullToAbsent ? const Value.absent() : Value(title),
      contentType: Value(contentType),
      contentJson: Value(contentJson),
      sortOrder: Value(sortOrder),
    );
  }

  factory CachedSectionRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedSectionRow(
      id: serializer.fromJson<String>(json['id']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      sectionNumber: serializer.fromJson<int>(json['sectionNumber']),
      title: serializer.fromJson<String?>(json['title']),
      contentType: serializer.fromJson<String>(json['contentType']),
      contentJson: serializer.fromJson<String>(json['contentJson']),
      sortOrder: serializer.fromJson<int>(json['sortOrder']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'moduleId': serializer.toJson<String>(moduleId),
      'sectionNumber': serializer.toJson<int>(sectionNumber),
      'title': serializer.toJson<String?>(title),
      'contentType': serializer.toJson<String>(contentType),
      'contentJson': serializer.toJson<String>(contentJson),
      'sortOrder': serializer.toJson<int>(sortOrder),
    };
  }

  CachedSectionRow copyWith(
          {String? id,
          String? moduleId,
          int? sectionNumber,
          Value<String?> title = const Value.absent(),
          String? contentType,
          String? contentJson,
          int? sortOrder}) =>
      CachedSectionRow(
        id: id ?? this.id,
        moduleId: moduleId ?? this.moduleId,
        sectionNumber: sectionNumber ?? this.sectionNumber,
        title: title.present ? title.value : this.title,
        contentType: contentType ?? this.contentType,
        contentJson: contentJson ?? this.contentJson,
        sortOrder: sortOrder ?? this.sortOrder,
      );
  CachedSectionRow copyWithCompanion(CachedSectionsCompanion data) {
    return CachedSectionRow(
      id: data.id.present ? data.id.value : this.id,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      sectionNumber: data.sectionNumber.present
          ? data.sectionNumber.value
          : this.sectionNumber,
      title: data.title.present ? data.title.value : this.title,
      contentType:
          data.contentType.present ? data.contentType.value : this.contentType,
      contentJson:
          data.contentJson.present ? data.contentJson.value : this.contentJson,
      sortOrder: data.sortOrder.present ? data.sortOrder.value : this.sortOrder,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedSectionRow(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('sectionNumber: $sectionNumber, ')
          ..write('title: $title, ')
          ..write('contentType: $contentType, ')
          ..write('contentJson: $contentJson, ')
          ..write('sortOrder: $sortOrder')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, moduleId, sectionNumber, title, contentType, contentJson, sortOrder);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedSectionRow &&
          other.id == this.id &&
          other.moduleId == this.moduleId &&
          other.sectionNumber == this.sectionNumber &&
          other.title == this.title &&
          other.contentType == this.contentType &&
          other.contentJson == this.contentJson &&
          other.sortOrder == this.sortOrder);
}

class CachedSectionsCompanion extends UpdateCompanion<CachedSectionRow> {
  final Value<String> id;
  final Value<String> moduleId;
  final Value<int> sectionNumber;
  final Value<String?> title;
  final Value<String> contentType;
  final Value<String> contentJson;
  final Value<int> sortOrder;
  final Value<int> rowid;
  const CachedSectionsCompanion({
    this.id = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.sectionNumber = const Value.absent(),
    this.title = const Value.absent(),
    this.contentType = const Value.absent(),
    this.contentJson = const Value.absent(),
    this.sortOrder = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedSectionsCompanion.insert({
    required String id,
    required String moduleId,
    required int sectionNumber,
    this.title = const Value.absent(),
    required String contentType,
    required String contentJson,
    required int sortOrder,
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        moduleId = Value(moduleId),
        sectionNumber = Value(sectionNumber),
        contentType = Value(contentType),
        contentJson = Value(contentJson),
        sortOrder = Value(sortOrder);
  static Insertable<CachedSectionRow> custom({
    Expression<String>? id,
    Expression<String>? moduleId,
    Expression<int>? sectionNumber,
    Expression<String>? title,
    Expression<String>? contentType,
    Expression<String>? contentJson,
    Expression<int>? sortOrder,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleId != null) 'module_id': moduleId,
      if (sectionNumber != null) 'section_number': sectionNumber,
      if (title != null) 'title': title,
      if (contentType != null) 'content_type': contentType,
      if (contentJson != null) 'content_json': contentJson,
      if (sortOrder != null) 'sort_order': sortOrder,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedSectionsCompanion copyWith(
      {Value<String>? id,
      Value<String>? moduleId,
      Value<int>? sectionNumber,
      Value<String?>? title,
      Value<String>? contentType,
      Value<String>? contentJson,
      Value<int>? sortOrder,
      Value<int>? rowid}) {
    return CachedSectionsCompanion(
      id: id ?? this.id,
      moduleId: moduleId ?? this.moduleId,
      sectionNumber: sectionNumber ?? this.sectionNumber,
      title: title ?? this.title,
      contentType: contentType ?? this.contentType,
      contentJson: contentJson ?? this.contentJson,
      sortOrder: sortOrder ?? this.sortOrder,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (sectionNumber.present) {
      map['section_number'] = Variable<int>(sectionNumber.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (contentType.present) {
      map['content_type'] = Variable<String>(contentType.value);
    }
    if (contentJson.present) {
      map['content_json'] = Variable<String>(contentJson.value);
    }
    if (sortOrder.present) {
      map['sort_order'] = Variable<int>(sortOrder.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedSectionsCompanion(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('sectionNumber: $sectionNumber, ')
          ..write('title: $title, ')
          ..write('contentType: $contentType, ')
          ..write('contentJson: $contentJson, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedMediaTable extends CachedMedia
    with TableInfo<$CachedMediaTable, CachedMediaRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedMediaTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _assetTypeMeta =
      const VerificationMeta('assetType');
  @override
  late final GeneratedColumn<String> assetType = GeneratedColumn<String>(
      'asset_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _filenameMeta =
      const VerificationMeta('filename');
  @override
  late final GeneratedColumn<String> filename = GeneratedColumn<String>(
      'filename', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _localPathMeta =
      const VerificationMeta('localPath');
  @override
  late final GeneratedColumn<String> localPath = GeneratedColumn<String>(
      'local_path', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _checksumMeta =
      const VerificationMeta('checksum');
  @override
  late final GeneratedColumn<String> checksum = GeneratedColumn<String>(
      'checksum', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sizeBytesMeta =
      const VerificationMeta('sizeBytes');
  @override
  late final GeneratedColumn<int> sizeBytes = GeneratedColumn<int>(
      'size_bytes', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _mimeTypeMeta =
      const VerificationMeta('mimeType');
  @override
  late final GeneratedColumn<String> mimeType = GeneratedColumn<String>(
      'mime_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _downloadedAtMeta =
      const VerificationMeta('downloadedAt');
  @override
  late final GeneratedColumn<DateTime> downloadedAt = GeneratedColumn<DateTime>(
      'downloaded_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        assetType,
        filename,
        localPath,
        checksum,
        sizeBytes,
        mimeType,
        downloadedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_media';
  @override
  VerificationContext validateIntegrity(Insertable<CachedMediaRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('asset_type')) {
      context.handle(_assetTypeMeta,
          assetType.isAcceptableOrUnknown(data['asset_type']!, _assetTypeMeta));
    } else if (isInserting) {
      context.missing(_assetTypeMeta);
    }
    if (data.containsKey('filename')) {
      context.handle(_filenameMeta,
          filename.isAcceptableOrUnknown(data['filename']!, _filenameMeta));
    } else if (isInserting) {
      context.missing(_filenameMeta);
    }
    if (data.containsKey('local_path')) {
      context.handle(_localPathMeta,
          localPath.isAcceptableOrUnknown(data['local_path']!, _localPathMeta));
    }
    if (data.containsKey('checksum')) {
      context.handle(_checksumMeta,
          checksum.isAcceptableOrUnknown(data['checksum']!, _checksumMeta));
    } else if (isInserting) {
      context.missing(_checksumMeta);
    }
    if (data.containsKey('size_bytes')) {
      context.handle(_sizeBytesMeta,
          sizeBytes.isAcceptableOrUnknown(data['size_bytes']!, _sizeBytesMeta));
    } else if (isInserting) {
      context.missing(_sizeBytesMeta);
    }
    if (data.containsKey('mime_type')) {
      context.handle(_mimeTypeMeta,
          mimeType.isAcceptableOrUnknown(data['mime_type']!, _mimeTypeMeta));
    } else if (isInserting) {
      context.missing(_mimeTypeMeta);
    }
    if (data.containsKey('downloaded_at')) {
      context.handle(
          _downloadedAtMeta,
          downloadedAt.isAcceptableOrUnknown(
              data['downloaded_at']!, _downloadedAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedMediaRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedMediaRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      assetType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}asset_type'])!,
      filename: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}filename'])!,
      localPath: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}local_path']),
      checksum: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}checksum'])!,
      sizeBytes: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}size_bytes'])!,
      mimeType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}mime_type'])!,
      downloadedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}downloaded_at']),
    );
  }

  @override
  $CachedMediaTable createAlias(String alias) {
    return $CachedMediaTable(attachedDatabase, alias);
  }
}

class CachedMediaRow extends DataClass implements Insertable<CachedMediaRow> {
  final String id;
  final String assetType;
  final String filename;
  final String? localPath;
  final String checksum;
  final int sizeBytes;
  final String mimeType;
  final DateTime? downloadedAt;
  const CachedMediaRow(
      {required this.id,
      required this.assetType,
      required this.filename,
      this.localPath,
      required this.checksum,
      required this.sizeBytes,
      required this.mimeType,
      this.downloadedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['asset_type'] = Variable<String>(assetType);
    map['filename'] = Variable<String>(filename);
    if (!nullToAbsent || localPath != null) {
      map['local_path'] = Variable<String>(localPath);
    }
    map['checksum'] = Variable<String>(checksum);
    map['size_bytes'] = Variable<int>(sizeBytes);
    map['mime_type'] = Variable<String>(mimeType);
    if (!nullToAbsent || downloadedAt != null) {
      map['downloaded_at'] = Variable<DateTime>(downloadedAt);
    }
    return map;
  }

  CachedMediaCompanion toCompanion(bool nullToAbsent) {
    return CachedMediaCompanion(
      id: Value(id),
      assetType: Value(assetType),
      filename: Value(filename),
      localPath: localPath == null && nullToAbsent
          ? const Value.absent()
          : Value(localPath),
      checksum: Value(checksum),
      sizeBytes: Value(sizeBytes),
      mimeType: Value(mimeType),
      downloadedAt: downloadedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(downloadedAt),
    );
  }

  factory CachedMediaRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedMediaRow(
      id: serializer.fromJson<String>(json['id']),
      assetType: serializer.fromJson<String>(json['assetType']),
      filename: serializer.fromJson<String>(json['filename']),
      localPath: serializer.fromJson<String?>(json['localPath']),
      checksum: serializer.fromJson<String>(json['checksum']),
      sizeBytes: serializer.fromJson<int>(json['sizeBytes']),
      mimeType: serializer.fromJson<String>(json['mimeType']),
      downloadedAt: serializer.fromJson<DateTime?>(json['downloadedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'assetType': serializer.toJson<String>(assetType),
      'filename': serializer.toJson<String>(filename),
      'localPath': serializer.toJson<String?>(localPath),
      'checksum': serializer.toJson<String>(checksum),
      'sizeBytes': serializer.toJson<int>(sizeBytes),
      'mimeType': serializer.toJson<String>(mimeType),
      'downloadedAt': serializer.toJson<DateTime?>(downloadedAt),
    };
  }

  CachedMediaRow copyWith(
          {String? id,
          String? assetType,
          String? filename,
          Value<String?> localPath = const Value.absent(),
          String? checksum,
          int? sizeBytes,
          String? mimeType,
          Value<DateTime?> downloadedAt = const Value.absent()}) =>
      CachedMediaRow(
        id: id ?? this.id,
        assetType: assetType ?? this.assetType,
        filename: filename ?? this.filename,
        localPath: localPath.present ? localPath.value : this.localPath,
        checksum: checksum ?? this.checksum,
        sizeBytes: sizeBytes ?? this.sizeBytes,
        mimeType: mimeType ?? this.mimeType,
        downloadedAt:
            downloadedAt.present ? downloadedAt.value : this.downloadedAt,
      );
  CachedMediaRow copyWithCompanion(CachedMediaCompanion data) {
    return CachedMediaRow(
      id: data.id.present ? data.id.value : this.id,
      assetType: data.assetType.present ? data.assetType.value : this.assetType,
      filename: data.filename.present ? data.filename.value : this.filename,
      localPath: data.localPath.present ? data.localPath.value : this.localPath,
      checksum: data.checksum.present ? data.checksum.value : this.checksum,
      sizeBytes: data.sizeBytes.present ? data.sizeBytes.value : this.sizeBytes,
      mimeType: data.mimeType.present ? data.mimeType.value : this.mimeType,
      downloadedAt: data.downloadedAt.present
          ? data.downloadedAt.value
          : this.downloadedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedMediaRow(')
          ..write('id: $id, ')
          ..write('assetType: $assetType, ')
          ..write('filename: $filename, ')
          ..write('localPath: $localPath, ')
          ..write('checksum: $checksum, ')
          ..write('sizeBytes: $sizeBytes, ')
          ..write('mimeType: $mimeType, ')
          ..write('downloadedAt: $downloadedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, assetType, filename, localPath, checksum,
      sizeBytes, mimeType, downloadedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedMediaRow &&
          other.id == this.id &&
          other.assetType == this.assetType &&
          other.filename == this.filename &&
          other.localPath == this.localPath &&
          other.checksum == this.checksum &&
          other.sizeBytes == this.sizeBytes &&
          other.mimeType == this.mimeType &&
          other.downloadedAt == this.downloadedAt);
}

class CachedMediaCompanion extends UpdateCompanion<CachedMediaRow> {
  final Value<String> id;
  final Value<String> assetType;
  final Value<String> filename;
  final Value<String?> localPath;
  final Value<String> checksum;
  final Value<int> sizeBytes;
  final Value<String> mimeType;
  final Value<DateTime?> downloadedAt;
  final Value<int> rowid;
  const CachedMediaCompanion({
    this.id = const Value.absent(),
    this.assetType = const Value.absent(),
    this.filename = const Value.absent(),
    this.localPath = const Value.absent(),
    this.checksum = const Value.absent(),
    this.sizeBytes = const Value.absent(),
    this.mimeType = const Value.absent(),
    this.downloadedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedMediaCompanion.insert({
    required String id,
    required String assetType,
    required String filename,
    this.localPath = const Value.absent(),
    required String checksum,
    required int sizeBytes,
    required String mimeType,
    this.downloadedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        assetType = Value(assetType),
        filename = Value(filename),
        checksum = Value(checksum),
        sizeBytes = Value(sizeBytes),
        mimeType = Value(mimeType);
  static Insertable<CachedMediaRow> custom({
    Expression<String>? id,
    Expression<String>? assetType,
    Expression<String>? filename,
    Expression<String>? localPath,
    Expression<String>? checksum,
    Expression<int>? sizeBytes,
    Expression<String>? mimeType,
    Expression<DateTime>? downloadedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (assetType != null) 'asset_type': assetType,
      if (filename != null) 'filename': filename,
      if (localPath != null) 'local_path': localPath,
      if (checksum != null) 'checksum': checksum,
      if (sizeBytes != null) 'size_bytes': sizeBytes,
      if (mimeType != null) 'mime_type': mimeType,
      if (downloadedAt != null) 'downloaded_at': downloadedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedMediaCompanion copyWith(
      {Value<String>? id,
      Value<String>? assetType,
      Value<String>? filename,
      Value<String?>? localPath,
      Value<String>? checksum,
      Value<int>? sizeBytes,
      Value<String>? mimeType,
      Value<DateTime?>? downloadedAt,
      Value<int>? rowid}) {
    return CachedMediaCompanion(
      id: id ?? this.id,
      assetType: assetType ?? this.assetType,
      filename: filename ?? this.filename,
      localPath: localPath ?? this.localPath,
      checksum: checksum ?? this.checksum,
      sizeBytes: sizeBytes ?? this.sizeBytes,
      mimeType: mimeType ?? this.mimeType,
      downloadedAt: downloadedAt ?? this.downloadedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (assetType.present) {
      map['asset_type'] = Variable<String>(assetType.value);
    }
    if (filename.present) {
      map['filename'] = Variable<String>(filename.value);
    }
    if (localPath.present) {
      map['local_path'] = Variable<String>(localPath.value);
    }
    if (checksum.present) {
      map['checksum'] = Variable<String>(checksum.value);
    }
    if (sizeBytes.present) {
      map['size_bytes'] = Variable<int>(sizeBytes.value);
    }
    if (mimeType.present) {
      map['mime_type'] = Variable<String>(mimeType.value);
    }
    if (downloadedAt.present) {
      map['downloaded_at'] = Variable<DateTime>(downloadedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedMediaCompanion(')
          ..write('id: $id, ')
          ..write('assetType: $assetType, ')
          ..write('filename: $filename, ')
          ..write('localPath: $localPath, ')
          ..write('checksum: $checksum, ')
          ..write('sizeBytes: $sizeBytes, ')
          ..write('mimeType: $mimeType, ')
          ..write('downloadedAt: $downloadedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedVideosTable extends CachedVideos
    with TableInfo<$CachedVideosTable, CachedVideoRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedVideosTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _durationSecondsMeta =
      const VerificationMeta('durationSeconds');
  @override
  late final GeneratedColumn<int> durationSeconds = GeneratedColumn<int>(
      'duration_seconds', aliasedName, true,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _languageMeta =
      const VerificationMeta('language');
  @override
  late final GeneratedColumn<String> language = GeneratedColumn<String>(
      'language', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _offlineAvailableMeta =
      const VerificationMeta('offlineAvailable');
  @override
  late final GeneratedColumn<bool> offlineAvailable = GeneratedColumn<bool>(
      'offline_available', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("offline_available" IN (0, 1))'));
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _hasFileMeta =
      const VerificationMeta('hasFile');
  @override
  late final GeneratedColumn<bool> hasFile = GeneratedColumn<bool>(
      'has_file', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("has_file" IN (0, 1))'));
  static const VerificationMeta _localPathMeta =
      const VerificationMeta('localPath');
  @override
  late final GeneratedColumn<String> localPath = GeneratedColumn<String>(
      'local_path', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        title,
        description,
        moduleId,
        durationSeconds,
        language,
        offlineAvailable,
        status,
        hasFile,
        localPath
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_videos';
  @override
  VerificationContext validateIntegrity(Insertable<CachedVideoRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    }
    if (data.containsKey('duration_seconds')) {
      context.handle(
          _durationSecondsMeta,
          durationSeconds.isAcceptableOrUnknown(
              data['duration_seconds']!, _durationSecondsMeta));
    }
    if (data.containsKey('language')) {
      context.handle(_languageMeta,
          language.isAcceptableOrUnknown(data['language']!, _languageMeta));
    } else if (isInserting) {
      context.missing(_languageMeta);
    }
    if (data.containsKey('offline_available')) {
      context.handle(
          _offlineAvailableMeta,
          offlineAvailable.isAcceptableOrUnknown(
              data['offline_available']!, _offlineAvailableMeta));
    } else if (isInserting) {
      context.missing(_offlineAvailableMeta);
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('has_file')) {
      context.handle(_hasFileMeta,
          hasFile.isAcceptableOrUnknown(data['has_file']!, _hasFileMeta));
    } else if (isInserting) {
      context.missing(_hasFileMeta);
    }
    if (data.containsKey('local_path')) {
      context.handle(_localPathMeta,
          localPath.isAcceptableOrUnknown(data['local_path']!, _localPathMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedVideoRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedVideoRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description']),
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id']),
      durationSeconds: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}duration_seconds']),
      language: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}language'])!,
      offlineAvailable: attachedDatabase.typeMapping.read(
          DriftSqlType.bool, data['${effectivePrefix}offline_available'])!,
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      hasFile: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}has_file'])!,
      localPath: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}local_path']),
    );
  }

  @override
  $CachedVideosTable createAlias(String alias) {
    return $CachedVideosTable(attachedDatabase, alias);
  }
}

class CachedVideoRow extends DataClass implements Insertable<CachedVideoRow> {
  final String id;
  final String title;
  final String? description;
  final String? moduleId;
  final int? durationSeconds;
  final String language;
  final bool offlineAvailable;
  final String status;
  final bool hasFile;
  final String? localPath;
  const CachedVideoRow(
      {required this.id,
      required this.title,
      this.description,
      this.moduleId,
      this.durationSeconds,
      required this.language,
      required this.offlineAvailable,
      required this.status,
      required this.hasFile,
      this.localPath});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['title'] = Variable<String>(title);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    if (!nullToAbsent || moduleId != null) {
      map['module_id'] = Variable<String>(moduleId);
    }
    if (!nullToAbsent || durationSeconds != null) {
      map['duration_seconds'] = Variable<int>(durationSeconds);
    }
    map['language'] = Variable<String>(language);
    map['offline_available'] = Variable<bool>(offlineAvailable);
    map['status'] = Variable<String>(status);
    map['has_file'] = Variable<bool>(hasFile);
    if (!nullToAbsent || localPath != null) {
      map['local_path'] = Variable<String>(localPath);
    }
    return map;
  }

  CachedVideosCompanion toCompanion(bool nullToAbsent) {
    return CachedVideosCompanion(
      id: Value(id),
      title: Value(title),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      moduleId: moduleId == null && nullToAbsent
          ? const Value.absent()
          : Value(moduleId),
      durationSeconds: durationSeconds == null && nullToAbsent
          ? const Value.absent()
          : Value(durationSeconds),
      language: Value(language),
      offlineAvailable: Value(offlineAvailable),
      status: Value(status),
      hasFile: Value(hasFile),
      localPath: localPath == null && nullToAbsent
          ? const Value.absent()
          : Value(localPath),
    );
  }

  factory CachedVideoRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedVideoRow(
      id: serializer.fromJson<String>(json['id']),
      title: serializer.fromJson<String>(json['title']),
      description: serializer.fromJson<String?>(json['description']),
      moduleId: serializer.fromJson<String?>(json['moduleId']),
      durationSeconds: serializer.fromJson<int?>(json['durationSeconds']),
      language: serializer.fromJson<String>(json['language']),
      offlineAvailable: serializer.fromJson<bool>(json['offlineAvailable']),
      status: serializer.fromJson<String>(json['status']),
      hasFile: serializer.fromJson<bool>(json['hasFile']),
      localPath: serializer.fromJson<String?>(json['localPath']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'title': serializer.toJson<String>(title),
      'description': serializer.toJson<String?>(description),
      'moduleId': serializer.toJson<String?>(moduleId),
      'durationSeconds': serializer.toJson<int?>(durationSeconds),
      'language': serializer.toJson<String>(language),
      'offlineAvailable': serializer.toJson<bool>(offlineAvailable),
      'status': serializer.toJson<String>(status),
      'hasFile': serializer.toJson<bool>(hasFile),
      'localPath': serializer.toJson<String?>(localPath),
    };
  }

  CachedVideoRow copyWith(
          {String? id,
          String? title,
          Value<String?> description = const Value.absent(),
          Value<String?> moduleId = const Value.absent(),
          Value<int?> durationSeconds = const Value.absent(),
          String? language,
          bool? offlineAvailable,
          String? status,
          bool? hasFile,
          Value<String?> localPath = const Value.absent()}) =>
      CachedVideoRow(
        id: id ?? this.id,
        title: title ?? this.title,
        description: description.present ? description.value : this.description,
        moduleId: moduleId.present ? moduleId.value : this.moduleId,
        durationSeconds: durationSeconds.present
            ? durationSeconds.value
            : this.durationSeconds,
        language: language ?? this.language,
        offlineAvailable: offlineAvailable ?? this.offlineAvailable,
        status: status ?? this.status,
        hasFile: hasFile ?? this.hasFile,
        localPath: localPath.present ? localPath.value : this.localPath,
      );
  CachedVideoRow copyWithCompanion(CachedVideosCompanion data) {
    return CachedVideoRow(
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      description:
          data.description.present ? data.description.value : this.description,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      durationSeconds: data.durationSeconds.present
          ? data.durationSeconds.value
          : this.durationSeconds,
      language: data.language.present ? data.language.value : this.language,
      offlineAvailable: data.offlineAvailable.present
          ? data.offlineAvailable.value
          : this.offlineAvailable,
      status: data.status.present ? data.status.value : this.status,
      hasFile: data.hasFile.present ? data.hasFile.value : this.hasFile,
      localPath: data.localPath.present ? data.localPath.value : this.localPath,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedVideoRow(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('moduleId: $moduleId, ')
          ..write('durationSeconds: $durationSeconds, ')
          ..write('language: $language, ')
          ..write('offlineAvailable: $offlineAvailable, ')
          ..write('status: $status, ')
          ..write('hasFile: $hasFile, ')
          ..write('localPath: $localPath')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, title, description, moduleId,
      durationSeconds, language, offlineAvailable, status, hasFile, localPath);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedVideoRow &&
          other.id == this.id &&
          other.title == this.title &&
          other.description == this.description &&
          other.moduleId == this.moduleId &&
          other.durationSeconds == this.durationSeconds &&
          other.language == this.language &&
          other.offlineAvailable == this.offlineAvailable &&
          other.status == this.status &&
          other.hasFile == this.hasFile &&
          other.localPath == this.localPath);
}

class CachedVideosCompanion extends UpdateCompanion<CachedVideoRow> {
  final Value<String> id;
  final Value<String> title;
  final Value<String?> description;
  final Value<String?> moduleId;
  final Value<int?> durationSeconds;
  final Value<String> language;
  final Value<bool> offlineAvailable;
  final Value<String> status;
  final Value<bool> hasFile;
  final Value<String?> localPath;
  final Value<int> rowid;
  const CachedVideosCompanion({
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.description = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.durationSeconds = const Value.absent(),
    this.language = const Value.absent(),
    this.offlineAvailable = const Value.absent(),
    this.status = const Value.absent(),
    this.hasFile = const Value.absent(),
    this.localPath = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedVideosCompanion.insert({
    required String id,
    required String title,
    this.description = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.durationSeconds = const Value.absent(),
    required String language,
    required bool offlineAvailable,
    required String status,
    required bool hasFile,
    this.localPath = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        title = Value(title),
        language = Value(language),
        offlineAvailable = Value(offlineAvailable),
        status = Value(status),
        hasFile = Value(hasFile);
  static Insertable<CachedVideoRow> custom({
    Expression<String>? id,
    Expression<String>? title,
    Expression<String>? description,
    Expression<String>? moduleId,
    Expression<int>? durationSeconds,
    Expression<String>? language,
    Expression<bool>? offlineAvailable,
    Expression<String>? status,
    Expression<bool>? hasFile,
    Expression<String>? localPath,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (description != null) 'description': description,
      if (moduleId != null) 'module_id': moduleId,
      if (durationSeconds != null) 'duration_seconds': durationSeconds,
      if (language != null) 'language': language,
      if (offlineAvailable != null) 'offline_available': offlineAvailable,
      if (status != null) 'status': status,
      if (hasFile != null) 'has_file': hasFile,
      if (localPath != null) 'local_path': localPath,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedVideosCompanion copyWith(
      {Value<String>? id,
      Value<String>? title,
      Value<String?>? description,
      Value<String?>? moduleId,
      Value<int?>? durationSeconds,
      Value<String>? language,
      Value<bool>? offlineAvailable,
      Value<String>? status,
      Value<bool>? hasFile,
      Value<String?>? localPath,
      Value<int>? rowid}) {
    return CachedVideosCompanion(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      moduleId: moduleId ?? this.moduleId,
      durationSeconds: durationSeconds ?? this.durationSeconds,
      language: language ?? this.language,
      offlineAvailable: offlineAvailable ?? this.offlineAvailable,
      status: status ?? this.status,
      hasFile: hasFile ?? this.hasFile,
      localPath: localPath ?? this.localPath,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (durationSeconds.present) {
      map['duration_seconds'] = Variable<int>(durationSeconds.value);
    }
    if (language.present) {
      map['language'] = Variable<String>(language.value);
    }
    if (offlineAvailable.present) {
      map['offline_available'] = Variable<bool>(offlineAvailable.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (hasFile.present) {
      map['has_file'] = Variable<bool>(hasFile.value);
    }
    if (localPath.present) {
      map['local_path'] = Variable<String>(localPath.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedVideosCompanion(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('moduleId: $moduleId, ')
          ..write('durationSeconds: $durationSeconds, ')
          ..write('language: $language, ')
          ..write('offlineAvailable: $offlineAvailable, ')
          ..write('status: $status, ')
          ..write('hasFile: $hasFile, ')
          ..write('localPath: $localPath, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalProgressTable extends LocalProgress
    with TableInfo<$LocalProgressTable, LocalProgressRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalProgressTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _progressPercentMeta =
      const VerificationMeta('progressPercent');
  @override
  late final GeneratedColumn<int> progressPercent = GeneratedColumn<int>(
      'progress_percent', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  static const VerificationMeta _completedMeta =
      const VerificationMeta('completed');
  @override
  late final GeneratedColumn<bool> completed = GeneratedColumn<bool>(
      'completed', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("completed" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _lastSectionMeta =
      const VerificationMeta('lastSection');
  @override
  late final GeneratedColumn<String> lastSection = GeneratedColumn<String>(
      'last_section', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _lastOpenedAtMeta =
      const VerificationMeta('lastOpenedAt');
  @override
  late final GeneratedColumn<DateTime> lastOpenedAt = GeneratedColumn<DateTime>(
      'last_opened_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _completedAtMeta =
      const VerificationMeta('completedAt');
  @override
  late final GeneratedColumn<DateTime> completedAt = GeneratedColumn<DateTime>(
      'completed_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _readingCompletedAtMeta =
      const VerificationMeta('readingCompletedAt');
  @override
  late final GeneratedColumn<DateTime> readingCompletedAt =
      GeneratedColumn<DateTime>('reading_completed_at', aliasedName, true,
          type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _syncedMeta = const VerificationMeta('synced');
  @override
  late final GeneratedColumn<bool> synced = GeneratedColumn<bool>(
      'synced', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("synced" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _userIdMeta = const VerificationMeta('userId');
  @override
  late final GeneratedColumn<String> userId = GeneratedColumn<String>(
      'user_id', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        moduleId,
        progressPercent,
        completed,
        lastSection,
        lastOpenedAt,
        completedAt,
        readingCompletedAt,
        synced,
        userId
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_progress';
  @override
  VerificationContext validateIntegrity(Insertable<LocalProgressRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('progress_percent')) {
      context.handle(
          _progressPercentMeta,
          progressPercent.isAcceptableOrUnknown(
              data['progress_percent']!, _progressPercentMeta));
    }
    if (data.containsKey('completed')) {
      context.handle(_completedMeta,
          completed.isAcceptableOrUnknown(data['completed']!, _completedMeta));
    }
    if (data.containsKey('last_section')) {
      context.handle(
          _lastSectionMeta,
          lastSection.isAcceptableOrUnknown(
              data['last_section']!, _lastSectionMeta));
    }
    if (data.containsKey('last_opened_at')) {
      context.handle(
          _lastOpenedAtMeta,
          lastOpenedAt.isAcceptableOrUnknown(
              data['last_opened_at']!, _lastOpenedAtMeta));
    }
    if (data.containsKey('completed_at')) {
      context.handle(
          _completedAtMeta,
          completedAt.isAcceptableOrUnknown(
              data['completed_at']!, _completedAtMeta));
    }
    if (data.containsKey('reading_completed_at')) {
      context.handle(
          _readingCompletedAtMeta,
          readingCompletedAt.isAcceptableOrUnknown(
              data['reading_completed_at']!, _readingCompletedAtMeta));
    }
    if (data.containsKey('synced')) {
      context.handle(_syncedMeta,
          synced.isAcceptableOrUnknown(data['synced']!, _syncedMeta));
    }
    if (data.containsKey('user_id')) {
      context.handle(_userIdMeta,
          userId.isAcceptableOrUnknown(data['user_id']!, _userIdMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalProgressRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalProgressRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      progressPercent: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}progress_percent'])!,
      completed: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}completed'])!,
      lastSection: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}last_section']),
      lastOpenedAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}last_opened_at']),
      completedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}completed_at']),
      readingCompletedAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime,
          data['${effectivePrefix}reading_completed_at']),
      synced: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}synced'])!,
      userId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}user_id'])!,
    );
  }

  @override
  $LocalProgressTable createAlias(String alias) {
    return $LocalProgressTable(attachedDatabase, alias);
  }
}

class LocalProgressRow extends DataClass
    implements Insertable<LocalProgressRow> {
  final int id;
  final String moduleId;
  final int progressPercent;
  final bool completed;
  final String? lastSection;
  final DateTime? lastOpenedAt;
  final DateTime? completedAt;
  final DateTime? readingCompletedAt;
  final bool synced;

  /// Owner of this row: every account on a shared phone keeps its own progress.
  final String userId;
  const LocalProgressRow(
      {required this.id,
      required this.moduleId,
      required this.progressPercent,
      required this.completed,
      this.lastSection,
      this.lastOpenedAt,
      this.completedAt,
      this.readingCompletedAt,
      required this.synced,
      required this.userId});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['module_id'] = Variable<String>(moduleId);
    map['progress_percent'] = Variable<int>(progressPercent);
    map['completed'] = Variable<bool>(completed);
    if (!nullToAbsent || lastSection != null) {
      map['last_section'] = Variable<String>(lastSection);
    }
    if (!nullToAbsent || lastOpenedAt != null) {
      map['last_opened_at'] = Variable<DateTime>(lastOpenedAt);
    }
    if (!nullToAbsent || completedAt != null) {
      map['completed_at'] = Variable<DateTime>(completedAt);
    }
    if (!nullToAbsent || readingCompletedAt != null) {
      map['reading_completed_at'] = Variable<DateTime>(readingCompletedAt);
    }
    map['synced'] = Variable<bool>(synced);
    map['user_id'] = Variable<String>(userId);
    return map;
  }

  LocalProgressCompanion toCompanion(bool nullToAbsent) {
    return LocalProgressCompanion(
      id: Value(id),
      moduleId: Value(moduleId),
      progressPercent: Value(progressPercent),
      completed: Value(completed),
      lastSection: lastSection == null && nullToAbsent
          ? const Value.absent()
          : Value(lastSection),
      lastOpenedAt: lastOpenedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(lastOpenedAt),
      completedAt: completedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(completedAt),
      readingCompletedAt: readingCompletedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(readingCompletedAt),
      synced: Value(synced),
      userId: Value(userId),
    );
  }

  factory LocalProgressRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalProgressRow(
      id: serializer.fromJson<int>(json['id']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      progressPercent: serializer.fromJson<int>(json['progressPercent']),
      completed: serializer.fromJson<bool>(json['completed']),
      lastSection: serializer.fromJson<String?>(json['lastSection']),
      lastOpenedAt: serializer.fromJson<DateTime?>(json['lastOpenedAt']),
      completedAt: serializer.fromJson<DateTime?>(json['completedAt']),
      readingCompletedAt:
          serializer.fromJson<DateTime?>(json['readingCompletedAt']),
      synced: serializer.fromJson<bool>(json['synced']),
      userId: serializer.fromJson<String>(json['userId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'moduleId': serializer.toJson<String>(moduleId),
      'progressPercent': serializer.toJson<int>(progressPercent),
      'completed': serializer.toJson<bool>(completed),
      'lastSection': serializer.toJson<String?>(lastSection),
      'lastOpenedAt': serializer.toJson<DateTime?>(lastOpenedAt),
      'completedAt': serializer.toJson<DateTime?>(completedAt),
      'readingCompletedAt': serializer.toJson<DateTime?>(readingCompletedAt),
      'synced': serializer.toJson<bool>(synced),
      'userId': serializer.toJson<String>(userId),
    };
  }

  LocalProgressRow copyWith(
          {int? id,
          String? moduleId,
          int? progressPercent,
          bool? completed,
          Value<String?> lastSection = const Value.absent(),
          Value<DateTime?> lastOpenedAt = const Value.absent(),
          Value<DateTime?> completedAt = const Value.absent(),
          Value<DateTime?> readingCompletedAt = const Value.absent(),
          bool? synced,
          String? userId}) =>
      LocalProgressRow(
        id: id ?? this.id,
        moduleId: moduleId ?? this.moduleId,
        progressPercent: progressPercent ?? this.progressPercent,
        completed: completed ?? this.completed,
        lastSection: lastSection.present ? lastSection.value : this.lastSection,
        lastOpenedAt:
            lastOpenedAt.present ? lastOpenedAt.value : this.lastOpenedAt,
        completedAt: completedAt.present ? completedAt.value : this.completedAt,
        readingCompletedAt: readingCompletedAt.present
            ? readingCompletedAt.value
            : this.readingCompletedAt,
        synced: synced ?? this.synced,
        userId: userId ?? this.userId,
      );
  LocalProgressRow copyWithCompanion(LocalProgressCompanion data) {
    return LocalProgressRow(
      id: data.id.present ? data.id.value : this.id,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      progressPercent: data.progressPercent.present
          ? data.progressPercent.value
          : this.progressPercent,
      completed: data.completed.present ? data.completed.value : this.completed,
      lastSection:
          data.lastSection.present ? data.lastSection.value : this.lastSection,
      lastOpenedAt: data.lastOpenedAt.present
          ? data.lastOpenedAt.value
          : this.lastOpenedAt,
      completedAt:
          data.completedAt.present ? data.completedAt.value : this.completedAt,
      readingCompletedAt: data.readingCompletedAt.present
          ? data.readingCompletedAt.value
          : this.readingCompletedAt,
      synced: data.synced.present ? data.synced.value : this.synced,
      userId: data.userId.present ? data.userId.value : this.userId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalProgressRow(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('progressPercent: $progressPercent, ')
          ..write('completed: $completed, ')
          ..write('lastSection: $lastSection, ')
          ..write('lastOpenedAt: $lastOpenedAt, ')
          ..write('completedAt: $completedAt, ')
          ..write('readingCompletedAt: $readingCompletedAt, ')
          ..write('synced: $synced, ')
          ..write('userId: $userId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      moduleId,
      progressPercent,
      completed,
      lastSection,
      lastOpenedAt,
      completedAt,
      readingCompletedAt,
      synced,
      userId);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalProgressRow &&
          other.id == this.id &&
          other.moduleId == this.moduleId &&
          other.progressPercent == this.progressPercent &&
          other.completed == this.completed &&
          other.lastSection == this.lastSection &&
          other.lastOpenedAt == this.lastOpenedAt &&
          other.completedAt == this.completedAt &&
          other.readingCompletedAt == this.readingCompletedAt &&
          other.synced == this.synced &&
          other.userId == this.userId);
}

class LocalProgressCompanion extends UpdateCompanion<LocalProgressRow> {
  final Value<int> id;
  final Value<String> moduleId;
  final Value<int> progressPercent;
  final Value<bool> completed;
  final Value<String?> lastSection;
  final Value<DateTime?> lastOpenedAt;
  final Value<DateTime?> completedAt;
  final Value<DateTime?> readingCompletedAt;
  final Value<bool> synced;
  final Value<String> userId;
  const LocalProgressCompanion({
    this.id = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.progressPercent = const Value.absent(),
    this.completed = const Value.absent(),
    this.lastSection = const Value.absent(),
    this.lastOpenedAt = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.readingCompletedAt = const Value.absent(),
    this.synced = const Value.absent(),
    this.userId = const Value.absent(),
  });
  LocalProgressCompanion.insert({
    this.id = const Value.absent(),
    required String moduleId,
    this.progressPercent = const Value.absent(),
    this.completed = const Value.absent(),
    this.lastSection = const Value.absent(),
    this.lastOpenedAt = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.readingCompletedAt = const Value.absent(),
    this.synced = const Value.absent(),
    this.userId = const Value.absent(),
  }) : moduleId = Value(moduleId);
  static Insertable<LocalProgressRow> custom({
    Expression<int>? id,
    Expression<String>? moduleId,
    Expression<int>? progressPercent,
    Expression<bool>? completed,
    Expression<String>? lastSection,
    Expression<DateTime>? lastOpenedAt,
    Expression<DateTime>? completedAt,
    Expression<DateTime>? readingCompletedAt,
    Expression<bool>? synced,
    Expression<String>? userId,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleId != null) 'module_id': moduleId,
      if (progressPercent != null) 'progress_percent': progressPercent,
      if (completed != null) 'completed': completed,
      if (lastSection != null) 'last_section': lastSection,
      if (lastOpenedAt != null) 'last_opened_at': lastOpenedAt,
      if (completedAt != null) 'completed_at': completedAt,
      if (readingCompletedAt != null)
        'reading_completed_at': readingCompletedAt,
      if (synced != null) 'synced': synced,
      if (userId != null) 'user_id': userId,
    });
  }

  LocalProgressCompanion copyWith(
      {Value<int>? id,
      Value<String>? moduleId,
      Value<int>? progressPercent,
      Value<bool>? completed,
      Value<String?>? lastSection,
      Value<DateTime?>? lastOpenedAt,
      Value<DateTime?>? completedAt,
      Value<DateTime?>? readingCompletedAt,
      Value<bool>? synced,
      Value<String>? userId}) {
    return LocalProgressCompanion(
      id: id ?? this.id,
      moduleId: moduleId ?? this.moduleId,
      progressPercent: progressPercent ?? this.progressPercent,
      completed: completed ?? this.completed,
      lastSection: lastSection ?? this.lastSection,
      lastOpenedAt: lastOpenedAt ?? this.lastOpenedAt,
      completedAt: completedAt ?? this.completedAt,
      readingCompletedAt: readingCompletedAt ?? this.readingCompletedAt,
      synced: synced ?? this.synced,
      userId: userId ?? this.userId,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (progressPercent.present) {
      map['progress_percent'] = Variable<int>(progressPercent.value);
    }
    if (completed.present) {
      map['completed'] = Variable<bool>(completed.value);
    }
    if (lastSection.present) {
      map['last_section'] = Variable<String>(lastSection.value);
    }
    if (lastOpenedAt.present) {
      map['last_opened_at'] = Variable<DateTime>(lastOpenedAt.value);
    }
    if (completedAt.present) {
      map['completed_at'] = Variable<DateTime>(completedAt.value);
    }
    if (readingCompletedAt.present) {
      map['reading_completed_at'] =
          Variable<DateTime>(readingCompletedAt.value);
    }
    if (synced.present) {
      map['synced'] = Variable<bool>(synced.value);
    }
    if (userId.present) {
      map['user_id'] = Variable<String>(userId.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalProgressCompanion(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('progressPercent: $progressPercent, ')
          ..write('completed: $completed, ')
          ..write('lastSection: $lastSection, ')
          ..write('lastOpenedAt: $lastOpenedAt, ')
          ..write('completedAt: $completedAt, ')
          ..write('readingCompletedAt: $readingCompletedAt, ')
          ..write('synced: $synced, ')
          ..write('userId: $userId')
          ..write(')'))
        .toString();
  }
}

class $PendingSyncTable extends PendingSync
    with TableInfo<$PendingSyncTable, PendingSyncRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PendingSyncTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _entityTypeMeta =
      const VerificationMeta('entityType');
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
      'entity_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _payloadJsonMeta =
      const VerificationMeta('payloadJson');
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
      'payload_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _syncedAtMeta =
      const VerificationMeta('syncedAt');
  @override
  late final GeneratedColumn<DateTime> syncedAt = GeneratedColumn<DateTime>(
      'synced_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _userIdMeta = const VerificationMeta('userId');
  @override
  late final GeneratedColumn<String> userId = GeneratedColumn<String>(
      'user_id', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  @override
  List<GeneratedColumn> get $columns =>
      [id, entityType, payloadJson, createdAt, syncedAt, userId];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'pending_sync';
  @override
  VerificationContext validateIntegrity(Insertable<PendingSyncRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('entity_type')) {
      context.handle(
          _entityTypeMeta,
          entityType.isAcceptableOrUnknown(
              data['entity_type']!, _entityTypeMeta));
    } else if (isInserting) {
      context.missing(_entityTypeMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
          _payloadJsonMeta,
          payloadJson.isAcceptableOrUnknown(
              data['payload_json']!, _payloadJsonMeta));
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('synced_at')) {
      context.handle(_syncedAtMeta,
          syncedAt.isAcceptableOrUnknown(data['synced_at']!, _syncedAtMeta));
    }
    if (data.containsKey('user_id')) {
      context.handle(_userIdMeta,
          userId.isAcceptableOrUnknown(data['user_id']!, _userIdMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  PendingSyncRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PendingSyncRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      entityType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}entity_type'])!,
      payloadJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload_json'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      syncedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}synced_at']),
      userId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}user_id'])!,
    );
  }

  @override
  $PendingSyncTable createAlias(String alias) {
    return $PendingSyncTable(attachedDatabase, alias);
  }
}

class PendingSyncRow extends DataClass implements Insertable<PendingSyncRow> {
  final int id;
  final String entityType;
  final String payloadJson;
  final DateTime createdAt;
  final DateTime? syncedAt;
  final String userId;
  const PendingSyncRow(
      {required this.id,
      required this.entityType,
      required this.payloadJson,
      required this.createdAt,
      this.syncedAt,
      required this.userId});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['entity_type'] = Variable<String>(entityType);
    map['payload_json'] = Variable<String>(payloadJson);
    map['created_at'] = Variable<DateTime>(createdAt);
    if (!nullToAbsent || syncedAt != null) {
      map['synced_at'] = Variable<DateTime>(syncedAt);
    }
    map['user_id'] = Variable<String>(userId);
    return map;
  }

  PendingSyncCompanion toCompanion(bool nullToAbsent) {
    return PendingSyncCompanion(
      id: Value(id),
      entityType: Value(entityType),
      payloadJson: Value(payloadJson),
      createdAt: Value(createdAt),
      syncedAt: syncedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(syncedAt),
      userId: Value(userId),
    );
  }

  factory PendingSyncRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PendingSyncRow(
      id: serializer.fromJson<int>(json['id']),
      entityType: serializer.fromJson<String>(json['entityType']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      syncedAt: serializer.fromJson<DateTime?>(json['syncedAt']),
      userId: serializer.fromJson<String>(json['userId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'entityType': serializer.toJson<String>(entityType),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'syncedAt': serializer.toJson<DateTime?>(syncedAt),
      'userId': serializer.toJson<String>(userId),
    };
  }

  PendingSyncRow copyWith(
          {int? id,
          String? entityType,
          String? payloadJson,
          DateTime? createdAt,
          Value<DateTime?> syncedAt = const Value.absent(),
          String? userId}) =>
      PendingSyncRow(
        id: id ?? this.id,
        entityType: entityType ?? this.entityType,
        payloadJson: payloadJson ?? this.payloadJson,
        createdAt: createdAt ?? this.createdAt,
        syncedAt: syncedAt.present ? syncedAt.value : this.syncedAt,
        userId: userId ?? this.userId,
      );
  PendingSyncRow copyWithCompanion(PendingSyncCompanion data) {
    return PendingSyncRow(
      id: data.id.present ? data.id.value : this.id,
      entityType:
          data.entityType.present ? data.entityType.value : this.entityType,
      payloadJson:
          data.payloadJson.present ? data.payloadJson.value : this.payloadJson,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      syncedAt: data.syncedAt.present ? data.syncedAt.value : this.syncedAt,
      userId: data.userId.present ? data.userId.value : this.userId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PendingSyncRow(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('syncedAt: $syncedAt, ')
          ..write('userId: $userId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, entityType, payloadJson, createdAt, syncedAt, userId);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PendingSyncRow &&
          other.id == this.id &&
          other.entityType == this.entityType &&
          other.payloadJson == this.payloadJson &&
          other.createdAt == this.createdAt &&
          other.syncedAt == this.syncedAt &&
          other.userId == this.userId);
}

class PendingSyncCompanion extends UpdateCompanion<PendingSyncRow> {
  final Value<int> id;
  final Value<String> entityType;
  final Value<String> payloadJson;
  final Value<DateTime> createdAt;
  final Value<DateTime?> syncedAt;
  final Value<String> userId;
  const PendingSyncCompanion({
    this.id = const Value.absent(),
    this.entityType = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.syncedAt = const Value.absent(),
    this.userId = const Value.absent(),
  });
  PendingSyncCompanion.insert({
    this.id = const Value.absent(),
    required String entityType,
    required String payloadJson,
    required DateTime createdAt,
    this.syncedAt = const Value.absent(),
    this.userId = const Value.absent(),
  })  : entityType = Value(entityType),
        payloadJson = Value(payloadJson),
        createdAt = Value(createdAt);
  static Insertable<PendingSyncRow> custom({
    Expression<int>? id,
    Expression<String>? entityType,
    Expression<String>? payloadJson,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? syncedAt,
    Expression<String>? userId,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (entityType != null) 'entity_type': entityType,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (createdAt != null) 'created_at': createdAt,
      if (syncedAt != null) 'synced_at': syncedAt,
      if (userId != null) 'user_id': userId,
    });
  }

  PendingSyncCompanion copyWith(
      {Value<int>? id,
      Value<String>? entityType,
      Value<String>? payloadJson,
      Value<DateTime>? createdAt,
      Value<DateTime?>? syncedAt,
      Value<String>? userId}) {
    return PendingSyncCompanion(
      id: id ?? this.id,
      entityType: entityType ?? this.entityType,
      payloadJson: payloadJson ?? this.payloadJson,
      createdAt: createdAt ?? this.createdAt,
      syncedAt: syncedAt ?? this.syncedAt,
      userId: userId ?? this.userId,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (syncedAt.present) {
      map['synced_at'] = Variable<DateTime>(syncedAt.value);
    }
    if (userId.present) {
      map['user_id'] = Variable<String>(userId.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PendingSyncCompanion(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('syncedAt: $syncedAt, ')
          ..write('userId: $userId')
          ..write(')'))
        .toString();
  }
}

class $AppSettingsTable extends AppSettings
    with TableInfo<$AppSettingsTable, AppSettingRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $AppSettingsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
      'key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
      'value', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'app_settings';
  @override
  VerificationContext validateIntegrity(Insertable<AppSettingRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
          _keyMeta, key.isAcceptableOrUnknown(data['key']!, _keyMeta));
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
          _valueMeta, value.isAcceptableOrUnknown(data['value']!, _valueMeta));
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  AppSettingRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return AppSettingRow(
      key: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}key'])!,
      value: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}value'])!,
    );
  }

  @override
  $AppSettingsTable createAlias(String alias) {
    return $AppSettingsTable(attachedDatabase, alias);
  }
}

class AppSettingRow extends DataClass implements Insertable<AppSettingRow> {
  final String key;
  final String value;
  const AppSettingRow({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  AppSettingsCompanion toCompanion(bool nullToAbsent) {
    return AppSettingsCompanion(
      key: Value(key),
      value: Value(value),
    );
  }

  factory AppSettingRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return AppSettingRow(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  AppSettingRow copyWith({String? key, String? value}) => AppSettingRow(
        key: key ?? this.key,
        value: value ?? this.value,
      );
  AppSettingRow copyWithCompanion(AppSettingsCompanion data) {
    return AppSettingRow(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('AppSettingRow(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is AppSettingRow &&
          other.key == this.key &&
          other.value == this.value);
}

class AppSettingsCompanion extends UpdateCompanion<AppSettingRow> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const AppSettingsCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  AppSettingsCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  })  : key = Value(key),
        value = Value(value);
  static Insertable<AppSettingRow> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  AppSettingsCompanion copyWith(
      {Value<String>? key, Value<String>? value, Value<int>? rowid}) {
    return AppSettingsCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('AppSettingsCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $InstalledReleasesTable extends InstalledReleases
    with TableInfo<$InstalledReleasesTable, InstalledReleaseRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $InstalledReleasesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _releaseCodeMeta =
      const VerificationMeta('releaseCode');
  @override
  late final GeneratedColumn<String> releaseCode = GeneratedColumn<String>(
      'release_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _versionMeta =
      const VerificationMeta('version');
  @override
  late final GeneratedColumn<String> version = GeneratedColumn<String>(
      'version', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _installedAtMeta =
      const VerificationMeta('installedAt');
  @override
  late final GeneratedColumn<DateTime> installedAt = GeneratedColumn<DateTime>(
      'installed_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _moduleCountMeta =
      const VerificationMeta('moduleCount');
  @override
  late final GeneratedColumn<int> moduleCount = GeneratedColumn<int>(
      'module_count', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _sectionCountMeta =
      const VerificationMeta('sectionCount');
  @override
  late final GeneratedColumn<int> sectionCount = GeneratedColumn<int>(
      'section_count', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns =>
      [id, releaseCode, version, installedAt, moduleCount, sectionCount];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'installed_releases';
  @override
  VerificationContext validateIntegrity(
      Insertable<InstalledReleaseRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('release_code')) {
      context.handle(
          _releaseCodeMeta,
          releaseCode.isAcceptableOrUnknown(
              data['release_code']!, _releaseCodeMeta));
    } else if (isInserting) {
      context.missing(_releaseCodeMeta);
    }
    if (data.containsKey('version')) {
      context.handle(_versionMeta,
          version.isAcceptableOrUnknown(data['version']!, _versionMeta));
    } else if (isInserting) {
      context.missing(_versionMeta);
    }
    if (data.containsKey('installed_at')) {
      context.handle(
          _installedAtMeta,
          installedAt.isAcceptableOrUnknown(
              data['installed_at']!, _installedAtMeta));
    } else if (isInserting) {
      context.missing(_installedAtMeta);
    }
    if (data.containsKey('module_count')) {
      context.handle(
          _moduleCountMeta,
          moduleCount.isAcceptableOrUnknown(
              data['module_count']!, _moduleCountMeta));
    } else if (isInserting) {
      context.missing(_moduleCountMeta);
    }
    if (data.containsKey('section_count')) {
      context.handle(
          _sectionCountMeta,
          sectionCount.isAcceptableOrUnknown(
              data['section_count']!, _sectionCountMeta));
    } else if (isInserting) {
      context.missing(_sectionCountMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  InstalledReleaseRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return InstalledReleaseRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      releaseCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}release_code'])!,
      version: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}version'])!,
      installedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}installed_at'])!,
      moduleCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}module_count'])!,
      sectionCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}section_count'])!,
    );
  }

  @override
  $InstalledReleasesTable createAlias(String alias) {
    return $InstalledReleasesTable(attachedDatabase, alias);
  }
}

class InstalledReleaseRow extends DataClass
    implements Insertable<InstalledReleaseRow> {
  final int id;
  final String releaseCode;
  final String version;
  final DateTime installedAt;
  final int moduleCount;
  final int sectionCount;
  const InstalledReleaseRow(
      {required this.id,
      required this.releaseCode,
      required this.version,
      required this.installedAt,
      required this.moduleCount,
      required this.sectionCount});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['release_code'] = Variable<String>(releaseCode);
    map['version'] = Variable<String>(version);
    map['installed_at'] = Variable<DateTime>(installedAt);
    map['module_count'] = Variable<int>(moduleCount);
    map['section_count'] = Variable<int>(sectionCount);
    return map;
  }

  InstalledReleasesCompanion toCompanion(bool nullToAbsent) {
    return InstalledReleasesCompanion(
      id: Value(id),
      releaseCode: Value(releaseCode),
      version: Value(version),
      installedAt: Value(installedAt),
      moduleCount: Value(moduleCount),
      sectionCount: Value(sectionCount),
    );
  }

  factory InstalledReleaseRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return InstalledReleaseRow(
      id: serializer.fromJson<int>(json['id']),
      releaseCode: serializer.fromJson<String>(json['releaseCode']),
      version: serializer.fromJson<String>(json['version']),
      installedAt: serializer.fromJson<DateTime>(json['installedAt']),
      moduleCount: serializer.fromJson<int>(json['moduleCount']),
      sectionCount: serializer.fromJson<int>(json['sectionCount']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'releaseCode': serializer.toJson<String>(releaseCode),
      'version': serializer.toJson<String>(version),
      'installedAt': serializer.toJson<DateTime>(installedAt),
      'moduleCount': serializer.toJson<int>(moduleCount),
      'sectionCount': serializer.toJson<int>(sectionCount),
    };
  }

  InstalledReleaseRow copyWith(
          {int? id,
          String? releaseCode,
          String? version,
          DateTime? installedAt,
          int? moduleCount,
          int? sectionCount}) =>
      InstalledReleaseRow(
        id: id ?? this.id,
        releaseCode: releaseCode ?? this.releaseCode,
        version: version ?? this.version,
        installedAt: installedAt ?? this.installedAt,
        moduleCount: moduleCount ?? this.moduleCount,
        sectionCount: sectionCount ?? this.sectionCount,
      );
  InstalledReleaseRow copyWithCompanion(InstalledReleasesCompanion data) {
    return InstalledReleaseRow(
      id: data.id.present ? data.id.value : this.id,
      releaseCode:
          data.releaseCode.present ? data.releaseCode.value : this.releaseCode,
      version: data.version.present ? data.version.value : this.version,
      installedAt:
          data.installedAt.present ? data.installedAt.value : this.installedAt,
      moduleCount:
          data.moduleCount.present ? data.moduleCount.value : this.moduleCount,
      sectionCount: data.sectionCount.present
          ? data.sectionCount.value
          : this.sectionCount,
    );
  }

  @override
  String toString() {
    return (StringBuffer('InstalledReleaseRow(')
          ..write('id: $id, ')
          ..write('releaseCode: $releaseCode, ')
          ..write('version: $version, ')
          ..write('installedAt: $installedAt, ')
          ..write('moduleCount: $moduleCount, ')
          ..write('sectionCount: $sectionCount')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id, releaseCode, version, installedAt, moduleCount, sectionCount);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is InstalledReleaseRow &&
          other.id == this.id &&
          other.releaseCode == this.releaseCode &&
          other.version == this.version &&
          other.installedAt == this.installedAt &&
          other.moduleCount == this.moduleCount &&
          other.sectionCount == this.sectionCount);
}

class InstalledReleasesCompanion extends UpdateCompanion<InstalledReleaseRow> {
  final Value<int> id;
  final Value<String> releaseCode;
  final Value<String> version;
  final Value<DateTime> installedAt;
  final Value<int> moduleCount;
  final Value<int> sectionCount;
  const InstalledReleasesCompanion({
    this.id = const Value.absent(),
    this.releaseCode = const Value.absent(),
    this.version = const Value.absent(),
    this.installedAt = const Value.absent(),
    this.moduleCount = const Value.absent(),
    this.sectionCount = const Value.absent(),
  });
  InstalledReleasesCompanion.insert({
    this.id = const Value.absent(),
    required String releaseCode,
    required String version,
    required DateTime installedAt,
    required int moduleCount,
    required int sectionCount,
  })  : releaseCode = Value(releaseCode),
        version = Value(version),
        installedAt = Value(installedAt),
        moduleCount = Value(moduleCount),
        sectionCount = Value(sectionCount);
  static Insertable<InstalledReleaseRow> custom({
    Expression<int>? id,
    Expression<String>? releaseCode,
    Expression<String>? version,
    Expression<DateTime>? installedAt,
    Expression<int>? moduleCount,
    Expression<int>? sectionCount,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (releaseCode != null) 'release_code': releaseCode,
      if (version != null) 'version': version,
      if (installedAt != null) 'installed_at': installedAt,
      if (moduleCount != null) 'module_count': moduleCount,
      if (sectionCount != null) 'section_count': sectionCount,
    });
  }

  InstalledReleasesCompanion copyWith(
      {Value<int>? id,
      Value<String>? releaseCode,
      Value<String>? version,
      Value<DateTime>? installedAt,
      Value<int>? moduleCount,
      Value<int>? sectionCount}) {
    return InstalledReleasesCompanion(
      id: id ?? this.id,
      releaseCode: releaseCode ?? this.releaseCode,
      version: version ?? this.version,
      installedAt: installedAt ?? this.installedAt,
      moduleCount: moduleCount ?? this.moduleCount,
      sectionCount: sectionCount ?? this.sectionCount,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (releaseCode.present) {
      map['release_code'] = Variable<String>(releaseCode.value);
    }
    if (version.present) {
      map['version'] = Variable<String>(version.value);
    }
    if (installedAt.present) {
      map['installed_at'] = Variable<DateTime>(installedAt.value);
    }
    if (moduleCount.present) {
      map['module_count'] = Variable<int>(moduleCount.value);
    }
    if (sectionCount.present) {
      map['section_count'] = Variable<int>(sectionCount.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('InstalledReleasesCompanion(')
          ..write('id: $id, ')
          ..write('releaseCode: $releaseCode, ')
          ..write('version: $version, ')
          ..write('installedAt: $installedAt, ')
          ..write('moduleCount: $moduleCount, ')
          ..write('sectionCount: $sectionCount')
          ..write(')'))
        .toString();
  }
}

class $LocalAiQuestionsTable extends LocalAiQuestions
    with TableInfo<$LocalAiQuestionsTable, LocalAiQuestionRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalAiQuestionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _questionMeta =
      const VerificationMeta('question');
  @override
  late final GeneratedColumn<String> question = GeneratedColumn<String>(
      'question', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _answerMeta = const VerificationMeta('answer');
  @override
  late final GeneratedColumn<String> answer = GeneratedColumn<String>(
      'answer', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _matchedMeta =
      const VerificationMeta('matched');
  @override
  late final GeneratedColumn<bool> matched = GeneratedColumn<bool>(
      'matched', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("matched" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _askedAtMeta =
      const VerificationMeta('askedAt');
  @override
  late final GeneratedColumn<DateTime> askedAt = GeneratedColumn<DateTime>(
      'asked_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _syncedMeta = const VerificationMeta('synced');
  @override
  late final GeneratedColumn<bool> synced = GeneratedColumn<bool>(
      'synced', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("synced" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _userIdMeta = const VerificationMeta('userId');
  @override
  late final GeneratedColumn<String> userId = GeneratedColumn<String>(
      'user_id', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  @override
  List<GeneratedColumn> get $columns =>
      [id, question, answer, matched, askedAt, synced, userId];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_ai_questions';
  @override
  VerificationContext validateIntegrity(Insertable<LocalAiQuestionRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('question')) {
      context.handle(_questionMeta,
          question.isAcceptableOrUnknown(data['question']!, _questionMeta));
    } else if (isInserting) {
      context.missing(_questionMeta);
    }
    if (data.containsKey('answer')) {
      context.handle(_answerMeta,
          answer.isAcceptableOrUnknown(data['answer']!, _answerMeta));
    }
    if (data.containsKey('matched')) {
      context.handle(_matchedMeta,
          matched.isAcceptableOrUnknown(data['matched']!, _matchedMeta));
    }
    if (data.containsKey('asked_at')) {
      context.handle(_askedAtMeta,
          askedAt.isAcceptableOrUnknown(data['asked_at']!, _askedAtMeta));
    } else if (isInserting) {
      context.missing(_askedAtMeta);
    }
    if (data.containsKey('synced')) {
      context.handle(_syncedMeta,
          synced.isAcceptableOrUnknown(data['synced']!, _syncedMeta));
    }
    if (data.containsKey('user_id')) {
      context.handle(_userIdMeta,
          userId.isAcceptableOrUnknown(data['user_id']!, _userIdMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalAiQuestionRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalAiQuestionRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      question: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}question'])!,
      answer: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}answer']),
      matched: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}matched'])!,
      askedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}asked_at'])!,
      synced: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}synced'])!,
      userId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}user_id'])!,
    );
  }

  @override
  $LocalAiQuestionsTable createAlias(String alias) {
    return $LocalAiQuestionsTable(attachedDatabase, alias);
  }
}

class LocalAiQuestionRow extends DataClass
    implements Insertable<LocalAiQuestionRow> {
  final int id;
  final String question;
  final String? answer;
  final bool matched;
  final DateTime askedAt;
  final bool synced;
  final String userId;
  const LocalAiQuestionRow(
      {required this.id,
      required this.question,
      this.answer,
      required this.matched,
      required this.askedAt,
      required this.synced,
      required this.userId});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['question'] = Variable<String>(question);
    if (!nullToAbsent || answer != null) {
      map['answer'] = Variable<String>(answer);
    }
    map['matched'] = Variable<bool>(matched);
    map['asked_at'] = Variable<DateTime>(askedAt);
    map['synced'] = Variable<bool>(synced);
    map['user_id'] = Variable<String>(userId);
    return map;
  }

  LocalAiQuestionsCompanion toCompanion(bool nullToAbsent) {
    return LocalAiQuestionsCompanion(
      id: Value(id),
      question: Value(question),
      answer:
          answer == null && nullToAbsent ? const Value.absent() : Value(answer),
      matched: Value(matched),
      askedAt: Value(askedAt),
      synced: Value(synced),
      userId: Value(userId),
    );
  }

  factory LocalAiQuestionRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalAiQuestionRow(
      id: serializer.fromJson<int>(json['id']),
      question: serializer.fromJson<String>(json['question']),
      answer: serializer.fromJson<String?>(json['answer']),
      matched: serializer.fromJson<bool>(json['matched']),
      askedAt: serializer.fromJson<DateTime>(json['askedAt']),
      synced: serializer.fromJson<bool>(json['synced']),
      userId: serializer.fromJson<String>(json['userId']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'question': serializer.toJson<String>(question),
      'answer': serializer.toJson<String?>(answer),
      'matched': serializer.toJson<bool>(matched),
      'askedAt': serializer.toJson<DateTime>(askedAt),
      'synced': serializer.toJson<bool>(synced),
      'userId': serializer.toJson<String>(userId),
    };
  }

  LocalAiQuestionRow copyWith(
          {int? id,
          String? question,
          Value<String?> answer = const Value.absent(),
          bool? matched,
          DateTime? askedAt,
          bool? synced,
          String? userId}) =>
      LocalAiQuestionRow(
        id: id ?? this.id,
        question: question ?? this.question,
        answer: answer.present ? answer.value : this.answer,
        matched: matched ?? this.matched,
        askedAt: askedAt ?? this.askedAt,
        synced: synced ?? this.synced,
        userId: userId ?? this.userId,
      );
  LocalAiQuestionRow copyWithCompanion(LocalAiQuestionsCompanion data) {
    return LocalAiQuestionRow(
      id: data.id.present ? data.id.value : this.id,
      question: data.question.present ? data.question.value : this.question,
      answer: data.answer.present ? data.answer.value : this.answer,
      matched: data.matched.present ? data.matched.value : this.matched,
      askedAt: data.askedAt.present ? data.askedAt.value : this.askedAt,
      synced: data.synced.present ? data.synced.value : this.synced,
      userId: data.userId.present ? data.userId.value : this.userId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalAiQuestionRow(')
          ..write('id: $id, ')
          ..write('question: $question, ')
          ..write('answer: $answer, ')
          ..write('matched: $matched, ')
          ..write('askedAt: $askedAt, ')
          ..write('synced: $synced, ')
          ..write('userId: $userId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, question, answer, matched, askedAt, synced, userId);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalAiQuestionRow &&
          other.id == this.id &&
          other.question == this.question &&
          other.answer == this.answer &&
          other.matched == this.matched &&
          other.askedAt == this.askedAt &&
          other.synced == this.synced &&
          other.userId == this.userId);
}

class LocalAiQuestionsCompanion extends UpdateCompanion<LocalAiQuestionRow> {
  final Value<int> id;
  final Value<String> question;
  final Value<String?> answer;
  final Value<bool> matched;
  final Value<DateTime> askedAt;
  final Value<bool> synced;
  final Value<String> userId;
  const LocalAiQuestionsCompanion({
    this.id = const Value.absent(),
    this.question = const Value.absent(),
    this.answer = const Value.absent(),
    this.matched = const Value.absent(),
    this.askedAt = const Value.absent(),
    this.synced = const Value.absent(),
    this.userId = const Value.absent(),
  });
  LocalAiQuestionsCompanion.insert({
    this.id = const Value.absent(),
    required String question,
    this.answer = const Value.absent(),
    this.matched = const Value.absent(),
    required DateTime askedAt,
    this.synced = const Value.absent(),
    this.userId = const Value.absent(),
  })  : question = Value(question),
        askedAt = Value(askedAt);
  static Insertable<LocalAiQuestionRow> custom({
    Expression<int>? id,
    Expression<String>? question,
    Expression<String>? answer,
    Expression<bool>? matched,
    Expression<DateTime>? askedAt,
    Expression<bool>? synced,
    Expression<String>? userId,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (question != null) 'question': question,
      if (answer != null) 'answer': answer,
      if (matched != null) 'matched': matched,
      if (askedAt != null) 'asked_at': askedAt,
      if (synced != null) 'synced': synced,
      if (userId != null) 'user_id': userId,
    });
  }

  LocalAiQuestionsCompanion copyWith(
      {Value<int>? id,
      Value<String>? question,
      Value<String?>? answer,
      Value<bool>? matched,
      Value<DateTime>? askedAt,
      Value<bool>? synced,
      Value<String>? userId}) {
    return LocalAiQuestionsCompanion(
      id: id ?? this.id,
      question: question ?? this.question,
      answer: answer ?? this.answer,
      matched: matched ?? this.matched,
      askedAt: askedAt ?? this.askedAt,
      synced: synced ?? this.synced,
      userId: userId ?? this.userId,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (question.present) {
      map['question'] = Variable<String>(question.value);
    }
    if (answer.present) {
      map['answer'] = Variable<String>(answer.value);
    }
    if (matched.present) {
      map['matched'] = Variable<bool>(matched.value);
    }
    if (askedAt.present) {
      map['asked_at'] = Variable<DateTime>(askedAt.value);
    }
    if (synced.present) {
      map['synced'] = Variable<bool>(synced.value);
    }
    if (userId.present) {
      map['user_id'] = Variable<String>(userId.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalAiQuestionsCompanion(')
          ..write('id: $id, ')
          ..write('question: $question, ')
          ..write('answer: $answer, ')
          ..write('matched: $matched, ')
          ..write('askedAt: $askedAt, ')
          ..write('synced: $synced, ')
          ..write('userId: $userId')
          ..write(')'))
        .toString();
  }
}

class $RagMetadataTable extends RagMetadata
    with TableInfo<$RagMetadataTable, RagMetadataRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $RagMetadataTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sectionIdMeta =
      const VerificationMeta('sectionId');
  @override
  late final GeneratedColumn<String> sectionId = GeneratedColumn<String>(
      'section_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _chunkTextMeta =
      const VerificationMeta('chunkText');
  @override
  late final GeneratedColumn<String> chunkText = GeneratedColumn<String>(
      'chunk_text', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _embeddingJsonMeta =
      const VerificationMeta('embeddingJson');
  @override
  late final GeneratedColumn<String> embeddingJson = GeneratedColumn<String>(
      'embedding_json', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, moduleId, sectionId, chunkText, embeddingJson];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'rag_metadata';
  @override
  VerificationContext validateIntegrity(Insertable<RagMetadataRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('section_id')) {
      context.handle(_sectionIdMeta,
          sectionId.isAcceptableOrUnknown(data['section_id']!, _sectionIdMeta));
    }
    if (data.containsKey('chunk_text')) {
      context.handle(_chunkTextMeta,
          chunkText.isAcceptableOrUnknown(data['chunk_text']!, _chunkTextMeta));
    } else if (isInserting) {
      context.missing(_chunkTextMeta);
    }
    if (data.containsKey('embedding_json')) {
      context.handle(
          _embeddingJsonMeta,
          embeddingJson.isAcceptableOrUnknown(
              data['embedding_json']!, _embeddingJsonMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  RagMetadataRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return RagMetadataRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      sectionId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}section_id']),
      chunkText: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}chunk_text'])!,
      embeddingJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}embedding_json']),
    );
  }

  @override
  $RagMetadataTable createAlias(String alias) {
    return $RagMetadataTable(attachedDatabase, alias);
  }
}

class RagMetadataRow extends DataClass implements Insertable<RagMetadataRow> {
  final int id;
  final String moduleId;
  final String? sectionId;
  final String chunkText;
  final String? embeddingJson;
  const RagMetadataRow(
      {required this.id,
      required this.moduleId,
      this.sectionId,
      required this.chunkText,
      this.embeddingJson});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['module_id'] = Variable<String>(moduleId);
    if (!nullToAbsent || sectionId != null) {
      map['section_id'] = Variable<String>(sectionId);
    }
    map['chunk_text'] = Variable<String>(chunkText);
    if (!nullToAbsent || embeddingJson != null) {
      map['embedding_json'] = Variable<String>(embeddingJson);
    }
    return map;
  }

  RagMetadataCompanion toCompanion(bool nullToAbsent) {
    return RagMetadataCompanion(
      id: Value(id),
      moduleId: Value(moduleId),
      sectionId: sectionId == null && nullToAbsent
          ? const Value.absent()
          : Value(sectionId),
      chunkText: Value(chunkText),
      embeddingJson: embeddingJson == null && nullToAbsent
          ? const Value.absent()
          : Value(embeddingJson),
    );
  }

  factory RagMetadataRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return RagMetadataRow(
      id: serializer.fromJson<int>(json['id']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      sectionId: serializer.fromJson<String?>(json['sectionId']),
      chunkText: serializer.fromJson<String>(json['chunkText']),
      embeddingJson: serializer.fromJson<String?>(json['embeddingJson']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'moduleId': serializer.toJson<String>(moduleId),
      'sectionId': serializer.toJson<String?>(sectionId),
      'chunkText': serializer.toJson<String>(chunkText),
      'embeddingJson': serializer.toJson<String?>(embeddingJson),
    };
  }

  RagMetadataRow copyWith(
          {int? id,
          String? moduleId,
          Value<String?> sectionId = const Value.absent(),
          String? chunkText,
          Value<String?> embeddingJson = const Value.absent()}) =>
      RagMetadataRow(
        id: id ?? this.id,
        moduleId: moduleId ?? this.moduleId,
        sectionId: sectionId.present ? sectionId.value : this.sectionId,
        chunkText: chunkText ?? this.chunkText,
        embeddingJson:
            embeddingJson.present ? embeddingJson.value : this.embeddingJson,
      );
  RagMetadataRow copyWithCompanion(RagMetadataCompanion data) {
    return RagMetadataRow(
      id: data.id.present ? data.id.value : this.id,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      sectionId: data.sectionId.present ? data.sectionId.value : this.sectionId,
      chunkText: data.chunkText.present ? data.chunkText.value : this.chunkText,
      embeddingJson: data.embeddingJson.present
          ? data.embeddingJson.value
          : this.embeddingJson,
    );
  }

  @override
  String toString() {
    return (StringBuffer('RagMetadataRow(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('sectionId: $sectionId, ')
          ..write('chunkText: $chunkText, ')
          ..write('embeddingJson: $embeddingJson')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, moduleId, sectionId, chunkText, embeddingJson);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is RagMetadataRow &&
          other.id == this.id &&
          other.moduleId == this.moduleId &&
          other.sectionId == this.sectionId &&
          other.chunkText == this.chunkText &&
          other.embeddingJson == this.embeddingJson);
}

class RagMetadataCompanion extends UpdateCompanion<RagMetadataRow> {
  final Value<int> id;
  final Value<String> moduleId;
  final Value<String?> sectionId;
  final Value<String> chunkText;
  final Value<String?> embeddingJson;
  const RagMetadataCompanion({
    this.id = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.sectionId = const Value.absent(),
    this.chunkText = const Value.absent(),
    this.embeddingJson = const Value.absent(),
  });
  RagMetadataCompanion.insert({
    this.id = const Value.absent(),
    required String moduleId,
    this.sectionId = const Value.absent(),
    required String chunkText,
    this.embeddingJson = const Value.absent(),
  })  : moduleId = Value(moduleId),
        chunkText = Value(chunkText);
  static Insertable<RagMetadataRow> custom({
    Expression<int>? id,
    Expression<String>? moduleId,
    Expression<String>? sectionId,
    Expression<String>? chunkText,
    Expression<String>? embeddingJson,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleId != null) 'module_id': moduleId,
      if (sectionId != null) 'section_id': sectionId,
      if (chunkText != null) 'chunk_text': chunkText,
      if (embeddingJson != null) 'embedding_json': embeddingJson,
    });
  }

  RagMetadataCompanion copyWith(
      {Value<int>? id,
      Value<String>? moduleId,
      Value<String?>? sectionId,
      Value<String>? chunkText,
      Value<String?>? embeddingJson}) {
    return RagMetadataCompanion(
      id: id ?? this.id,
      moduleId: moduleId ?? this.moduleId,
      sectionId: sectionId ?? this.sectionId,
      chunkText: chunkText ?? this.chunkText,
      embeddingJson: embeddingJson ?? this.embeddingJson,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (sectionId.present) {
      map['section_id'] = Variable<String>(sectionId.value);
    }
    if (chunkText.present) {
      map['chunk_text'] = Variable<String>(chunkText.value);
    }
    if (embeddingJson.present) {
      map['embedding_json'] = Variable<String>(embeddingJson.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('RagMetadataCompanion(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('sectionId: $sectionId, ')
          ..write('chunkText: $chunkText, ')
          ..write('embeddingJson: $embeddingJson')
          ..write(')'))
        .toString();
  }
}

class $ContentChunksTable extends ContentChunks
    with TableInfo<$ContentChunksTable, ContentChunkRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ContentChunksTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleCodeMeta =
      const VerificationMeta('moduleCode');
  @override
  late final GeneratedColumn<String> moduleCode = GeneratedColumn<String>(
      'module_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sectionIdMeta =
      const VerificationMeta('sectionId');
  @override
  late final GeneratedColumn<String> sectionId = GeneratedColumn<String>(
      'section_id', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _sectionTitleMeta =
      const VerificationMeta('sectionTitle');
  @override
  late final GeneratedColumn<String> sectionTitle = GeneratedColumn<String>(
      'section_title', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _languageMeta =
      const VerificationMeta('language');
  @override
  late final GeneratedColumn<String> language = GeneratedColumn<String>(
      'language', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _sourceTitleMeta =
      const VerificationMeta('sourceTitle');
  @override
  late final GeneratedColumn<String> sourceTitle = GeneratedColumn<String>(
      'source_title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _chunkTextMeta =
      const VerificationMeta('chunkText');
  @override
  late final GeneratedColumn<String> chunkText = GeneratedColumn<String>(
      'chunk_text', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _faqQuestionsMeta =
      const VerificationMeta('faqQuestions');
  @override
  late final GeneratedColumn<String> faqQuestions = GeneratedColumn<String>(
      'faq_questions', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        moduleId,
        moduleCode,
        sectionId,
        sectionTitle,
        language,
        sourceTitle,
        chunkText,
        faqQuestions
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'content_chunks';
  @override
  VerificationContext validateIntegrity(Insertable<ContentChunkRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('module_code')) {
      context.handle(
          _moduleCodeMeta,
          moduleCode.isAcceptableOrUnknown(
              data['module_code']!, _moduleCodeMeta));
    } else if (isInserting) {
      context.missing(_moduleCodeMeta);
    }
    if (data.containsKey('section_id')) {
      context.handle(_sectionIdMeta,
          sectionId.isAcceptableOrUnknown(data['section_id']!, _sectionIdMeta));
    }
    if (data.containsKey('section_title')) {
      context.handle(
          _sectionTitleMeta,
          sectionTitle.isAcceptableOrUnknown(
              data['section_title']!, _sectionTitleMeta));
    }
    if (data.containsKey('language')) {
      context.handle(_languageMeta,
          language.isAcceptableOrUnknown(data['language']!, _languageMeta));
    } else if (isInserting) {
      context.missing(_languageMeta);
    }
    if (data.containsKey('source_title')) {
      context.handle(
          _sourceTitleMeta,
          sourceTitle.isAcceptableOrUnknown(
              data['source_title']!, _sourceTitleMeta));
    } else if (isInserting) {
      context.missing(_sourceTitleMeta);
    }
    if (data.containsKey('chunk_text')) {
      context.handle(_chunkTextMeta,
          chunkText.isAcceptableOrUnknown(data['chunk_text']!, _chunkTextMeta));
    } else if (isInserting) {
      context.missing(_chunkTextMeta);
    }
    if (data.containsKey('faq_questions')) {
      context.handle(
          _faqQuestionsMeta,
          faqQuestions.isAcceptableOrUnknown(
              data['faq_questions']!, _faqQuestionsMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ContentChunkRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ContentChunkRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      moduleCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_code'])!,
      sectionId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}section_id']),
      sectionTitle: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}section_title']),
      language: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}language'])!,
      sourceTitle: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}source_title'])!,
      chunkText: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}chunk_text'])!,
      faqQuestions: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}faq_questions']),
    );
  }

  @override
  $ContentChunksTable createAlias(String alias) {
    return $ContentChunksTable(attachedDatabase, alias);
  }
}

class ContentChunkRow extends DataClass implements Insertable<ContentChunkRow> {
  final String id;
  final String moduleId;
  final String moduleCode;
  final String? sectionId;
  final String? sectionTitle;
  final String language;
  final String sourceTitle;
  final String chunkText;
  final String? faqQuestions;
  const ContentChunkRow(
      {required this.id,
      required this.moduleId,
      required this.moduleCode,
      this.sectionId,
      this.sectionTitle,
      required this.language,
      required this.sourceTitle,
      required this.chunkText,
      this.faqQuestions});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['module_id'] = Variable<String>(moduleId);
    map['module_code'] = Variable<String>(moduleCode);
    if (!nullToAbsent || sectionId != null) {
      map['section_id'] = Variable<String>(sectionId);
    }
    if (!nullToAbsent || sectionTitle != null) {
      map['section_title'] = Variable<String>(sectionTitle);
    }
    map['language'] = Variable<String>(language);
    map['source_title'] = Variable<String>(sourceTitle);
    map['chunk_text'] = Variable<String>(chunkText);
    if (!nullToAbsent || faqQuestions != null) {
      map['faq_questions'] = Variable<String>(faqQuestions);
    }
    return map;
  }

  ContentChunksCompanion toCompanion(bool nullToAbsent) {
    return ContentChunksCompanion(
      id: Value(id),
      moduleId: Value(moduleId),
      moduleCode: Value(moduleCode),
      sectionId: sectionId == null && nullToAbsent
          ? const Value.absent()
          : Value(sectionId),
      sectionTitle: sectionTitle == null && nullToAbsent
          ? const Value.absent()
          : Value(sectionTitle),
      language: Value(language),
      sourceTitle: Value(sourceTitle),
      chunkText: Value(chunkText),
      faqQuestions: faqQuestions == null && nullToAbsent
          ? const Value.absent()
          : Value(faqQuestions),
    );
  }

  factory ContentChunkRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ContentChunkRow(
      id: serializer.fromJson<String>(json['id']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      moduleCode: serializer.fromJson<String>(json['moduleCode']),
      sectionId: serializer.fromJson<String?>(json['sectionId']),
      sectionTitle: serializer.fromJson<String?>(json['sectionTitle']),
      language: serializer.fromJson<String>(json['language']),
      sourceTitle: serializer.fromJson<String>(json['sourceTitle']),
      chunkText: serializer.fromJson<String>(json['chunkText']),
      faqQuestions: serializer.fromJson<String?>(json['faqQuestions']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'moduleId': serializer.toJson<String>(moduleId),
      'moduleCode': serializer.toJson<String>(moduleCode),
      'sectionId': serializer.toJson<String?>(sectionId),
      'sectionTitle': serializer.toJson<String?>(sectionTitle),
      'language': serializer.toJson<String>(language),
      'sourceTitle': serializer.toJson<String>(sourceTitle),
      'chunkText': serializer.toJson<String>(chunkText),
      'faqQuestions': serializer.toJson<String?>(faqQuestions),
    };
  }

  ContentChunkRow copyWith(
          {String? id,
          String? moduleId,
          String? moduleCode,
          Value<String?> sectionId = const Value.absent(),
          Value<String?> sectionTitle = const Value.absent(),
          String? language,
          String? sourceTitle,
          String? chunkText,
          Value<String?> faqQuestions = const Value.absent()}) =>
      ContentChunkRow(
        id: id ?? this.id,
        moduleId: moduleId ?? this.moduleId,
        moduleCode: moduleCode ?? this.moduleCode,
        sectionId: sectionId.present ? sectionId.value : this.sectionId,
        sectionTitle:
            sectionTitle.present ? sectionTitle.value : this.sectionTitle,
        language: language ?? this.language,
        sourceTitle: sourceTitle ?? this.sourceTitle,
        chunkText: chunkText ?? this.chunkText,
        faqQuestions:
            faqQuestions.present ? faqQuestions.value : this.faqQuestions,
      );
  ContentChunkRow copyWithCompanion(ContentChunksCompanion data) {
    return ContentChunkRow(
      id: data.id.present ? data.id.value : this.id,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      moduleCode:
          data.moduleCode.present ? data.moduleCode.value : this.moduleCode,
      sectionId: data.sectionId.present ? data.sectionId.value : this.sectionId,
      sectionTitle: data.sectionTitle.present
          ? data.sectionTitle.value
          : this.sectionTitle,
      language: data.language.present ? data.language.value : this.language,
      sourceTitle:
          data.sourceTitle.present ? data.sourceTitle.value : this.sourceTitle,
      chunkText: data.chunkText.present ? data.chunkText.value : this.chunkText,
      faqQuestions: data.faqQuestions.present
          ? data.faqQuestions.value
          : this.faqQuestions,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ContentChunkRow(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('moduleCode: $moduleCode, ')
          ..write('sectionId: $sectionId, ')
          ..write('sectionTitle: $sectionTitle, ')
          ..write('language: $language, ')
          ..write('sourceTitle: $sourceTitle, ')
          ..write('chunkText: $chunkText, ')
          ..write('faqQuestions: $faqQuestions')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, moduleId, moduleCode, sectionId,
      sectionTitle, language, sourceTitle, chunkText, faqQuestions);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ContentChunkRow &&
          other.id == this.id &&
          other.moduleId == this.moduleId &&
          other.moduleCode == this.moduleCode &&
          other.sectionId == this.sectionId &&
          other.sectionTitle == this.sectionTitle &&
          other.language == this.language &&
          other.sourceTitle == this.sourceTitle &&
          other.chunkText == this.chunkText &&
          other.faqQuestions == this.faqQuestions);
}

class ContentChunksCompanion extends UpdateCompanion<ContentChunkRow> {
  final Value<String> id;
  final Value<String> moduleId;
  final Value<String> moduleCode;
  final Value<String?> sectionId;
  final Value<String?> sectionTitle;
  final Value<String> language;
  final Value<String> sourceTitle;
  final Value<String> chunkText;
  final Value<String?> faqQuestions;
  final Value<int> rowid;
  const ContentChunksCompanion({
    this.id = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.moduleCode = const Value.absent(),
    this.sectionId = const Value.absent(),
    this.sectionTitle = const Value.absent(),
    this.language = const Value.absent(),
    this.sourceTitle = const Value.absent(),
    this.chunkText = const Value.absent(),
    this.faqQuestions = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ContentChunksCompanion.insert({
    required String id,
    required String moduleId,
    required String moduleCode,
    this.sectionId = const Value.absent(),
    this.sectionTitle = const Value.absent(),
    required String language,
    required String sourceTitle,
    required String chunkText,
    this.faqQuestions = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        moduleId = Value(moduleId),
        moduleCode = Value(moduleCode),
        language = Value(language),
        sourceTitle = Value(sourceTitle),
        chunkText = Value(chunkText);
  static Insertable<ContentChunkRow> custom({
    Expression<String>? id,
    Expression<String>? moduleId,
    Expression<String>? moduleCode,
    Expression<String>? sectionId,
    Expression<String>? sectionTitle,
    Expression<String>? language,
    Expression<String>? sourceTitle,
    Expression<String>? chunkText,
    Expression<String>? faqQuestions,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleId != null) 'module_id': moduleId,
      if (moduleCode != null) 'module_code': moduleCode,
      if (sectionId != null) 'section_id': sectionId,
      if (sectionTitle != null) 'section_title': sectionTitle,
      if (language != null) 'language': language,
      if (sourceTitle != null) 'source_title': sourceTitle,
      if (chunkText != null) 'chunk_text': chunkText,
      if (faqQuestions != null) 'faq_questions': faqQuestions,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ContentChunksCompanion copyWith(
      {Value<String>? id,
      Value<String>? moduleId,
      Value<String>? moduleCode,
      Value<String?>? sectionId,
      Value<String?>? sectionTitle,
      Value<String>? language,
      Value<String>? sourceTitle,
      Value<String>? chunkText,
      Value<String?>? faqQuestions,
      Value<int>? rowid}) {
    return ContentChunksCompanion(
      id: id ?? this.id,
      moduleId: moduleId ?? this.moduleId,
      moduleCode: moduleCode ?? this.moduleCode,
      sectionId: sectionId ?? this.sectionId,
      sectionTitle: sectionTitle ?? this.sectionTitle,
      language: language ?? this.language,
      sourceTitle: sourceTitle ?? this.sourceTitle,
      chunkText: chunkText ?? this.chunkText,
      faqQuestions: faqQuestions ?? this.faqQuestions,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (moduleCode.present) {
      map['module_code'] = Variable<String>(moduleCode.value);
    }
    if (sectionId.present) {
      map['section_id'] = Variable<String>(sectionId.value);
    }
    if (sectionTitle.present) {
      map['section_title'] = Variable<String>(sectionTitle.value);
    }
    if (language.present) {
      map['language'] = Variable<String>(language.value);
    }
    if (sourceTitle.present) {
      map['source_title'] = Variable<String>(sourceTitle.value);
    }
    if (chunkText.present) {
      map['chunk_text'] = Variable<String>(chunkText.value);
    }
    if (faqQuestions.present) {
      map['faq_questions'] = Variable<String>(faqQuestions.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ContentChunksCompanion(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('moduleCode: $moduleCode, ')
          ..write('sectionId: $sectionId, ')
          ..write('sectionTitle: $sectionTitle, ')
          ..write('language: $language, ')
          ..write('sourceTitle: $sourceTitle, ')
          ..write('chunkText: $chunkText, ')
          ..write('faqQuestions: $faqQuestions, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedQuizQuestionsTable extends CachedQuizQuestions
    with TableInfo<$CachedQuizQuestionsTable, CachedQuizQuestionRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedQuizQuestionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _questionTypeMeta =
      const VerificationMeta('questionType');
  @override
  late final GeneratedColumn<String> questionType = GeneratedColumn<String>(
      'question_type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _promptMeta = const VerificationMeta('prompt');
  @override
  late final GeneratedColumn<String> prompt = GeneratedColumn<String>(
      'prompt', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _contentJsonMeta =
      const VerificationMeta('contentJson');
  @override
  late final GeneratedColumn<String> contentJson = GeneratedColumn<String>(
      'content_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _explanationMeta =
      const VerificationMeta('explanation');
  @override
  late final GeneratedColumn<String> explanation = GeneratedColumn<String>(
      'explanation', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _sortOrderMeta =
      const VerificationMeta('sortOrder');
  @override
  late final GeneratedColumn<int> sortOrder = GeneratedColumn<int>(
      'sort_order', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _usageMeta = const VerificationMeta('usage');
  @override
  late final GeneratedColumn<String> usage = GeneratedColumn<String>(
      'usage', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('BOTH'));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        moduleId,
        questionType,
        prompt,
        contentJson,
        explanation,
        sortOrder,
        usage
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_quiz_questions';
  @override
  VerificationContext validateIntegrity(
      Insertable<CachedQuizQuestionRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('question_type')) {
      context.handle(
          _questionTypeMeta,
          questionType.isAcceptableOrUnknown(
              data['question_type']!, _questionTypeMeta));
    } else if (isInserting) {
      context.missing(_questionTypeMeta);
    }
    if (data.containsKey('prompt')) {
      context.handle(_promptMeta,
          prompt.isAcceptableOrUnknown(data['prompt']!, _promptMeta));
    } else if (isInserting) {
      context.missing(_promptMeta);
    }
    if (data.containsKey('content_json')) {
      context.handle(
          _contentJsonMeta,
          contentJson.isAcceptableOrUnknown(
              data['content_json']!, _contentJsonMeta));
    } else if (isInserting) {
      context.missing(_contentJsonMeta);
    }
    if (data.containsKey('explanation')) {
      context.handle(
          _explanationMeta,
          explanation.isAcceptableOrUnknown(
              data['explanation']!, _explanationMeta));
    }
    if (data.containsKey('sort_order')) {
      context.handle(_sortOrderMeta,
          sortOrder.isAcceptableOrUnknown(data['sort_order']!, _sortOrderMeta));
    } else if (isInserting) {
      context.missing(_sortOrderMeta);
    }
    if (data.containsKey('usage')) {
      context.handle(
          _usageMeta, usage.isAcceptableOrUnknown(data['usage']!, _usageMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedQuizQuestionRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedQuizQuestionRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      questionType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}question_type'])!,
      prompt: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}prompt'])!,
      contentJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}content_json'])!,
      explanation: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}explanation']),
      sortOrder: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}sort_order'])!,
      usage: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}usage'])!,
    );
  }

  @override
  $CachedQuizQuestionsTable createAlias(String alias) {
    return $CachedQuizQuestionsTable(attachedDatabase, alias);
  }
}

class CachedQuizQuestionRow extends DataClass
    implements Insertable<CachedQuizQuestionRow> {
  final String id;
  final String moduleId;
  final String questionType;
  final String prompt;
  final String contentJson;
  final String? explanation;
  final int sortOrder;
  final String usage;
  const CachedQuizQuestionRow(
      {required this.id,
      required this.moduleId,
      required this.questionType,
      required this.prompt,
      required this.contentJson,
      this.explanation,
      required this.sortOrder,
      required this.usage});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['module_id'] = Variable<String>(moduleId);
    map['question_type'] = Variable<String>(questionType);
    map['prompt'] = Variable<String>(prompt);
    map['content_json'] = Variable<String>(contentJson);
    if (!nullToAbsent || explanation != null) {
      map['explanation'] = Variable<String>(explanation);
    }
    map['sort_order'] = Variable<int>(sortOrder);
    map['usage'] = Variable<String>(usage);
    return map;
  }

  CachedQuizQuestionsCompanion toCompanion(bool nullToAbsent) {
    return CachedQuizQuestionsCompanion(
      id: Value(id),
      moduleId: Value(moduleId),
      questionType: Value(questionType),
      prompt: Value(prompt),
      contentJson: Value(contentJson),
      explanation: explanation == null && nullToAbsent
          ? const Value.absent()
          : Value(explanation),
      sortOrder: Value(sortOrder),
      usage: Value(usage),
    );
  }

  factory CachedQuizQuestionRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedQuizQuestionRow(
      id: serializer.fromJson<String>(json['id']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      questionType: serializer.fromJson<String>(json['questionType']),
      prompt: serializer.fromJson<String>(json['prompt']),
      contentJson: serializer.fromJson<String>(json['contentJson']),
      explanation: serializer.fromJson<String?>(json['explanation']),
      sortOrder: serializer.fromJson<int>(json['sortOrder']),
      usage: serializer.fromJson<String>(json['usage']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'moduleId': serializer.toJson<String>(moduleId),
      'questionType': serializer.toJson<String>(questionType),
      'prompt': serializer.toJson<String>(prompt),
      'contentJson': serializer.toJson<String>(contentJson),
      'explanation': serializer.toJson<String?>(explanation),
      'sortOrder': serializer.toJson<int>(sortOrder),
      'usage': serializer.toJson<String>(usage),
    };
  }

  CachedQuizQuestionRow copyWith(
          {String? id,
          String? moduleId,
          String? questionType,
          String? prompt,
          String? contentJson,
          Value<String?> explanation = const Value.absent(),
          int? sortOrder,
          String? usage}) =>
      CachedQuizQuestionRow(
        id: id ?? this.id,
        moduleId: moduleId ?? this.moduleId,
        questionType: questionType ?? this.questionType,
        prompt: prompt ?? this.prompt,
        contentJson: contentJson ?? this.contentJson,
        explanation: explanation.present ? explanation.value : this.explanation,
        sortOrder: sortOrder ?? this.sortOrder,
        usage: usage ?? this.usage,
      );
  CachedQuizQuestionRow copyWithCompanion(CachedQuizQuestionsCompanion data) {
    return CachedQuizQuestionRow(
      id: data.id.present ? data.id.value : this.id,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      questionType: data.questionType.present
          ? data.questionType.value
          : this.questionType,
      prompt: data.prompt.present ? data.prompt.value : this.prompt,
      contentJson:
          data.contentJson.present ? data.contentJson.value : this.contentJson,
      explanation:
          data.explanation.present ? data.explanation.value : this.explanation,
      sortOrder: data.sortOrder.present ? data.sortOrder.value : this.sortOrder,
      usage: data.usage.present ? data.usage.value : this.usage,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedQuizQuestionRow(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('questionType: $questionType, ')
          ..write('prompt: $prompt, ')
          ..write('contentJson: $contentJson, ')
          ..write('explanation: $explanation, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('usage: $usage')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, moduleId, questionType, prompt,
      contentJson, explanation, sortOrder, usage);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedQuizQuestionRow &&
          other.id == this.id &&
          other.moduleId == this.moduleId &&
          other.questionType == this.questionType &&
          other.prompt == this.prompt &&
          other.contentJson == this.contentJson &&
          other.explanation == this.explanation &&
          other.sortOrder == this.sortOrder &&
          other.usage == this.usage);
}

class CachedQuizQuestionsCompanion
    extends UpdateCompanion<CachedQuizQuestionRow> {
  final Value<String> id;
  final Value<String> moduleId;
  final Value<String> questionType;
  final Value<String> prompt;
  final Value<String> contentJson;
  final Value<String?> explanation;
  final Value<int> sortOrder;
  final Value<String> usage;
  final Value<int> rowid;
  const CachedQuizQuestionsCompanion({
    this.id = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.questionType = const Value.absent(),
    this.prompt = const Value.absent(),
    this.contentJson = const Value.absent(),
    this.explanation = const Value.absent(),
    this.sortOrder = const Value.absent(),
    this.usage = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedQuizQuestionsCompanion.insert({
    required String id,
    required String moduleId,
    required String questionType,
    required String prompt,
    required String contentJson,
    this.explanation = const Value.absent(),
    required int sortOrder,
    this.usage = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : id = Value(id),
        moduleId = Value(moduleId),
        questionType = Value(questionType),
        prompt = Value(prompt),
        contentJson = Value(contentJson),
        sortOrder = Value(sortOrder);
  static Insertable<CachedQuizQuestionRow> custom({
    Expression<String>? id,
    Expression<String>? moduleId,
    Expression<String>? questionType,
    Expression<String>? prompt,
    Expression<String>? contentJson,
    Expression<String>? explanation,
    Expression<int>? sortOrder,
    Expression<String>? usage,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (moduleId != null) 'module_id': moduleId,
      if (questionType != null) 'question_type': questionType,
      if (prompt != null) 'prompt': prompt,
      if (contentJson != null) 'content_json': contentJson,
      if (explanation != null) 'explanation': explanation,
      if (sortOrder != null) 'sort_order': sortOrder,
      if (usage != null) 'usage': usage,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedQuizQuestionsCompanion copyWith(
      {Value<String>? id,
      Value<String>? moduleId,
      Value<String>? questionType,
      Value<String>? prompt,
      Value<String>? contentJson,
      Value<String?>? explanation,
      Value<int>? sortOrder,
      Value<String>? usage,
      Value<int>? rowid}) {
    return CachedQuizQuestionsCompanion(
      id: id ?? this.id,
      moduleId: moduleId ?? this.moduleId,
      questionType: questionType ?? this.questionType,
      prompt: prompt ?? this.prompt,
      contentJson: contentJson ?? this.contentJson,
      explanation: explanation ?? this.explanation,
      sortOrder: sortOrder ?? this.sortOrder,
      usage: usage ?? this.usage,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (questionType.present) {
      map['question_type'] = Variable<String>(questionType.value);
    }
    if (prompt.present) {
      map['prompt'] = Variable<String>(prompt.value);
    }
    if (contentJson.present) {
      map['content_json'] = Variable<String>(contentJson.value);
    }
    if (explanation.present) {
      map['explanation'] = Variable<String>(explanation.value);
    }
    if (sortOrder.present) {
      map['sort_order'] = Variable<int>(sortOrder.value);
    }
    if (usage.present) {
      map['usage'] = Variable<String>(usage.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedQuizQuestionsCompanion(')
          ..write('id: $id, ')
          ..write('moduleId: $moduleId, ')
          ..write('questionType: $questionType, ')
          ..write('prompt: $prompt, ')
          ..write('contentJson: $contentJson, ')
          ..write('explanation: $explanation, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('usage: $usage, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalQuizAttemptsTable extends LocalQuizAttempts
    with TableInfo<$LocalQuizAttemptsTable, LocalQuizAttemptRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalQuizAttemptsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _userIdMeta = const VerificationMeta('userId');
  @override
  late final GeneratedColumn<String> userId = GeneratedColumn<String>(
      'user_id', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _clientIdMeta =
      const VerificationMeta('clientId');
  @override
  late final GeneratedColumn<String> clientId = GeneratedColumn<String>(
      'client_id', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: true,
      defaultConstraints: GeneratedColumn.constraintIsAlways('UNIQUE'));
  static const VerificationMeta _correctCountMeta =
      const VerificationMeta('correctCount');
  @override
  late final GeneratedColumn<int> correctCount = GeneratedColumn<int>(
      'correct_count', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _totalCountMeta =
      const VerificationMeta('totalCount');
  @override
  late final GeneratedColumn<int> totalCount = GeneratedColumn<int>(
      'total_count', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _scorePercentMeta =
      const VerificationMeta('scorePercent');
  @override
  late final GeneratedColumn<int> scorePercent = GeneratedColumn<int>(
      'score_percent', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _passedMeta = const VerificationMeta('passed');
  @override
  late final GeneratedColumn<bool> passed = GeneratedColumn<bool>(
      'passed', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: true,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("passed" IN (0, 1))'));
  static const VerificationMeta _resultsJsonMeta =
      const VerificationMeta('resultsJson');
  @override
  late final GeneratedColumn<String> resultsJson = GeneratedColumn<String>(
      'results_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _takenAtMeta =
      const VerificationMeta('takenAt');
  @override
  late final GeneratedColumn<DateTime> takenAt = GeneratedColumn<DateTime>(
      'taken_at', aliasedName, false,
      type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _syncedMeta = const VerificationMeta('synced');
  @override
  late final GeneratedColumn<bool> synced = GeneratedColumn<bool>(
      'synced', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("synced" IN (0, 1))'),
      defaultValue: const Constant(false));
  static const VerificationMeta _testTypeMeta =
      const VerificationMeta('testType');
  @override
  late final GeneratedColumn<String> testType = GeneratedColumn<String>(
      'test_type', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('POST'));
  static const VerificationMeta _serverValidMeta =
      const VerificationMeta('serverValid');
  @override
  late final GeneratedColumn<bool> serverValid = GeneratedColumn<bool>(
      'server_valid', aliasedName, true,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("server_valid" IN (0, 1))'));
  static const VerificationMeta _invalidReasonMeta =
      const VerificationMeta('invalidReason');
  @override
  late final GeneratedColumn<String> invalidReason = GeneratedColumn<String>(
      'invalid_reason', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        userId,
        moduleId,
        clientId,
        correctCount,
        totalCount,
        scorePercent,
        passed,
        resultsJson,
        takenAt,
        synced,
        testType,
        serverValid,
        invalidReason
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_quiz_attempts';
  @override
  VerificationContext validateIntegrity(
      Insertable<LocalQuizAttemptRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('user_id')) {
      context.handle(_userIdMeta,
          userId.isAcceptableOrUnknown(data['user_id']!, _userIdMeta));
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('client_id')) {
      context.handle(_clientIdMeta,
          clientId.isAcceptableOrUnknown(data['client_id']!, _clientIdMeta));
    } else if (isInserting) {
      context.missing(_clientIdMeta);
    }
    if (data.containsKey('correct_count')) {
      context.handle(
          _correctCountMeta,
          correctCount.isAcceptableOrUnknown(
              data['correct_count']!, _correctCountMeta));
    } else if (isInserting) {
      context.missing(_correctCountMeta);
    }
    if (data.containsKey('total_count')) {
      context.handle(
          _totalCountMeta,
          totalCount.isAcceptableOrUnknown(
              data['total_count']!, _totalCountMeta));
    } else if (isInserting) {
      context.missing(_totalCountMeta);
    }
    if (data.containsKey('score_percent')) {
      context.handle(
          _scorePercentMeta,
          scorePercent.isAcceptableOrUnknown(
              data['score_percent']!, _scorePercentMeta));
    } else if (isInserting) {
      context.missing(_scorePercentMeta);
    }
    if (data.containsKey('passed')) {
      context.handle(_passedMeta,
          passed.isAcceptableOrUnknown(data['passed']!, _passedMeta));
    } else if (isInserting) {
      context.missing(_passedMeta);
    }
    if (data.containsKey('results_json')) {
      context.handle(
          _resultsJsonMeta,
          resultsJson.isAcceptableOrUnknown(
              data['results_json']!, _resultsJsonMeta));
    } else if (isInserting) {
      context.missing(_resultsJsonMeta);
    }
    if (data.containsKey('taken_at')) {
      context.handle(_takenAtMeta,
          takenAt.isAcceptableOrUnknown(data['taken_at']!, _takenAtMeta));
    } else if (isInserting) {
      context.missing(_takenAtMeta);
    }
    if (data.containsKey('synced')) {
      context.handle(_syncedMeta,
          synced.isAcceptableOrUnknown(data['synced']!, _syncedMeta));
    }
    if (data.containsKey('test_type')) {
      context.handle(_testTypeMeta,
          testType.isAcceptableOrUnknown(data['test_type']!, _testTypeMeta));
    }
    if (data.containsKey('server_valid')) {
      context.handle(
          _serverValidMeta,
          serverValid.isAcceptableOrUnknown(
              data['server_valid']!, _serverValidMeta));
    }
    if (data.containsKey('invalid_reason')) {
      context.handle(
          _invalidReasonMeta,
          invalidReason.isAcceptableOrUnknown(
              data['invalid_reason']!, _invalidReasonMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalQuizAttemptRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalQuizAttemptRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      userId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}user_id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      clientId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}client_id'])!,
      correctCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}correct_count'])!,
      totalCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}total_count'])!,
      scorePercent: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}score_percent'])!,
      passed: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}passed'])!,
      resultsJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}results_json'])!,
      takenAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}taken_at'])!,
      synced: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}synced'])!,
      testType: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}test_type'])!,
      serverValid: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}server_valid']),
      invalidReason: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}invalid_reason']),
    );
  }

  @override
  $LocalQuizAttemptsTable createAlias(String alias) {
    return $LocalQuizAttemptsTable(attachedDatabase, alias);
  }
}

class LocalQuizAttemptRow extends DataClass
    implements Insertable<LocalQuizAttemptRow> {
  final int id;
  final String userId;
  final String moduleId;
  final String clientId;
  final int correctCount;
  final int totalCount;
  final int scorePercent;
  final bool passed;
  final String resultsJson;
  final DateTime takenAt;
  final bool synced;
  final String testType;
  final bool? serverValid;
  final String? invalidReason;
  const LocalQuizAttemptRow(
      {required this.id,
      required this.userId,
      required this.moduleId,
      required this.clientId,
      required this.correctCount,
      required this.totalCount,
      required this.scorePercent,
      required this.passed,
      required this.resultsJson,
      required this.takenAt,
      required this.synced,
      required this.testType,
      this.serverValid,
      this.invalidReason});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['user_id'] = Variable<String>(userId);
    map['module_id'] = Variable<String>(moduleId);
    map['client_id'] = Variable<String>(clientId);
    map['correct_count'] = Variable<int>(correctCount);
    map['total_count'] = Variable<int>(totalCount);
    map['score_percent'] = Variable<int>(scorePercent);
    map['passed'] = Variable<bool>(passed);
    map['results_json'] = Variable<String>(resultsJson);
    map['taken_at'] = Variable<DateTime>(takenAt);
    map['synced'] = Variable<bool>(synced);
    map['test_type'] = Variable<String>(testType);
    if (!nullToAbsent || serverValid != null) {
      map['server_valid'] = Variable<bool>(serverValid);
    }
    if (!nullToAbsent || invalidReason != null) {
      map['invalid_reason'] = Variable<String>(invalidReason);
    }
    return map;
  }

  LocalQuizAttemptsCompanion toCompanion(bool nullToAbsent) {
    return LocalQuizAttemptsCompanion(
      id: Value(id),
      userId: Value(userId),
      moduleId: Value(moduleId),
      clientId: Value(clientId),
      correctCount: Value(correctCount),
      totalCount: Value(totalCount),
      scorePercent: Value(scorePercent),
      passed: Value(passed),
      resultsJson: Value(resultsJson),
      takenAt: Value(takenAt),
      synced: Value(synced),
      testType: Value(testType),
      serverValid: serverValid == null && nullToAbsent
          ? const Value.absent()
          : Value(serverValid),
      invalidReason: invalidReason == null && nullToAbsent
          ? const Value.absent()
          : Value(invalidReason),
    );
  }

  factory LocalQuizAttemptRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalQuizAttemptRow(
      id: serializer.fromJson<int>(json['id']),
      userId: serializer.fromJson<String>(json['userId']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      clientId: serializer.fromJson<String>(json['clientId']),
      correctCount: serializer.fromJson<int>(json['correctCount']),
      totalCount: serializer.fromJson<int>(json['totalCount']),
      scorePercent: serializer.fromJson<int>(json['scorePercent']),
      passed: serializer.fromJson<bool>(json['passed']),
      resultsJson: serializer.fromJson<String>(json['resultsJson']),
      takenAt: serializer.fromJson<DateTime>(json['takenAt']),
      synced: serializer.fromJson<bool>(json['synced']),
      testType: serializer.fromJson<String>(json['testType']),
      serverValid: serializer.fromJson<bool?>(json['serverValid']),
      invalidReason: serializer.fromJson<String?>(json['invalidReason']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'userId': serializer.toJson<String>(userId),
      'moduleId': serializer.toJson<String>(moduleId),
      'clientId': serializer.toJson<String>(clientId),
      'correctCount': serializer.toJson<int>(correctCount),
      'totalCount': serializer.toJson<int>(totalCount),
      'scorePercent': serializer.toJson<int>(scorePercent),
      'passed': serializer.toJson<bool>(passed),
      'resultsJson': serializer.toJson<String>(resultsJson),
      'takenAt': serializer.toJson<DateTime>(takenAt),
      'synced': serializer.toJson<bool>(synced),
      'testType': serializer.toJson<String>(testType),
      'serverValid': serializer.toJson<bool?>(serverValid),
      'invalidReason': serializer.toJson<String?>(invalidReason),
    };
  }

  LocalQuizAttemptRow copyWith(
          {int? id,
          String? userId,
          String? moduleId,
          String? clientId,
          int? correctCount,
          int? totalCount,
          int? scorePercent,
          bool? passed,
          String? resultsJson,
          DateTime? takenAt,
          bool? synced,
          String? testType,
          Value<bool?> serverValid = const Value.absent(),
          Value<String?> invalidReason = const Value.absent()}) =>
      LocalQuizAttemptRow(
        id: id ?? this.id,
        userId: userId ?? this.userId,
        moduleId: moduleId ?? this.moduleId,
        clientId: clientId ?? this.clientId,
        correctCount: correctCount ?? this.correctCount,
        totalCount: totalCount ?? this.totalCount,
        scorePercent: scorePercent ?? this.scorePercent,
        passed: passed ?? this.passed,
        resultsJson: resultsJson ?? this.resultsJson,
        takenAt: takenAt ?? this.takenAt,
        synced: synced ?? this.synced,
        testType: testType ?? this.testType,
        serverValid: serverValid.present ? serverValid.value : this.serverValid,
        invalidReason:
            invalidReason.present ? invalidReason.value : this.invalidReason,
      );
  LocalQuizAttemptRow copyWithCompanion(LocalQuizAttemptsCompanion data) {
    return LocalQuizAttemptRow(
      id: data.id.present ? data.id.value : this.id,
      userId: data.userId.present ? data.userId.value : this.userId,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      clientId: data.clientId.present ? data.clientId.value : this.clientId,
      correctCount: data.correctCount.present
          ? data.correctCount.value
          : this.correctCount,
      totalCount:
          data.totalCount.present ? data.totalCount.value : this.totalCount,
      scorePercent: data.scorePercent.present
          ? data.scorePercent.value
          : this.scorePercent,
      passed: data.passed.present ? data.passed.value : this.passed,
      resultsJson:
          data.resultsJson.present ? data.resultsJson.value : this.resultsJson,
      takenAt: data.takenAt.present ? data.takenAt.value : this.takenAt,
      synced: data.synced.present ? data.synced.value : this.synced,
      testType: data.testType.present ? data.testType.value : this.testType,
      serverValid:
          data.serverValid.present ? data.serverValid.value : this.serverValid,
      invalidReason: data.invalidReason.present
          ? data.invalidReason.value
          : this.invalidReason,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalQuizAttemptRow(')
          ..write('id: $id, ')
          ..write('userId: $userId, ')
          ..write('moduleId: $moduleId, ')
          ..write('clientId: $clientId, ')
          ..write('correctCount: $correctCount, ')
          ..write('totalCount: $totalCount, ')
          ..write('scorePercent: $scorePercent, ')
          ..write('passed: $passed, ')
          ..write('resultsJson: $resultsJson, ')
          ..write('takenAt: $takenAt, ')
          ..write('synced: $synced, ')
          ..write('testType: $testType, ')
          ..write('serverValid: $serverValid, ')
          ..write('invalidReason: $invalidReason')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      id,
      userId,
      moduleId,
      clientId,
      correctCount,
      totalCount,
      scorePercent,
      passed,
      resultsJson,
      takenAt,
      synced,
      testType,
      serverValid,
      invalidReason);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalQuizAttemptRow &&
          other.id == this.id &&
          other.userId == this.userId &&
          other.moduleId == this.moduleId &&
          other.clientId == this.clientId &&
          other.correctCount == this.correctCount &&
          other.totalCount == this.totalCount &&
          other.scorePercent == this.scorePercent &&
          other.passed == this.passed &&
          other.resultsJson == this.resultsJson &&
          other.takenAt == this.takenAt &&
          other.synced == this.synced &&
          other.testType == this.testType &&
          other.serverValid == this.serverValid &&
          other.invalidReason == this.invalidReason);
}

class LocalQuizAttemptsCompanion extends UpdateCompanion<LocalQuizAttemptRow> {
  final Value<int> id;
  final Value<String> userId;
  final Value<String> moduleId;
  final Value<String> clientId;
  final Value<int> correctCount;
  final Value<int> totalCount;
  final Value<int> scorePercent;
  final Value<bool> passed;
  final Value<String> resultsJson;
  final Value<DateTime> takenAt;
  final Value<bool> synced;
  final Value<String> testType;
  final Value<bool?> serverValid;
  final Value<String?> invalidReason;
  const LocalQuizAttemptsCompanion({
    this.id = const Value.absent(),
    this.userId = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.clientId = const Value.absent(),
    this.correctCount = const Value.absent(),
    this.totalCount = const Value.absent(),
    this.scorePercent = const Value.absent(),
    this.passed = const Value.absent(),
    this.resultsJson = const Value.absent(),
    this.takenAt = const Value.absent(),
    this.synced = const Value.absent(),
    this.testType = const Value.absent(),
    this.serverValid = const Value.absent(),
    this.invalidReason = const Value.absent(),
  });
  LocalQuizAttemptsCompanion.insert({
    this.id = const Value.absent(),
    this.userId = const Value.absent(),
    required String moduleId,
    required String clientId,
    required int correctCount,
    required int totalCount,
    required int scorePercent,
    required bool passed,
    required String resultsJson,
    required DateTime takenAt,
    this.synced = const Value.absent(),
    this.testType = const Value.absent(),
    this.serverValid = const Value.absent(),
    this.invalidReason = const Value.absent(),
  })  : moduleId = Value(moduleId),
        clientId = Value(clientId),
        correctCount = Value(correctCount),
        totalCount = Value(totalCount),
        scorePercent = Value(scorePercent),
        passed = Value(passed),
        resultsJson = Value(resultsJson),
        takenAt = Value(takenAt);
  static Insertable<LocalQuizAttemptRow> custom({
    Expression<int>? id,
    Expression<String>? userId,
    Expression<String>? moduleId,
    Expression<String>? clientId,
    Expression<int>? correctCount,
    Expression<int>? totalCount,
    Expression<int>? scorePercent,
    Expression<bool>? passed,
    Expression<String>? resultsJson,
    Expression<DateTime>? takenAt,
    Expression<bool>? synced,
    Expression<String>? testType,
    Expression<bool>? serverValid,
    Expression<String>? invalidReason,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (userId != null) 'user_id': userId,
      if (moduleId != null) 'module_id': moduleId,
      if (clientId != null) 'client_id': clientId,
      if (correctCount != null) 'correct_count': correctCount,
      if (totalCount != null) 'total_count': totalCount,
      if (scorePercent != null) 'score_percent': scorePercent,
      if (passed != null) 'passed': passed,
      if (resultsJson != null) 'results_json': resultsJson,
      if (takenAt != null) 'taken_at': takenAt,
      if (synced != null) 'synced': synced,
      if (testType != null) 'test_type': testType,
      if (serverValid != null) 'server_valid': serverValid,
      if (invalidReason != null) 'invalid_reason': invalidReason,
    });
  }

  LocalQuizAttemptsCompanion copyWith(
      {Value<int>? id,
      Value<String>? userId,
      Value<String>? moduleId,
      Value<String>? clientId,
      Value<int>? correctCount,
      Value<int>? totalCount,
      Value<int>? scorePercent,
      Value<bool>? passed,
      Value<String>? resultsJson,
      Value<DateTime>? takenAt,
      Value<bool>? synced,
      Value<String>? testType,
      Value<bool?>? serverValid,
      Value<String?>? invalidReason}) {
    return LocalQuizAttemptsCompanion(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      moduleId: moduleId ?? this.moduleId,
      clientId: clientId ?? this.clientId,
      correctCount: correctCount ?? this.correctCount,
      totalCount: totalCount ?? this.totalCount,
      scorePercent: scorePercent ?? this.scorePercent,
      passed: passed ?? this.passed,
      resultsJson: resultsJson ?? this.resultsJson,
      takenAt: takenAt ?? this.takenAt,
      synced: synced ?? this.synced,
      testType: testType ?? this.testType,
      serverValid: serverValid ?? this.serverValid,
      invalidReason: invalidReason ?? this.invalidReason,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (userId.present) {
      map['user_id'] = Variable<String>(userId.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (clientId.present) {
      map['client_id'] = Variable<String>(clientId.value);
    }
    if (correctCount.present) {
      map['correct_count'] = Variable<int>(correctCount.value);
    }
    if (totalCount.present) {
      map['total_count'] = Variable<int>(totalCount.value);
    }
    if (scorePercent.present) {
      map['score_percent'] = Variable<int>(scorePercent.value);
    }
    if (passed.present) {
      map['passed'] = Variable<bool>(passed.value);
    }
    if (resultsJson.present) {
      map['results_json'] = Variable<String>(resultsJson.value);
    }
    if (takenAt.present) {
      map['taken_at'] = Variable<DateTime>(takenAt.value);
    }
    if (synced.present) {
      map['synced'] = Variable<bool>(synced.value);
    }
    if (testType.present) {
      map['test_type'] = Variable<String>(testType.value);
    }
    if (serverValid.present) {
      map['server_valid'] = Variable<bool>(serverValid.value);
    }
    if (invalidReason.present) {
      map['invalid_reason'] = Variable<String>(invalidReason.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalQuizAttemptsCompanion(')
          ..write('id: $id, ')
          ..write('userId: $userId, ')
          ..write('moduleId: $moduleId, ')
          ..write('clientId: $clientId, ')
          ..write('correctCount: $correctCount, ')
          ..write('totalCount: $totalCount, ')
          ..write('scorePercent: $scorePercent, ')
          ..write('passed: $passed, ')
          ..write('resultsJson: $resultsJson, ')
          ..write('takenAt: $takenAt, ')
          ..write('synced: $synced, ')
          ..write('testType: $testType, ')
          ..write('serverValid: $serverValid, ')
          ..write('invalidReason: $invalidReason')
          ..write(')'))
        .toString();
  }
}

class $CachedSectionTranslationsTable extends CachedSectionTranslations
    with
        TableInfo<$CachedSectionTranslationsTable,
            CachedSectionTranslationRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedSectionTranslationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _sectionIdMeta =
      const VerificationMeta('sectionId');
  @override
  late final GeneratedColumn<String> sectionId = GeneratedColumn<String>(
      'section_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _moduleIdMeta =
      const VerificationMeta('moduleId');
  @override
  late final GeneratedColumn<String> moduleId = GeneratedColumn<String>(
      'module_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _languageCodeMeta =
      const VerificationMeta('languageCode');
  @override
  late final GeneratedColumn<String> languageCode = GeneratedColumn<String>(
      'language_code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _contentJsonMeta =
      const VerificationMeta('contentJson');
  @override
  late final GeneratedColumn<String> contentJson = GeneratedColumn<String>(
      'content_json', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns =>
      [sectionId, moduleId, languageCode, title, contentJson];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_section_translations';
  @override
  VerificationContext validateIntegrity(
      Insertable<CachedSectionTranslationRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('section_id')) {
      context.handle(_sectionIdMeta,
          sectionId.isAcceptableOrUnknown(data['section_id']!, _sectionIdMeta));
    } else if (isInserting) {
      context.missing(_sectionIdMeta);
    }
    if (data.containsKey('module_id')) {
      context.handle(_moduleIdMeta,
          moduleId.isAcceptableOrUnknown(data['module_id']!, _moduleIdMeta));
    } else if (isInserting) {
      context.missing(_moduleIdMeta);
    }
    if (data.containsKey('language_code')) {
      context.handle(
          _languageCodeMeta,
          languageCode.isAcceptableOrUnknown(
              data['language_code']!, _languageCodeMeta));
    } else if (isInserting) {
      context.missing(_languageCodeMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    }
    if (data.containsKey('content_json')) {
      context.handle(
          _contentJsonMeta,
          contentJson.isAcceptableOrUnknown(
              data['content_json']!, _contentJsonMeta));
    } else if (isInserting) {
      context.missing(_contentJsonMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {sectionId, languageCode};
  @override
  CachedSectionTranslationRow map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedSectionTranslationRow(
      sectionId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}section_id'])!,
      moduleId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}module_id'])!,
      languageCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}language_code'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title']),
      contentJson: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}content_json'])!,
    );
  }

  @override
  $CachedSectionTranslationsTable createAlias(String alias) {
    return $CachedSectionTranslationsTable(attachedDatabase, alias);
  }
}

class CachedSectionTranslationRow extends DataClass
    implements Insertable<CachedSectionTranslationRow> {
  final String sectionId;
  final String moduleId;
  final String languageCode;
  final String? title;
  final String contentJson;
  const CachedSectionTranslationRow(
      {required this.sectionId,
      required this.moduleId,
      required this.languageCode,
      this.title,
      required this.contentJson});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['section_id'] = Variable<String>(sectionId);
    map['module_id'] = Variable<String>(moduleId);
    map['language_code'] = Variable<String>(languageCode);
    if (!nullToAbsent || title != null) {
      map['title'] = Variable<String>(title);
    }
    map['content_json'] = Variable<String>(contentJson);
    return map;
  }

  CachedSectionTranslationsCompanion toCompanion(bool nullToAbsent) {
    return CachedSectionTranslationsCompanion(
      sectionId: Value(sectionId),
      moduleId: Value(moduleId),
      languageCode: Value(languageCode),
      title:
          title == null && nullToAbsent ? const Value.absent() : Value(title),
      contentJson: Value(contentJson),
    );
  }

  factory CachedSectionTranslationRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedSectionTranslationRow(
      sectionId: serializer.fromJson<String>(json['sectionId']),
      moduleId: serializer.fromJson<String>(json['moduleId']),
      languageCode: serializer.fromJson<String>(json['languageCode']),
      title: serializer.fromJson<String?>(json['title']),
      contentJson: serializer.fromJson<String>(json['contentJson']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'sectionId': serializer.toJson<String>(sectionId),
      'moduleId': serializer.toJson<String>(moduleId),
      'languageCode': serializer.toJson<String>(languageCode),
      'title': serializer.toJson<String?>(title),
      'contentJson': serializer.toJson<String>(contentJson),
    };
  }

  CachedSectionTranslationRow copyWith(
          {String? sectionId,
          String? moduleId,
          String? languageCode,
          Value<String?> title = const Value.absent(),
          String? contentJson}) =>
      CachedSectionTranslationRow(
        sectionId: sectionId ?? this.sectionId,
        moduleId: moduleId ?? this.moduleId,
        languageCode: languageCode ?? this.languageCode,
        title: title.present ? title.value : this.title,
        contentJson: contentJson ?? this.contentJson,
      );
  CachedSectionTranslationRow copyWithCompanion(
      CachedSectionTranslationsCompanion data) {
    return CachedSectionTranslationRow(
      sectionId: data.sectionId.present ? data.sectionId.value : this.sectionId,
      moduleId: data.moduleId.present ? data.moduleId.value : this.moduleId,
      languageCode: data.languageCode.present
          ? data.languageCode.value
          : this.languageCode,
      title: data.title.present ? data.title.value : this.title,
      contentJson:
          data.contentJson.present ? data.contentJson.value : this.contentJson,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedSectionTranslationRow(')
          ..write('sectionId: $sectionId, ')
          ..write('moduleId: $moduleId, ')
          ..write('languageCode: $languageCode, ')
          ..write('title: $title, ')
          ..write('contentJson: $contentJson')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(sectionId, moduleId, languageCode, title, contentJson);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedSectionTranslationRow &&
          other.sectionId == this.sectionId &&
          other.moduleId == this.moduleId &&
          other.languageCode == this.languageCode &&
          other.title == this.title &&
          other.contentJson == this.contentJson);
}

class CachedSectionTranslationsCompanion
    extends UpdateCompanion<CachedSectionTranslationRow> {
  final Value<String> sectionId;
  final Value<String> moduleId;
  final Value<String> languageCode;
  final Value<String?> title;
  final Value<String> contentJson;
  final Value<int> rowid;
  const CachedSectionTranslationsCompanion({
    this.sectionId = const Value.absent(),
    this.moduleId = const Value.absent(),
    this.languageCode = const Value.absent(),
    this.title = const Value.absent(),
    this.contentJson = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedSectionTranslationsCompanion.insert({
    required String sectionId,
    required String moduleId,
    required String languageCode,
    this.title = const Value.absent(),
    required String contentJson,
    this.rowid = const Value.absent(),
  })  : sectionId = Value(sectionId),
        moduleId = Value(moduleId),
        languageCode = Value(languageCode),
        contentJson = Value(contentJson);
  static Insertable<CachedSectionTranslationRow> custom({
    Expression<String>? sectionId,
    Expression<String>? moduleId,
    Expression<String>? languageCode,
    Expression<String>? title,
    Expression<String>? contentJson,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (sectionId != null) 'section_id': sectionId,
      if (moduleId != null) 'module_id': moduleId,
      if (languageCode != null) 'language_code': languageCode,
      if (title != null) 'title': title,
      if (contentJson != null) 'content_json': contentJson,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedSectionTranslationsCompanion copyWith(
      {Value<String>? sectionId,
      Value<String>? moduleId,
      Value<String>? languageCode,
      Value<String?>? title,
      Value<String>? contentJson,
      Value<int>? rowid}) {
    return CachedSectionTranslationsCompanion(
      sectionId: sectionId ?? this.sectionId,
      moduleId: moduleId ?? this.moduleId,
      languageCode: languageCode ?? this.languageCode,
      title: title ?? this.title,
      contentJson: contentJson ?? this.contentJson,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (sectionId.present) {
      map['section_id'] = Variable<String>(sectionId.value);
    }
    if (moduleId.present) {
      map['module_id'] = Variable<String>(moduleId.value);
    }
    if (languageCode.present) {
      map['language_code'] = Variable<String>(languageCode.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (contentJson.present) {
      map['content_json'] = Variable<String>(contentJson.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedSectionTranslationsCompanion(')
          ..write('sectionId: $sectionId, ')
          ..write('moduleId: $moduleId, ')
          ..write('languageCode: $languageCode, ')
          ..write('title: $title, ')
          ..write('contentJson: $contentJson, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$LocalDatabase extends GeneratedDatabase {
  _$LocalDatabase(QueryExecutor e) : super(e);
  $LocalDatabaseManager get managers => $LocalDatabaseManager(this);
  late final $CachedModulesTable cachedModules = $CachedModulesTable(this);
  late final $CachedTranslationsTable cachedTranslations =
      $CachedTranslationsTable(this);
  late final $CachedSectionsTable cachedSections = $CachedSectionsTable(this);
  late final $CachedMediaTable cachedMedia = $CachedMediaTable(this);
  late final $CachedVideosTable cachedVideos = $CachedVideosTable(this);
  late final $LocalProgressTable localProgress = $LocalProgressTable(this);
  late final $PendingSyncTable pendingSync = $PendingSyncTable(this);
  late final $AppSettingsTable appSettings = $AppSettingsTable(this);
  late final $InstalledReleasesTable installedReleases =
      $InstalledReleasesTable(this);
  late final $LocalAiQuestionsTable localAiQuestions =
      $LocalAiQuestionsTable(this);
  late final $RagMetadataTable ragMetadata = $RagMetadataTable(this);
  late final $ContentChunksTable contentChunks = $ContentChunksTable(this);
  late final $CachedQuizQuestionsTable cachedQuizQuestions =
      $CachedQuizQuestionsTable(this);
  late final $LocalQuizAttemptsTable localQuizAttempts =
      $LocalQuizAttemptsTable(this);
  late final $CachedSectionTranslationsTable cachedSectionTranslations =
      $CachedSectionTranslationsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
        cachedModules,
        cachedTranslations,
        cachedSections,
        cachedMedia,
        cachedVideos,
        localProgress,
        pendingSync,
        appSettings,
        installedReleases,
        localAiQuestions,
        ragMetadata,
        contentChunks,
        cachedQuizQuestions,
        localQuizAttempts,
        cachedSectionTranslations
      ];
}

typedef $$CachedModulesTableCreateCompanionBuilder = CachedModulesCompanion
    Function({
  required String id,
  required String moduleCode,
  required int moduleNumber,
  required String title,
  Value<String?> description,
  required String status,
  required int sortOrder,
  required DateTime cachedAt,
  Value<String> audience,
  Value<String> learnerRolesJson,
  Value<int> rowid,
});
typedef $$CachedModulesTableUpdateCompanionBuilder = CachedModulesCompanion
    Function({
  Value<String> id,
  Value<String> moduleCode,
  Value<int> moduleNumber,
  Value<String> title,
  Value<String?> description,
  Value<String> status,
  Value<int> sortOrder,
  Value<DateTime> cachedAt,
  Value<String> audience,
  Value<String> learnerRolesJson,
  Value<int> rowid,
});

class $$CachedModulesTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedModulesTable> {
  $$CachedModulesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleCode => $composableBuilder(
      column: $table.moduleCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get moduleNumber => $composableBuilder(
      column: $table.moduleNumber, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get audience => $composableBuilder(
      column: $table.audience, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get learnerRolesJson => $composableBuilder(
      column: $table.learnerRolesJson,
      builder: (column) => ColumnFilters(column));
}

class $$CachedModulesTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedModulesTable> {
  $$CachedModulesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleCode => $composableBuilder(
      column: $table.moduleCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get moduleNumber => $composableBuilder(
      column: $table.moduleNumber,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get cachedAt => $composableBuilder(
      column: $table.cachedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get audience => $composableBuilder(
      column: $table.audience, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get learnerRolesJson => $composableBuilder(
      column: $table.learnerRolesJson,
      builder: (column) => ColumnOrderings(column));
}

class $$CachedModulesTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedModulesTable> {
  $$CachedModulesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleCode => $composableBuilder(
      column: $table.moduleCode, builder: (column) => column);

  GeneratedColumn<int> get moduleNumber => $composableBuilder(
      column: $table.moduleNumber, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<int> get sortOrder =>
      $composableBuilder(column: $table.sortOrder, builder: (column) => column);

  GeneratedColumn<DateTime> get cachedAt =>
      $composableBuilder(column: $table.cachedAt, builder: (column) => column);

  GeneratedColumn<String> get audience =>
      $composableBuilder(column: $table.audience, builder: (column) => column);

  GeneratedColumn<String> get learnerRolesJson => $composableBuilder(
      column: $table.learnerRolesJson, builder: (column) => column);
}

class $$CachedModulesTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedModulesTable,
    CachedModuleRow,
    $$CachedModulesTableFilterComposer,
    $$CachedModulesTableOrderingComposer,
    $$CachedModulesTableAnnotationComposer,
    $$CachedModulesTableCreateCompanionBuilder,
    $$CachedModulesTableUpdateCompanionBuilder,
    (
      CachedModuleRow,
      BaseReferences<_$LocalDatabase, $CachedModulesTable, CachedModuleRow>
    ),
    CachedModuleRow,
    PrefetchHooks Function()> {
  $$CachedModulesTableTableManager(
      _$LocalDatabase db, $CachedModulesTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedModulesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedModulesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedModulesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> moduleCode = const Value.absent(),
            Value<int> moduleNumber = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String?> description = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<int> sortOrder = const Value.absent(),
            Value<DateTime> cachedAt = const Value.absent(),
            Value<String> audience = const Value.absent(),
            Value<String> learnerRolesJson = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedModulesCompanion(
            id: id,
            moduleCode: moduleCode,
            moduleNumber: moduleNumber,
            title: title,
            description: description,
            status: status,
            sortOrder: sortOrder,
            cachedAt: cachedAt,
            audience: audience,
            learnerRolesJson: learnerRolesJson,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String moduleCode,
            required int moduleNumber,
            required String title,
            Value<String?> description = const Value.absent(),
            required String status,
            required int sortOrder,
            required DateTime cachedAt,
            Value<String> audience = const Value.absent(),
            Value<String> learnerRolesJson = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedModulesCompanion.insert(
            id: id,
            moduleCode: moduleCode,
            moduleNumber: moduleNumber,
            title: title,
            description: description,
            status: status,
            sortOrder: sortOrder,
            cachedAt: cachedAt,
            audience: audience,
            learnerRolesJson: learnerRolesJson,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedModulesTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedModulesTable,
    CachedModuleRow,
    $$CachedModulesTableFilterComposer,
    $$CachedModulesTableOrderingComposer,
    $$CachedModulesTableAnnotationComposer,
    $$CachedModulesTableCreateCompanionBuilder,
    $$CachedModulesTableUpdateCompanionBuilder,
    (
      CachedModuleRow,
      BaseReferences<_$LocalDatabase, $CachedModulesTable, CachedModuleRow>
    ),
    CachedModuleRow,
    PrefetchHooks Function()>;
typedef $$CachedTranslationsTableCreateCompanionBuilder
    = CachedTranslationsCompanion Function({
  required String id,
  required String moduleId,
  required String languageId,
  required String languageCode,
  required String title,
  Value<String?> description,
  Value<String?> body,
  Value<String?> audioText,
  required String status,
  Value<int> rowid,
});
typedef $$CachedTranslationsTableUpdateCompanionBuilder
    = CachedTranslationsCompanion Function({
  Value<String> id,
  Value<String> moduleId,
  Value<String> languageId,
  Value<String> languageCode,
  Value<String> title,
  Value<String?> description,
  Value<String?> body,
  Value<String?> audioText,
  Value<String> status,
  Value<int> rowid,
});

class $$CachedTranslationsTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedTranslationsTable> {
  $$CachedTranslationsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get languageId => $composableBuilder(
      column: $table.languageId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get languageCode => $composableBuilder(
      column: $table.languageCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get body => $composableBuilder(
      column: $table.body, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get audioText => $composableBuilder(
      column: $table.audioText, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));
}

class $$CachedTranslationsTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedTranslationsTable> {
  $$CachedTranslationsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get languageId => $composableBuilder(
      column: $table.languageId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get languageCode => $composableBuilder(
      column: $table.languageCode,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get body => $composableBuilder(
      column: $table.body, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get audioText => $composableBuilder(
      column: $table.audioText, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));
}

class $$CachedTranslationsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedTranslationsTable> {
  $$CachedTranslationsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<String> get languageId => $composableBuilder(
      column: $table.languageId, builder: (column) => column);

  GeneratedColumn<String> get languageCode => $composableBuilder(
      column: $table.languageCode, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get body =>
      $composableBuilder(column: $table.body, builder: (column) => column);

  GeneratedColumn<String> get audioText =>
      $composableBuilder(column: $table.audioText, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);
}

class $$CachedTranslationsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedTranslationsTable,
    CachedTranslationRow,
    $$CachedTranslationsTableFilterComposer,
    $$CachedTranslationsTableOrderingComposer,
    $$CachedTranslationsTableAnnotationComposer,
    $$CachedTranslationsTableCreateCompanionBuilder,
    $$CachedTranslationsTableUpdateCompanionBuilder,
    (
      CachedTranslationRow,
      BaseReferences<_$LocalDatabase, $CachedTranslationsTable,
          CachedTranslationRow>
    ),
    CachedTranslationRow,
    PrefetchHooks Function()> {
  $$CachedTranslationsTableTableManager(
      _$LocalDatabase db, $CachedTranslationsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedTranslationsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedTranslationsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedTranslationsTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<String> languageId = const Value.absent(),
            Value<String> languageCode = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String?> description = const Value.absent(),
            Value<String?> body = const Value.absent(),
            Value<String?> audioText = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedTranslationsCompanion(
            id: id,
            moduleId: moduleId,
            languageId: languageId,
            languageCode: languageCode,
            title: title,
            description: description,
            body: body,
            audioText: audioText,
            status: status,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String moduleId,
            required String languageId,
            required String languageCode,
            required String title,
            Value<String?> description = const Value.absent(),
            Value<String?> body = const Value.absent(),
            Value<String?> audioText = const Value.absent(),
            required String status,
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedTranslationsCompanion.insert(
            id: id,
            moduleId: moduleId,
            languageId: languageId,
            languageCode: languageCode,
            title: title,
            description: description,
            body: body,
            audioText: audioText,
            status: status,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedTranslationsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedTranslationsTable,
    CachedTranslationRow,
    $$CachedTranslationsTableFilterComposer,
    $$CachedTranslationsTableOrderingComposer,
    $$CachedTranslationsTableAnnotationComposer,
    $$CachedTranslationsTableCreateCompanionBuilder,
    $$CachedTranslationsTableUpdateCompanionBuilder,
    (
      CachedTranslationRow,
      BaseReferences<_$LocalDatabase, $CachedTranslationsTable,
          CachedTranslationRow>
    ),
    CachedTranslationRow,
    PrefetchHooks Function()>;
typedef $$CachedSectionsTableCreateCompanionBuilder = CachedSectionsCompanion
    Function({
  required String id,
  required String moduleId,
  required int sectionNumber,
  Value<String?> title,
  required String contentType,
  required String contentJson,
  required int sortOrder,
  Value<int> rowid,
});
typedef $$CachedSectionsTableUpdateCompanionBuilder = CachedSectionsCompanion
    Function({
  Value<String> id,
  Value<String> moduleId,
  Value<int> sectionNumber,
  Value<String?> title,
  Value<String> contentType,
  Value<String> contentJson,
  Value<int> sortOrder,
  Value<int> rowid,
});

class $$CachedSectionsTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedSectionsTable> {
  $$CachedSectionsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sectionNumber => $composableBuilder(
      column: $table.sectionNumber, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get contentType => $composableBuilder(
      column: $table.contentType, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnFilters(column));
}

class $$CachedSectionsTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedSectionsTable> {
  $$CachedSectionsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sectionNumber => $composableBuilder(
      column: $table.sectionNumber,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get contentType => $composableBuilder(
      column: $table.contentType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnOrderings(column));
}

class $$CachedSectionsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedSectionsTable> {
  $$CachedSectionsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<int> get sectionNumber => $composableBuilder(
      column: $table.sectionNumber, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get contentType => $composableBuilder(
      column: $table.contentType, builder: (column) => column);

  GeneratedColumn<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => column);

  GeneratedColumn<int> get sortOrder =>
      $composableBuilder(column: $table.sortOrder, builder: (column) => column);
}

class $$CachedSectionsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedSectionsTable,
    CachedSectionRow,
    $$CachedSectionsTableFilterComposer,
    $$CachedSectionsTableOrderingComposer,
    $$CachedSectionsTableAnnotationComposer,
    $$CachedSectionsTableCreateCompanionBuilder,
    $$CachedSectionsTableUpdateCompanionBuilder,
    (
      CachedSectionRow,
      BaseReferences<_$LocalDatabase, $CachedSectionsTable, CachedSectionRow>
    ),
    CachedSectionRow,
    PrefetchHooks Function()> {
  $$CachedSectionsTableTableManager(
      _$LocalDatabase db, $CachedSectionsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedSectionsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedSectionsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedSectionsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<int> sectionNumber = const Value.absent(),
            Value<String?> title = const Value.absent(),
            Value<String> contentType = const Value.absent(),
            Value<String> contentJson = const Value.absent(),
            Value<int> sortOrder = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedSectionsCompanion(
            id: id,
            moduleId: moduleId,
            sectionNumber: sectionNumber,
            title: title,
            contentType: contentType,
            contentJson: contentJson,
            sortOrder: sortOrder,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String moduleId,
            required int sectionNumber,
            Value<String?> title = const Value.absent(),
            required String contentType,
            required String contentJson,
            required int sortOrder,
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedSectionsCompanion.insert(
            id: id,
            moduleId: moduleId,
            sectionNumber: sectionNumber,
            title: title,
            contentType: contentType,
            contentJson: contentJson,
            sortOrder: sortOrder,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedSectionsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedSectionsTable,
    CachedSectionRow,
    $$CachedSectionsTableFilterComposer,
    $$CachedSectionsTableOrderingComposer,
    $$CachedSectionsTableAnnotationComposer,
    $$CachedSectionsTableCreateCompanionBuilder,
    $$CachedSectionsTableUpdateCompanionBuilder,
    (
      CachedSectionRow,
      BaseReferences<_$LocalDatabase, $CachedSectionsTable, CachedSectionRow>
    ),
    CachedSectionRow,
    PrefetchHooks Function()>;
typedef $$CachedMediaTableCreateCompanionBuilder = CachedMediaCompanion
    Function({
  required String id,
  required String assetType,
  required String filename,
  Value<String?> localPath,
  required String checksum,
  required int sizeBytes,
  required String mimeType,
  Value<DateTime?> downloadedAt,
  Value<int> rowid,
});
typedef $$CachedMediaTableUpdateCompanionBuilder = CachedMediaCompanion
    Function({
  Value<String> id,
  Value<String> assetType,
  Value<String> filename,
  Value<String?> localPath,
  Value<String> checksum,
  Value<int> sizeBytes,
  Value<String> mimeType,
  Value<DateTime?> downloadedAt,
  Value<int> rowid,
});

class $$CachedMediaTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedMediaTable> {
  $$CachedMediaTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get assetType => $composableBuilder(
      column: $table.assetType, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get filename => $composableBuilder(
      column: $table.filename, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get localPath => $composableBuilder(
      column: $table.localPath, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get checksum => $composableBuilder(
      column: $table.checksum, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sizeBytes => $composableBuilder(
      column: $table.sizeBytes, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get mimeType => $composableBuilder(
      column: $table.mimeType, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get downloadedAt => $composableBuilder(
      column: $table.downloadedAt, builder: (column) => ColumnFilters(column));
}

class $$CachedMediaTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedMediaTable> {
  $$CachedMediaTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get assetType => $composableBuilder(
      column: $table.assetType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get filename => $composableBuilder(
      column: $table.filename, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get localPath => $composableBuilder(
      column: $table.localPath, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get checksum => $composableBuilder(
      column: $table.checksum, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sizeBytes => $composableBuilder(
      column: $table.sizeBytes, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get mimeType => $composableBuilder(
      column: $table.mimeType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get downloadedAt => $composableBuilder(
      column: $table.downloadedAt,
      builder: (column) => ColumnOrderings(column));
}

class $$CachedMediaTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedMediaTable> {
  $$CachedMediaTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get assetType =>
      $composableBuilder(column: $table.assetType, builder: (column) => column);

  GeneratedColumn<String> get filename =>
      $composableBuilder(column: $table.filename, builder: (column) => column);

  GeneratedColumn<String> get localPath =>
      $composableBuilder(column: $table.localPath, builder: (column) => column);

  GeneratedColumn<String> get checksum =>
      $composableBuilder(column: $table.checksum, builder: (column) => column);

  GeneratedColumn<int> get sizeBytes =>
      $composableBuilder(column: $table.sizeBytes, builder: (column) => column);

  GeneratedColumn<String> get mimeType =>
      $composableBuilder(column: $table.mimeType, builder: (column) => column);

  GeneratedColumn<DateTime> get downloadedAt => $composableBuilder(
      column: $table.downloadedAt, builder: (column) => column);
}

class $$CachedMediaTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedMediaTable,
    CachedMediaRow,
    $$CachedMediaTableFilterComposer,
    $$CachedMediaTableOrderingComposer,
    $$CachedMediaTableAnnotationComposer,
    $$CachedMediaTableCreateCompanionBuilder,
    $$CachedMediaTableUpdateCompanionBuilder,
    (
      CachedMediaRow,
      BaseReferences<_$LocalDatabase, $CachedMediaTable, CachedMediaRow>
    ),
    CachedMediaRow,
    PrefetchHooks Function()> {
  $$CachedMediaTableTableManager(_$LocalDatabase db, $CachedMediaTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedMediaTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedMediaTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedMediaTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> assetType = const Value.absent(),
            Value<String> filename = const Value.absent(),
            Value<String?> localPath = const Value.absent(),
            Value<String> checksum = const Value.absent(),
            Value<int> sizeBytes = const Value.absent(),
            Value<String> mimeType = const Value.absent(),
            Value<DateTime?> downloadedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedMediaCompanion(
            id: id,
            assetType: assetType,
            filename: filename,
            localPath: localPath,
            checksum: checksum,
            sizeBytes: sizeBytes,
            mimeType: mimeType,
            downloadedAt: downloadedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String assetType,
            required String filename,
            Value<String?> localPath = const Value.absent(),
            required String checksum,
            required int sizeBytes,
            required String mimeType,
            Value<DateTime?> downloadedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedMediaCompanion.insert(
            id: id,
            assetType: assetType,
            filename: filename,
            localPath: localPath,
            checksum: checksum,
            sizeBytes: sizeBytes,
            mimeType: mimeType,
            downloadedAt: downloadedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedMediaTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedMediaTable,
    CachedMediaRow,
    $$CachedMediaTableFilterComposer,
    $$CachedMediaTableOrderingComposer,
    $$CachedMediaTableAnnotationComposer,
    $$CachedMediaTableCreateCompanionBuilder,
    $$CachedMediaTableUpdateCompanionBuilder,
    (
      CachedMediaRow,
      BaseReferences<_$LocalDatabase, $CachedMediaTable, CachedMediaRow>
    ),
    CachedMediaRow,
    PrefetchHooks Function()>;
typedef $$CachedVideosTableCreateCompanionBuilder = CachedVideosCompanion
    Function({
  required String id,
  required String title,
  Value<String?> description,
  Value<String?> moduleId,
  Value<int?> durationSeconds,
  required String language,
  required bool offlineAvailable,
  required String status,
  required bool hasFile,
  Value<String?> localPath,
  Value<int> rowid,
});
typedef $$CachedVideosTableUpdateCompanionBuilder = CachedVideosCompanion
    Function({
  Value<String> id,
  Value<String> title,
  Value<String?> description,
  Value<String?> moduleId,
  Value<int?> durationSeconds,
  Value<String> language,
  Value<bool> offlineAvailable,
  Value<String> status,
  Value<bool> hasFile,
  Value<String?> localPath,
  Value<int> rowid,
});

class $$CachedVideosTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedVideosTable> {
  $$CachedVideosTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get durationSeconds => $composableBuilder(
      column: $table.durationSeconds,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get language => $composableBuilder(
      column: $table.language, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get offlineAvailable => $composableBuilder(
      column: $table.offlineAvailable,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get hasFile => $composableBuilder(
      column: $table.hasFile, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get localPath => $composableBuilder(
      column: $table.localPath, builder: (column) => ColumnFilters(column));
}

class $$CachedVideosTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedVideosTable> {
  $$CachedVideosTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get durationSeconds => $composableBuilder(
      column: $table.durationSeconds,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get language => $composableBuilder(
      column: $table.language, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get offlineAvailable => $composableBuilder(
      column: $table.offlineAvailable,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get hasFile => $composableBuilder(
      column: $table.hasFile, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get localPath => $composableBuilder(
      column: $table.localPath, builder: (column) => ColumnOrderings(column));
}

class $$CachedVideosTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedVideosTable> {
  $$CachedVideosTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<int> get durationSeconds => $composableBuilder(
      column: $table.durationSeconds, builder: (column) => column);

  GeneratedColumn<String> get language =>
      $composableBuilder(column: $table.language, builder: (column) => column);

  GeneratedColumn<bool> get offlineAvailable => $composableBuilder(
      column: $table.offlineAvailable, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<bool> get hasFile =>
      $composableBuilder(column: $table.hasFile, builder: (column) => column);

  GeneratedColumn<String> get localPath =>
      $composableBuilder(column: $table.localPath, builder: (column) => column);
}

class $$CachedVideosTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedVideosTable,
    CachedVideoRow,
    $$CachedVideosTableFilterComposer,
    $$CachedVideosTableOrderingComposer,
    $$CachedVideosTableAnnotationComposer,
    $$CachedVideosTableCreateCompanionBuilder,
    $$CachedVideosTableUpdateCompanionBuilder,
    (
      CachedVideoRow,
      BaseReferences<_$LocalDatabase, $CachedVideosTable, CachedVideoRow>
    ),
    CachedVideoRow,
    PrefetchHooks Function()> {
  $$CachedVideosTableTableManager(_$LocalDatabase db, $CachedVideosTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedVideosTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedVideosTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedVideosTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String?> description = const Value.absent(),
            Value<String?> moduleId = const Value.absent(),
            Value<int?> durationSeconds = const Value.absent(),
            Value<String> language = const Value.absent(),
            Value<bool> offlineAvailable = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<bool> hasFile = const Value.absent(),
            Value<String?> localPath = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedVideosCompanion(
            id: id,
            title: title,
            description: description,
            moduleId: moduleId,
            durationSeconds: durationSeconds,
            language: language,
            offlineAvailable: offlineAvailable,
            status: status,
            hasFile: hasFile,
            localPath: localPath,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String title,
            Value<String?> description = const Value.absent(),
            Value<String?> moduleId = const Value.absent(),
            Value<int?> durationSeconds = const Value.absent(),
            required String language,
            required bool offlineAvailable,
            required String status,
            required bool hasFile,
            Value<String?> localPath = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedVideosCompanion.insert(
            id: id,
            title: title,
            description: description,
            moduleId: moduleId,
            durationSeconds: durationSeconds,
            language: language,
            offlineAvailable: offlineAvailable,
            status: status,
            hasFile: hasFile,
            localPath: localPath,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedVideosTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedVideosTable,
    CachedVideoRow,
    $$CachedVideosTableFilterComposer,
    $$CachedVideosTableOrderingComposer,
    $$CachedVideosTableAnnotationComposer,
    $$CachedVideosTableCreateCompanionBuilder,
    $$CachedVideosTableUpdateCompanionBuilder,
    (
      CachedVideoRow,
      BaseReferences<_$LocalDatabase, $CachedVideosTable, CachedVideoRow>
    ),
    CachedVideoRow,
    PrefetchHooks Function()>;
typedef $$LocalProgressTableCreateCompanionBuilder = LocalProgressCompanion
    Function({
  Value<int> id,
  required String moduleId,
  Value<int> progressPercent,
  Value<bool> completed,
  Value<String?> lastSection,
  Value<DateTime?> lastOpenedAt,
  Value<DateTime?> completedAt,
  Value<DateTime?> readingCompletedAt,
  Value<bool> synced,
  Value<String> userId,
});
typedef $$LocalProgressTableUpdateCompanionBuilder = LocalProgressCompanion
    Function({
  Value<int> id,
  Value<String> moduleId,
  Value<int> progressPercent,
  Value<bool> completed,
  Value<String?> lastSection,
  Value<DateTime?> lastOpenedAt,
  Value<DateTime?> completedAt,
  Value<DateTime?> readingCompletedAt,
  Value<bool> synced,
  Value<String> userId,
});

class $$LocalProgressTableFilterComposer
    extends Composer<_$LocalDatabase, $LocalProgressTable> {
  $$LocalProgressTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get progressPercent => $composableBuilder(
      column: $table.progressPercent,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get completed => $composableBuilder(
      column: $table.completed, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get lastSection => $composableBuilder(
      column: $table.lastSection, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get lastOpenedAt => $composableBuilder(
      column: $table.lastOpenedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get completedAt => $composableBuilder(
      column: $table.completedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get readingCompletedAt => $composableBuilder(
      column: $table.readingCompletedAt,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnFilters(column));
}

class $$LocalProgressTableOrderingComposer
    extends Composer<_$LocalDatabase, $LocalProgressTable> {
  $$LocalProgressTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get progressPercent => $composableBuilder(
      column: $table.progressPercent,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get completed => $composableBuilder(
      column: $table.completed, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get lastSection => $composableBuilder(
      column: $table.lastSection, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get lastOpenedAt => $composableBuilder(
      column: $table.lastOpenedAt,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get completedAt => $composableBuilder(
      column: $table.completedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get readingCompletedAt => $composableBuilder(
      column: $table.readingCompletedAt,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnOrderings(column));
}

class $$LocalProgressTableAnnotationComposer
    extends Composer<_$LocalDatabase, $LocalProgressTable> {
  $$LocalProgressTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<int> get progressPercent => $composableBuilder(
      column: $table.progressPercent, builder: (column) => column);

  GeneratedColumn<bool> get completed =>
      $composableBuilder(column: $table.completed, builder: (column) => column);

  GeneratedColumn<String> get lastSection => $composableBuilder(
      column: $table.lastSection, builder: (column) => column);

  GeneratedColumn<DateTime> get lastOpenedAt => $composableBuilder(
      column: $table.lastOpenedAt, builder: (column) => column);

  GeneratedColumn<DateTime> get completedAt => $composableBuilder(
      column: $table.completedAt, builder: (column) => column);

  GeneratedColumn<DateTime> get readingCompletedAt => $composableBuilder(
      column: $table.readingCompletedAt, builder: (column) => column);

  GeneratedColumn<bool> get synced =>
      $composableBuilder(column: $table.synced, builder: (column) => column);

  GeneratedColumn<String> get userId =>
      $composableBuilder(column: $table.userId, builder: (column) => column);
}

class $$LocalProgressTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $LocalProgressTable,
    LocalProgressRow,
    $$LocalProgressTableFilterComposer,
    $$LocalProgressTableOrderingComposer,
    $$LocalProgressTableAnnotationComposer,
    $$LocalProgressTableCreateCompanionBuilder,
    $$LocalProgressTableUpdateCompanionBuilder,
    (
      LocalProgressRow,
      BaseReferences<_$LocalDatabase, $LocalProgressTable, LocalProgressRow>
    ),
    LocalProgressRow,
    PrefetchHooks Function()> {
  $$LocalProgressTableTableManager(
      _$LocalDatabase db, $LocalProgressTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalProgressTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalProgressTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalProgressTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<int> progressPercent = const Value.absent(),
            Value<bool> completed = const Value.absent(),
            Value<String?> lastSection = const Value.absent(),
            Value<DateTime?> lastOpenedAt = const Value.absent(),
            Value<DateTime?> completedAt = const Value.absent(),
            Value<DateTime?> readingCompletedAt = const Value.absent(),
            Value<bool> synced = const Value.absent(),
            Value<String> userId = const Value.absent(),
          }) =>
              LocalProgressCompanion(
            id: id,
            moduleId: moduleId,
            progressPercent: progressPercent,
            completed: completed,
            lastSection: lastSection,
            lastOpenedAt: lastOpenedAt,
            completedAt: completedAt,
            readingCompletedAt: readingCompletedAt,
            synced: synced,
            userId: userId,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String moduleId,
            Value<int> progressPercent = const Value.absent(),
            Value<bool> completed = const Value.absent(),
            Value<String?> lastSection = const Value.absent(),
            Value<DateTime?> lastOpenedAt = const Value.absent(),
            Value<DateTime?> completedAt = const Value.absent(),
            Value<DateTime?> readingCompletedAt = const Value.absent(),
            Value<bool> synced = const Value.absent(),
            Value<String> userId = const Value.absent(),
          }) =>
              LocalProgressCompanion.insert(
            id: id,
            moduleId: moduleId,
            progressPercent: progressPercent,
            completed: completed,
            lastSection: lastSection,
            lastOpenedAt: lastOpenedAt,
            completedAt: completedAt,
            readingCompletedAt: readingCompletedAt,
            synced: synced,
            userId: userId,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalProgressTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $LocalProgressTable,
    LocalProgressRow,
    $$LocalProgressTableFilterComposer,
    $$LocalProgressTableOrderingComposer,
    $$LocalProgressTableAnnotationComposer,
    $$LocalProgressTableCreateCompanionBuilder,
    $$LocalProgressTableUpdateCompanionBuilder,
    (
      LocalProgressRow,
      BaseReferences<_$LocalDatabase, $LocalProgressTable, LocalProgressRow>
    ),
    LocalProgressRow,
    PrefetchHooks Function()>;
typedef $$PendingSyncTableCreateCompanionBuilder = PendingSyncCompanion
    Function({
  Value<int> id,
  required String entityType,
  required String payloadJson,
  required DateTime createdAt,
  Value<DateTime?> syncedAt,
  Value<String> userId,
});
typedef $$PendingSyncTableUpdateCompanionBuilder = PendingSyncCompanion
    Function({
  Value<int> id,
  Value<String> entityType,
  Value<String> payloadJson,
  Value<DateTime> createdAt,
  Value<DateTime?> syncedAt,
  Value<String> userId,
});

class $$PendingSyncTableFilterComposer
    extends Composer<_$LocalDatabase, $PendingSyncTable> {
  $$PendingSyncTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get entityType => $composableBuilder(
      column: $table.entityType, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get syncedAt => $composableBuilder(
      column: $table.syncedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnFilters(column));
}

class $$PendingSyncTableOrderingComposer
    extends Composer<_$LocalDatabase, $PendingSyncTable> {
  $$PendingSyncTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get entityType => $composableBuilder(
      column: $table.entityType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get syncedAt => $composableBuilder(
      column: $table.syncedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnOrderings(column));
}

class $$PendingSyncTableAnnotationComposer
    extends Composer<_$LocalDatabase, $PendingSyncTable> {
  $$PendingSyncTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get entityType => $composableBuilder(
      column: $table.entityType, builder: (column) => column);

  GeneratedColumn<String> get payloadJson => $composableBuilder(
      column: $table.payloadJson, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<DateTime> get syncedAt =>
      $composableBuilder(column: $table.syncedAt, builder: (column) => column);

  GeneratedColumn<String> get userId =>
      $composableBuilder(column: $table.userId, builder: (column) => column);
}

class $$PendingSyncTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $PendingSyncTable,
    PendingSyncRow,
    $$PendingSyncTableFilterComposer,
    $$PendingSyncTableOrderingComposer,
    $$PendingSyncTableAnnotationComposer,
    $$PendingSyncTableCreateCompanionBuilder,
    $$PendingSyncTableUpdateCompanionBuilder,
    (
      PendingSyncRow,
      BaseReferences<_$LocalDatabase, $PendingSyncTable, PendingSyncRow>
    ),
    PendingSyncRow,
    PrefetchHooks Function()> {
  $$PendingSyncTableTableManager(_$LocalDatabase db, $PendingSyncTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PendingSyncTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PendingSyncTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PendingSyncTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> entityType = const Value.absent(),
            Value<String> payloadJson = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<DateTime?> syncedAt = const Value.absent(),
            Value<String> userId = const Value.absent(),
          }) =>
              PendingSyncCompanion(
            id: id,
            entityType: entityType,
            payloadJson: payloadJson,
            createdAt: createdAt,
            syncedAt: syncedAt,
            userId: userId,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String entityType,
            required String payloadJson,
            required DateTime createdAt,
            Value<DateTime?> syncedAt = const Value.absent(),
            Value<String> userId = const Value.absent(),
          }) =>
              PendingSyncCompanion.insert(
            id: id,
            entityType: entityType,
            payloadJson: payloadJson,
            createdAt: createdAt,
            syncedAt: syncedAt,
            userId: userId,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$PendingSyncTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $PendingSyncTable,
    PendingSyncRow,
    $$PendingSyncTableFilterComposer,
    $$PendingSyncTableOrderingComposer,
    $$PendingSyncTableAnnotationComposer,
    $$PendingSyncTableCreateCompanionBuilder,
    $$PendingSyncTableUpdateCompanionBuilder,
    (
      PendingSyncRow,
      BaseReferences<_$LocalDatabase, $PendingSyncTable, PendingSyncRow>
    ),
    PendingSyncRow,
    PrefetchHooks Function()>;
typedef $$AppSettingsTableCreateCompanionBuilder = AppSettingsCompanion
    Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$AppSettingsTableUpdateCompanionBuilder = AppSettingsCompanion
    Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$AppSettingsTableFilterComposer
    extends Composer<_$LocalDatabase, $AppSettingsTable> {
  $$AppSettingsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnFilters(column));
}

class $$AppSettingsTableOrderingComposer
    extends Composer<_$LocalDatabase, $AppSettingsTable> {
  $$AppSettingsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnOrderings(column));
}

class $$AppSettingsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $AppSettingsTable> {
  $$AppSettingsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$AppSettingsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $AppSettingsTable,
    AppSettingRow,
    $$AppSettingsTableFilterComposer,
    $$AppSettingsTableOrderingComposer,
    $$AppSettingsTableAnnotationComposer,
    $$AppSettingsTableCreateCompanionBuilder,
    $$AppSettingsTableUpdateCompanionBuilder,
    (
      AppSettingRow,
      BaseReferences<_$LocalDatabase, $AppSettingsTable, AppSettingRow>
    ),
    AppSettingRow,
    PrefetchHooks Function()> {
  $$AppSettingsTableTableManager(_$LocalDatabase db, $AppSettingsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$AppSettingsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$AppSettingsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$AppSettingsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              AppSettingsCompanion(
            key: key,
            value: value,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) =>
              AppSettingsCompanion.insert(
            key: key,
            value: value,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$AppSettingsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $AppSettingsTable,
    AppSettingRow,
    $$AppSettingsTableFilterComposer,
    $$AppSettingsTableOrderingComposer,
    $$AppSettingsTableAnnotationComposer,
    $$AppSettingsTableCreateCompanionBuilder,
    $$AppSettingsTableUpdateCompanionBuilder,
    (
      AppSettingRow,
      BaseReferences<_$LocalDatabase, $AppSettingsTable, AppSettingRow>
    ),
    AppSettingRow,
    PrefetchHooks Function()>;
typedef $$InstalledReleasesTableCreateCompanionBuilder
    = InstalledReleasesCompanion Function({
  Value<int> id,
  required String releaseCode,
  required String version,
  required DateTime installedAt,
  required int moduleCount,
  required int sectionCount,
});
typedef $$InstalledReleasesTableUpdateCompanionBuilder
    = InstalledReleasesCompanion Function({
  Value<int> id,
  Value<String> releaseCode,
  Value<String> version,
  Value<DateTime> installedAt,
  Value<int> moduleCount,
  Value<int> sectionCount,
});

class $$InstalledReleasesTableFilterComposer
    extends Composer<_$LocalDatabase, $InstalledReleasesTable> {
  $$InstalledReleasesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get releaseCode => $composableBuilder(
      column: $table.releaseCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get version => $composableBuilder(
      column: $table.version, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get installedAt => $composableBuilder(
      column: $table.installedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get moduleCount => $composableBuilder(
      column: $table.moduleCount, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sectionCount => $composableBuilder(
      column: $table.sectionCount, builder: (column) => ColumnFilters(column));
}

class $$InstalledReleasesTableOrderingComposer
    extends Composer<_$LocalDatabase, $InstalledReleasesTable> {
  $$InstalledReleasesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get releaseCode => $composableBuilder(
      column: $table.releaseCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get version => $composableBuilder(
      column: $table.version, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get installedAt => $composableBuilder(
      column: $table.installedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get moduleCount => $composableBuilder(
      column: $table.moduleCount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sectionCount => $composableBuilder(
      column: $table.sectionCount,
      builder: (column) => ColumnOrderings(column));
}

class $$InstalledReleasesTableAnnotationComposer
    extends Composer<_$LocalDatabase, $InstalledReleasesTable> {
  $$InstalledReleasesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get releaseCode => $composableBuilder(
      column: $table.releaseCode, builder: (column) => column);

  GeneratedColumn<String> get version =>
      $composableBuilder(column: $table.version, builder: (column) => column);

  GeneratedColumn<DateTime> get installedAt => $composableBuilder(
      column: $table.installedAt, builder: (column) => column);

  GeneratedColumn<int> get moduleCount => $composableBuilder(
      column: $table.moduleCount, builder: (column) => column);

  GeneratedColumn<int> get sectionCount => $composableBuilder(
      column: $table.sectionCount, builder: (column) => column);
}

class $$InstalledReleasesTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $InstalledReleasesTable,
    InstalledReleaseRow,
    $$InstalledReleasesTableFilterComposer,
    $$InstalledReleasesTableOrderingComposer,
    $$InstalledReleasesTableAnnotationComposer,
    $$InstalledReleasesTableCreateCompanionBuilder,
    $$InstalledReleasesTableUpdateCompanionBuilder,
    (
      InstalledReleaseRow,
      BaseReferences<_$LocalDatabase, $InstalledReleasesTable,
          InstalledReleaseRow>
    ),
    InstalledReleaseRow,
    PrefetchHooks Function()> {
  $$InstalledReleasesTableTableManager(
      _$LocalDatabase db, $InstalledReleasesTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$InstalledReleasesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$InstalledReleasesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$InstalledReleasesTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> releaseCode = const Value.absent(),
            Value<String> version = const Value.absent(),
            Value<DateTime> installedAt = const Value.absent(),
            Value<int> moduleCount = const Value.absent(),
            Value<int> sectionCount = const Value.absent(),
          }) =>
              InstalledReleasesCompanion(
            id: id,
            releaseCode: releaseCode,
            version: version,
            installedAt: installedAt,
            moduleCount: moduleCount,
            sectionCount: sectionCount,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String releaseCode,
            required String version,
            required DateTime installedAt,
            required int moduleCount,
            required int sectionCount,
          }) =>
              InstalledReleasesCompanion.insert(
            id: id,
            releaseCode: releaseCode,
            version: version,
            installedAt: installedAt,
            moduleCount: moduleCount,
            sectionCount: sectionCount,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$InstalledReleasesTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $InstalledReleasesTable,
    InstalledReleaseRow,
    $$InstalledReleasesTableFilterComposer,
    $$InstalledReleasesTableOrderingComposer,
    $$InstalledReleasesTableAnnotationComposer,
    $$InstalledReleasesTableCreateCompanionBuilder,
    $$InstalledReleasesTableUpdateCompanionBuilder,
    (
      InstalledReleaseRow,
      BaseReferences<_$LocalDatabase, $InstalledReleasesTable,
          InstalledReleaseRow>
    ),
    InstalledReleaseRow,
    PrefetchHooks Function()>;
typedef $$LocalAiQuestionsTableCreateCompanionBuilder
    = LocalAiQuestionsCompanion Function({
  Value<int> id,
  required String question,
  Value<String?> answer,
  Value<bool> matched,
  required DateTime askedAt,
  Value<bool> synced,
  Value<String> userId,
});
typedef $$LocalAiQuestionsTableUpdateCompanionBuilder
    = LocalAiQuestionsCompanion Function({
  Value<int> id,
  Value<String> question,
  Value<String?> answer,
  Value<bool> matched,
  Value<DateTime> askedAt,
  Value<bool> synced,
  Value<String> userId,
});

class $$LocalAiQuestionsTableFilterComposer
    extends Composer<_$LocalDatabase, $LocalAiQuestionsTable> {
  $$LocalAiQuestionsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get question => $composableBuilder(
      column: $table.question, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get answer => $composableBuilder(
      column: $table.answer, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get matched => $composableBuilder(
      column: $table.matched, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get askedAt => $composableBuilder(
      column: $table.askedAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnFilters(column));
}

class $$LocalAiQuestionsTableOrderingComposer
    extends Composer<_$LocalDatabase, $LocalAiQuestionsTable> {
  $$LocalAiQuestionsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get question => $composableBuilder(
      column: $table.question, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get answer => $composableBuilder(
      column: $table.answer, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get matched => $composableBuilder(
      column: $table.matched, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get askedAt => $composableBuilder(
      column: $table.askedAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnOrderings(column));
}

class $$LocalAiQuestionsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $LocalAiQuestionsTable> {
  $$LocalAiQuestionsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get question =>
      $composableBuilder(column: $table.question, builder: (column) => column);

  GeneratedColumn<String> get answer =>
      $composableBuilder(column: $table.answer, builder: (column) => column);

  GeneratedColumn<bool> get matched =>
      $composableBuilder(column: $table.matched, builder: (column) => column);

  GeneratedColumn<DateTime> get askedAt =>
      $composableBuilder(column: $table.askedAt, builder: (column) => column);

  GeneratedColumn<bool> get synced =>
      $composableBuilder(column: $table.synced, builder: (column) => column);

  GeneratedColumn<String> get userId =>
      $composableBuilder(column: $table.userId, builder: (column) => column);
}

class $$LocalAiQuestionsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $LocalAiQuestionsTable,
    LocalAiQuestionRow,
    $$LocalAiQuestionsTableFilterComposer,
    $$LocalAiQuestionsTableOrderingComposer,
    $$LocalAiQuestionsTableAnnotationComposer,
    $$LocalAiQuestionsTableCreateCompanionBuilder,
    $$LocalAiQuestionsTableUpdateCompanionBuilder,
    (
      LocalAiQuestionRow,
      BaseReferences<_$LocalDatabase, $LocalAiQuestionsTable,
          LocalAiQuestionRow>
    ),
    LocalAiQuestionRow,
    PrefetchHooks Function()> {
  $$LocalAiQuestionsTableTableManager(
      _$LocalDatabase db, $LocalAiQuestionsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalAiQuestionsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalAiQuestionsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalAiQuestionsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> question = const Value.absent(),
            Value<String?> answer = const Value.absent(),
            Value<bool> matched = const Value.absent(),
            Value<DateTime> askedAt = const Value.absent(),
            Value<bool> synced = const Value.absent(),
            Value<String> userId = const Value.absent(),
          }) =>
              LocalAiQuestionsCompanion(
            id: id,
            question: question,
            answer: answer,
            matched: matched,
            askedAt: askedAt,
            synced: synced,
            userId: userId,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String question,
            Value<String?> answer = const Value.absent(),
            Value<bool> matched = const Value.absent(),
            required DateTime askedAt,
            Value<bool> synced = const Value.absent(),
            Value<String> userId = const Value.absent(),
          }) =>
              LocalAiQuestionsCompanion.insert(
            id: id,
            question: question,
            answer: answer,
            matched: matched,
            askedAt: askedAt,
            synced: synced,
            userId: userId,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalAiQuestionsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $LocalAiQuestionsTable,
    LocalAiQuestionRow,
    $$LocalAiQuestionsTableFilterComposer,
    $$LocalAiQuestionsTableOrderingComposer,
    $$LocalAiQuestionsTableAnnotationComposer,
    $$LocalAiQuestionsTableCreateCompanionBuilder,
    $$LocalAiQuestionsTableUpdateCompanionBuilder,
    (
      LocalAiQuestionRow,
      BaseReferences<_$LocalDatabase, $LocalAiQuestionsTable,
          LocalAiQuestionRow>
    ),
    LocalAiQuestionRow,
    PrefetchHooks Function()>;
typedef $$RagMetadataTableCreateCompanionBuilder = RagMetadataCompanion
    Function({
  Value<int> id,
  required String moduleId,
  Value<String?> sectionId,
  required String chunkText,
  Value<String?> embeddingJson,
});
typedef $$RagMetadataTableUpdateCompanionBuilder = RagMetadataCompanion
    Function({
  Value<int> id,
  Value<String> moduleId,
  Value<String?> sectionId,
  Value<String> chunkText,
  Value<String?> embeddingJson,
});

class $$RagMetadataTableFilterComposer
    extends Composer<_$LocalDatabase, $RagMetadataTable> {
  $$RagMetadataTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get sectionId => $composableBuilder(
      column: $table.sectionId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get chunkText => $composableBuilder(
      column: $table.chunkText, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get embeddingJson => $composableBuilder(
      column: $table.embeddingJson, builder: (column) => ColumnFilters(column));
}

class $$RagMetadataTableOrderingComposer
    extends Composer<_$LocalDatabase, $RagMetadataTable> {
  $$RagMetadataTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get sectionId => $composableBuilder(
      column: $table.sectionId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get chunkText => $composableBuilder(
      column: $table.chunkText, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get embeddingJson => $composableBuilder(
      column: $table.embeddingJson,
      builder: (column) => ColumnOrderings(column));
}

class $$RagMetadataTableAnnotationComposer
    extends Composer<_$LocalDatabase, $RagMetadataTable> {
  $$RagMetadataTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<String> get sectionId =>
      $composableBuilder(column: $table.sectionId, builder: (column) => column);

  GeneratedColumn<String> get chunkText =>
      $composableBuilder(column: $table.chunkText, builder: (column) => column);

  GeneratedColumn<String> get embeddingJson => $composableBuilder(
      column: $table.embeddingJson, builder: (column) => column);
}

class $$RagMetadataTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $RagMetadataTable,
    RagMetadataRow,
    $$RagMetadataTableFilterComposer,
    $$RagMetadataTableOrderingComposer,
    $$RagMetadataTableAnnotationComposer,
    $$RagMetadataTableCreateCompanionBuilder,
    $$RagMetadataTableUpdateCompanionBuilder,
    (
      RagMetadataRow,
      BaseReferences<_$LocalDatabase, $RagMetadataTable, RagMetadataRow>
    ),
    RagMetadataRow,
    PrefetchHooks Function()> {
  $$RagMetadataTableTableManager(_$LocalDatabase db, $RagMetadataTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$RagMetadataTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$RagMetadataTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$RagMetadataTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<String?> sectionId = const Value.absent(),
            Value<String> chunkText = const Value.absent(),
            Value<String?> embeddingJson = const Value.absent(),
          }) =>
              RagMetadataCompanion(
            id: id,
            moduleId: moduleId,
            sectionId: sectionId,
            chunkText: chunkText,
            embeddingJson: embeddingJson,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String moduleId,
            Value<String?> sectionId = const Value.absent(),
            required String chunkText,
            Value<String?> embeddingJson = const Value.absent(),
          }) =>
              RagMetadataCompanion.insert(
            id: id,
            moduleId: moduleId,
            sectionId: sectionId,
            chunkText: chunkText,
            embeddingJson: embeddingJson,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$RagMetadataTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $RagMetadataTable,
    RagMetadataRow,
    $$RagMetadataTableFilterComposer,
    $$RagMetadataTableOrderingComposer,
    $$RagMetadataTableAnnotationComposer,
    $$RagMetadataTableCreateCompanionBuilder,
    $$RagMetadataTableUpdateCompanionBuilder,
    (
      RagMetadataRow,
      BaseReferences<_$LocalDatabase, $RagMetadataTable, RagMetadataRow>
    ),
    RagMetadataRow,
    PrefetchHooks Function()>;
typedef $$ContentChunksTableCreateCompanionBuilder = ContentChunksCompanion
    Function({
  required String id,
  required String moduleId,
  required String moduleCode,
  Value<String?> sectionId,
  Value<String?> sectionTitle,
  required String language,
  required String sourceTitle,
  required String chunkText,
  Value<String?> faqQuestions,
  Value<int> rowid,
});
typedef $$ContentChunksTableUpdateCompanionBuilder = ContentChunksCompanion
    Function({
  Value<String> id,
  Value<String> moduleId,
  Value<String> moduleCode,
  Value<String?> sectionId,
  Value<String?> sectionTitle,
  Value<String> language,
  Value<String> sourceTitle,
  Value<String> chunkText,
  Value<String?> faqQuestions,
  Value<int> rowid,
});

class $$ContentChunksTableFilterComposer
    extends Composer<_$LocalDatabase, $ContentChunksTable> {
  $$ContentChunksTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleCode => $composableBuilder(
      column: $table.moduleCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get sectionId => $composableBuilder(
      column: $table.sectionId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get sectionTitle => $composableBuilder(
      column: $table.sectionTitle, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get language => $composableBuilder(
      column: $table.language, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get sourceTitle => $composableBuilder(
      column: $table.sourceTitle, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get chunkText => $composableBuilder(
      column: $table.chunkText, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get faqQuestions => $composableBuilder(
      column: $table.faqQuestions, builder: (column) => ColumnFilters(column));
}

class $$ContentChunksTableOrderingComposer
    extends Composer<_$LocalDatabase, $ContentChunksTable> {
  $$ContentChunksTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleCode => $composableBuilder(
      column: $table.moduleCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get sectionId => $composableBuilder(
      column: $table.sectionId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get sectionTitle => $composableBuilder(
      column: $table.sectionTitle,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get language => $composableBuilder(
      column: $table.language, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get sourceTitle => $composableBuilder(
      column: $table.sourceTitle, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get chunkText => $composableBuilder(
      column: $table.chunkText, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get faqQuestions => $composableBuilder(
      column: $table.faqQuestions,
      builder: (column) => ColumnOrderings(column));
}

class $$ContentChunksTableAnnotationComposer
    extends Composer<_$LocalDatabase, $ContentChunksTable> {
  $$ContentChunksTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<String> get moduleCode => $composableBuilder(
      column: $table.moduleCode, builder: (column) => column);

  GeneratedColumn<String> get sectionId =>
      $composableBuilder(column: $table.sectionId, builder: (column) => column);

  GeneratedColumn<String> get sectionTitle => $composableBuilder(
      column: $table.sectionTitle, builder: (column) => column);

  GeneratedColumn<String> get language =>
      $composableBuilder(column: $table.language, builder: (column) => column);

  GeneratedColumn<String> get sourceTitle => $composableBuilder(
      column: $table.sourceTitle, builder: (column) => column);

  GeneratedColumn<String> get chunkText =>
      $composableBuilder(column: $table.chunkText, builder: (column) => column);

  GeneratedColumn<String> get faqQuestions => $composableBuilder(
      column: $table.faqQuestions, builder: (column) => column);
}

class $$ContentChunksTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $ContentChunksTable,
    ContentChunkRow,
    $$ContentChunksTableFilterComposer,
    $$ContentChunksTableOrderingComposer,
    $$ContentChunksTableAnnotationComposer,
    $$ContentChunksTableCreateCompanionBuilder,
    $$ContentChunksTableUpdateCompanionBuilder,
    (
      ContentChunkRow,
      BaseReferences<_$LocalDatabase, $ContentChunksTable, ContentChunkRow>
    ),
    ContentChunkRow,
    PrefetchHooks Function()> {
  $$ContentChunksTableTableManager(
      _$LocalDatabase db, $ContentChunksTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ContentChunksTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ContentChunksTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ContentChunksTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<String> moduleCode = const Value.absent(),
            Value<String?> sectionId = const Value.absent(),
            Value<String?> sectionTitle = const Value.absent(),
            Value<String> language = const Value.absent(),
            Value<String> sourceTitle = const Value.absent(),
            Value<String> chunkText = const Value.absent(),
            Value<String?> faqQuestions = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              ContentChunksCompanion(
            id: id,
            moduleId: moduleId,
            moduleCode: moduleCode,
            sectionId: sectionId,
            sectionTitle: sectionTitle,
            language: language,
            sourceTitle: sourceTitle,
            chunkText: chunkText,
            faqQuestions: faqQuestions,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String moduleId,
            required String moduleCode,
            Value<String?> sectionId = const Value.absent(),
            Value<String?> sectionTitle = const Value.absent(),
            required String language,
            required String sourceTitle,
            required String chunkText,
            Value<String?> faqQuestions = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              ContentChunksCompanion.insert(
            id: id,
            moduleId: moduleId,
            moduleCode: moduleCode,
            sectionId: sectionId,
            sectionTitle: sectionTitle,
            language: language,
            sourceTitle: sourceTitle,
            chunkText: chunkText,
            faqQuestions: faqQuestions,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$ContentChunksTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $ContentChunksTable,
    ContentChunkRow,
    $$ContentChunksTableFilterComposer,
    $$ContentChunksTableOrderingComposer,
    $$ContentChunksTableAnnotationComposer,
    $$ContentChunksTableCreateCompanionBuilder,
    $$ContentChunksTableUpdateCompanionBuilder,
    (
      ContentChunkRow,
      BaseReferences<_$LocalDatabase, $ContentChunksTable, ContentChunkRow>
    ),
    ContentChunkRow,
    PrefetchHooks Function()>;
typedef $$CachedQuizQuestionsTableCreateCompanionBuilder
    = CachedQuizQuestionsCompanion Function({
  required String id,
  required String moduleId,
  required String questionType,
  required String prompt,
  required String contentJson,
  Value<String?> explanation,
  required int sortOrder,
  Value<String> usage,
  Value<int> rowid,
});
typedef $$CachedQuizQuestionsTableUpdateCompanionBuilder
    = CachedQuizQuestionsCompanion Function({
  Value<String> id,
  Value<String> moduleId,
  Value<String> questionType,
  Value<String> prompt,
  Value<String> contentJson,
  Value<String?> explanation,
  Value<int> sortOrder,
  Value<String> usage,
  Value<int> rowid,
});

class $$CachedQuizQuestionsTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedQuizQuestionsTable> {
  $$CachedQuizQuestionsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get questionType => $composableBuilder(
      column: $table.questionType, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get prompt => $composableBuilder(
      column: $table.prompt, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get explanation => $composableBuilder(
      column: $table.explanation, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get usage => $composableBuilder(
      column: $table.usage, builder: (column) => ColumnFilters(column));
}

class $$CachedQuizQuestionsTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedQuizQuestionsTable> {
  $$CachedQuizQuestionsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get questionType => $composableBuilder(
      column: $table.questionType,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get prompt => $composableBuilder(
      column: $table.prompt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get explanation => $composableBuilder(
      column: $table.explanation, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get sortOrder => $composableBuilder(
      column: $table.sortOrder, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get usage => $composableBuilder(
      column: $table.usage, builder: (column) => ColumnOrderings(column));
}

class $$CachedQuizQuestionsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedQuizQuestionsTable> {
  $$CachedQuizQuestionsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<String> get questionType => $composableBuilder(
      column: $table.questionType, builder: (column) => column);

  GeneratedColumn<String> get prompt =>
      $composableBuilder(column: $table.prompt, builder: (column) => column);

  GeneratedColumn<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => column);

  GeneratedColumn<String> get explanation => $composableBuilder(
      column: $table.explanation, builder: (column) => column);

  GeneratedColumn<int> get sortOrder =>
      $composableBuilder(column: $table.sortOrder, builder: (column) => column);

  GeneratedColumn<String> get usage =>
      $composableBuilder(column: $table.usage, builder: (column) => column);
}

class $$CachedQuizQuestionsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedQuizQuestionsTable,
    CachedQuizQuestionRow,
    $$CachedQuizQuestionsTableFilterComposer,
    $$CachedQuizQuestionsTableOrderingComposer,
    $$CachedQuizQuestionsTableAnnotationComposer,
    $$CachedQuizQuestionsTableCreateCompanionBuilder,
    $$CachedQuizQuestionsTableUpdateCompanionBuilder,
    (
      CachedQuizQuestionRow,
      BaseReferences<_$LocalDatabase, $CachedQuizQuestionsTable,
          CachedQuizQuestionRow>
    ),
    CachedQuizQuestionRow,
    PrefetchHooks Function()> {
  $$CachedQuizQuestionsTableTableManager(
      _$LocalDatabase db, $CachedQuizQuestionsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedQuizQuestionsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedQuizQuestionsTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedQuizQuestionsTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<String> questionType = const Value.absent(),
            Value<String> prompt = const Value.absent(),
            Value<String> contentJson = const Value.absent(),
            Value<String?> explanation = const Value.absent(),
            Value<int> sortOrder = const Value.absent(),
            Value<String> usage = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedQuizQuestionsCompanion(
            id: id,
            moduleId: moduleId,
            questionType: questionType,
            prompt: prompt,
            contentJson: contentJson,
            explanation: explanation,
            sortOrder: sortOrder,
            usage: usage,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String moduleId,
            required String questionType,
            required String prompt,
            required String contentJson,
            Value<String?> explanation = const Value.absent(),
            required int sortOrder,
            Value<String> usage = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedQuizQuestionsCompanion.insert(
            id: id,
            moduleId: moduleId,
            questionType: questionType,
            prompt: prompt,
            contentJson: contentJson,
            explanation: explanation,
            sortOrder: sortOrder,
            usage: usage,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedQuizQuestionsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedQuizQuestionsTable,
    CachedQuizQuestionRow,
    $$CachedQuizQuestionsTableFilterComposer,
    $$CachedQuizQuestionsTableOrderingComposer,
    $$CachedQuizQuestionsTableAnnotationComposer,
    $$CachedQuizQuestionsTableCreateCompanionBuilder,
    $$CachedQuizQuestionsTableUpdateCompanionBuilder,
    (
      CachedQuizQuestionRow,
      BaseReferences<_$LocalDatabase, $CachedQuizQuestionsTable,
          CachedQuizQuestionRow>
    ),
    CachedQuizQuestionRow,
    PrefetchHooks Function()>;
typedef $$LocalQuizAttemptsTableCreateCompanionBuilder
    = LocalQuizAttemptsCompanion Function({
  Value<int> id,
  Value<String> userId,
  required String moduleId,
  required String clientId,
  required int correctCount,
  required int totalCount,
  required int scorePercent,
  required bool passed,
  required String resultsJson,
  required DateTime takenAt,
  Value<bool> synced,
  Value<String> testType,
  Value<bool?> serverValid,
  Value<String?> invalidReason,
});
typedef $$LocalQuizAttemptsTableUpdateCompanionBuilder
    = LocalQuizAttemptsCompanion Function({
  Value<int> id,
  Value<String> userId,
  Value<String> moduleId,
  Value<String> clientId,
  Value<int> correctCount,
  Value<int> totalCount,
  Value<int> scorePercent,
  Value<bool> passed,
  Value<String> resultsJson,
  Value<DateTime> takenAt,
  Value<bool> synced,
  Value<String> testType,
  Value<bool?> serverValid,
  Value<String?> invalidReason,
});

class $$LocalQuizAttemptsTableFilterComposer
    extends Composer<_$LocalDatabase, $LocalQuizAttemptsTable> {
  $$LocalQuizAttemptsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get clientId => $composableBuilder(
      column: $table.clientId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get correctCount => $composableBuilder(
      column: $table.correctCount, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get totalCount => $composableBuilder(
      column: $table.totalCount, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get scorePercent => $composableBuilder(
      column: $table.scorePercent, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get passed => $composableBuilder(
      column: $table.passed, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get resultsJson => $composableBuilder(
      column: $table.resultsJson, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get takenAt => $composableBuilder(
      column: $table.takenAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get testType => $composableBuilder(
      column: $table.testType, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get serverValid => $composableBuilder(
      column: $table.serverValid, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get invalidReason => $composableBuilder(
      column: $table.invalidReason, builder: (column) => ColumnFilters(column));
}

class $$LocalQuizAttemptsTableOrderingComposer
    extends Composer<_$LocalDatabase, $LocalQuizAttemptsTable> {
  $$LocalQuizAttemptsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get userId => $composableBuilder(
      column: $table.userId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get clientId => $composableBuilder(
      column: $table.clientId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get correctCount => $composableBuilder(
      column: $table.correctCount,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get totalCount => $composableBuilder(
      column: $table.totalCount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get scorePercent => $composableBuilder(
      column: $table.scorePercent,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get passed => $composableBuilder(
      column: $table.passed, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get resultsJson => $composableBuilder(
      column: $table.resultsJson, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get takenAt => $composableBuilder(
      column: $table.takenAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get synced => $composableBuilder(
      column: $table.synced, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get testType => $composableBuilder(
      column: $table.testType, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get serverValid => $composableBuilder(
      column: $table.serverValid, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get invalidReason => $composableBuilder(
      column: $table.invalidReason,
      builder: (column) => ColumnOrderings(column));
}

class $$LocalQuizAttemptsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $LocalQuizAttemptsTable> {
  $$LocalQuizAttemptsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get userId =>
      $composableBuilder(column: $table.userId, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<String> get clientId =>
      $composableBuilder(column: $table.clientId, builder: (column) => column);

  GeneratedColumn<int> get correctCount => $composableBuilder(
      column: $table.correctCount, builder: (column) => column);

  GeneratedColumn<int> get totalCount => $composableBuilder(
      column: $table.totalCount, builder: (column) => column);

  GeneratedColumn<int> get scorePercent => $composableBuilder(
      column: $table.scorePercent, builder: (column) => column);

  GeneratedColumn<bool> get passed =>
      $composableBuilder(column: $table.passed, builder: (column) => column);

  GeneratedColumn<String> get resultsJson => $composableBuilder(
      column: $table.resultsJson, builder: (column) => column);

  GeneratedColumn<DateTime> get takenAt =>
      $composableBuilder(column: $table.takenAt, builder: (column) => column);

  GeneratedColumn<bool> get synced =>
      $composableBuilder(column: $table.synced, builder: (column) => column);

  GeneratedColumn<String> get testType =>
      $composableBuilder(column: $table.testType, builder: (column) => column);

  GeneratedColumn<bool> get serverValid => $composableBuilder(
      column: $table.serverValid, builder: (column) => column);

  GeneratedColumn<String> get invalidReason => $composableBuilder(
      column: $table.invalidReason, builder: (column) => column);
}

class $$LocalQuizAttemptsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $LocalQuizAttemptsTable,
    LocalQuizAttemptRow,
    $$LocalQuizAttemptsTableFilterComposer,
    $$LocalQuizAttemptsTableOrderingComposer,
    $$LocalQuizAttemptsTableAnnotationComposer,
    $$LocalQuizAttemptsTableCreateCompanionBuilder,
    $$LocalQuizAttemptsTableUpdateCompanionBuilder,
    (
      LocalQuizAttemptRow,
      BaseReferences<_$LocalDatabase, $LocalQuizAttemptsTable,
          LocalQuizAttemptRow>
    ),
    LocalQuizAttemptRow,
    PrefetchHooks Function()> {
  $$LocalQuizAttemptsTableTableManager(
      _$LocalDatabase db, $LocalQuizAttemptsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalQuizAttemptsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalQuizAttemptsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalQuizAttemptsTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> userId = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<String> clientId = const Value.absent(),
            Value<int> correctCount = const Value.absent(),
            Value<int> totalCount = const Value.absent(),
            Value<int> scorePercent = const Value.absent(),
            Value<bool> passed = const Value.absent(),
            Value<String> resultsJson = const Value.absent(),
            Value<DateTime> takenAt = const Value.absent(),
            Value<bool> synced = const Value.absent(),
            Value<String> testType = const Value.absent(),
            Value<bool?> serverValid = const Value.absent(),
            Value<String?> invalidReason = const Value.absent(),
          }) =>
              LocalQuizAttemptsCompanion(
            id: id,
            userId: userId,
            moduleId: moduleId,
            clientId: clientId,
            correctCount: correctCount,
            totalCount: totalCount,
            scorePercent: scorePercent,
            passed: passed,
            resultsJson: resultsJson,
            takenAt: takenAt,
            synced: synced,
            testType: testType,
            serverValid: serverValid,
            invalidReason: invalidReason,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> userId = const Value.absent(),
            required String moduleId,
            required String clientId,
            required int correctCount,
            required int totalCount,
            required int scorePercent,
            required bool passed,
            required String resultsJson,
            required DateTime takenAt,
            Value<bool> synced = const Value.absent(),
            Value<String> testType = const Value.absent(),
            Value<bool?> serverValid = const Value.absent(),
            Value<String?> invalidReason = const Value.absent(),
          }) =>
              LocalQuizAttemptsCompanion.insert(
            id: id,
            userId: userId,
            moduleId: moduleId,
            clientId: clientId,
            correctCount: correctCount,
            totalCount: totalCount,
            scorePercent: scorePercent,
            passed: passed,
            resultsJson: resultsJson,
            takenAt: takenAt,
            synced: synced,
            testType: testType,
            serverValid: serverValid,
            invalidReason: invalidReason,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$LocalQuizAttemptsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $LocalQuizAttemptsTable,
    LocalQuizAttemptRow,
    $$LocalQuizAttemptsTableFilterComposer,
    $$LocalQuizAttemptsTableOrderingComposer,
    $$LocalQuizAttemptsTableAnnotationComposer,
    $$LocalQuizAttemptsTableCreateCompanionBuilder,
    $$LocalQuizAttemptsTableUpdateCompanionBuilder,
    (
      LocalQuizAttemptRow,
      BaseReferences<_$LocalDatabase, $LocalQuizAttemptsTable,
          LocalQuizAttemptRow>
    ),
    LocalQuizAttemptRow,
    PrefetchHooks Function()>;
typedef $$CachedSectionTranslationsTableCreateCompanionBuilder
    = CachedSectionTranslationsCompanion Function({
  required String sectionId,
  required String moduleId,
  required String languageCode,
  Value<String?> title,
  required String contentJson,
  Value<int> rowid,
});
typedef $$CachedSectionTranslationsTableUpdateCompanionBuilder
    = CachedSectionTranslationsCompanion Function({
  Value<String> sectionId,
  Value<String> moduleId,
  Value<String> languageCode,
  Value<String?> title,
  Value<String> contentJson,
  Value<int> rowid,
});

class $$CachedSectionTranslationsTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedSectionTranslationsTable> {
  $$CachedSectionTranslationsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get sectionId => $composableBuilder(
      column: $table.sectionId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get languageCode => $composableBuilder(
      column: $table.languageCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => ColumnFilters(column));
}

class $$CachedSectionTranslationsTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedSectionTranslationsTable> {
  $$CachedSectionTranslationsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get sectionId => $composableBuilder(
      column: $table.sectionId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get moduleId => $composableBuilder(
      column: $table.moduleId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get languageCode => $composableBuilder(
      column: $table.languageCode,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => ColumnOrderings(column));
}

class $$CachedSectionTranslationsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedSectionTranslationsTable> {
  $$CachedSectionTranslationsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get sectionId =>
      $composableBuilder(column: $table.sectionId, builder: (column) => column);

  GeneratedColumn<String> get moduleId =>
      $composableBuilder(column: $table.moduleId, builder: (column) => column);

  GeneratedColumn<String> get languageCode => $composableBuilder(
      column: $table.languageCode, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get contentJson => $composableBuilder(
      column: $table.contentJson, builder: (column) => column);
}

class $$CachedSectionTranslationsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedSectionTranslationsTable,
    CachedSectionTranslationRow,
    $$CachedSectionTranslationsTableFilterComposer,
    $$CachedSectionTranslationsTableOrderingComposer,
    $$CachedSectionTranslationsTableAnnotationComposer,
    $$CachedSectionTranslationsTableCreateCompanionBuilder,
    $$CachedSectionTranslationsTableUpdateCompanionBuilder,
    (
      CachedSectionTranslationRow,
      BaseReferences<_$LocalDatabase, $CachedSectionTranslationsTable,
          CachedSectionTranslationRow>
    ),
    CachedSectionTranslationRow,
    PrefetchHooks Function()> {
  $$CachedSectionTranslationsTableTableManager(
      _$LocalDatabase db, $CachedSectionTranslationsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedSectionTranslationsTableFilterComposer(
                  $db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedSectionTranslationsTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedSectionTranslationsTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> sectionId = const Value.absent(),
            Value<String> moduleId = const Value.absent(),
            Value<String> languageCode = const Value.absent(),
            Value<String?> title = const Value.absent(),
            Value<String> contentJson = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedSectionTranslationsCompanion(
            sectionId: sectionId,
            moduleId: moduleId,
            languageCode: languageCode,
            title: title,
            contentJson: contentJson,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String sectionId,
            required String moduleId,
            required String languageCode,
            Value<String?> title = const Value.absent(),
            required String contentJson,
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedSectionTranslationsCompanion.insert(
            sectionId: sectionId,
            moduleId: moduleId,
            languageCode: languageCode,
            title: title,
            contentJson: contentJson,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedSectionTranslationsTableProcessedTableManager
    = ProcessedTableManager<
        _$LocalDatabase,
        $CachedSectionTranslationsTable,
        CachedSectionTranslationRow,
        $$CachedSectionTranslationsTableFilterComposer,
        $$CachedSectionTranslationsTableOrderingComposer,
        $$CachedSectionTranslationsTableAnnotationComposer,
        $$CachedSectionTranslationsTableCreateCompanionBuilder,
        $$CachedSectionTranslationsTableUpdateCompanionBuilder,
        (
          CachedSectionTranslationRow,
          BaseReferences<_$LocalDatabase, $CachedSectionTranslationsTable,
              CachedSectionTranslationRow>
        ),
        CachedSectionTranslationRow,
        PrefetchHooks Function()>;

class $LocalDatabaseManager {
  final _$LocalDatabase _db;
  $LocalDatabaseManager(this._db);
  $$CachedModulesTableTableManager get cachedModules =>
      $$CachedModulesTableTableManager(_db, _db.cachedModules);
  $$CachedTranslationsTableTableManager get cachedTranslations =>
      $$CachedTranslationsTableTableManager(_db, _db.cachedTranslations);
  $$CachedSectionsTableTableManager get cachedSections =>
      $$CachedSectionsTableTableManager(_db, _db.cachedSections);
  $$CachedMediaTableTableManager get cachedMedia =>
      $$CachedMediaTableTableManager(_db, _db.cachedMedia);
  $$CachedVideosTableTableManager get cachedVideos =>
      $$CachedVideosTableTableManager(_db, _db.cachedVideos);
  $$LocalProgressTableTableManager get localProgress =>
      $$LocalProgressTableTableManager(_db, _db.localProgress);
  $$PendingSyncTableTableManager get pendingSync =>
      $$PendingSyncTableTableManager(_db, _db.pendingSync);
  $$AppSettingsTableTableManager get appSettings =>
      $$AppSettingsTableTableManager(_db, _db.appSettings);
  $$InstalledReleasesTableTableManager get installedReleases =>
      $$InstalledReleasesTableTableManager(_db, _db.installedReleases);
  $$LocalAiQuestionsTableTableManager get localAiQuestions =>
      $$LocalAiQuestionsTableTableManager(_db, _db.localAiQuestions);
  $$RagMetadataTableTableManager get ragMetadata =>
      $$RagMetadataTableTableManager(_db, _db.ragMetadata);
  $$ContentChunksTableTableManager get contentChunks =>
      $$ContentChunksTableTableManager(_db, _db.contentChunks);
  $$CachedQuizQuestionsTableTableManager get cachedQuizQuestions =>
      $$CachedQuizQuestionsTableTableManager(_db, _db.cachedQuizQuestions);
  $$LocalQuizAttemptsTableTableManager get localQuizAttempts =>
      $$LocalQuizAttemptsTableTableManager(_db, _db.localQuizAttempts);
  $$CachedSectionTranslationsTableTableManager get cachedSectionTranslations =>
      $$CachedSectionTranslationsTableTableManager(
          _db, _db.cachedSectionTranslations);
}
