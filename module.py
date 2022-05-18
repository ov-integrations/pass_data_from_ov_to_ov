from enum import Enum
from onevizion import LogLevel, Trackor, WorkPlan, Task, HTTPBearerAuth
import json
import re
import requests


class Module:
    def __init__(self, ov_module_log, data_handler, trackor_data, workplan_data):
        self._module_log = ov_module_log
        self._data_handler = data_handler
        self._trackor_data = trackor_data
        self._workplan_data = workplan_data

    def start(self):
        self._module_log.add(LogLevel.INFO, 'Starting Module')

        try:
            source_trackors = self._trackor_data.get_source_trackors()
        except Exception as e:
            self._module_log.add(LogLevel.WARNING, str(e))
            raise e

        len_source_trackors = len(source_trackors)
        if len_source_trackors == 0:
            self._module_log.add(LogLevel.INFO, f'{self._trackor_data._ov_source_trackor_type_name} Trackors not found')

        else:
            self._module_log.add(LogLevel.INFO, f'Found {len_source_trackors} {self._trackor_data._ov_source_trackor_type_name} Trackors')
            for source_trackor in source_trackors:
                source_data, field_dict, task_dict = self.get_source_data(source_trackor)
                if len(source_data) != 0:
                    self.update_destination_data(source_trackor, source_data, field_dict, task_dict)

        self._module_log.add(LogLevel.INFO, 'Module has been completed')

    def get_source_data(self, trackor):
        source_data = []
        source_trigger = trackor[self._trackor_data._ov_source_fields.trigger]
        source_key_field = trackor[self._trackor_data._ov_source_fields.source_key_field]
        source_trackor_id = trackor[self._trackor_data._ov_source_fields.id]
        source_trackor_type = trackor[self._trackor_data._ov_source_fields.source_trackor_type]
        fields_list = self._data_handler._ov_mapping_fields.get_list()

        try:
            mapping_trackor_fields = self._trackor_data.get_mapping_trackors(source_trackor_id, fields_list)
        except Exception as e:
            self._module_log.add(LogLevel.WARNING, str(e))
            raise e

        len_mapping_trackor_fields = len(mapping_trackor_fields)
        if len_mapping_trackor_fields == 0:
            self._module_log.add(LogLevel.INFO, f'{self._trackor_data.ov_mapping_trackor_type_name} Trackors have not been found.')

        else:
            self._module_log.add(LogLevel.INFO, f'Found {len_mapping_trackor_fields} {self._trackor_data._ov_mapping_trackor_type_name} Trackors')
            field_list = self._data_handler.get_field_lists(mapping_trackor_fields, source_key_field)
            field_dict, task_dict = self._data_handler.get_dicts(mapping_trackor_fields)

            try:
                source_data = self._trackor_data.get_trackor_data(source_trackor_type, field_list, source_trigger)
            except Exception as e:
                self._module_log.add(LogLevel.WARNING, str(e))

            len_source_data = len(source_data)
            if len_source_data == 0:
                self._module_log.add(LogLevel.INFO, 'No data found for transfer')

            else:
                self._module_log.add(LogLevel.INFO, f'Found {len_source_data} {source_trackor_type} Trackor data to transfer')

        return source_data, field_dict, task_dict

    def update_destination_data(self, trackor, source_data, field_dict, task_dict):
        source_key_field = trackor[self._trackor_data._ov_source_fields.source_key_field]
        source_trackor_type = trackor[self._trackor_data._ov_source_fields.source_trackor_type]
        source_clear_trigger = json.loads(trackor[self._trackor_data._ov_source_fields.clear_trigger])
        source_wp = trackor[self._trackor_data._ov_source_fields.source_wp]
        destination_trackor_type = trackor[self._trackor_data._ov_source_fields.destination_trackor_type]
        destination_key_field = trackor[self._trackor_data._ov_source_fields.destination_key_field]
        destination_wp = trackor[self._trackor_data._ov_source_fields.destination_wp]

        is_field_clean_trigger = False
        is_clean_trigger_task  = False
        for data in source_data:
            trackor_id = data[self._trackor_data._ov_source_fields.id]
            trackor_key = data[source_key_field]
            clean_trigger_dict = {self._trackor_data._ov_source_fields.id: trackor_id}
            dest_key_dict = {destination_key_field: trackor_key}
            self._module_log.add(LogLevel.INFO, f'Get {source_trackor_type} Trackor data from - {trackor_key}')

            is_field_clean_trigger, destination_trackor = self.update_field_data(field_dict, data, destination_trackor_type, dest_key_dict, trackor_key)
            is_clean_trigger_task = self.update_task_data(task_dict, destination_trackor, destination_trackor_type, dest_key_dict, destination_wp, trackor_key, \
                                                            trackor_id, source_wp)

            self.clean_trigger(is_field_clean_trigger, is_clean_trigger_task, source_trackor_type, clean_trigger_dict, source_clear_trigger, trackor_key)

    def update_field_data(self, field_dict, data, destination_trackor_type, dest_key_dict, trackor_key):
        destination_trackor = []
        fields_dict = self._data_handler.update_fields_dict(field_dict, data)
        if len(fields_dict) > 0:
            try:
                is_field_clean_trigger, destination_trackor = self._trackor_data.update_field_data(trackor_key, destination_trackor_type, dest_key_dict, \
                                                                                                        fields_dict)
                self._module_log.add(LogLevel.INFO, f'Fields Data updated for {trackor_key}')
            except Exception as e:
                self._module_log.add(LogLevel.WARNING, str(e))
                is_field_clean_trigger = False

        else:
            is_field_clean_trigger = True

        return is_field_clean_trigger, destination_trackor

    def update_task_data(self, task_dict, destination_trackor, destination_trackor_type, dest_key_dict, destination_wp, trackor_key, trackor_id, source_wp):
        if len(task_dict) > 0:
            if len(destination_trackor) == 0:
                try:
                    destination_trackor = self._trackor_data.get_destination_trackor(trackor_key, destination_trackor_type, dest_key_dict)
                except Exception as e:
                    self._module_log.add(LogLevel.WARNING, str(e))

            if len(destination_trackor) == 0:
                self._module_log.add(LogLevel.WARNING, f'Not found {trackor_key} for Trackor Type {destination_trackor_type} - Tasks won''t be updated')

            else:
                destination_trackor_id  = destination_trackor[0][self._trackor_data._ov_source_fields.id]
                source_workplan_id = self.get_workplan_id(trackor_id, source_wp)
                tasks_dict = self._data_handler.get_task_dict(source_workplan_id, task_dict)
                destination_workplan_id = self.get_workplan_id(destination_trackor_id, destination_wp)
                is_clean_trigger_task = self._trackor_data.update_task_data(destination_workplan_id, tasks_dict, trackor_key)

        else:
            is_clean_trigger_task = True

        return is_clean_trigger_task

    def get_workplan_id(self, trackor_id, workplan_name):
        workplan_id = []

        try:
            workplan_data = self._workplan_data.get_workplan(trackor_id, workplan_name)
            for workplan in workplan_data:
                if workplan[self._data_handler._ov_task_fields.wp_active] is True:
                    workplan_id = workplan[self._data_handler._ov_task_fields.wp_id]

        except Exception as e:
            self._module_log.add(LogLevel.WARNING, str(e))

        return workplan_id

    def clean_trigger(self, is_field_clean_trigger, is_clean_trigger_task, source_trackor_type, clean_trigger_dict, source_clear_trigger, trackor_key):
        if is_field_clean_trigger and is_clean_trigger_task:
            try:
                self._trackor_data.clean_trigger(trackor_key, source_trackor_type, clean_trigger_dict, source_clear_trigger)
                self._module_log.add(LogLevel.INFO, f'Trigger has been updated for {trackor_key}')
            except Exception as e:
                self._module_log.add(LogLevel.WARNING, e)

        else:
            self._module_log.add(LogLevel.INFO, f'Trigger has not been updated for {trackor_key}')


