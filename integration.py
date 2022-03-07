from enum import Enum
from onevizion import LogLevel, Trackor


class Integration:
    def __init__(self, ov_integration_log, source_trackor, mapping_trackor, destination_trackor):
        self.integration_log = ov_integration_log
        self.source_trackor = source_trackor
        self.mapping_trackor = mapping_trackor
        self.destination_trackor = destination_trackor

    def start(self):
        # self.integration_log.add(LogLevel.INFO, 'Starting Integration')

        source_trackors = self.source_trackor.get_trackors()
        if len(source_trackors) == 0:
            # self.integration_log.add(LogLevel.INFO, 'Source Trackors have not been found. Integration is finished.')
            raise Exception('Source Trackors have not been found. Integration is finished.')

        mapping_fields_list = self.mapping_trackor.ov_mapping_fields.get_list()
        mapping_tasks_list = self.mapping_trackor.ov_mapping_tasks.get_list()
        for source_trackor in source_trackors:
            source_trackor_id = source_trackor[self.source_trackor.ov_source_fields.ID]
            mapping_fields_trackors = self.mapping_trackor.get_trackors(source_trackor_id, mapping_fields_list)
            for mapping_fields_trackor in mapping_fields_trackors:
                source_field_name = mapping_fields_trackor[self.mapping_trackor.ov_mapping_fields.SOURCE_FIELD_NAME]
                source_trackor_type = mapping_fields_trackor[self.mapping_trackor.ov_mapping_fields.SOURCE_FIELD_TRACKOR_TYPE]
                destination_field_name = mapping_fields_trackor[self.mapping_trackor.ov_mapping_fields.DESTINATION_FIELD_NAME]
                destination_trackor_type = mapping_fields_trackor[self.mapping_trackor.ov_mapping_fields.DESTINATION_FIELD_TRACKOR_TYPE]

                source_data = self.source_trackor.get_data(source_trackor_type, source_field_name)


                return
            mapping_tasks_trackors = self.mapping_trackor.get_trackors(source_trackor_id, mapping_tasks_list)
            for mapping_tasks_trackor in mapping_tasks_trackors:
                return

        # self.integration_log.add(LogLevel.INFO, 'Integration has been completed')


class SourceTrackor:
    def __init__(self, ov_url, ov_access_key, ov_secret_key, ov_source_trackor_type, ov_source_fields, ov_source_statuses, ov_source_types):
        self.ov_url = ov_url
        self.ov_access_key = ov_access_key
        self.ov_secret_key = ov_secret_key
        self.ov_source_fields = SourceTrackorFields(ov_source_fields)
        self.ov_source_statuses = SourceTrackorStatuses(ov_source_statuses)
        self.ov_source_types = SourceTrackorTypes(ov_source_types)
        self.ov_source_trackor_type = Trackor(trackorType=ov_source_trackor_type, URL=ov_url, userName=ov_access_key, \
                                                password=ov_secret_key, isTokenAuth=True)

    def get_trackors(self):
        self.ov_source_trackor_type.read(
            filters={self.ov_source_fields.STATUS: self.ov_source_statuses.ENABLED,
                     self.ov_source_fields.TYPE: self.ov_source_types.OV_TO_OV}
        )

        return self.ov_source_trackor_type.jsonData

    def get_data(self, trackor_type, fields_list):
        trackor_type = Trackor(trackorType=trackor_type, URL=self.ov_url, userName=self.ov_access_key, \
                                    password=self.ov_secret_key, isTokenAuth=True)
        trackor_type.read(
            fields=[fields_list]
        )

        return trackor_type.jsonData


class MappingTrackor:
    def __init__(self, ov_url, ov_access_key, ov_secret_key, ov_source_trackor_type, ov_mapping_trackor_type, ov_mapping_fields, ov_mapping_tasks, ov_source_fields):
        self.ov_url = ov_url
        self.ov_source_trackor_type = ov_source_trackor_type
        self.ov_source_fields = SourceTrackorFields(ov_source_fields)
        self.ov_mapping_fields = MappingTrackorFields(ov_mapping_fields)
        self.ov_mapping_tasks = MappingTrackorTasks(ov_mapping_tasks)
        self.ov_mapping_trackor_type = Trackor(trackorType=ov_mapping_trackor_type, URL=ov_url, userName=ov_access_key, \
                                                    password=ov_secret_key, isTokenAuth=True)

    def get_trackors(self, parent_trackor_id, fields_list):
        self.ov_mapping_trackor_type.read(
            filters={f'{self.ov_source_trackor_type}.{self.ov_source_fields.ID}': parent_trackor_id},
            fields=fields_list
        )

        return self.ov_mapping_trackor_type.jsonData


