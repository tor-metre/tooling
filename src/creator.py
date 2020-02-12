from utility.utils import gather_scripts
from utility.jobs import Jobs
import logging
import argparse

def make_job(experiment_id,zone,browser,agent_id,script_or_url,repeats,connectivity):
    return {
        "zone": zone,
        "browser": browser,
        "agent_id" : agent_id,
        "experiment_id" : experiment_id,
        "script" : script_or_url,
        "runs" : repeats,
        "connectivity" : connectivity
        }

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    p = argparse.ArgumentParser(description="CLI Tool for creating test jobs")
    p.add_argument("-d","--db",type=str,default="jobs.sqlite",help="Path to the Jobs DB")
    p.add_argument("-z","--zone", type=str, default="us-central1-a",
                        help='The zone to create the job in')
    p.add_argument("-b", "--browser",type=str,default="Firefox",help="The browser to use {Firefox, Tor}")
    p.add_argument("-a","--agent-id",type=str,default="test-agent",help="The agent id to use")
    p.add_argument("-e","--experiment-id",type=str,default="test-experiment",help="The experiment id to use")
    p.add_argument("script",type=str,help="The url or script file to test")
    p.add_argument("-r","--runs",type=int,help="The number of repeats to perform")
    p.add_argument("-c","--connectivity",type=str,default="Native",help="The connectivity to use {Native,...}")
    args = vars(p.parse_args())
    jobs = Jobs('test.db')
    j = make_job(args["experiment_id"],args["zone"],args["browser"],args["agent_id"],
                 args["script"],args["runs"],args["connectivity"])
    logging.debug(f"Submitting job: {j}")
    r = jobs.create_job(j)
    logging.info(f"Job submitted with id: {r}")
    exit(0)

if __name__ == '__main__':
    main()