class DataHandler:
    def __init__(self, module_log, ov_url, ov_access_key, ov_secret_key, ov_mapping_fields, ov_mapping_types, ov_task_fields, workplan_data):
        self._module_log = module_log
        self._ov_url = ov_url
        self._ov_access_key = ov_access_key
        self._ov_secret_key = ov_secret_key
        self._ov_mapping_fields = MappingTrackorFields(ov_mapping_fields)
        self._ov_mapping_types = MappingTrackorTypes(ov_mapping_types)
        self._ov_task_fields = TaskFields(ov_task_fields)
        self._workplan_data = workplan_data

    def get_field_lists(self, trackor_fields, key_field):
        field_list = []

        for field in trackor_fields:
            if field[self._ov_mapping_fields.mapping_class] == self._ov_mapping_types.field_transfer:
                source_field_name = field[self._ov_mapping_fields.source_field_name]

                if source_field_name is None:
                    self._module_log.add(LogLevel.WARNING, f'One or more fields are empty - {self._ov_mapping_fields.source_field_name}')

                else:
                    field_list.append(source_field_name)

            elif field[self._ov_mapping_fields.mapping_class] != self._ov_mapping_types.task_transfer:
                self._module_log.add(LogLevel.INFO, f'Unknown class name - {field[self._ov_mapping_fields.mapping_class]}')

        field_list.append(key_field)

        return field_list

    def get_dicts(self, trackor_fields):
        field_dict = {}
        task_dict  = {}
        for field in trackor_fields:
            if field[self._ov_mapping_fields.mapping_class] == self._ov_mapping_types.field_transfer:
                source_field_name      = field[self._ov_mapping_fields.source_field_name]
                destination_field_name = field[self._ov_mapping_fields.destination_field_name]

                if source_field_name is None or destination_field_name is None:
                    self._module_log.add(LogLevel.WARNING, f'One or more fields are empty - {self._ov_mapping_fields.source_field_name},' \
                                            f'{self._ov_mapping_fields.destination_field_name}')

                else:
                    field_dict.update({destination_field_name: source_field_name})

            elif field[self._ov_mapping_fields.mapping_class] == self._ov_mapping_types.task_transfer:
                source_order_number      = field[self._ov_mapping_fields.source_order_number]
                source_task_data         = field[self._ov_mapping_fields.source_task_data]
                destination_order_number = field[self._ov_mapping_fields.destination_order_number]

                if source_order_number is None or source_task_data is None or destination_order_number is None:
                    self._module_log.add(LogLevel.WARNING, f'One or more fields are empty - {self._ov_mapping_fields.source_order_number},' \
                                            f'{self._ov_mapping_fields.source_task_data}, {self._ov_mapping_fields.destination_order_number}')

                else:
                    task_dict.update({destination_order_number: {source_order_number: source_task_data}})

            else:
                self._module_log.add(LogLevel.INFO, f'Unknown class name - {field[self._ov_mapping_fields.mapping_class]}')
                continue

        return field_dict, task_dict

    def update_fields_dict(self, fields_dict, data):
        upd_fields_dict = fields_dict.copy()
        for field_dict in upd_fields_dict.items():
            upd_fields_dict[field_dict[0]] = data[field_dict[1]]

        return upd_fields_dict

    def get_task_dict(self, workplan_id, tasks_dict):
        upd_task_dict = {}

        for task_dict in tasks_dict.items():
            for fd in task_dict[1].items():
                source_order_number = fd[0]
                source_task_data = fd[1]

            task_data = []
            try:
                task_data = self._workplan_data.get_task_data(workplan_id, source_order_number)
            except Exception as e:
                self._module_log.add(LogLevel.WARNING, str(e))

            if len(task_data) == 0:
                continue

            if re.search('\.', source_task_data) is None:
                upd_task_dict.update({task_dict[0]: {source_task_data: task_data[source_task_data]}})

            else:
                task_data_split = re.split('\.', source_task_data, 2)
                dynamic_dates = task_data[task_data_split[0]]
                for dd in dynamic_dates:
                    if dd[self._ov_task_fields.task_label] == task_data_split[1]:
                        upd_task_dict.update({task_dict[0]: {self._ov_task_fields.task_label: task_data_split[1], task_data_split[2]: dd[task_data_split[2]]}})

        return upd_task_dict

    def update_task_data(self, workplan_id, tasks_dict, trackor_key):
        is_clean_trigger = False
        is_update_task_warning = False
        for task in tasks_dict.items():
            task_data = []
            try:
                task_data = self._workplan_data.get_task_data(workplan_id, task[0])
            except Exception as e:
                self._module_log.add(LogLevel.WARNING, str(e))

            if len(task_data) == 0:
                continue

            order_number = task[0]
            task_dict = task[1]
            task_id = task_data[self._ov_task_fields.wp_id]
            task_fields = {}
            dynamic_dates_list = []
            if len(task_dict) == 1:
                is_clean_trigger = self.update_workplan_task(task_id, order_number, trackor_key, task_dict, dynamic_dates_list)
                if is_clean_trigger is False:
                    is_update_task_warning = True

            else:
                task_label = None
                for task in task_dict.items():
                    if task[0] == self._ov_task_fields.task_label:
                        task_label = task[1]

                if task_label is None:
                    self._module_log.add(LogLevel.WARNING, f'Failed to update_task_data for {trackor_key}: Exception ["' \
                                            f'{self._ov_task_fields.task_label}" is not found in the dictionary]')

                else:
                    dynamic_dates = task_data[self._ov_task_fields.task_dynamic_dates]
                    for dynamic_date in dynamic_dates:
                        if dynamic_date[self._ov_task_fields.task_label] == task_label:
                            task_dict[self._ov_task_fields.task_date_type] = dynamic_date[self._ov_task_fields.task_date_type]

                    dynamic_dates_list.append(task_dict)

                is_clean_trigger = self.update_workplan_task(task_id, order_number, trackor_key, task_fields, dynamic_dates_list)
                if is_clean_trigger is False:
                    is_update_task_warning = True

        if is_update_task_warning is True:
            is_clean_trigger = False

        return is_clean_trigger

    def update_workplan_task(self, task_id, order_number, trackor_key, task_fields, dynamic_dates_list):
        update_task = self._workplan_data.update_task(task_id, task_fields, dynamic_dates_list)

        if update_task.ok:
            is_clean_trigger = True
            self._module_log.add(LogLevel.INFO, f'Task Date updated for Order Number {order_number} for {trackor_key}')

        else:
            is_clean_trigger = False
            self._module_log.add(LogLevel.WARNING, f'Failed to update_workplan_task for Order Number {order_number}' \
                                    f'for {trackor_key}: Exception [{update_task.text}]')

        return is_clean_trigger


