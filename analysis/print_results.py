from wpt_test import gatherJSONResults
from tqdm import tqdm
import logging
from pprint import pprint

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
            output = stepToDict(path,location,label,run,'1',r['data']['runs'][run]['firstView'])
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

dicts = gatherDicts('latest/')

for d in dicts:
    if 'TTFB' in d.keys() and d['TTFB'] != 'MISSING' and d['TTFB'] < 100 and d['step'] in ['1',1,'0',0]:
        pprint(d['pages'])

interested = ['responses_200', 'bytesOut', 'responses_404', 'URL', 'date', 
            'responses_other', 'TTFB', 'test_run_time_ms', 'bytesIn', 'firstPaint', 
            'domElements', 'SpeedIndex', 'visualComplete85', 'visualComplete90', 'visualComplete95',
            'visualComplete99', 'visualComplete', 'requestsFull', 'maybeCaptcha'
    ]

series = dict()
for i in interested:
    series[i] = list()

from collections import Counter

missing = Counter()
for d in dicts:
    if d['step'] not in ['1',1,'0',0]:
        continue
    for i in interested:
        if d[i] in ['MISSING']:
            missing.update([i])
        else:
            series[i].append(d[i])


import plotly.graph_objs as go
from plotly.offline import plot 

for (k,v) in series.items():
    if k in ['test_run_time_ms','TTFB','SpeedIndex','firstPaint','visualComplete85']:
        plot([go.Box(y=v,name=k,boxpoints='all',jitter=0.3,pointpos=-1.8)])
        from time import sleep
        sleep(1)
  

pprint(missing)

