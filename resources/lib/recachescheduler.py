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
"""Scheduling and running of the background re-cache job.

The job is the same recache_items() crawl the cronxbmc job triggers via
'?re-cache=2', but run from the addon's service: it fires when the
'recache.cronexpression' setting last matched (persisted across restarts
in a small state file), and only while Kodi is idle if the idle gate is
enabled. Deliberately free of Kodi imports: the progress dialog, idle
check and Api construction are injected, which keeps the logic unit-
testable without the Kodi stub modules.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from resources.lib.cronmatch import matched_since

STATE_FILE = 'recache.state'


class RecacheState:
    """Persists the last cron slot the service acted on."""

    def __init__(self, cache_path: Path) -> None:
        self.path = cache_path / STATE_FILE
        self.last_slot: Optional[datetime] = None

    def load(self) -> Optional[datetime]:
        if self.path.exists():
            try:
                self.last_slot = datetime.fromisoformat(self.path.read_text().strip())
            except ValueError:
                self.last_slot = None
        return self.last_slot

    def save(self, slot: datetime) -> None:
        self.path.write_text(slot.isoformat())
        self.last_slot = slot


def recache_due(state: RecacheState, expression: str, now: datetime) -> Optional[datetime]:
    """The cron slot to act on in this pass, or None.

    A missing state file means the service (or a new expression) has never
    run: seed it with 'now' so a fresh install does not fire immediately.
    A slot missed while Kodi was down is caught up on the first pass.
    """
    if not state.path.exists():
        state.save(now)
        return None
    last = state.load()
    if last is None:
        state.save(now)
        return None
    return matched_since(expression, last, now)


class IdleAbortProgress:
    """Adapts an xbmcgui.DialogProgressBG to the iscanceled() protocol.

    The background dialog has no cancel button; 'canceled' instead means
    the user became active again, so recache_items() aborts between pages
    and the slot is left unsaved for the next idle pass.

    The dialog is optional: when it is None (the service could not create
    one) progress updates are dropped and only the abort signal remains.
    """

    def __init__(self, dialog: Any, idle_check: Optional[Callable[[], bool]] = None) -> None:
        self.dialog = dialog
        self.idle_check = idle_check or (lambda: True)
        self.was_aborted = False

    def update(self, percent: int, msg: str) -> None:
        if self.dialog is not None:
            self.dialog.update(int(percent), message=msg)

    def iscanceled(self) -> bool:
        if self.was_aborted:
            return True
        if self.idle_check():
            return False
        self.was_aborted = True
        return True


def recache_pass(get_setting: Callable[[str], str], api_factory: Callable[[], Any],
                 cache_path: Path, now: datetime, idle_check: Callable[[], bool],
                 dialog_factory: Callable[[], Any],
                 progress_factory: Optional[Callable[[Any, Callable[[], bool]], Any]] = None) -> bool:
    """One service pass: run the recache crawl if the cron slot is due.

    Returns True when the crawl ran to completion (slot is marked done),
    False when it was skipped, blocked by the idle gate, or aborted.
    """
    if get_setting('recache.enabled') != 'true' or get_setting('recache.service') != 'true':
        return False
    state = RecacheState(cache_path)
    slot = recache_due(state, get_setting('recache.cronexpression'), now)
    if slot is None:
        return False
    gate_enabled = get_setting('recache.service.idle') != 'false'
    if gate_enabled and not idle_check():
        return False

    if progress_factory is None:
        progress_factory = IdleAbortProgress
    # with the gate disabled the crawl runs to completion like the cronjob
    # variant; the abort signal only makes sense while the gate is active
    # the factory returns a created dialog (or None when Kodi has no GUI)
    dialog = dialog_factory()
    progress = progress_factory(dialog, idle_check if gate_enabled else None)

    try:
        api = api_factory()
        api.recache_items(progress=progress, clear_expired=True)
        if progress.was_aborted:
            return False
        state.save(slot)
        return True
    finally:
        if dialog is not None:
            dialog.close()
