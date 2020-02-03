from wpt import WPT
from utils import saveResults
import sqlite3
from time import sleep
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from jobs import setFinished, setErrors


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


def getFinished(doJob, sql, db):
    # Get Pending where have been pending for >60 seconds
    # Check status with server
    # Return list
    query = """
        SELECT queue_id, submitted_time FROM jobs WHERE status='SUBMITTED' LIMIT 2000;
    """
    sql.execute(query)
    results = list(sql.fetchall())
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
                setFinished(i, sql, db)
            else:
                set_errors += 1
                setErrors(i, f[1], f[2], sql, db)
    db.commit()
    print("Timestamp: " + str(datetime.now()))
    print("Errors or missing: " + str(errors_or_missing))
    print("Set Errors: " + str(set_errors))
    print("Successes: " + str(success))
    executor.shutdown(wait=True)


if __name__ == '__main__':
    while True:
        db = sqlite3.connect('test.db')
        db.row_factory = sqlite3.Row
        sql = db.cursor()
        getFinished(sql, db)
        sleep(1)
