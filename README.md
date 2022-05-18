# pass_data_from_ov_to_ov

Module for migration of data from one OneVizion installation to another OneVizion installation

## Usage
1. Create and fill IntegrationTrackor and IntegrationFieldMapping Trackor Types.
2. Fill the integration settings file (see example below)
3. Enable the integration

Example of settings.json

```json
{
    "ovSourceUrl": "https://***.onevizion.com/",
    "ovSourceAccessKey": "******",
    "ovSourceSecretKey": "************",
    "ovSourceTrackorType": "IntegrationTrackor",
    "ovMappingTrackorType": "IntegrationFieldMapping",

    "ovDestinationUrl": "https://***.onevizion.com/",
    "ovDestinationAccessKey": "******",
    "ovDestinationSecretKey": "************",

    "ovSourceFields": {
        "id": "TRACKOR_ID",
        "key": "TRACKOR_KEY",
        "type": "TRACKOR_CLASS_ID",
        "status": "IT_INTEGRATION_ENABLED",
        "trigger": "IT_OV_SOURCE_TRIGGER",
        "clearTrigger": "IT_OV_SOURCE_CLEAR_TRIGGER",
        "sourceTrackorType": "IT_OV_SOURCE_TRACKOR_TYPE",
        "sourceKeyField": "IT_OV_SOURCE_KEY_FIELD",
        "sourceWP": "IT_OV_SOURCE_WORKPLAN_NAME",
        "destinationTrackorType": "IT_OV_DESTINATION_TRACKOR_TYPE",
        "destinationKeyField": "IT_OV_DESTINATION_KEY_FIELD",
        "destinationWP": "IT_OV_DEST_WORKPLAN_NAME"
    },
    "ovSourceTypes": {
        "ovToOv": "OV to OV"
    },
    "ovSourceStatus": {
        "enabled": 1
    },
    "ovMappingFields": {
        "mappingClass": "TRACKOR_CLASS_ID",
        "sourceFieldName": "IFM_OV_FIELD_NAME",
        "sourceFieldTrackorType": "IFM_TRACKOR_TYPE",
        "destinationFieldName": "IFM_EXTERNAL_OV_FIELD_NAME",
        "destinationFieldTrackorType": "IFM_EXTERNAL_OV_TT_NAME",

        "sourceWPName": "IFM_OV_WORKPLAN_NAME",
        "sourceOrderNumber": "IFM_ORDER_NUMBER",
        "sourceTaskData": "IFM_TASK_DATA",
        "destinationWPName": "IFM_EXTERNAL_WORKPLAN_NAME",
        "destinationOrderNumber": "IFM_EXTERNAL_ORDER_NUMBER"
    },
    "ovTaskFields": {
        "wpId": "id",
        "wpActive": "active",
        "taskLabel": "label",
        "taskDateType": "date_type_id",
        "taskDynamicDates": "dynamic_dates"
    },
    "ovMappingTypes": {
        "fieldTransfer": "Field Transfer",
        "taskTransfer": "Task Transfer"
    }
}
```