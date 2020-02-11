from .utility.utils import gather_scripts
from .utility.jobs import Jobs


def generate_jobs(jobs, regions, browsers, ids, scripts, reps, experiment_id):
    total = 0
    for r in regions:
        for b in browsers:
            for i in ids:
                for _ in reps:
                    step = 0
                    for s in scripts.values():
                        #TODO Make Dict
                        jobs.create_job(r, b, i, s, experiment_id,1)
                        step += 1 
                        total += 1
    jobs.persist()
    print(str(total)+' jobs created')


def main():
    jobs = Jobs('test.db')
    experiment_id = 'Testing-EPT'
    scripts = gather_scripts('../wpt-instrumentation/baseline/original')
    generate_jobs(jobs, ['us-central1-a'], ['tor-without-timer'], range(1000, 1010), scripts, range(2), experiment_id)
    generate_jobs(jobs, ['us-central1-a'], ['tor-with-timer'], range(1010, 1020), scripts, range(2), experiment_id)
    scripts = gather_scripts('../wpt-instrumentation/baseline/ublock')
    generate_jobs(jobs, ['us-central1-a'], ['tor-without-timer'], range(1020, 1030), scripts, range(2), experiment_id)
    generate_jobs(jobs, ['us-central1-a'], ['tor-with-timer'], range(1030, 1040), scripts, range(2), experiment_id)


if __name__ == '__main__':
    main()
