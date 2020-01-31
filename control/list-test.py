from pprint import pprint

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

credentials = GoogleCredentials.get_application_default()

service = discovery.build('compute', 'v1', credentials=credentials)

# Project ID for this request.
project = 'moz-fx-dev-djackson-torperf'  # TODO: Update placeholder value.

# The name of the zone for this request.
zone = 'us-central1-a'  # TODO: Update placeholder value.

request = service.instances().list(project=project, zone=zone)
while request is not None:
    response = request.execute()

    for instance in response['items']:
        # TODO: Change code below to process each `instance` resource:
        pprint(instance['name'])
        pprint(instance['status'])
        pprint(instance['metadata'])

    request = service.instances().list_next(previous_request=request, previous_response=response)

