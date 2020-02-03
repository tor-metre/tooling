from wpt import WPT
from utils import saveResults
from time import sleep
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from jobs import Jobs


def downloadJob(wpt, i, output):
    return saveResults(wpt.getResult(i), output)

def doJob(r):
    try:
        server = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
        key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'
        output = '../temp-steady-street'
        wpt = WPT(server, key)
        i, t = r
        return i, downloadJob(wpt, i, output)
    except Exception as E:
        print("Error performing job: " + str(E))
        return None


def getFinished(doJob, jobs):
    # Get Pending where have been pending for >60 seconds
    # Check status with server
    # Return list
    results = jobs.getSubmitted()
    print('Checking ' + str(len(results)) + ' new jobs')
    executor = ThreadPoolExecutor(max_workers=40)
    futures = executor.map(doJob, results)
    errors_or_missing = 0
    set_errors = 0
    success = 0
    for fu in tqdm(futures):
        if fu is None:
            errors_or_missing += 1
            continue
        else:
            i, f = fu
            if f[0]:
                success += 1
                jobs.setFinished(i)
            else:
                set_errors += 1
                jobs.setErrors(i, f[1], f[2])
    jobs.persist()
    print("Timestamp: " + str(datetime.now()))
    print("Errors or missing: " + str(errors_or_missing))
    print("Set Errors: " + str(set_errors))
    print("Successes: " + str(success))
    executor.shutdown(wait=True)


if __name__ == '__main__':
    while True:
        jobs = Jobs('test.db')
        getFinished(doJob, jobs)
        sleep(1)
