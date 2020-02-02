""" This library file holds functions for interacting with the Google Compute Platform.
"""

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from utils import zoneFromName, rowToLocation, locationToRow

def create_instance(zone, name, location, stateFile):
    compute = discovery.build('compute', 'v1')
    project = "tor-metre-personal"
    source_disk_image = "firefox-works"

    # Configure the machine
    machine_type = "zones/%s/machineTypes/n1-standard-2" % zone

    config = {
        'name': name,
        'machineType': machine_type,
        'scheduling' :
        {
            'preemptible' : True
        },
        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': 'projects/'+project+'/global/images/'+source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [{
                'key': 'shutdown-script',
                'value': "./shutdown.sh"
            }, {
                'key': 'location',
                'value': location
            }, {
                'key': 'stateFile',
                'value': stateFile
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()
# [END create_instance]


# [START delete_instance]
def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()
# [END delete_instance]

def getInstances(zones):
    results = list()
    for zone in zones:
        credentials = GoogleCredentials.get_application_default()
        service = discovery.build('compute', 'v1', credentials=credentials)
        project = 'moz-fx-dev-djackson-torperf'

        # The name of the zone for this request.
        #zone = 'us-central1-a'  
        request = service.instances().list(project=project, zone=zone)
        while request is not None:
            response = request.execute()
            for instance in response['items']:
                idict = dict()
                idict['name'] = instance['name']
                idict['zone'] = zone 
                idict['creation_time'] = instance['creationTimestamp']
                idict['status'] = instance['status']
                if 'location' in instance['metadata'].keys():
                    idict['location'] = instance['metadata']['location']
                    idict['stateFile'] = instance['metadata']['stateFile']
                results.append(idict)
            request = service.instances().list_next(previous_request=request, previous_response=response)
    return results


def getActiveInstances():
    #Return a list of active GCE instances (that have been up for 60 seconds at least)
    zones = ['us-central1-a']
    results = getInstances(zones)
    up = [r for r in results if r['status'] == 'RUNNING'] #TODO and r['creation_time']]
    return up 

def getStoppedInstances():
    #Return a list of active GCE instances (that have been up for 60 seconds at least)
    zones = ['us-central1-a']
    results = getInstances(zones)
    up = [r for r in results if r['status'] == 'TERMINATED'] #TODO and r['creation_time']]
    return up 

def startInstance(zone,browser,i):
    #Start an instance
    #Handle the case where the instance already exists!
    name = rowToLocation({
        'region' : zone,
        'browser' : browser,
        'id' : i
    })
    stateFile = "gs://hungry-serpent//"+str(i)+'.state'
    return create_instance(zone,name,name,stateFile)

def restartInstance(zone,name):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    project = 'moz-fx-dev-djackson-torperf'
    request = service.instances().start(project=project, zone=zone, instance=name)
    response = request.execute()

def stopInstance(name):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    # Project ID for this request.
    project = 'moz-fx-dev-djackson-torperf' 
    # The name of the zone for this request.
    zone = zoneFromName(name)
    # Name of the instance resource to stop.
    request = service.instances().stop(project=project, zone=zone, instance=name)
    response = request.execute()


def deleteInstance(name):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    # Project ID for this request.
    project = 'moz-fx-dev-djackson-torperf' 
    # The name of the zone for this request.
    zone = zoneFromName(name)
    # Name of the instance resource to stop.
    request = service.instances().delete(project=project, zone=zone, instance=name)
    response = request.execute()