import sys
import subprocess


subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'python_dependencies.txt'])


from onevizion import IntegrationLog, LogLevel
from integration import *
from jsonschema import validate
import json
import re

with open('settings.json', "rb") as PFile:
    settings_data = json.loads(PFile.read().decode('utf-8'))

with open('settings_schema.json', "rb") as PFile:
    data_schema = json.loads(PFile.read().decode('utf-8'))

try:
    validate(instance=settings_data, schema=data_schema)
except Exception as e:
    raise Exception("Incorrect value in the settings file\n{}".format(str(e)))

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

with open('ihub_parameters.json', "rb") as PFile:
    ihub_data = json.loads(PFile.read().decode('utf-8'))

process_id = ihub_data['processId']
log_level = ihub_data['logLevel']

integration_log = IntegrationLog(process_id, ov_source_url, ov_source_access_key, ov_source_secret_key, None, True, log_level)
source_trackor = SourceTrackor(integration_log, ov_source_url, ov_source_access_key, ov_source_secret_key, ov_source_trackor_type, ov_source_fields, \
                                    ov_source_types, ov_source_status, ov_mapping_trackor_type, ov_mapping_fields, ov_mapping_types)
destination_trackor = DestinationTrackor(integration_log, ov_destination_url, ov_destination_access_key, ov_destination_secret_key, ov_task_fields)
data_trackor = DataTrackor(integration_log, ov_source_url, ov_source_access_key, ov_source_secret_key, ov_mapping_fields, ov_mapping_types, ov_task_fields)
integration = Integration(integration_log, source_trackor, destination_trackor, data_trackor)

try:
    integration.start()
except Exception as e:
    integration_log.add(LogLevel.ERROR, str(e))
    raise e