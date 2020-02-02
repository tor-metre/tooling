from wpt import getQueueStatus

wptserver = 'http://wpt-server.us-central1-a.c.moz-fx-dev-djackson-torperf.internal'
key = '1Wa1cxFtIzeg85vBqS4hdHNX11tEwqa2'

qu = getQueueStatus(wptserver)

count = 0
count2 = 0
if 'data' not in qu['response'].keys():
        print("No testers active")
        exit(0)
for v in qu['response']['data']['location']:
    l = v['id']
    t = v['PendingTests']['Total']
    if t < 2:
        count += 1
    if t < 1:
        count2 += 1
        #print(l)

print(str(count))
print(str(count2))