""" This library file holds functions for interacting with the Google Compute Platform.
"""
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
    from start_test import create_instance
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

def checkandStartInstances(sql):
    #Get locations From server
    #Where offline
    #and exist Queued or Upcoming
    #Start. 
    zones = ['us-central1-a']
    AllInstances = getInstances(zones)
    AllInstances = set([x['name'] for x in AllInstances])
    PendingLocations = getPendingLocations(sql)
    ActiveInstances = getActiveInstances()
    StoppedInstances = getStoppedInstances()
    ActiveLocations = set([x['name'] for x in ActiveInstances])
    StoppedLocations = set([x['name'] for x in StoppedInstances])
    print('Stopped locations: '+str(StoppedLocations))
    ToStart = PendingLocations - ActiveLocations
    print('Identified '+str(len(ToStart))+' instances to start')
    for s in ToStart:
        try:
            if s in StoppedLocations:
                print("Restarting instance "+str(s))
                restartInstance(zoneFromName(s),s)
            else:
                print("Starting instance "+str(s))
                r = locationToRow(s)
                if s in AllInstances:
                    continue #Do Nothing!
                startInstance(r['region'],r['browser'],r['id'])
        except Exception as E:
            print("Error starting instance, continuing. Message: " + str(E))
    return True