from peewee import *
import datetime
from google.cloud import storage
import os.path

#TODO Define diff location

db = SqliteDatabase(None)

def init_database(location):
    #Open the connection
    #Setup defaults for the below
    db = SqliteDatabase(location)
    if not os.path.isfile(location):
        db.create_tables([BaseImage,BrowserArchive,Experiment,Instance,Job])

def create_image_type(name, description, gcp):
    img = BaseImage(name=name,description=description,gcp_id=gcp.get_instance_image_id(name))
    img.save()

def create_browser_archive(bucket_name,blob_name,description):
    #Check exists, get hash and store
    c = storage.Client()
    bucket = c.bucket(bucket_name)
    j = bucket.get_blob(blob_name)
    ba = BrowserArchive(bucket=bucket_name,blob=blob_name,description=description,hash=j)
    ba.save()

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
    #Metadata
    created_date = DateTimeField(default=datetime.datetime.now)

    def _get_pending(self):
        return [i for i in self.instances if len(i._get_awaiting(1))>0]

    def is_finished(self):
        #TODO Implement (return true if all jobs either have a result or error)
        return False

    def get_results(self):
        #TODO Implement.
        #Return iterator over the results
        return list()

class Instance(BaseModel):
    experiment = ForeignKeyField(Experiment, backref='instances')
    name = CharField()
    zone = CharField()
    base_image = ForeignKeyField(BaseImage, backref='instances')
    browser_archive = ForeignKeyField(BrowserArchive, backref='instances')
    #Metadata
    created_date = DateTimeField(default=datetime.datetime.now)

    #TODO Fix and Enforce
    #class Meta:
    #    constraints = [SQL('UNIQUE(experiment,name)')]

    def _get_location(self):
        return f"{self.experiment.name}_{self.name}"

    def _get_awaiting(self,limit):
        return self.jobs.select().where(Job.status=="AWAITING")\
            .order_by(Job.notBefore,Job.id).limit(limit)

    def _get_oldest_submitted(self,limit,at_least=30):
        #TODO - Implement requirement for at_least submitted for X seconds
        return self.jobs.select().where(Job.status=="SUBMITTED")\
            .order_by(Job.submitted_date).limit(limit)

class Job(BaseModel):
    instance = ForeignKeyField(Instance, backref='jobs')
    name = CharField(unique=True)
    target = CharField()
    notBefore = DateTimeField()
    notAfter = DateTimeField()
    status = CharField()
    options = BlobField()
    #Metadata
    created_date = DateTimeField(default=datetime.datetime.now)
    result_url = CharField(unique=True)
    error_msg = CharField()
    submitted_date = DateTimeField()
    finished_date = DateTimeField()

    def _set_submitted(self,url):
        self.status = 'SUBMITTED'
        self.result_url = url
        self.submitted_date = datetime.datetime.now()
        self.save()

    def _set_error_testing(self, result):
        self.status = 'ERROR_TESTING'
        self.finished_date = datetime.datetime.now()
        self.error_msg = result
        self.save()

    def _set_error_submission(self, result):
        self.status = 'ERROR_SUBMITTING'
        self.finished_date = datetime.datetime.now()
        self.error_msg = result
        self.save()

    def _set_finished(self):
        self.status = 'FINISHED'
        self.finished_date = datetime.datetime.now()
        self.save()
