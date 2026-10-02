"""Unit tests for resources/lib/cronmatch.py (no Kodi needed)."""
from datetime import datetime

import pytest

from resources.lib.cronmatch import CronParseError, CronExpression, matched_since


def test_parse_and_match_simple():
    cron = CronExpression('0 3 * * *')
    assert cron.matches(datetime(2026, 9, 29, 3, 0))
    assert not cron.matches(datetime(2026, 9, 29, 3, 1))
    assert not cron.matches(datetime(2026, 9, 29, 4, 0))


def test_parse_list_and_range():
    cron = CronExpression('0,30 2-4 * * *')
    assert cron.matches(datetime(2026, 9, 29, 2, 30))
    assert cron.matches(datetime(2026, 9, 29, 4, 0))
    assert not cron.matches(datetime(2026, 9, 29, 5, 0))
    assert not cron.matches(datetime(2026, 9, 29, 3, 15))


def test_parse_step():
    cron = CronExpression('*/15 9 * * *')
    assert cron.matches(datetime(2026, 9, 29, 9, 45))
    assert not cron.matches(datetime(2026, 9, 29, 9, 50))
    # "5/15" = 5,20,35,50
    cron = CronExpression('5/15 * * * *')
    assert cron.matches(datetime(2026, 9, 29, 8, 35))
    assert not cron.matches(datetime(2026, 9, 29, 8, 5 - 1))


def test_parse_names_and_dow7():
    cron = CronExpression('0 3 * * mon')
    assert cron.matches(datetime(2026, 9, 28, 3, 0))  # a monday
    assert not cron.matches(datetime(2026, 9, 29, 3, 0))  # a tuesday
    cron = CronExpression('0 3 * * 7')
    assert cron.matches(datetime(2026, 9, 27, 3, 0))  # a sunday
    assert not cron.matches(datetime(2026, 9, 28, 3, 0))


def test_parse_aliases():
    assert CronExpression('@daily').matches(datetime(2026, 9, 29, 0, 0))
    assert CronExpression('@weekly').matches(datetime(2026, 9, 27, 0, 0))
    assert not CronExpression('@weekly').matches(datetime(2026, 9, 28, 0, 0))


def test_parse_error_cases():
    for bad in ['61 3 * * *', '* 24 * * *', '0 3 * * 8', 'bogus', '0 3 * *',
                '0 3 * * 1-5,9', '0 3 * * 5-1', '*/0 * * * *', '0 3 * jan-bogus']:
        with pytest.raises(CronParseError):
            CronExpression(bad)


def test_dom_dow_restriction_semantics():
    # both restricted: OR (vixie cron semantics)
    cron = CronExpression('0 3 13 * fri')
    assert cron.matches(datetime(2026, 9, 13, 3, 0))  # sunday, dom hit
    assert cron.matches(datetime(2026, 9, 25, 3, 0))  # friday, dow hit
    assert not cron.matches(datetime(2026, 9, 24, 3, 0))
    # only dom restricted
    assert CronExpression('0 3 13 * *').matches(datetime(2026, 9, 13, 3, 0))
    assert not CronExpression('0 3 13 * *').matches(datetime(2026, 9, 14, 3, 0))


def test_matched_since_window():
    now = datetime(2026, 9, 29, 3, 5)
    # slot inside the window
    assert matched_since('0 3 * * *', datetime(2026, 9, 29, 2, 0), now) == datetime(2026, 9, 29, 3, 0)
    # slot exactly at last_check is not re-reported
    assert matched_since('0 3 * * *', datetime(2026, 9, 29, 3, 0), now) is None
    # no slot in window
    assert matched_since('0 3 * * *', datetime(2026, 9, 29, 3, 1), now) is None
    # multi-day window picks the latest slot
    assert matched_since('0 3 * * *', datetime(2026, 9, 27, 4, 0), now) == datetime(2026, 9, 29, 3, 0)
    # every-minute expression finds the latest minute
    assert matched_since('* * * * *', datetime(2026, 9, 29, 3, 0), now) == datetime(2026, 9, 29, 3, 5)
    # last_check=None tests only 'now'
    assert matched_since('0 3 * * *', None, datetime(2026, 9, 29, 3, 0)) == datetime(2026, 9, 29, 3, 0)
    assert matched_since('0 3 * * *', None, datetime(2026, 9, 29, 3, 1)) is None


def test_matched_since_month_boundary():
    assert matched_since('0 0 1 * *', datetime(2026, 8, 31, 12, 0), datetime(2026, 9, 2, 0, 1)) \
        == datetime(2026, 9, 1, 0, 0)


def test_matches_month_name():
    assert CronExpression('0 3 * sep *').matches(datetime(2026, 9, 29, 3, 0))
    assert not CronExpression('0 3 * sep *').matches(datetime(2026, 8, 29, 3, 0))
