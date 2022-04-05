from enum import Enum
from onevizion import LogLevel, Trackor, WorkPlan, Task, HTTPBearerAuth
import json
import re
import requests


class Integration:
    def __init__(self, ov_integration_log, source_trackor, destination_trackor, data_trackor):
        self.integration_log = ov_integration_log
        self.source_trackor = source_trackor
        self.destination_trackor = destination_trackor
        self.data_trackor = data_trackor

    def start(self):
        self.integration_log.add(LogLevel.INFO, 'Starting Integration')

        source_trackors = self.source_trackor.get_source_trackors()
        len_source_trackors = len(source_trackors)
        if len_source_trackors == 0:
            self.integration_log.add(LogLevel.INFO, f'{self.source_trackor.ov_source_trackor_type_name} Trackors not found')
        else:
            self.integration_log.add(LogLevel.INFO, f'Found {len_source_trackors} {self.source_trackor.ov_source_trackor_type_name} Trackors')
            for source_trackor in source_trackors:
                self.data_handler(source_trackor)

        self.integration_log.add(LogLevel.INFO, 'Integration has been completed')

    def data_handler(self, trackor):
        source_trackor_id = trackor[self.source_trackor.ov_source_fields.ID]
        source_trigger = trackor[self.source_trackor.ov_source_fields.TRIGGER]
        source_clear_trigger = json.loads(trackor[self.source_trackor.ov_source_fields.CLEAR_TRIGGER])
        source_trackor_type = trackor[self.source_trackor.ov_source_fields.SOURCE_TRACKOR_TYPE]
        source_key_field = trackor[self.source_trackor.ov_source_fields.SOURCE_KEY_FIELD]
        source_wp = trackor[self.source_trackor.ov_source_fields.SOURCE_WP]
        destination_trackor_type = trackor[self.source_trackor.ov_source_fields.DESTINATION_TRACKOR_TYPE]
        destination_key_field = trackor[self.source_trackor.ov_source_fields.DESTINATION_KEY_FIELD]
        destination_wp = trackor[self.source_trackor.ov_source_fields.DESTINATION_WP]

        fields_list = self.source_trackor.ov_mapping_fields.get_list()
        mapping_trackor_fields = self.source_trackor.get_mapping_trackors(source_trackor_id, fields_list)
        len_mapping_trackor_fields = len(mapping_trackor_fields)
        if len_mapping_trackor_fields == 0:
            self.integration_log.add(LogLevel.INFO, f'{self.source_trackor.ov_mapping_trackor_type_name} Trackors have not been found. Integration is finished.')
            quit()

        self.integration_log.add(LogLevel.INFO, f'Found {len_mapping_trackor_fields} {self.source_trackor.ov_mapping_trackor_type_name} Trackors')
        field_list = self.data_trackor.get_field_lists(mapping_trackor_fields, source_key_field)
        field_dict, task_dict = self.data_trackor.get_dicts(mapping_trackor_fields)

        is_field_clean_trigger = False
        is_clean_trigger_task = False
        source_data = self.data_trackor.get_trackor_data(source_trackor_type, field_list, source_trigger)
        len_source_data = len(source_data)
        if len_source_data == 0:
            self.integration_log.add(LogLevel.INFO, 'No data found for transfer')
        else:
            self.integration_log.add(LogLevel.INFO, f'Found {len_source_data} {source_trackor_type} Trackor data to transfer')

        for data in source_data:
            trackor_id = data[self.source_trackor.ov_source_fields.ID]
            trackor_key = data[source_key_field]
            clean_trigger_dict = {self.source_trackor.ov_source_fields.ID: trackor_id}
            dest_key_dict = {destination_key_field: trackor_key}
            self.integration_log.add(LogLevel.INFO, f'Get {source_trackor_type} Trackor data from - {trackor_key}')

            destination_trackor = None
            fields_dict = self.data_trackor.update_fields_dict(field_dict, data)
            if len(fields_dict) > 0:
                destination_trackor, is_field_clean_trigger = self.destination_trackor.update_field_data(destination_trackor_type, trackor_key, dest_key_dict, \
                                                                                                            fields_dict)
            else:
                is_field_clean_trigger = True

            if len(task_dict) > 0:
                if destination_trackor is None:
                    destination_trackor = self.destination_trackor.get_destination_trackor(destination_trackor_type, dest_key_dict, trackor_key)
                    if destination_trackor is None:
                        continue

                destination_trackor_id = destination_trackor[self.source_trackor.ov_source_fields.ID]
                source_workplan_id = self.data_trackor.get_workplan_id(trackor_id, source_wp)
                tasks_dict = self.data_trackor.get_task_data(source_workplan_id, task_dict)
                destination_workplan_id = self.destination_trackor.get_workplan_id(destination_trackor_id, destination_wp)
                is_clean_trigger_task = self.destination_trackor.update_task_data(destination_workplan_id, tasks_dict, trackor_key)
            else:
                is_clean_trigger_task = True

            if is_field_clean_trigger and is_clean_trigger_task:
                self.data_trackor.clean_trigger(source_trackor_type, trackor_key, clean_trigger_dict, source_clear_trigger)
            else:
                self.integration_log.add(LogLevel.INFO, f'Trigger has not been updated for {trackor_key}')


