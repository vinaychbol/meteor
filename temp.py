import json


data = '[{\"django_lambdas\": [\"Deployed BL-103345-hdhriehr in AsyncActuators-DEVINTAI6\", \"Deployed BL-103345-hdhriehr in Emails-DEVINTAI6\", \"Deployed BL-103345-hdhriehr in exif_data_disposer-DEVINTAI6\", \"Deployed BL-103345-hdhriehr in BAMDataInjector-DEVINTAI6\", \"Deployed DI-BL-103345-hdhriehr in EventSubscriber-DEVINTAI6\", \"Deployed DI-BL-103345-hdhriehr in Bpp-DEVINTAI6\", \"failed to deploy lambda Bpp-BG-DEVINTAI6, tag:DI-BL-103345-hdhriehr with error: An error occurred (InvalidParameterValueException) when calling the UpdateFunctionCode operation: Source image 975910769154.dkr.ecr.eu-west-1.amazonaws.com/gravty/bolapi:bpp-bg-backend-release-DI-BL-103345-hdhriehr does not exist. Provide a valid source image.\", \"Deployed DI-BL-103345-hdhriehr in ToggleManagement-DEVINTAI6\", \"Deployed DI-BL-103345-hdhriehr in BAMAlertProcessor-DEVINTAI6\"], \"engine_lambdas\": []}, [[[\"successfully deployed :backend-release-DI-BL-103345-hdhriehr on webapp-mainV2-devintai6\"], [\"successfully deployed :celery-backend-release-DI-BL-103345-hdhriehr on webapp-celery\"], [\"successfully deployed :targets-backend-release-DI-BL-103345-hdhriehr on webapp-offer-targetting\"]], \"Deployed tag DI-BL-103345-hdhriehr,None successfully in webapp-combined\"], [[\"Deployed :bpp-bg-backend-release-DI-BL-103345-hdhriehr on bpp-bg-definition-devintai6\", \"Deployed :event-batch-release-DI-BL-103345-hdhriehr on event-batch-definition-devintai6\", \"Deployed :offer-launch-notifier-release-DI-BL-103345-hdhriehr on offer-launch-notifier-devintai6\"]]]'


print(json.dumps(json.loads(data), indent=4))   

