""" This library file holds functions for interacting with the Google Compute Platform.
"""

from googleapiclient import discovery
from utils import zoneFromName, rowToLocation


class GCP:

    # project = "tor-metre-personal"
    # source_disk_image = "firefox-works"
    # machine_type = "zones/%s/machineTypes/n1-standard-2" % zone
    def __init__(self, project, source_disk, instance_type, state_file_storage):
        self.compute = discovery.build('compute', 'v1')
        self.project = project
        self.source_disk = source_disk
        self.instance_type = instance_type
        self.state_file_storage = state_file_storage
        self.global_zones = self._fetchZones()

    def _fetchZones(self):
        request = self.compute.zones().list(project=self.project)
        zoneNames = set()
        while request is not None:
            response = request.execute()
            rZones = [z['id'] for z in response['items'] if z['deprecated']['state'] == "ACTIVE"]
            zoneNames.update(rZones)
            request = self.compute.zones().list_next(previous_request=request, previous_response=response)
        return frozenset(zoneNames)

    def getZones(self):
        return self.global_zones

    def _setZonesOptional(self, zones):
        if zones is None:
            return self.getZones()
        else:
            assert(zones.issubset(self.getZones()))
            return zones

    def create_instance(self, zone, name, location, stateFile):
        assert (zone in self.global_zones)
        machine_type_url = "zones/{zone}/machineTypes/{type}".format(zone=zone, type=self.instance_type)
        image_url = 'projects/{project}/global/images/{image}'.format(project=self.project, image=self.source_disk)
        permission_url = 'https://www.googleapis.com/auth/'
        config = {
            'name': name,
            'machineType': machine_type_url,
            'scheduling': {'preemptible': True},
            'disks': [{'boot': True, 'autoDelete': True, 'initializeParams': {'sourceImage': image_url}}],
            'networkInterfaces': [{'network': 'global/networks/default',
                                   'accessConfigs': [{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}]
                                   }],
            'serviceAccounts': [{'email': 'default',
                                 'scopes': [permission_url + 'devstorage.read_write', permission_url + 'logging.write']
                                 }],
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
        return self.compute.instances().insert(
            project=self.project,
            zone=zone,
            body=config).execute()

    def newInstance(self, zone, browser, i):
        name = rowToLocation({
            'region': zone,
            'browser': browser,
            'id': i
        })
        stateFile = "gs://hungry-serpent//{id}.state".format(id=i)
        return self.create_instance(zone, name, name, stateFile)

    def startInstance(self, name):
        zone = zoneFromName(name)
        return self.compute.instances().start(project=self.project, zone=zone, instance=name).execute()

    def stopInstance(self, name):
        zone = zoneFromName(name)
        return self.compute.instances().stop(project=self.project, zone=zone, instance=name).execute()

    def delete_instance(self, name):
        zone = zoneFromName(name)
        return self.compute.instances().delete(project=self.project, zone=zone, instance=name).execute()

    def getInstances(self, zones=None):
        zones = self._setZonesOptional(zones)
        results = list()
        for zone in zones:
            request = self.compute.instances().list(project=self.project, zone=zone)
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
                request = self.compute.instances().list_next(previous_request=request, previous_response=response)
        return results

    def getActiveInstances(self, zones=None):
        return [r for r in self.getInstances(zones) if r['status'] == 'RUNNING']

    def getStoppedInstances(self, zones=None):
        return [r for r in self.getInstances(zones) if r['status'] == 'TERMINATED']