class SourceTrackor:
    def __init__(self, integration_log, ov_url, ov_access_key, ov_secret_key, ov_source_trackor_type, ov_source_fields, ov_source_types, ov_source_status, \
                    ov_mapping_trackor_type, ov_mapping_fields, ov_mapping_types):
        self.integration_log = integration_log
        self.ov_mapping_trackor_type_name = ov_mapping_trackor_type
        self.ov_source_trackor_type_name = ov_source_trackor_type
        self.ov_source_fields = SourceTrackorFields(ov_source_fields)
        self.ov_source_types = SourceTrackorTypes(ov_source_types)
        self.ov_source_status = SourceTrackorStatuses(ov_source_status)
        self.ov_mapping_fields = MappingTrackorFields(ov_mapping_fields)
        self.ov_mapping_types = MappingTrackorTypes(ov_mapping_types)
        self.ov_source_trackor_type = Trackor(trackorType=ov_source_trackor_type, URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)
        self.ov_mapping_trackor_type = Trackor(trackorType=ov_mapping_trackor_type, URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)

    def get_source_trackors(self):
        self.ov_source_trackor_type.read(
            filters={self.ov_source_fields.STATUS: self.ov_source_status.ENABLED,
                     self.ov_source_fields.TYPE: self.ov_source_types.OV_TO_OV},
            fields=self.ov_source_fields.get_list()
        )

        if len(self.ov_source_trackor_type.errors) == 0:
            return self.ov_source_trackor_type.jsonData

        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to SourceTrackor.get_source_trackors: Exception [{self.ov_source_trackor_type.errors}]')
            return None

    def get_mapping_trackors(self, parent_trackor_id, fields_list):
        self.ov_mapping_trackor_type.read(
            filters={f'{self.ov_source_trackor_type_name}.{self.ov_source_fields.ID}': parent_trackor_id},
            fields=fields_list
        )

        if len(self.ov_mapping_trackor_type.errors) == 0:
            return self.ov_mapping_trackor_type.jsonData

        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to SourceTrackor.get_source_trackors: Exception [{self.ov_mapping_trackor_type.errors}]')
            return None


