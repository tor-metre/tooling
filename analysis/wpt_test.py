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
            if len(output)>200:
                break
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
    id = result['data']['id']
    label = result['data']['label']
    folder = outFolder+'/'+label+'-'+id
    makedirs(folder,exist_ok=True)
    f = open(folder+'/results.json.bz2','wb')
    s = dumps(result).encode('utf-8')
    f.write(compress(s))
    f.close()
    urls = list()
    for rnum,r in result['data']['runs'].items():
        for snum,s in enumerate(r['firstView']['steps']):
            u = s['images']['screenShot']
            urls.append((rnum,snum,u))
    for rnum,snum,u in urls:
        fname = 'R'+str(rnum)+'S'+str(snum)+'.jpg'
        urlretrieve(u,filename=folder+'/'+fname)

def loadResults(result):
    #Open 
    f = open(result,'rb')
    #Decompress
    try:
        s = decompress(f.read())
    except ValueError as E:
        print(E)
        return None
    f.close()
    #Jsonise
    try:
        j = loads(s)
    except JSONDecodeError as E:
        print(E)
        return None 
    #
    # return
    return j

