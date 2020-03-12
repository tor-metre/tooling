from peewee import *
import datetime
from google.cloud import storage
import os.path
import json

db = SqliteDatabase(None)


# 'Public' API

def init_database(location):
    # Open the connection
    # Setup defaults for the below
    db = SqliteDatabase(location)
    if not os.path.isfile(location):
        db.create_tables([BaseImage, BrowserArchive, Experiment, Instance, Job])


def create_image_type(name, description, gcp):
    img = BaseImage(name=name, description=description, gcp_id=gcp.get_instance_image_id(name))
    img.save()


def create_browser_archive(bucket_name, blob_name, description):
    # Check exists, get hash and store
    c = storage.Client()
    bucket = c.bucket(bucket_name)
    j = bucket.get_blob(blob_name)
    ba = BrowserArchive(bucket=bucket_name, blob=blob_name, description=description, hash=j)
    ba.save()


def create_experiment():
    return None


def get_experiment():
    return None


# 'Private' API

def get_pending_instances():
    experiments = Experiment.select()
    pending = list()
    for e in experiments:
        pending.extend(e.get_pending_instances())
    return pending


def get_maybe_finished_jobs(limit, submitted_before=None):
    if submitted_before is None:
        submitted_before = datetime.datetime.now()  - datetime.timedelta(minutes=2)
    all_instances = get_all_instances()
    jobs = list()
    fair_cap = max(1, limit / len(all_instances))  # Evenly divide the slots
    # In general we expect all active instances to be processing jobs at roughly the same rate
    # so this should be reasonable effecitve (not too many under reports from asymmetric queues)
    for i in all_instances:
        new_jobs = i.get_maybe_finished_jobs(fair_cap, submitted_before)
        jobs.extend(new_jobs)
    return jobs


def get_awaiting_jobs_by_wpt_location(wpt_location, limit):
    i = get_instance_by_gcp_name(wpt_location_to_gcp_name(wpt_location))
    return i.get_awaiting(limit)


def get_all_wpt_locations():
    results = Instance.select(Instance.wpt_location).distinct()
    return set([x.wpt_location for x in results])


def wpt_location_to_gcp_name(location):
    return Instance.get(Instance.wpt_location == location).gcp_name


def get_instance_by_gcp_name(name):
    return Instance.get(Instance.gcp_name == name)


def get_all_instances():
    return Instance.select()


class BaseModel(Model):
    class Meta:
        database = db


class BaseImage(BaseModel):
    name = CharField(unique=True)
    gcp_id = CharField()
    description = CharField()


class BrowserArchive(BaseModel):
    bucket = CharField()
    blob = CharField()
    description = CharField()
    hash = CharField()


class Experiment(BaseModel):
    name = CharField(unique=True)
    description = CharField()
    defaults = BlobField()
    # Metadata
    created_date = DateTimeField(default=datetime.datetime.now)

    def get_pending_instances(self):
        return [i for i in self.instances if len(i.get_awaiting(1)) > 0]

    # Public
    def is_finished(self):
        # TODO Implement (return true if all jobs either have a result or error)
        return False

    # Public
    def get_results(self):
        # TODO Implement.
        # Return iterator over the results
        return list()

    # Public
    def get_instances(self):
        return self.instances

    # Public
    def add_instance(self):
        # TODO
        return None


class Instance(BaseModel):
    experiment = ForeignKeyField(Experiment, backref='instances')
    gcp_name = CharField(unique=True)
    zone = CharField()
    wpt_location = CharField(unique=True)
    base_image = ForeignKeyField(BaseImage, backref='instances')
    browser_archive = ForeignKeyField(BrowserArchive, backref='instances')
    instance_type = CharField()
    description = CharField()
    # Metadata
    created_date = DateTimeField(default=datetime.datetime.now)
    desired_state = CharField()
    last_changed = DateTimeField()
    storage_location = CharField()

    # Public
    def get_jobs(self):
        return self.jobs

    # Public
    def add_jobs(self):
        # TODO
        return None

    def get_maybe_finished_jobs(self, limit, submitted_before):
        return self.jobs.select().where(Job.status == "SUBMITTED" and Job.submitted_date < submitted_before) \
            .order_by(Job.submitted_date).asc().limit(limit)

    def get_awaiting_jobs(self, limit):
        current_time = datetime.datetime.now()
        return self.jobs.select().where(Job.status == "AWAITING" and Job.notAfter > current_time > Job.notBefore) \
            .order_by(Job.notBefore, Job.id).limit(limit)


class Job(BaseModel):
    instance = ForeignKeyField(Instance, backref='jobs')
    description = CharField()
    target = CharField()
    notBefore = DateTimeField()
    notAfter = DateTimeField()
    options = BlobField()
    # Metadata
    status = CharField()
    wpt_id = CharField(unique=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    result_url = CharField(unique=True)
    error_msg = CharField()
    submitted_date = DateTimeField()
    finished_date = DateTimeField()

    def get_options_list(self):
        d = json.loads(self.options)  # Double check if this is safe?
        r = list()
        for k, v in d.items():
            r.append(f"--{k}")
            r.append(f"{v}")
        return r

    def set_submitted(self, url):
        self.status = 'SUBMITTED'
        self.result_url = url
        self.submitted_date = datetime.datetime.now()
        self.save()

    def set_error_testing(self, result):
        self.status = 'ERROR_TESTING'
        self.finished_date = datetime.datetime.now()
        self.error_msg = result
        self.save()

    def set_error_submission(self, result):
        self.status = 'ERROR_SUBMITTING'
        self.finished_date = datetime.datetime.now()
        self.error_msg = result
        self.save()

    def set_finished(self):
        self.status = 'FINISHED'
        self.finished_date = datetime.datetime.now()
        self.save()
