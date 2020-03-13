""" This library file holds functions for interacting with the Google Compute Platform.
"""

from googleapiclient import discovery
import logging
import datetime


class GCP:
    # WARNING - This class is NOT Thread Safe

    def __init__(self, project,wpt_server_url):
        self.logger = logging.getLogger("utility." + __name__)
        self.logger.debug(f"Initialised logging for GCP Object attached to project {project}")
        self.compute = discovery.build('compute', 'v1')
        self.project = project
        self.wpt_server_url = wpt_server_url
        self.global_zones = None
        self.global_zones = self._fetch_zones()

    def _fetch_zones(self):
        if self.global_zones is not None:
            return self.global_zones
        request = self.compute.zones().list(project=self.project)
        zone_names = set()
        while request is not None:
            response = request.execute()
            zone_names.update([z['name'] for z in response['items']])
            request = self.compute.zones().list_next(previous_request=request, previous_response=response)
        self.logger.debug(f"Fetched {len(zone_names)} zones from GCP API")
        return frozenset(zone_names)

    def _set_zones_if_empty(self, zones):
        if zones is None:
            return self.get_zones()
        else:
            assert (zones.issubset(self.get_zones()))
            return zones

    def get_zones(self):
        return self.global_zones

    def get_instance_image_id(self,name):
        response = self.compute.images().get(project=self.project, image=name).execute()
        return response['id']

    def _create_instance(self, instance):
        zone = instance.zone
        name = instance.gcp_name
        disk = instance.base_image.name
        location = instance.wpt_location
        archive = instance.browser_archive
        assert (zone in self.global_zones)
        self.logger.debug(f"Creating an instance in {zone} with {name} of type {instance.instance_type}")
        machine_type_url = f"zones/{zone}/machineTypes/{instance.instance_type}"
        image_url = f'projects/{self.project}/global/images/{disk}'
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
                    'value': "./shutdown.sh" #TODO Fix
                }, {
                    'key': 'location',
                    'value': location
                }, {
                    'key': 'archive',
                    'value': archive.hash #TODO Fix and add check?
                }, {
                    'key': 'wpt_server',
                    'value': self.wpt_server_url
                }
                ]
            }
        }
        instance.desired_state = 'CREATED'
        instance.last_changed = datetime.datetime.now()
        instance.save()
        return self.compute.instances().insert(
            project=self.project,
            zone=zone,
            body=config).execute()

    def _start_instance(self, instance):
        name = instance.gcp_name
        zone = instance.zone
        self.logger.debug(f"Starting instance {name} in {zone}")
        instance.desired_state = 'STARTED'
        instance.last_changed = datetime.datetime.now()
        instance.save()
        return self.compute.instances().start(project=self.project, zone=zone, instance=name).execute()

    def _stop_instance(self, instance):
        name = instance.gcp_name
        zone = instance.zone
        self.logger.debug(f"Stopping instance {name} in {zone}")
        instance.desired_state = 'STOPPED'
        instance.last_changed = datetime.datetime.now()
        instance.save()
        return self.compute.instances().stop(project=self.project, zone=zone, instance=name).execute()

    def delete_instance(self, instance):
        name = instance.gcp_name
        zone = instance.zone
        self.logger.debug(f"Deleting instance {name} in {zone}")
        instance.desired_state = 'DELETED'
        instance.last_changed = datetime.datetime.now()
        instance.save()
        return self.compute.instances().delete(project=self.project, zone=zone, instance=name).execute()

    def get_instances(self, zones=None):
        zones = self._set_zones_if_empty(zones)
        results = list()
        self.logger.debug(f"Looking for instances in {len(zones)} zones")
        for zone in zones:
            self.logger.debug(f"Looking for instances in {zone}")
            request = self.compute.instances().list(project=self.project, zone=zone)
            while request is not None:
                response = request.execute()
                instances = response.get('items')
                if instances is not None:
                    for instance in instances:
                        instance_dict = dict()
                        instance_dict['name'] = instance['name']
                        instance_dict['zone'] = zone
                        instance_dict['creation_time'] = instance['creationTimestamp']
                        instance_dict['status'] = instance['status']
                        instance_dict.update(instance['metadata'])
                        results.append(instance_dict)
                request = self.compute.instances().list_next(previous_request=request, previous_response=response)
        self.logger.debug(f"Discovered {len(results)} in {len(zones)} zones")
        return results

    def get_running_instances(self, zones=None, instances=None):
        if instances is None:
            instances = self.get_instances(zones)
        return [r for r in instances if r['status'] == 'RUNNING']

    def get_stopped_instances(self, zones=None, instances=None):
        if instances is None:
            instances = self.get_instances(zones)
        return [r for r in instances if r['status'] == 'TERMINATED']

    def activate_instances(self, new_instances, instances=None):
        initial_size = len(new_instances)
        self.logger.debug(f"Attempting to activate {initial_size} instances.")
        name_to_instance = {i.gcp_name: i for i in new_instances}
        if instances is None:
            instances = self.get_instances()
        to_restart = set()
        for i in instances:
            if i['name'] in name_to_instance.keys():
                if i['status'] == 'TERMINATED':
                    to_restart.add(name_to_instance[i['name']])
                del name_to_instance[i['name']]
        self.logger.debug(f"Restarting {len(to_restart)} instances")
        for t in to_restart:
            self._start_instance(t)
        self.logger.debug(f"Creating {len(name_to_instance.keys())} instances")
        to_create = name_to_instance.values()
        for v in to_create:
            self._create_instance(v)
        self.logger.debug(f"{initial_size - len(to_create) - len(to_restart)} instances were in transitional state(s) and ignored.")

    def deactivate_instances(self, stop_instances, instances=None):
        name_to_instance = {i.gcp_name: i for i in stop_instances}
        if instances is None:
            instances = self.get_instances()
        stopped = 0
        for i in instances:
            if i['name'] in name_to_instance.keys() and i['status'] == "RUNNING":
                self._stop_instance(i['name'])
                stopped += 1
        self.logger.debug(f"Deactivated {stopped} instance(s) out of {len(name_to_instance.keys())} requested")