class DataTrackor:
    def __init__(self, integration_log, ov_url, ov_access_key, ov_secret_key, ov_mapping_fields, ov_mapping_types, ov_task_fields):
        self.integration_log = integration_log
        self.ov_url = ov_url
        self.ov_access_key = ov_access_key
        self.ov_secret_key = ov_secret_key
        self.ov_mapping_fields = MappingTrackorFields(ov_mapping_fields)
        self.ov_mapping_types = MappingTrackorTypes(ov_mapping_types)
        self.ov_task_fields = TaskFields(ov_task_fields)
        self.workplan = WorkPlan(URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)
        self.task = Task(URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)

    def get_trackor_data(self, trackor_type, fields_list, source_trigger):
        data_trackor_type = Trackor(trackorType=trackor_type, URL=self.ov_url, userName=self.ov_access_key, password=self.ov_secret_key, isTokenAuth=True)
        data_trackor_type.read(
            fields=fields_list,
            search=source_trigger
        )
        if len(data_trackor_type.errors) == 0:
            return data_trackor_type.jsonData

        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DataTrackor.get_trackor_data: Exception [{data_trackor_type.errors}]')
            return None

    def get_field_lists(self, trackor_fields, key_field):
        field_list = []

        for field in trackor_fields:
            if field[self.ov_mapping_fields.CLASS] == self.ov_mapping_types.FIELD_TRANSFER:
                source_field_name = field[self.ov_mapping_fields.SOURCE_FIELD_NAME]

                if source_field_name is None:
                    self.integration_log.add(LogLevel.WARNING, f'DataTrackor.get_field_lists: One or more fields are empty - ' \
                                                f'{self.ov_mapping_fields.SOURCE_FIELD_NAME}')

                else:
                    field_list.append(source_field_name)

            elif field[self.ov_mapping_fields.CLASS] != self.ov_mapping_types.TASK_TRANSFER:
                self.integration_log.add(LogLevel.INFO, f'DataTrackor.get_field_lists: Unknown class name - {field[self.ov_mapping_fields.CLASS]}')

        field_list.append(key_field)

        return field_list

    def get_dicts(self, trackor_fields):
        field_dict = {}
        task_dict = {}
        for field in trackor_fields:
            if field[self.ov_mapping_fields.CLASS] == self.ov_mapping_types.FIELD_TRANSFER:
                source_field_name = field[self.ov_mapping_fields.SOURCE_FIELD_NAME]
                destination_field_name = field[self.ov_mapping_fields.DESTINATION_FIELD_NAME]

                if source_field_name is None or destination_field_name is None:
                    self.integration_log.add(LogLevel.WARNING, f'DataTrackor.get_dicts: One or more fields are empty - ' \
                                                f'{self.ov_mapping_fields.SOURCE_FIELD_NAME}, {self.ov_mapping_fields.DESTINATION_FIELD_NAME}')

                else:
                    field_dict.update({destination_field_name: source_field_name})

            elif field[self.ov_mapping_fields.CLASS] == self.ov_mapping_types.TASK_TRANSFER:
                source_order_number = field[self.ov_mapping_fields.SOURCE_ORDER_NUMBER]
                source_task_data = field[self.ov_mapping_fields.SOURCE_TASK_DATA]
                destination_order_number = field[self.ov_mapping_fields.DESTINATION_ORDER_NUMBER]

                if source_order_number is None or source_task_data is None or destination_order_number is None:
                    self.integration_log.add(LogLevel.WARNING, f'DataTrackor.get_dicts: One or more fields are empty - ' \
                                                f'{self.ov_mapping_fields.SOURCE_ORDER_NUMBER}, {self.ov_mapping_fields.SOURCE_TASK_DATA}, ' \
                                                    f'{self.ov_mapping_fields.DESTINATION_ORDER_NUMBER}')

                else:
                    task_dict.update({destination_order_number: {source_order_number: source_task_data}})

            else:
                self.integration_log.add(LogLevel.INFO, f'DataTrackor.get_dicts: Unknown class name - {field[self.ov_mapping_fields.CLASS]}')
                continue

        return field_dict, task_dict

    def update_fields_dict(self, fields_dict, data):
        upd_fields_dict = fields_dict.copy()
        for field_dict in upd_fields_dict.items():
            upd_fields_dict[field_dict[0]] = data[field_dict[1]]

        return upd_fields_dict

    def clean_trigger(self, trackor_type, trackor_key, filter_dict, field_dict):        
        data_trackor_type = Trackor(trackorType=trackor_type, URL=self.ov_url, userName=self.ov_access_key, password=self.ov_secret_key, isTokenAuth=True)
        data_trackor_type.update(
            filters=filter_dict, 
            fields=field_dict
        )

        if len(data_trackor_type.errors) == 0:
            self.integration_log.add(LogLevel.INFO, f'Trigger has been updated for {trackor_key}')
        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DataTrackor.clean_trigger for {trackor_key}: Exception [{data_trackor_type.errors}]')

    def get_workplan_id(self, trackor_id, workplan_name):
        workplans = self.get_workplan(trackor_id, workplan_name)

        workplan_id = None
        for workplan in workplans:
            if workplan[self.ov_task_fields.WP_ACTIVE] is True:
                workplan_id = workplan[self.ov_task_fields.WP_ID]

        return workplan_id

    def get_workplan(self, trackor_id, workplan_name):
        self.workplan.read(
            trackorId=trackor_id,
            workplanTemplate=workplan_name
        )

        if len(self.workplan.errors) == 0:
            return self.workplan.jsonData
        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DataTrackor.get_workplan: Exception [{self.workplan.errors}]')
            return None

    def get_task_data(self, workplan_id, tasks_dict):
        upd_task_dict = {}

        for task_dict in tasks_dict.items():
            for fd in task_dict[1].items():
                source_order_number = fd[0]
                source_task_data = fd[1]

            self.task.read(
                workplanId=workplan_id,
                orderNumber=source_order_number
            )

            task_data_search = re.search('\.', source_task_data)
            data = None
            if task_data_search is None:
                data = self.task.jsonData[source_task_data]
                upd_task_dict.update({task_dict[0]: {source_task_data: data}})
            else:
                task_data_split = re.split('\.', source_task_data, 2)
                dynamic_dates = self.task.jsonData[task_data_split[0]]
                for dd in dynamic_dates:
                    if dd[self.ov_task_fields.TASK_LABEL] == task_data_split[1]:
                        data = dd[task_data_split[2]]
                        upd_task_dict.update({task_dict[0]: {self.ov_task_fields.TASK_LABEL: task_data_split[1], task_data_split[2]: data}})

        return upd_task_dict


