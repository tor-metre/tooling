
#Using Firefox and Tor Firefox. 
#Fetch each website, spider it a few times. 
#Record the path and timings / resources / measurements. 
#Purpose of Tor Firefox is to check repeatability cheaply. 
#Store in a table as blobl (id - base url - list of links.)

# open list of urls for testing

from random import choice
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException,JavascriptException,WebDriverException,StaleElementReferenceException
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm
from tldextract import extract

def badURL(currentURL,oldURL):
    #Return True if any of these conditions is met.
    verdict = currentURL is None 
    verdict = verdict or currentURL is ""
    verdict = verdict or 'https' not in currentURL 
    verdict = verdict or oldURL == currentURL
    verdict = verdict or extract(oldURL).registered_domain != extract(currentURL).registered_domain
    return verdict  
            

def genSpecimen(baseURL,driver):
    #Given a url, create a specimen session 
    driver.set_page_load_timeout(120)
    maxLength = 2
    length = 0
    currentURL = baseURL
    path = []
    try:
        while length < maxLength:
            length += 1
            if 'http' not in currentURL:
                currentURL = 'https://'+currentURL
            elif 'https' not in currentURL:
                currentURL = currentURL.replace('http://','https://')
            if  not currentURL.startswith('https://'):
                raise RuntimeError('Not HTTPS URL selected! '+currentURL)
            print('Fetching: '+str(currentURL))
            driver.get(currentURL)
            path.append(currentURL)
            oldURL = currentURL
            currentURL = None
            links = set(map(lambda x:x.get_attribute('href'),driver.find_elements_by_tag_name('a')))
            while badURL(currentURL,oldURL):
                if len(links) == 0:
                    raise RuntimeError('No good outgoing links found! '+currentURL)
                currentURL = choice(list(links))
                links.remove(currentURL)
    except Exception as E:
        print('Error: ' +str(E))
        return []
    return path 

def getFirefoxDriver():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('privacy.trackingprotection.enabled',True)
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options,firefox_profile=profile)
    return driver

def getTorFirefoxDriver():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('privacy.trackingprotection.enabled',False)
    profile.set_preference('dom.performance.time_to_contentful_paint.enabled',True)
    profile.set_preference('dom.performance.time_to_non_blank_paint.enabled',True)
    profile.set_preference( "network.proxy.type", 1 )
    profile.set_preference( "network.proxy.socks_version", 5 )
    profile.set_preference( "network.proxy.socks", '127.0.0.1' )
    profile.set_preference( "network.proxy.socks_port", 9050 )
    profile.set_preference( "network.proxy.socks_remote_dns", True )
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options,firefox_profile=profile)
    driver.db_name = 'Firefox-Over-Tor'
    return driver

with open('alexa-top-1000.txt', 'r') as url_file:
    loaded_urls = url_file.readlines()

from random import sample 
test_urls = list()
test_urls.extend(sample(loaded_urls[0:100],25))
test_urls.extend(sample(loaded_urls[-100:],25))
test_urls.extend(sample(loaded_urls[100:-100],100))

#firefox = getFirefoxDriver()
firefoxTor = getTorFirefoxDriver()
torBrowser = ""
drivers = [firefoxTor]#,firefox,torBrowser]
specimens = list()
for url in tqdm(test_urls):
    specimen = genSpecimen(url.replace('\n',''),firefoxTor)
    if specimen == []:
        continue
    else:
        specimens.append(specimen)
    if len(specimens) > 100:
        break

folder = 'sessionlets/baseline'

from os import makedirs
makedirs(folder,exist_ok=True)

id = 0
for specimen in specimens:
    id += 1
    with open(folder + '/' + str(id)+'.wpt','w') as out_file:
        step = 0
        for p in specimen:
            step += 1
            out_file.write('setEventName ' + str(step)+'\n')
            out_file.write('navigate '+ p.replace('\n','')+'\n')