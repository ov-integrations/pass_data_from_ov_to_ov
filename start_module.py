from onevizion import IntegrationLog, LogLevel
from module import *
from jsonschema import validate
import json
import re


with open('settings.json', 'rb') as PFile:
    settings_data = json.loads(PFile.read().decode('utf-8'))

with open('settings_schema.json', 'rb') as PFile:
    data_schema = json.loads(PFile.read().decode('utf-8'))

try:
    validate(instance=settings_data, schema=data_schema)
except Exception as e:
    raise Exception('Incorrect value in the settings file\n{}'.format(str(e)))

ov_source_url = re.sub('^http://|^https://', '', settings_data['ovSourceUrl'][:-1])
ov_source_access_key = settings_data['ovSourceAccessKey']
ov_source_secret_key = settings_data['ovSourceSecretKey']
ov_source_trackor_type = settings_data['ovSourceTrackorType']
ov_source_fields = settings_data['ovSourceFields']
ov_source_types = settings_data['ovSourceTypes']
ov_source_status = settings_data['ovSourceStatus']

ov_mapping_trackor_type = settings_data['ovMappingTrackorType']
ov_mapping_fields = settings_data['ovMappingFields']
ov_task_fields = settings_data['ovTaskFields']
ov_mapping_types = settings_data['ovMappingTypes']

ov_destination_url = re.sub('^http://|^https://', '', settings_data['ovDestinationUrl'][:-1])
ov_destination_access_key = settings_data['ovDestinationAccessKey']
ov_destination_secret_key = settings_data['ovDestinationSecretKey']

with open('ihub_parameters.json', 'rb') as PFile:
    module_data = json.loads(PFile.read().decode('utf-8'))

process_id = module_data['processId']
log_level = module_data['logLevel']

module_log = IntegrationLog(process_id, ov_source_url, ov_source_access_key, ov_source_secret_key, None, True, log_level)
workplan_data = WorkplanData(ov_source_url, ov_source_access_key, ov_source_secret_key, ov_task_fields)
trackor_data = TrackorData(ov_source_url, ov_source_access_key, ov_source_secret_key, ov_source_trackor_type, ov_source_fields, ov_source_types, \
                                ov_source_status, ov_mapping_trackor_type)
data_handler = DataHandler(module_log, ov_source_url, ov_source_access_key, ov_source_secret_key, ov_mapping_fields, ov_mapping_types, ov_task_fields, workplan_data)
module = Module(module_log, data_handler, trackor_data, workplan_data)

try:
    module.start()
except Exception as e:
    module_log.add(LogLevel.ERROR, str(e))
    raise e