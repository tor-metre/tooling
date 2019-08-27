from wpt_test import gatherJSONResults
from tqdm import tqdm
import logging
from pprint import pprint
import sqlite3 

def stepToDict(path,location,label,run,step,contents):
    keys = ['responses_200', 'bytesOut', 'responses_404', 'URL', 'date', 
            'responses_other', 'TTFB', 'test_run_time_ms', 'bytesIn', 'firstPaint', 
            'domElements', 'SpeedIndex', 'visualComplete85', 'visualComplete90', 'visualComplete95',
            'visualComplete99', 'visualComplete', 'requestsFull', 'maybeCaptcha', 'pages'
    ]
    output = dict()
    output['location'] = location
    output['label'] = label
    output['run'] = run 
    output['step'] = step
    output['path'] = path
    for k in keys:
        if k not in contents.keys() :
            output[k] = 'MISSING'
        else:
            output[k] = contents[k]
    return output

def resultToDicts(p,r):
    results = list()
    path = p
    label = r['data']['label']
    location = r['data']['location']
    for run in r['data']['runs'].keys():
        if 'steps' not in r['data']['runs'][run]['firstView'].keys():
            output = stepToDict(path,location,label,run,'0',r['data']['runs'][run]['firstView'])
            results.append(output)
        else:
            for step, contents in enumerate(r['data']['runs'][run]['firstView']['steps']):
                output = stepToDict(path,location,label,run,step,contents)
                results.append(output)
    return results 

def gatherDicts(path):
    jresults = gatherJSONResults(path,tqdm_en=True)
    dicts = list()
    for p,j in tqdm(jresults,desc='Converting JSON to flat dictionaries'):
        r = resultToDicts(p,j)
        dicts.extend(r)
    return dicts

def dictToRow(d,cols):
    row = "("
    for k in cols:
        if k in d.keys():
            v = str(d[k])
            v = v.replace("'","''")
            row += "'" + v + "',"
        else:
            row += "'MISSING'" + ","
    row = row.rstrip(",")
    row += ")"
    return row

if __name__ =='__main__':
    dicts = gatherDicts('short-comparative-run')
    db = sqlite3.connect('short-comparative-run/data.sqlite')
    sql = db.cursor()

    columns = set() 
    for d in tqdm(dicts,desc='Building list of columns'):
        columns.update(d.keys())

    print("Discovered "+str(len(columns))+" unique columns")
    if len(columns) == 0:
        print('Error!')
        exit(-1)
    colList = sorted(list(columns))
    print(colList)
    createTable = """CREATE TABLE IF NOT EXISTS results ("""
    for col in colList:
        createTable += col + " TEXT,"
    createTable += """PRIMARY KEY (path,run,step)"""
    createTable += """ );"""
    sql.execute(createTable)
    db.commit()
    for d in tqdm(dicts,desc="Storing rows"):
        r = dictToRow(d,colList)
        query ="""INSERT INTO results VALUES """+r+";"
        sql.execute(query)

    db.commit()