""" This library file holds functions that don't fit in other locations.
"""

from glob import glob
import json
import bz2
import os
import urllib.request

def getLocation(region,browser,id):
    """ Turns a GCP Location into a WPT Location

    This function converts a GCP location into a WPT location.
    Parameters:
        region - The GCP Region
        browser - The desired browser
        id - The desired identity

    Returns a string describing the WPT location.
    """
    regions = ['US-Central','EU-Central'] #TODO check 
    torBrowsers = ['tor-browser-with-changes','tor-browser-without-changes'] #TODO Check
    browsers = list(torBrowsers)
    browsers.append('Firefox')
    if id and 'tor' not in browser:
        raise RuntimeError('ID specified but not Tor Version '+str(browser))
    if 'tor' in browser and not id:
        raise RuntimeError('Tor specified but not id' + str(browser))
    if region not in regions or browser not in browsers:
        raise RuntimeError("Incorrect region or browser specified: "+str(region)+" "+str(browser))
    #Checks passed.
    if id:
        return region+'-'+browser+'-'+id
    else:
        return region +'-' + browser

def zoneFromName(name):
    components = name.split('--')
    return components[0]

def idFromName(name):
    components = name.split('--')
    return components[2]

def locationToRow(location):
    components = location.split('--')
    row = dict()
    row['region'] = components[0]
    row['browser'] = components[1]
    row['id'] = components[2]
    return row

def rowToLocation(row):
    """ Turns a GCP Location into a WPT Location. 
    """
    return row['region']+'--'+row['browser']+'--'+row['id']

def gatherScripts(folder,suffix='.wpt'):
    """ Gathers all WPT Script files from a directory (recursively)

    Parameters:
        Folder - The folder to recursively search 
        Suffix - The suffix for WPT script files. 
    """
    scripts = glob(folder+'/**/*'+suffix,recursive=True)
    return {os.path.split(os.path.splitext(s)[0])[1] : s for s in scripts}

def gatherResults(folder,suffix='.bz2'):
    """ Gathers all WPT Results files from a directory (recursively)

    Parameters:
        Folder - The folder to recursively search 
        Suffix - The suffix for WPT Results files. 
    """
    results = glob(folder+'/**/*'+suffix,recursive=True)
    return results

def gatherJSONResults(folder):
    """ Loads all WPT Result files from a directory (recursively) into memory

    Parameters:
        Folder - The folder to recursively search 

    Output: A list results, each result is a Python dictionary.
    """
    results = gatherResults(folder)
    return list(map(loadResults,results))

def loadScript(p):
    """ Given a script file, load it as a string
    """
    f = open(p,'r')
    s = f.read()
    return s 

def saveResults(result,outFolder='out'):
    """  Given a result, extract key data, compress it and store it
    """
    i = result['data']['id']
    label = result['data']['label']
    label = label.replace('..','')
    folder = outFolder+'/'+label+'-'+i
    os.makedirs(folder,exist_ok=True)
    f = open(folder+'/results.json.bz2','wb')
    s = json.dumps(result).encode('utf-8')
    f.write(bz2.compress(s))
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
            urllib.request.urlretrieve(u,filename=folder+'/'+fname)
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
    """ Given a result file, decompress it and load the object into memory. 
    """
    f = open(result,'rb')
    s = bz2.decompress(f.read())
    f.close()
    try:
        j = json.loads(s)
    except json.JSONDecodeError as E:
        print(E)
        return None
    return j
