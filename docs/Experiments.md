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