class DestinationTrackor:
    def __init__(self, integration_log, ov_url, ov_access_key, ov_secret_key, ov_task_fields, ov_source_fields):
        self.integration_log = integration_log
        self.ov_url = ov_url
        self.ov_access_key = ov_access_key
        self.ov_secret_key = ov_secret_key
        self.ov_task_fields = TaskFields(ov_task_fields)
        self.ov_source_fields = SourceTrackorFields(ov_source_fields)
        self.workplan = WorkPlan(URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)
        self.task = Task(URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)

    def get_destination_trackor(self, trackor_type, filter_dict, trackor_key):
        dest_trackor_type = Trackor(trackorType=trackor_type, URL=self.ov_url, userName=self.ov_access_key, password=self.ov_secret_key, isTokenAuth=True)
        dest_trackor_type.read(
            filters=filter_dict
        )

        if len(dest_trackor_type.errors) == 0:
            if len(dest_trackor_type.jsonData) == 0:
                self.integration_log.add(LogLevel.WARNING, f'Not found {trackor_key} for Trackor Type {trackor_type} - Tasks won''t be updated')
                return None
            else:
                return dest_trackor_type.jsonData[0]

        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DestinationTrackor.get_destination_trackor for {trackor_key}:' \
                                        f'Exception [{dest_trackor_type.errors}]')
            return None

    def update_field_data(self, trackor_type, trackor_key, filter_dict, field_dict):
        dest_trackor_type = Trackor(trackorType=trackor_type, URL=self.ov_url, userName=self.ov_access_key, password=self.ov_secret_key, isTokenAuth=True)

        dest_trackor_type.update(
            filters=filter_dict, 
            fields=field_dict
        )

        if len(dest_trackor_type.errors) == 0:
            self.integration_log.add(LogLevel.INFO, f'Fields Data updated for {trackor_key}')
            return dest_trackor_type.jsonData, True
        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DestinationTrackor.update_field_data for {trackor_key}:' \
                                        f'Exception [{dest_trackor_type.errors}]')
            return None, False

    def get_workplan_id(self, trackor_id, workplan_name):
        workplans = self.get_workplan(trackor_id, workplan_name)

        workplan_id = None
        for workplan in workplans:
            if workplan[self.ov_task_fields.WP_ACTIVE] is True:
                workplan_id = workplan[self.ov_task_fields.WP_ID]

        return workplan_id

    def get_workplan(self, trackor_id, workplan_name):
        self.workplan.read(
            trackorId=trackor_id,
            workplanTemplate=workplan_name
        )

        if len(self.workplan.errors) == 0:
            return self.workplan.jsonData
        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DestinationTrackor.get_workplan: Exception [{self.workplan.errors}]')
            return None

    def update_task_data(self, workplan_id, tasks_dict, trackor_key):
        is_clean_trigger = False
        is_update_task_warning = False
        for task in tasks_dict.items():
            task_data = self.get_task_data(workplan_id, task[0])
            if task_data is None:
                continue

            order_number = task[0]
            task_dict = task[1]
            task_id = task_data[self.ov_task_fields.WP_ID]
            task_fields = {}
            dynamic_dates_list = []
            if len(task_dict) == 1:
                task_fields = task_dict
                is_clean_trigger = self.update_task(task_id, order_number, trackor_key, task_fields, dynamic_dates_list)
                if is_clean_trigger is False:
                    is_update_task_warning = True

            else:
                task_label = None
                for task in task_dict.items():
                    if task[0] == self.ov_task_fields.TASK_LABEL:
                        task_label = task[1]
                
                if task_label is None:
                    self.integration_log.add(LogLevel.WARNING, f'Failed to DestinationTrackor.update_task_data for {trackor_key}: Exception ["' \
                                                f'{self.ov_task_fields.TASK_LABEL}" is not found in the dictionary]')

                else:
                    dynamic_dates = task_data[self.ov_task_fields.TASK_DYNAMIC_DATES]
                    for dynamic_date in dynamic_dates:
                        if dynamic_date[self.ov_task_fields.TASK_LABEL] == task_label:
                            task_dict[self.ov_task_fields.TASK_DATE_TYPE] = dynamic_date[self.ov_task_fields.TASK_DATE_TYPE]

                    dynamic_dates_list.append(task_dict)

                is_clean_trigger = self.update_task(task_id, order_number, trackor_key, task_fields, dynamic_dates_list)
                if is_clean_trigger is False:
                    is_update_task_warning = True

        if is_update_task_warning is True:
            is_clean_trigger = False

        return is_clean_trigger

    def get_task_data(self, workplan_id, order_number):
        self.task.read(
            workplanId=workplan_id,
            orderNumber=order_number
        )

        if len(self.task.errors) == 0:
            return self.task.jsonData
        
        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DestinationTrackor.get_task_data: Exception [{self.task.errors}]')
            return None

    def update_task(self, task_id, order_number, trackor_key, fields={}, dynamic_dates=[]):
        if len(dynamic_dates)>0:
            fields[self.ov_task_fields.TASK_DYNAMIC_DATES] = dynamic_dates

        url = f'https://{self.ov_url}/api/v3/tasks/{task_id}'
        auth = HTTPBearerAuth(self.ov_access_key, self.ov_secret_key)
        header = {'content-type': 'application/x-www-form-urlencoded'}
        answer = requests.patch(url, headers=header, data=json.dumps(fields), auth=auth)

        if answer.ok:
            self.integration_log.add(LogLevel.INFO, f'Task Date updated for Order Number {order_number} for {trackor_key}')
            return True
        else:
            self.integration_log.add(LogLevel.WARNING, f'Failed to DestinationTrackor.update_task for Order Number {order_number}' \
                                        f'for {trackor_key}: Exception [{answer.text}]')
            return False

