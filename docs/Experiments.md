# Experiments

This document describes the Experiment API for submitting experiments and extracting results. 

## Overview

The Experiments API is a three tier hierarchy of objects. Experiments contain Instances which
contain jobs. Each tier provides context for the next tier. Further, programmatic controls 
ensure the experiment is well formed and tries to ensure configuration errors will not be 
discovered at run time. 

## Experiment Objects

Global State Used:
 * Jobs DB 
 * WPT Results Folder

An Experiment records the following data:
 * A Unique ID 
 * Description (Human Readable)
 * A list of instances
 * Defaults (Optional):
    * Storage Location
    * Instance Type
    * Base VM Image
    * Tor Browser Archive
 
The following 'constructors' are exposed:
 * Get Experiment by ID (loads from DB)
 * Create New Experiment 
 
An Experiment has the following methods:
 * Add Instance
 * Get Instance
 * Check Finished (Returns whether or not it has finished )
 * Get Results (Iterator that returns paths to each result)

## Instance Objects

An Instance is *always* attached to an Experiment. 

An Instance records the following data:
 * ID 
 * Instance Type
 * Base VM Image
 * Tor Browser Acrhive
 * Diff Storage Location
 * A list of Jobs
 
It can be 'constructed' through the Experiment Object. 

## Job Objects

This is a WPT Job object. It is always attached to an Instance.

It exposes all the WPT Job Options. As well as scheduling etc. 

Relevant Arguments from WPT API:

    -y, --connectivity <profile>        connectivity profile (Cable|DSL|3GSlow|3G|3GFast|4G|LTE|Edge|2G|Dial|FIOS|Native|custom) [Cable]
    -r, --runs <number>                 number of test runs [1]
    -f, --first                         skip the Repeat View test
    -L, --label <label>                 label for the test
    -i, --onload                        stop test at document complete. typically, tests run until all activity stops
    -S, --noscript                      disable JavaScript (IE, Chrome, Firefox)
    -C, --clearcerts                    clear SSL certificate caches
    -R, --ignoressl                     ignore SSL certificate errors, e.g. name mismatch, self-signed certificates, etc
    -u, --tcpdump                       capture network packet trace (tcpdump)
    -O, --bodies                        save response bodies for text resources
    -K, --keepua                        do not add PTST to the original browser User Agent string
    -m, --dom <element>                 DOM element to record for sub-measurement
    -N, --duration <seconds>            minimum test duration in seconds
    -E, --tester <name>                 run the test on a specific PC (name must match exactly or the test will not run)
    -b, --block <urls>                  space-delimited list of urls to block (substring match)
    -Z, --spof <domains>                space-delimited list of domains to simulate failure by re-routing to blackhole.webpagetest.org to silently drop all requests
    -c, --custom <script>               execute arbitrary JavaScript at the end of a test to collect custom metrics
    -D, --bwdown <bandwidth>            download bandwidth in Kbps (used when specifying a custom connectivity profile)
    -U, --bwup <bandwidth>              upload bandwidth in Kbps (used when specifying a custom connectivity profile)
    -Y, --latency <time>                first-hop Round Trip Time in ms (used when specifying a custom connectivity profile)
    -P, --plr <percentage>              packet loss rate - percent of packets to drop (used when specifying a custom connectivity profile)
    -z, --noopt                         disable optimization checks (for faster testing)
    -I, --noimages                      disable screen shot capturing
    -F, --full                          save a full-resolution version of the fully loaded screen shot as a PNG
    -j, --jpeg <level>                  jpeg compression level (30-100) for the screen shots and video capture
        --breakdown                     include the breakdown of requests and bytes by mime type
        --domains                       include the breakdown of requests and bytes by domain
        --pagespeed                     include the PageSpeed score in the response (may be slower)
        --requests                      include the request data in the response (slower and results in much larger responses)