class TrackorData:

    def __init__(self, ov_url, ov_access_key, ov_secret_key, ov_source_trackor_type, ov_source_fields, ov_source_types, ov_source_status, ov_mapping_trackor_type):
        self._ov_url = ov_url
        self._ov_access_key = ov_access_key
        self._ov_secret_key = ov_secret_key
        self._ov_mapping_trackor_type_name = ov_mapping_trackor_type
        self._ov_source_trackor_type_name = ov_source_trackor_type
        self._ov_source_fields = SourceTrackorFields(ov_source_fields)
        self._ov_source_types = SourceTrackorTypes(ov_source_types)
        self._ov_source_status = SourceTrackorStatuses(ov_source_status)
        self._ov_source_trackor_type = Trackor(trackorType=ov_source_trackor_type, URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)
        self._ov_mapping_trackor_type = Trackor(trackorType=ov_mapping_trackor_type, URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)

    def get_source_trackors(self):
        self._ov_source_trackor_type.read(
            filters={self._ov_source_fields.status: self._ov_source_status.enabled,
                     self._ov_source_fields.type: self._ov_source_types.ov_to_ov},
            fields=self._ov_source_fields.get_list()
        )

        if len(self._ov_source_trackor_type.errors) != 0:
            raise Exception(f'Failed to get_source_trackors: Exception [{self._ov_source_trackor_type.errors}]')

        return self._ov_source_trackor_type.jsonData

    def get_mapping_trackors(self, parent_trackor_id, fields_list):
        self._ov_mapping_trackor_type.read(
            filters={f'{self._ov_source_trackor_type_name}.{self._ov_source_fields.id}': parent_trackor_id},
            fields=fields_list
        )

        if len(self._ov_mapping_trackor_type.errors) != 0:
            raise Exception(f'Failed to get_mapping_trackors: Exception [{self._ov_mapping_trackor_type.errors}]')

        return self._ov_mapping_trackor_type.jsonData

    def get_destination_trackor(self, trackor_key, trackor_type, filter_dict):
        dest_trackor_type = Trackor(trackorType=trackor_type, URL=self._ov_url, userName=self._ov_access_key, password=self._ov_secret_key, isTokenAuth=True)
        dest_trackor_type.read(filters=filter_dict)

        if len(dest_trackor_type.errors) != 0:
            raise Exception(f'Failed to get_destination_trackor for {trackor_key}: Exception [{dest_trackor_type.errors}]')

        return dest_trackor_type.jsonData

    def get_trackor_data(self, trackor_type, fields_list, source_trigger):
        data_trackor_type = Trackor(trackorType=trackor_type, URL=self._ov_url, userName=self._ov_access_key, password=self._ov_secret_key, isTokenAuth=True)
        data_trackor_type.read(fields=fields_list, search=source_trigger)
                    
        if len(data_trackor_type.errors) != 0:
            raise Exception(f'Failed to get_trackor_data: Exception [{data_trackor_type.errors}]')
        
        return data_trackor_type.jsonData

    def update_field_data(self, trackor_key, trackor_type, filter_dict, field_dict):
        dest_trackor_type = Trackor(trackorType=trackor_type, URL=self._ov_url, userName=self._ov_access_key, password=self._ov_secret_key, isTokenAuth=True)
        dest_trackor_type.update(filters=filter_dict, fields=field_dict)

        if len(dest_trackor_type.errors) != 0:
            raise Exception(f'Failed to update_field_data for {trackor_key}: Exception [{dest_trackor_type.errors}]')

        return True, dest_trackor_type.jsonData

    def clean_trigger(self, trackor_key, trackor_type, filter_dict, field_dict):        
        data_trackor_type = Trackor(trackorType=trackor_type, URL=self._ov_url, userName=self._ov_access_key, password=self._ov_secret_key, isTokenAuth=True)
        data_trackor_type.update(filters=filter_dict, fields=field_dict)

        if len(data_trackor_type.errors) != 0:
            raise Exception(f'Failed to clean_trigger for {trackor_key}: Exception [{data_trackor_type.errors}]')


