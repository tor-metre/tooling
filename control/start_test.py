
import googleapiclient.discovery 

def create_instance(zone, name, location, stateFile):
    compute = googleapiclient.discovery.build('compute', 'v1')
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

if __name__ == '__main__':
    name = 'test-image'
    zone = 'us-central1-a'
    location = 'tor-with-timer'
    stateFile = 'gs://hungry-serpent//1.state'
    create_instance(zone,name,location,stateFile)