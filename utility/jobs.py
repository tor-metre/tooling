from utils import rowToLocation, locationToRow
from wpt import getQueuedJobs
from datetime import datetime


def getAllLocations(sql):
    query = "SELECT region,browser,id FROM jobs GROUP BY region,browser,id"
    sql.execute(query)
    locations = set()
    for r in sql.fetchall():
        l = rowToLocation(r)
        locations.add(l)
    return locations


def setJobQueued(j, r, db, sql):
    # Upsert submitted_time, output_location (JSON), queue_ID,status
    newStatus = 'SUBMITTED'
    from datetime import datetime
    submitted_time = datetime.now()
    queue_id = r['data']['testId']
    query = """
        UPDATE jobs
        SET submitted_time = '""" + str(submitted_time) + """',
            queue_id = '""" + str(queue_id) + """',
            status = '""" + str(newStatus) + """'
        WHERE
            region = '""" + str(j['region']) + """'
            AND browser = '""" + str(j['browser']) + """'
            AND id = '""" + str(j['id']) + """'
            AND script = '""" + str(j['script']) + """'
            AND step = '""" + str(j['step']) + """'
            AND iter = '""" + str(j['iter']) + """'
    ;"""
    # print(query)
    sql.execute(query)
    db.commit()
    if sql.rowcount != 1:
        raise RuntimeError("Error performing upsert on " + str(j))


def getPendingLocations(sql):
    # Do Query, get locations with pending jobs
    # Remove any which are active in the server queue
    query = """
        SELECT region,browser,id FROM jobs WHERE status='AWAITING' GROUP BY region,browser,id
    """
    # print(query)
    sql.execute(query)
    results = sql.fetchall()
    locations = set()
    for r in results:
        locations.add(rowToLocation(r))
    print('Found ' + str(len(locations)) + ' pending locations')
    return locations


def getJobs(location, status, limit, sql, orderby="", ):
    # Get all jobs matching a particualr location,status up to some limit
    # Not tested.

    row = locationToRow(location)
    cmd = """ SELECT * FROM jobs where region = '""" + row['region'] + """'
    AND browser = '""" + row['browser'] + """'
    AND id = '""" + row['id'] + """'
    AND status = '""" + str(status) + "' " + orderby + """ LIMIT """ + str(limit) + ";"
    # print(cmd)
    sql.execute(cmd)
    return list(sql.fetchall())

def setJobFailed(j, r, db, sql):
    # Upsert submitted_time, output_location (JSON), queue_ID,status
    newStatus = 'FAILED'
    from datetime import datetime
    submitted_time = datetime.now()
    query = """
        UPDATE jobs
        SET submitted_time = '""" + str(submitted_time) + """',
            status = '""" + str(newStatus) + """',
            output_location = '""" + str(r).replace("'", "''") + """'
        WHERE
            region = '""" + str(j['region']) + """'
            AND browser = '""" + str(j['browser']) + """'
            AND id = '""" + str(j['id']) + """'
            AND script = '""" + str(j['script']) + """'
            AND step = '""" + str(j['step']) + """'
            AND iter = '""" + str(j['iter']) + """' ;"""
    sql.execute(query)
    db.commit()
    if sql.rowcount != 1:
        raise RuntimeError("Error performing upsert on " + str(j))





def setErrors(i, f, e, sql, db):
    query = """
    UPDATE jobs
        SET status = 'ERROR',
            output_location = '""" + str(f) + ' ' + str(e).replace("'", "''") + """',
            finished_time = '""" + str(datetime.now()) + """'
        WHERE queue_id = '""" + str(i) + """';
    """
    sql.execute(query)
    return True


def setFinished(i, sql, db):
    query = """
    UPDATE jobs
        SET status = 'FINISHED',
            finished_time = '""" + str(datetime.now()) + """'
        WHERE queue_id = '""" + str(i) + """';
    """
    sql.execute(query)
    return True