class WorkplanData:

    def __init__(self, ov_url, ov_access_key, ov_secret_key, ov_task_fields):
        self._ov_url = ov_url
        self._ov_access_key = ov_access_key
        self._ov_secret_key = ov_secret_key
        self._ov_task_fields = TaskFields(ov_task_fields)
        self._workplan = WorkPlan(URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)
        self._task = Task(URL=ov_url, userName=ov_access_key, password=ov_secret_key, isTokenAuth=True)

    def get_workplan(self, trackor_id, workplan_name):
        self._workplan.read(trackorId=trackor_id, workplanTemplate=workplan_name)

        if len(self._workplan.errors) != 0:
            raise Exception(LogLevel.WARNING, f'Failed to get_workplan: Exception [{self._workplan.errors}]')

        return self._workplan.jsonData

    def get_task_data(self, workplan_id, order_number):
        self._task.read(workplanId=workplan_id, orderNumber=order_number)

        if len(self._task.errors) != 0:
            raise Exception(LogLevel.WARNING, f'Failed to get_task_data: Exception [{self._task.errors}]')

        return self._task.jsonData

    def update_task(self, task_id, fields={}, dynamic_dates=[]):
        if len(dynamic_dates)>0:
            fields[self._ov_task_fields.task_dynamic_dates] = dynamic_dates

        url = f'https://{self._ov_url}/api/v3/tasks/{task_id}'
        auth = HTTPBearerAuth(self._ov_access_key, self._ov_secret_key)
        header = {'content-type': 'application/x-www-form-urlencoded'}
        return requests.patch(url, headers=header, data=json.dumps(fields), auth=auth)


