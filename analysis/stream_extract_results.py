from extract_results import stepToDict, resultToDicts,dictToRow
from wpt_test import loadResults,gatherResults
import sqlite3
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat 
from random import choice

def getColNames(sql,table):
    cols = list()
    sql.execute('PRAGMA table_info(results);')
    for r in sql.fetchall():
        cols.append(r[1])
    return cols 

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def doJob(resultFiles,cols):
    queries = list()
    corrupt = 0
    for p in resultFiles:
        c = loadResults(p)
        if c is None:
            corrupt += 1  
            continue
        d = resultToDicts(p,c)
        for e in d:
            r = dictToRow(e,cols)
            query ="""INSERT INTO results VALUES """+r+";"
            queries.append(query)
    print("Corrupted Count: "+str(corrupt) + " out of " + str(len(resultFiles)))
    return queries

def getAlreadyStored(sql):
    sql.execute("""
        SELECT path from results;
    """)
    return set([x[0] for x in sql.fetchall()])

if __name__ == '__main__':
    db = sqlite3.connect('short-comparative-run/data.sqlite')
    sql = db.cursor()
    cols = getColNames(sql,'results')
    rFiles = set(gatherResults('short-comparative-run'))
    toCheck = list(rFiles - getAlreadyStored(sql))
    threads = 24
    cs = 1000
    t = tqdm(total = len(toCheck),desc='Results files to process')
    with ProcessPoolExecutor(max_workers=threads) as executor:
        futures = executor.map(doJob,chunks(toCheck,cs),repeat(cols))
        for f in futures:
            t.update(len(f))
            for q in f:
                try:
                    sql.execute(q)
                    if choice([True,False,False,False,False]):
                        db.commit()
                except sqlite3.IntegrityError as E:
                    continue 
        executor.shutdown(wait=True)


