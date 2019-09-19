from draw_scatter_dataset import draw_graph
from ci_analysis import gatherDicts,bootstrap
from numpy import mean 

dicts = gatherDicts()

def drawMetric(metric):
    times = []
    values = []
    for d in dicts:
        if 'tor' not in d['location']:
            continue
        if d['date'] != 'MISSING' and d[metric] != 'MISSING':
            times.append(float(d['date']))
            values.append(float(d[metric]))
        else:
            continue 

    draw_graph(metric+' samples over Tor',0,100000,times,values,'graphs/'+metric+'.png')

drawMetric('SpeedIndex')
drawMetric('visualComplete85')
drawMetric('firstPaint')
drawMetric('test_run_time_ms')
drawMetric('TTFB')


testTime = list()
for d in dicts:
    if d['VisualComplete85'] == 'MISSING' or 'tor' not in d['location']:
        continue
    if float(d['VisualComplete85']) >90000 and float(d['VisualComplete85']) <95000:
        print('~90 seconds')
        print(d['URL'])
        print(d['path'])
    if float(d['VisualComplete85']) <500:
        print('~0 seconds')
        print(d['URL'])
        print(d['path'])
    if int(d['step']) != 0:
        testTime.append(float(d['test_run_time_ms']))

print(mean(testTime))
print(bootstrap(testTime))