class SourceTrackorFields:
    def __init__(self, ov_source_fields):
        self.id = ov_source_fields[SourceTrackorField.ID.value]
        self.key = ov_source_fields[SourceTrackorField.KEY.value]
        self.type = ov_source_fields[SourceTrackorField.TYPE.value]
        self.status = ov_source_fields[SourceTrackorField.STATUS.value]
        self.trigger = ov_source_fields[SourceTrackorField.TRIGGER.value]
        self.clear_trigger = ov_source_fields[SourceTrackorField.CLEAR_TRIGGER.value]
        self.source_trackor_type = ov_source_fields[SourceTrackorField.SOURCE_TRACKOR_TYPE.value]
        self.source_key_field = ov_source_fields[SourceTrackorField.SOURCE_KEY_FIELD.value]
        self.source_wp = ov_source_fields[SourceTrackorField.SOURCE_WP.value]
        self.destination_trackor_type = ov_source_fields[SourceTrackorField.DESTINATION_TRACKOR_TYPE.value]
        self.destination_key_field = ov_source_fields[SourceTrackorField.DESTINATION_KEY_FIELD.value]
        self.destination_wp = ov_source_fields[SourceTrackorField.DESTINATION_WP.value]

    def get_list(self):
        return [self.key, self.trigger, self.clear_trigger, self.source_trackor_type, self.source_key_field, self.source_wp, self.destination_trackor_type, \
                    self.destination_key_field, self.destination_wp]


