
#Open a folder of sessionlets
#Create a new folder where each sessionlet has been given a flag. 

from wpt_test import gatherScripts
from tqdm import tqdm
from os import makedirs
versions = [
    #'original', 'trackingprotection','resistfingerprinting','tor','doh','tordoh', 'ublock'
    'original', 'ublock'
]
inDir = 'sessionlets/baseline'
outDir = 'versioned/baseline'
makedirs(outDir,exist_ok=True)

for n,s in tqdm(gatherScripts(inDir).items()):
    f = open(s,'r')
    c = f.read()
    #a = c.split('\n')
    if "FEATURES:" in c:
        print("Skipping (already present): " + str(s))
    for v in versions:
        name = n+'-'+v+'.wpt'
        l = '//FEATURES:' + v + '\n'
        t = l + c
        o = open(outDir+'/'+name,'w')
        o.write(t)
        o.close()
    f.close()