class SourceTrackorFields:
    def __init__(self, ov_source_fields):
        self.ID = ov_source_fields[SourceTrackorField.ID.value]
        self.KEY = ov_source_fields[SourceTrackorField.KEY.value]
        self.TYPE = ov_source_fields[SourceTrackorField.TYPE.value]
        self.STATUS = ov_source_fields[SourceTrackorField.STATUS.value]
        self.TRIGGER = ov_source_fields[SourceTrackorField.TRIGGER.value]
        self.CLEAR_TRIGGER = ov_source_fields[SourceTrackorField.CLEAR_TRIGGER.value]
        self.SOURCE_TRACKOR_TYPE = ov_source_fields[SourceTrackorField.SOURCE_TRACKOR_TYPE.value]
        self.SOURCE_KEY_FIELD = ov_source_fields[SourceTrackorField.SOURCE_KEY_FIELD.value]
        self.SOURCE_WP = ov_source_fields[SourceTrackorField.SOURCE_WP.value]
        self.DESTINATION_TRACKOR_TYPE = ov_source_fields[SourceTrackorField.DESTINATION_TRACKOR_TYPE.value]
        self.DESTINATION_KEY_FIELD = ov_source_fields[SourceTrackorField.DESTINATION_KEY_FIELD.value]
        self.DESTINATION_WP = ov_source_fields[SourceTrackorField.DESTINATION_WP.value]

    def get_list(self):
        return [self.KEY, self.TRIGGER, self.CLEAR_TRIGGER, self.SOURCE_TRACKOR_TYPE, self.SOURCE_KEY_FIELD, self.SOURCE_WP, self.DESTINATION_TRACKOR_TYPE, \
                    self.DESTINATION_KEY_FIELD, self.DESTINATION_WP]

class SourceTrackorTypes:
    def __init__(self, ov_source_types):
        self.OV_TO_OV = ov_source_types[SourceTrackorType.OV_TO_OV.value]


class MappingTrackorTypes:
    def __init__(self, ov_mapping_types):
        self.FIELD_TRANSFER = ov_mapping_types[MappingTrackorType.FIELD_TRANSFER.value]
        self.TASK_TRANSFER = ov_mapping_types[MappingTrackorType.TASK_TRANSFER.value]


class SourceTrackorStatuses:
    def __init__(self, ov_source_status):
        self.ENABLED = ov_source_status[SourceTrackorStatus.ENABLED.value]

