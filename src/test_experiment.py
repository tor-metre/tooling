from experiment import *
from utility.gcp import GCP
from utility import configuration as cl
from datetime import datetime,timedelta

parser = cl.get_full_args_parser("Handles instance creation, monitoring and shutdown on GCP",
                        wpt_location=False, gcp_instances=True)
result, config = cl.get_config(fixed_config=vars(parser.parse_args()), default_config={
cl.FILE_CONFIG_PATH_ENTRY: 'settings.yaml',
cl.GCP_PROJECT_NAME_ENTRY: None,
cl.WPT_SERVER_URL_ENTRY:None,
})

if not result:
    print("Invalid configuration. Quitting...")
    exit(-1)

g = GCP(config[cl.GCP_PROJECT_NAME_ENTRY], config[cl.WPT_SERVER_URL_ENTRY],config[cl.WPT_API_KEY_ENTRY])

init_database('/home/dennis/dev_storage/experiments.db')
img = create_image_type('gce-fresh-image','old image',g)
#img = BaseImage.get(BaseImage.name=='gce-fresh-image')
ba = create_browser_archive("malerie","browser-archives/test-archive.tar","Empty Archive")
#ba = BrowserArchive.get(BrowserArchive.bucket=='malerie')
#print("Created image")
print(config[cl.GCP_INSTANCE_TYPE_ENTRY])
exp = Experiment.get_or_create(name='test-01',description='very first test!')[0]
inst = Instance.get_or_create(experiment=exp,
                    gcp_name='test-instance-1',
                    zone = 'us-central1-a',
                    wpt_location='test-instance-1',
                    base_image=img,
                    instance_type = config[cl.GCP_INSTANCE_TYPE_ENTRY],
                    browser_archive=ba,
                    description='Test instance',
                    storage_location = 'malerie' #TODO TODO
                        )[0]
j = Job.create(
    instance=inst,
    description='Test job number 1',
    target='www.google.com',
)
print("Finished creating job")