class SourceTrackorTypes:
    def __init__(self, ov_source_types):
        self.ov_to_ov = ov_source_types[SourceTrackorType.OV_TO_OV.value]


class MappingTrackorTypes:
    def __init__(self, ov_mapping_types):
        self.field_transfer = ov_mapping_types[MappingTrackorType.FIELD_TRANSFER.value]
        self.task_transfer = ov_mapping_types[MappingTrackorType.TASK_TRANSFER.value]


class SourceTrackorStatuses:
    def __init__(self, ov_source_status):
        self.enabled = ov_source_status[SourceTrackorStatus.ENABLED.value]


class MappingTrackorFields:
    def __init__(self, ov_mapping_fields):
        self.mapping_class = ov_mapping_fields[MappingTrackorField.MAPPING_CLASS.value]
        self.source_field_name = ov_mapping_fields[MappingTrackorField.SOURCE_FIELD_NAME.value]
        self.source_field_trackor_type = ov_mapping_fields[MappingTrackorField.SOURCE_FIELD_TRACKOR_TYPE.value]
        self.destination_field_name = ov_mapping_fields[MappingTrackorField.DESTINATION_FIELD_NAME.value]
        self.destination_field_trackor_type = ov_mapping_fields[MappingTrackorField.DESTINATION_FIELD_TRACKOR_TYPE.value]

        self.source_wp_name = ov_mapping_fields[MappingTrackorField.SOURCE_WP_NAME.value]
        self.source_order_number = ov_mapping_fields[MappingTrackorField.SOURCE_ORDER_NUMBER.value]
        self.source_task_data = ov_mapping_fields[MappingTrackorField.SOURCE_TASK_DATA.value]
        self.destination_wp_name = ov_mapping_fields[MappingTrackorField.DESTINATION_WP_NAME.value]
        self.destination_order_number = ov_mapping_fields[MappingTrackorField.DESTINATION_ORDER_NUMBER.value]

    def get_list(self):
        return [self.mapping_class, self.source_field_name, self.source_field_trackor_type, self.destination_field_name, self.destination_field_trackor_type, \
                    self.source_wp_name, self.source_order_number, self.source_task_data, self.destination_wp_name, self.destination_order_number]


class TaskFields:
    def __init__(self, ov_task_fields):
        self.wp_id = ov_task_fields[TaskField.WP_ID.value]
        self.wp_active = ov_task_fields[TaskField.WP_ACTIVE.value]
        self.task_label = ov_task_fields[TaskField.TASK_LABEL.value]
        self.task_date_type = ov_task_fields[TaskField.TASK_DATE_TYPE.value]
        self.task_dynamic_dates = ov_task_fields[TaskField.TASK_DYNAMIC_DATES.value]


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
    MAPPING_CLASS = 'mappingClass'
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
