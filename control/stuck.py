from time import sleep

from gcp import GCP
from wpt import WPT
from tqdm import tqdm

def getCandidates(wpt,gcp):
    aliveInstances = set([x['name'] for x in gcp.get_active_instances()])
    activeQueues = set(wpt.get_active_job_queues())
    candidateStuck = aliveInstances - activeQueues
    actualStuck = set()
    for c in candidateStuck:
        if 'watchdog' in c or 'wpt-server' in c or '--' not in c:
            continue
        else:
            actualStuck.add(c)
    return actualStuck

if __name__ == '__main__':
    gcp = GCP("tor-metre-personal", "firefox-works", "n1-standard-2", "None")
    server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
    key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
    wpt = WPT(server,key)
    c1 = getCandidates(wpt,gcp)
    print("There are "+str(len(c1))+" candidates for being stuck")

    for t in tqdm(range(0,300),desc='Waiting',disable=True):
        sleep(1)

    c2 = getCandidates(wpt,gcp)
    print("There are now "+str(len(c2))+" candidates for being stuck")

    c = c1.intersection(c2)
    print("There are "+str(len(c))+" candidates apparently stuck both times")

    for l in tqdm(c,desc="Deleting apparently stuck instances",disable=True):
        gcp.delete_instance(l)






