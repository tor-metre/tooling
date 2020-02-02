""" Library file for functions that interact with the WPT server.
"""

import json
import subprocess
import tempfile
import utils

def runTest(path,server,key,connectivity='Native',location='firefox'):
    """ Sychronously run a WPT test and return the output.

    This function calls the WPT javascript API and submits a test. It polls
    (every 5 seconds) for the job to finish and returns the results as an object
    (parsed from the JSON). 

    Positional Arguments:
        path - The location of the script to test, or the website URL
        server - The WPT server to use
        key - The API key for the WPT server

    Keyword Arguments:
        connectivity - The connectivity profile to use for the test
        location - The location that should run the test.
    """
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
    ]
    outT = tempfile.SpooledTemporaryFile(mode='w+') 
    result = subprocess.run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = json.loads(result) #String to JSON
    return output  

def submitTest(job,server,key):
    """ Asychronously run a WPT test.

    This function calls the WPT javascript API and submits a test. It returns the result
    of the request as an object, including success code and a unique ID for the submitted
    job.

    Positional Arguments:
        job - A python dictionary containing a 'script' key with a string value
        server - The WPT server to use
        key - The API key for the WPT server
    """
    location = utils.rowToLocation(job)
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
    outT = tempfile.SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    result = subprocess.run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = json.loads(result) #String to JSON
    return output

def successfulResult(result):
    """ Checks that a WPT test was successful.

    Returns a boolean value indicating success or failure.

    Parameters:
        result - A result returned from the WPT API converted into a python object. 

    """
    return result['statusCode'] == 200 and result['statusText'] == 'Test Complete'

def runTask(path,location):
    """ Runs a WPT test (synchronously), checks the result and saves it
    """
    r = runTest(path,location=location)
    if not successfulResult(r):
        logging.warning("Task Failed: " + r['statusText'] )
    utils.saveResults(r)

def getTesters(wptserver):
    #See which locations the server thinks are up. 
    #Check all active instances appear on this list
    #Its okay if the server thinks some locations are up but the instances are down. It just hasn't realised yet.
    args = ['webpagetest',
            'testers',
            '--server',
            wptserver
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
    #Format (not checked)
    #['data']['location] {id,status,testers}
    return output  


def getQueueStatus(server):
    #See which locations the server thinks are up. 
    #Check all active instances appear on this list
    #Its okay if the server thinks some locations are up but the instances are down. It just hasn't realised yet.
    args = ['webpagetest',
            'locations',
            '--server',
            server
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
    #Format (not checked)
    #['data']['location] {id,status,PendingTests} PendingTests{Total,Testing,Idle}
    return output  

def getQueuedJobs():
    q = getQueueStatus(wptserver)
    if 'data' not in q['response'].keys():
        #No queues up!
        return dict()
    result = dict()
    if isinstance(q['response']['data']['location'],list):
        for v in q['response']['data']['location']:
            l = v['id']
            t = v['PendingTests']['Total']
            result[l] = t
    else:
        return {
            q['response']['data']['location']['id'] : 
            q['response']['data']['location']['PendingTests']['Total']
        }
    return result

def setServerLocations(locations):
    #Get all the locations we need. 
    #Push them to the server.ini 
    #Using scp?
    f = open('newLocations.ini','w')
    data = """[locations]
1=Test_loc
default=Test_loc
  
[Test_loc]
1=TESTLOCATIONCHANGEME
"""
    count = 1
    for l in locations:
        count += 1 
        data+=  str(count)+"="+l+"\n"
    data += 'label="Test Location"\n'
    data += """
[TESTLOCATIONCHANGEME]
browser=Chrome,Firefox,Tor Browser
label="Test Location"

"""
    #TODO Add additional lines
    for l in locations:
        data+= "["+l+"]"+"\n"
        if 'tor' in l: 
            data+= "browser=Tor Browser\n"
        else:
            data+= "browser=Firefox\n"
        data+='label="Test Location"\n'
        data += '\n'
    f.write(data)
    f.close()
    args = [
        'cp',
        'newLocations.ini',
        '/var/www/webpagetest/www/settings/locations.ini'
    ]
    run(args)

def checkFinished(id,server):

    args = ['webpagetest',
            'status',
            id,
            '--server',
            server
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    if int(output['statusCode']) == 200:
        return True
    else:
        return False

def getJSON(id,server):
    args = ['webpagetest',
            'results',
            id,
            '--server',
            server
    ]
    outT = SpooledTemporaryFile(mode='w+') #We can specify the size of the memory buffer here if we need.
    result = run(args,stdout=outT,bufsize=4096,check=True)
    outT.seek(0) #Have to return to the start of the file to read it. 
    result = outT.read()
    outT.close()
    output = loads(result) #String to JSON
    return output 

def downloadJob(i):
    jRes= getJSON(i,wptserver)
    from wpt_test import saveResults
    return saveResults(jRes,'../temp-steady-street')