class MappingTrackorFields:
    def __init__(self, ov_mapping_fields):
        self.CLASS = ov_mapping_fields[MappingTrackorField.CLASS.value]
        self.SOURCE_FIELD_NAME = ov_mapping_fields[MappingTrackorField.SOURCE_FIELD_NAME.value]
        self.SOURCE_FIELD_TRACKOR_TYPE = ov_mapping_fields[MappingTrackorField.SOURCE_FIELD_TRACKOR_TYPE.value]
        self.DESTINATION_FIELD_NAME = ov_mapping_fields[MappingTrackorField.DESTINATION_FIELD_NAME.value]
        self.DESTINATION_FIELD_TRACKOR_TYPE = ov_mapping_fields[MappingTrackorField.DESTINATION_FIELD_TRACKOR_TYPE.value]

        self.SOURCE_WP_NAME = ov_mapping_fields[MappingTrackorField.SOURCE_WP_NAME.value]
        self.SOURCE_ORDER_NUMBER = ov_mapping_fields[MappingTrackorField.SOURCE_ORDER_NUMBER.value]
        self.SOURCE_TASK_DATA = ov_mapping_fields[MappingTrackorField.SOURCE_TASK_DATA.value]
        self.DESTINATION_WP_NAME = ov_mapping_fields[MappingTrackorField.DESTINATION_WP_NAME.value]
        self.DESTINATION_ORDER_NUMBER = ov_mapping_fields[MappingTrackorField.DESTINATION_ORDER_NUMBER.value]

    def get_list(self):
        return [self.CLASS, self.SOURCE_FIELD_NAME, self.SOURCE_FIELD_TRACKOR_TYPE, self.DESTINATION_FIELD_NAME, self.DESTINATION_FIELD_TRACKOR_TYPE, \
                    self.SOURCE_WP_NAME, self.SOURCE_ORDER_NUMBER, self.SOURCE_TASK_DATA, self.DESTINATION_WP_NAME, self.DESTINATION_ORDER_NUMBER]


class TaskFields:
    def __init__(self, ov_task_fields):
        self.WP_ID = ov_task_fields[TaskField.WP_ID.value]
        self.WP_ACTIVE = ov_task_fields[TaskField.WP_ACTIVE.value]
        self.TASK_LABEL = ov_task_fields[TaskField.TASK_LABEL.value]
        self.TASK_DATE_TYPE = ov_task_fields[TaskField.TASK_DATE_TYPE.value]
        self.TASK_DYNAMIC_DATES = ov_task_fields[TaskField.TASK_DYNAMIC_DATES.value]


class SourceTrackorField(Enum):
    ID = 'id'
    KEY = 'key'
    TYPE = 'type'
    STATUS = 'status'
    TRIGGER = 'trigger'
    CLEAR_TRIGGER = 'clearTrigger'
    SOURCE_TRACKOR_TYPE = 'sourceTrackorType'
    SOURCE_KEY_FIELD = 'sourceKeyField'
    SOURCE_WP = 'sourceWP'
    DESTINATION_TRACKOR_TYPE = 'destinationTrackorType'
    DESTINATION_KEY_FIELD = 'destinationKeyField'
    DESTINATION_WP = 'destinationWP'


class SourceTrackorStatus(Enum):
    ENABLED = 'enabled'


class SourceTrackorType(Enum):
    OV_TO_OV = 'ovToOv'


class MappingTrackorType(Enum):
    FIELD_TRANSFER = 'fieldTransfer'
    TASK_TRANSFER = 'taskTransfer'


class MappingTrackorField(Enum):
    CLASS = 'class'
    SOURCE_FIELD_NAME = 'sourceFieldName'
    SOURCE_FIELD_TRACKOR_TYPE = 'sourceFieldTrackorType'
    DESTINATION_FIELD_NAME = 'destinationFieldName'
    DESTINATION_FIELD_TRACKOR_TYPE = 'destinationFieldTrackorType'

    SOURCE_WP_NAME = 'sourceWPName'
    SOURCE_ORDER_NUMBER = 'sourceOrderNumber'
    SOURCE_TASK_DATA = 'sourceTaskData'
    DESTINATION_WP_NAME = 'destinationWPName'
    DESTINATION_ORDER_NUMBER = 'destinationOrderNumber'


class TaskField(Enum):
    WP_ID = 'wpId'
    WP_ACTIVE = 'wpActive'
    TASK_LABEL = 'taskLabel'
    TASK_DATE_TYPE = 'taskDateType'
    TASK_DYNAMIC_DATES = 'taskDynamicDates'
