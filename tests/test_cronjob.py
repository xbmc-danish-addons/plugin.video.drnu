"""Tests for the deprecated cronxbmc job removal (resources/lib/cronjob.py)."""
import cron
from resources.lib.cronjob import JOB_NAME, remove_cronjob


def test_remove_cronjob_deletes_only_drnu_job():
    drnu = cron.CronJob(id='1', name=JOB_NAME)
    other = cron.CronJob(id='2', name='someone else job')
    cron.JOBS.clear()
    cron.JOBS.extend([drnu, other])
    remove_cronjob()
    assert cron.JOBS == [other]


def test_remove_cronjob_noop_without_job():
    cron.JOBS.clear()
    remove_cronjob()
    assert cron.JOBS == []
