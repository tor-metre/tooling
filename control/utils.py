
regions = ['US-Central','EU-Central'] #TODO check 
torBrowsers = ['tor-browser-with-changes','tor-browser-without-changes'] #TODO Check
browsers = list(torBrowsers)
browsers.append('Firefox')

def getLocation(region,browser,id):
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

