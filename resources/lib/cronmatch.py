#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Minimal 5-field cron expression matcher (minute hour dom month dow).

Supports '*', lists, ranges, steps, month/day-of-week names and the @alias
forms — the subset cronxbmc accepts — so the background service can reuse
the addon's existing 'recache.cronexpression' setting. Matching is done in
local time with naive datetimes, like cron itself.
"""
from datetime import date, datetime, time, timedelta
from typing import NamedTuple, Optional, Set

MONTH_NAMES = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}
DOW_NAMES = {'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6}
ALIASES = {
    '@hourly': '0 * * * *',
    '@daily': '0 0 * * *',
    '@midnight': '0 0 * * *',
    '@weekly': '0 0 * * 0',
    '@monthly': '0 0 1 * *',
    '@yearly': '0 0 1 1 *',
    '@annually': '0 0 1 1 *',
}


class CronParseError(ValueError):
    """Raised when a cron expression cannot be parsed."""


class Field(NamedTuple):
    values: Optional[Set[int]]  # None when the field is a bare '*'


def _value(text: str, names: dict, low: int, high: int) -> int:
    if names and text in names:
        return names[text]
    try:
        value = int(text)
    except ValueError as e:
        raise CronParseError(f'invalid cron value: {text!r}') from e
    if not low <= value <= high:
        raise CronParseError(f'cron value {value} out of range {low}-{high}')
    return value


def _parse_field(text: str, low: int, high: int, names: dict = None) -> Field:
    text = text.strip().lower()
    if text == '*':
        return Field(None)
    values: Set[int] = set()
    for part in text.split(','):
        has_step = '/' in part
        step = 1
        if has_step:
            part, step_text = part.split('/', 1)
            try:
                step = int(step_text)
            except ValueError as e:
                raise CronParseError(f'invalid cron step: {step_text!r}') from e
            if step <= 0:
                raise CronParseError(f'cron step must be positive: {step}')
        if part == '*':
            lo, hi = low, high
        elif '-' in part:
            lo_text, hi_text = part.split('-', 1)
            lo, hi = _value(lo_text, names, low, high), _value(hi_text, names, low, high)
            if lo > hi:
                raise CronParseError(f'cron range start after end: {part!r}')
        else:
            lo = _value(part, names, low, high)
            # "5/15" means "from 5 to the field maximum, every 15" (vixie cron)
            hi = high if has_step else lo
        values.update(v for v in range(lo, hi + 1, step) if low <= v <= high)
    return Field(values)


class CronExpression:
    def __init__(self, expression: str) -> None:
        expr = ALIASES.get(expression.strip().lower(), expression.strip())
        parts = expr.split()
        if len(parts) != 5:
            raise CronParseError(f'expected 5 cron fields, got {len(parts)}: {expression!r}')
        self.minute = _parse_field(parts[0], 0, 59)
        self.hour = _parse_field(parts[1], 0, 23)
        self.dom = _parse_field(parts[2], 1, 31)
        self.month = _parse_field(parts[3], 1, 12, MONTH_NAMES)
        self.dow = _parse_field(parts[4], 0, 7, DOW_NAMES)
        if self.dow.values is not None:
            # cron sunday is 0 (and 7); python weekday() is monday-based
            self.dow = Field({0 if v == 7 else v for v in self.dow.values})

    def _day_matches(self, day: date) -> bool:
        if self.month.values is not None and day.month not in self.month.values:
            return False
        dom_ok = self.dom.values is None or day.day in self.dom.values
        dow_ok = self.dow.values is None or (day.weekday() + 1) % 7 in self.dow.values
        if self.dom.values is None and self.dow.values is None:
            return True
        if self.dom.values is None:
            return dow_ok
        if self.dow.values is None:
            return dom_ok
        return dom_ok or dow_ok

    def matches(self, dt: datetime) -> bool:
        if not self._day_matches(dt.date()):
            return False
        if self.hour.values is not None and dt.hour not in self.hour.values:
            return False
        return not (self.minute.values is not None and dt.minute not in self.minute.values)


def matched_since(expression: str, last_check: Optional[datetime],
                  now: datetime) -> Optional[datetime]:
    """Latest cron slot in the window (last_check, now], or None.

    With last_check=None only 'now' itself is tested. Slots sit on whole
    minutes; a slot at exactly last_check is not re-reported.
    """
    cron = CronExpression(expression)
    if last_check is None:
        return now if cron.matches(now) else None

    best = None
    day = last_check.date()
    while day <= now.date():
        if cron._day_matches(day):
            hours = range(24) if cron.hour.values is None else sorted(cron.hour.values)
            minutes = range(60) if cron.minute.values is None else sorted(cron.minute.values)
            for hour in hours:
                for minute in minutes:
                    slot = datetime.combine(day, time(hour, minute))
                    if last_check < slot <= now:
                        best = slot
        day += timedelta(days=1)
    return best
