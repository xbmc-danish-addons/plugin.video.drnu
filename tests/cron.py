"""Stub for the service.cronxbmc 'cron' module (deprecated integration).

Only used by resources/lib/cronjob.py to remove jobs left behind by older
addon versions; jobs are kept in a module-level list so tests can verify
the removal.
"""
JOBS = []


class CronJob:
    def __init__(self, id='', name='', command='', expression=''):
        self.id = id
        self.name = name
        self.command = command
        self.expression = expression


class CronManager:
    def getJobs(self):
        return list(JOBS)

    def getJob(self, job_id):
        for job in JOBS:
            if job.id == job_id:
                return job
        return None

    def addJob(self, job):
        JOBS.append(job)

    def deleteJob(self, job_id):
        for job in list(JOBS):
            if job.id == job_id:
                JOBS.remove(job)
