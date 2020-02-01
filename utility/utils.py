
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
