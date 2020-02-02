from killer import getActiveQueues
from initiator import getQueueStatus,getActiveInstances,zoneFromName

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

def getCandidates():
    aliveInstances = set([x['name'] for x in getActiveInstances()])
    activeQueues = set(getActiveQueues())
    candidateStuck = aliveInstances - activeQueues
    actualStuck = set()
    for c in candidateStuck:
        if 'watchdog' in c or 'wpt-server' in c or '--' not in c:
            continue
        else:
            actualStuck.add(c)
    return actualStuck

from time import sleep

c1 = getCandidates()
print("There are "+str(len(c1))+" candidates for being stuck")
from tqdm import tqdm

for t in tqdm(range(0,300),desc='Waiting',disable=True):
    sleep(1)

c2 = getCandidates()
print("There are now "+str(len(c2))+" candidates for being stuck")

c = c1.intersection(c2)
print("There are "+str(len(c))+" candidates apparently stuck both times")

for l in tqdm(c,desc="Deleting apparently stuck instances",disable=True):
    deleteInstance(l)






