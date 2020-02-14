# Design

This file lays out the high level design of the Watchdog.

## Overview

The watchdog is comprised of three core scripts which run continiously, with a 
number of further CLI tools for manual use. The three core scripts share state
with a sqlite database. 

The core scripts are:
 * `instance_controller` - This script considers the current job queue and 
 determines which GCP instances should be started, stopped or destroyed. It also
 attempts to detect stuck instances. 
 * `job_starter` - This script considers the current job queue and the available 
 agents for the WPT Server and dispatches jobs from the job queue to the WPT Server
 for processing.
 * `job_finisher`- This script considers the current job queue and determines 
 jobs may have recently finished. It checks they finished successfully and updates
 there status in the job queue. 
 
There are additionally a number of CLI tools:
 * `creator` - Used to manually insert jobs into the job queue, typically for
 testing purposes. 
 * `check_idle` - Used to inspect the WPT queues from the command line. 
 
 ## Code Structure
 
 The core scripts reside in this directory and contain the high level logic. They
 are responsible for parsing their specific arguments and their control flow. However,
 all interaction with the external services is wrapped in a number of helper classes. 
 These helper classes are stored in `utility`:
  * `configuration` - This class offers argument parsing and file configuration loading. 
  It can also be called directly and used to generate a new configuration file from 
  passed arguments. 
  * `gcp` - This class wraps all interactions with the Google Compute Platform. It can
  manage instances and report on their status. 
  * `jobs` - This class wraps all interactions with the jobs sqlite database. It can be 
  used to submit jobs, update their status and query the database. 
  * `logger` - This class handles logging initialisation and includes code for logging 
  directly to Google Stackdriver. As well as flat files, console logging, etc. 
  * `wpt` - This class wraps all interactions with the WPT server, including job submission,
  fetching results and querying the queue status. 
  * `utils` - This class holds various miscellaneous functions which do not fit in 
  other locations.  
 
 ## Job Lifecycle 
 
 The watchdog's primary unit of action is a job. A job is an atomic task which should
 be dispatched to the WPT server to be handed out to an agent. A job includes all 
 the required information for the performance of a test, including which browser to use,
 which WPT script or URL to check and any other configuration. Jobs are created as 
 simple Python dictionaries and persisted in the jobs sqlite database. They have 
 a finite number of possible statuses:
  * `AWAITING` - Newly created jobs which have not yet been submitted. 
  * `SUBMITTED` - After the job has been submitted to the WPT server. This can only 
  happen when a corresponding agent is available to process the job.
  * `FINISHED` - After the job has been checked and confirmed to have finished successfully. 
  This implies a WPT result exists for the job. 
  * `ERROR_SUBMITTING` - If the WPT Server rejected the creation of the job.
  * `ERROR_TESTING` - If the WPT Server reported the job failed after submission.
  
  ## Instance Lifecycle 
  
 The Google Compute Engine is used for instance management. Instances are created
 from a pre-provided image on demand. They are started when jobs exist in the job queue
 for them and are automatically halted when no jobs remain. Currently, a particular 
 instance is uniquely associated with a particular Tor Browser instance in terms 
 of persistent state. However, this is planned to change, as a cost is charged for each
 hard drive image stored with the Compute Engine.