class DestinationTrackor:
    def __init__(self, ov_url, ov_access_key, ov_secret_key):
        self.ov_url = ov_url,
        self.ov_access_key = ov_access_key,
        self.ov_secret_key = ov_secret_key

    def update(self, trackor_type):
        trackor_type = Trackor(trackorType=trackor_type, URL=self.ov_url, userName=self.ov_access_key, \
                                    password=self.ov_secret_key, isTokenAuth=True)
        trackor_type.update(
            filters={},
            fields={},
            parents={}
        )


class SourceTrackorFields:
    def __init__(self, ov_source_fields):
        self.STATUS = ov_source_fields[SourceTrackorField.STATUS.value]
        self.TYPE = ov_source_fields[SourceTrackorField.TYPE.value]
        self.ID = ov_source_fields[SourceTrackorField.ID.value]
        self.KEY = ov_source_fields[SourceTrackorField.KEY.value]


class SourceTrackorStatuses:
    def __init__(self, ov_source_statuses):
        self.ENABLED = ov_source_statuses[SourceTrackorStatus.ENABLED.value]


class SourceTrackorTypes:
    def __init__(self, ov_source_types):
        self.OV_TO_OV = ov_source_types[SourceTrackorType.OV_TO_OV.value]


class MappingTrackorFields:
    def __init__(self, ov_mapping_fields):
        self.SOURCE_FIELD_NAME = ov_mapping_fields[MappingTrackorField.SOURCE_FIELD_NAME.value]
        self.SOURCE_FIELD_TRACKOR_TYPE = ov_mapping_fields[MappingTrackorField.SOURCE_FIELD_TRACKOR_TYPE.value]
        self.DESTINATION_FIELD_NAME = ov_mapping_fields[MappingTrackorField.DESTINATION_FIELD_NAME.value]
        self.DESTINATION_FIELD_TRACKOR_TYPE = ov_mapping_fields[MappingTrackorField.DESTINATION_FIELD_TRACKOR_TYPE.value]

    def get_list(self):
       return [self.SOURCE_FIELD_NAME, self.SOURCE_FIELD_TRACKOR_TYPE, self.DESTINATION_FIELD_NAME, self.DESTINATION_FIELD_TRACKOR_TYPE]

class MappingTrackorTasks:
    def __init__(self, ov_mapping_tasks):
        self.SOURCE_WP_NAME = ov_mapping_tasks[MappingTrackorTask.SOURCE_WP_NAME.value]
        self.SOURCE_TASK = ov_mapping_tasks[MappingTrackorTask.SOURCE_TASK.value]
        self.SOURCE_SF = ov_mapping_tasks[MappingTrackorTask.SOURCE_SF.value]
        self.SOURCE_DATE_PAIR = ov_mapping_tasks[MappingTrackorTask.SOURCE_DATE_PAIR.value]
        self.DESTINATION_WP_NAME = ov_mapping_tasks[MappingTrackorTask.DESTINATION_WP_NAME.value]
        self.DESTINATION_TASK = ov_mapping_tasks[MappingTrackorTask.DESTINATION_TASK.value]

    def get_list(self):
        return [self.SOURCE_WP_NAME, self.SOURCE_TASK, self.SOURCE_SF, self.SOURCE_DATE_PAIR, self.DESTINATION_WP_NAME, self.DESTINATION_TASK]


class SourceTrackorField(Enum):
    STATUS = 'status'
    TYPE = 'type'
    ID = 'id'
    KEY = 'key'


class SourceTrackorStatus(Enum):
    ENABLED = 'enabled'


class SourceTrackorType(Enum):
    OV_TO_OV = 'ovToOv'


class MappingTrackorField(Enum):
    SOURCE_FIELD_NAME = 'sourceFieldName'
    SOURCE_FIELD_TRACKOR_TYPE = 'sourceFieldTrackorType'
    DESTINATION_FIELD_NAME = 'destinationFieldName'
    DESTINATION_FIELD_TRACKOR_TYPE = 'destinationFieldTrackorType'


class MappingTrackorTask(Enum):
    SOURCE_WP_NAME = 'sourceWPName'
    SOURCE_TASK = 'sourceTask'
    SOURCE_SF = 'sourceSF'
    SOURCE_DATE_PAIR = 'sourceDatePair'
    DESTINATION_WP_NAME = 'destinationWPName'
    DESTINATION_TASK = 'destinationTask'
