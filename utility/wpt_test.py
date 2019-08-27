from glob import glob 
from os import path,makedirs
from subprocess import run
from json import loads, dumps, JSONDecodeError
from urllib.request import urlretrieve
from tempfile import SpooledTemporaryFile
from bz2 import compress, decompress
import logging
import pprint
from tqdm import tqdm

server = '127.0.0.1:8999'
key = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'

def gatherScripts(folder,suffix='.wpt'):
    scripts = glob(folder+'/**/*'+suffix,recursive=True)
    return {path.split(path.splitext(s)[0])[1] : s for s in scripts}

def gatherResults(folder,suffix='.bz2'):
    results = glob(folder+'/**/*'+suffix,recursive=True)
    return results

def gatherJSONResults(folder,tqdm_en=False):
    results = gatherResults(folder)
    if tqdm_en:
        output = list()
        for r in tqdm(results,desc='Decompressing and loading JSON'):
            o = loadResults(r)
            output.append((r,o))
        return output
    else:
        return list(map(loadResults,results))

def loadScript(p):
    #Given a script file 
    #Load it and return the string.
    f = open(p,'r')
    s = f.read()
    return s 

def runTask(path,location):
    r = runTest(path,location=location)
    if not successfulResult(r):
        logging.warning("Task Failed: " + r['statusText'] )
    saveResults(r)

def rowToLocation(row):
    return row['region']+'--'+row['browser']+'--'+row['id']


def submitTest(job,server,key):
    location = rowToLocation(job)
    print(location +' '+job['script'])
    args = [
        'webpagetest',
        'test', job['script'],
        '--server', server,
        '--key', key,
        '--location', location,
        '--runs', '1',
        '--connectivity', 'Native',
        '--label',job['script'],
        '--keepua', #Don't change the useragent to indicate this is a bot
        '--first', #Don't try for a repeat view
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    #Stops us hitting the buffer limit if use pipe.
    #cmd = ""
    #for arg in args:
    #    cmd = cmd + arg + ' '
    #print(cmd)
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    return output

def runTest(path,connectivity='Native',location='firefox'):
    #Note that timeout is a global maxiumum and includes queuing time!
    #it does not relate to how long the test runs 
    #TODO Error Handling
    args = [
        'webpagetest',
        'test', path,
        '--server', server,
        '--key', key,
        '--location', location,
        '--runs', '1',
        '--connectivity', connectivity,
        '--label',path,
        '--keepua', #Don't change the useragent to indicate this is a bot
        '--first', #Don't try for a repeat view
        '--poll','5' #How frequently to poll the web server for the result
        #,'--timeout',str(timeout)
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    #Stops us hitting the buffer limit if use pipe.
    #cmd = ""
    #for arg in args:
    #    cmd = cmd + arg + ' '
    #print(cmd)
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    return output  

def successfulResult(result):
    return result['statusCode'] == 200 and result['statusText'] == 'Test Complete'

def saveResults(result,outFolder='out'):
    #TODO Error Handling
    i = result['data']['id']
    label = result['data']['label']
    label = label.replace('..','')
    folder = outFolder+'/'+label+'-'+i
    makedirs(folder,exist_ok=True)
    f = open(folder+'/results.json.bz2','wb')
    s = dumps(result).encode('utf-8')
    f.write(compress(s))
    f.close()
    urls = list()
    errors = list()
    for rnum,r in result['data']['runs'].items():
        if 'steps' not in r['firstView'].keys():
            u = r['firstView']['images']['screenShot']
            urls.append((rnum,0,u))
            continue 
        for snum,s in enumerate(r['firstView']['steps']):
            u = s['images']['screenShot']
            urls.append((rnum,snum,u))
    for rnum,snum,u in urls:
        from urllib.error import HTTPError
        fname = 'R'+str(rnum)+'S'+str(snum)+'.jpg'
        try:
            urlretrieve(u,filename=folder+'/'+fname)
        except HTTPError as E:
            print('HTTP Error: '+str(E))
            #TODO How to handle / persist this gracefully!?
            errors.append(str(E))
    if len(errors) > 0:
        #TODO This could be one line 
        return (False,folder,errors)
    else:
        return (True, folder,[]) 

def loadResults(result):
    #Open 
    f = open(result,'rb')
    #Decompress
    s = decompress(f.read())
    f.close()
    #Jsonise
    try:
        print("trying")
        j = loads(s)
    except JSONDecodeError as E:
        print(E)
        return None
    #return
    return j

