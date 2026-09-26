"""Unit tests for pure functions in resources/lib/kodiutils.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'resources' / 'lib'))

import kodiutils


def test_version_simple():
    assert kodiutils.version('6.2.0') == [6, 2, 0]


def test_version_with_dash_suffix():
    # callers pre-strip '+build' suffixes (addon.py), version() handles '-'
    assert kodiutils.version('6.2.0-matrix') == [6, 2, 0]


def test_version_single_component():
    assert kodiutils.version('20') == [20]
