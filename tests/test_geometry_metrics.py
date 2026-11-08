"""The distance measure behind every "find optimal tool diameter" check.

Isolation and non-copper clearance each measured the minimum distance between every pair
of geometry pieces with their own copy of the same loop. ``min_element_distance`` is that
loop once: it takes already-flattened geometry and reports the plain minimum, and leaves
both the message and the tool-specific convention (the trimming step, the unusable
distance) to the caller.
"""

import pytest
from shapely.geometry import box

from flatcam_plus.appCommon.Common import GracefulException
from flatcam_plus.appPlugins.ToolIsolation import ToolIsolation
from flatcam_plus.camlib import min_element_distance


def test_measures_the_gap_between_two_separated_pieces():
    # Two 1 mm squares, 2 mm apart along X. The helper measures and does not trim: one
    # decimal step below this gap is the caller's convention, not the measurement.
    assert min_element_distance([box(0, 0, 1, 1), box(3, 0, 4, 1)], 2) == pytest.approx(2.0)


def test_leaves_the_trimming_step_to_the_caller():
    # The same input through the isolation seam comes back one decimal step lower, because
    # that caller keeps its own trimming convention. This difference is the contract.
    assert min_element_distance([box(0, 0, 1, 1), box(3, 0, 4, 1)], 2) == pytest.approx(2.0)

    aperture_storage = {10: {"geometry": [{"solid": solid}
                                          for solid in (box(0, 0, 1, 1), box(3, 0, 4, 1))]}}
    msg, min_dist = ToolIsolation.find_optim_mp(aperture_storage, 2)
    assert msg == "ok"
    assert min_dist == pytest.approx(1.99)


def test_finds_the_nearest_pair_when_it_is_not_the_first():
    # The first pair measured is (0, 1) at 9 mm; the nearest pair is (0, 2) at 1 mm and is
    # only reached later in the loop, so the minimum must not be the first distance measured.
    geometries = [box(0, 0, 1, 1), box(10, 0, 11, 1), box(0, 2, 1, 3)]
    assert min_element_distance(geometries, 2) == pytest.approx(1.0)


@pytest.mark.parametrize("geometries", [[], [box(0, 0, 1, 1)]])
def test_returns_none_when_there_is_no_pair_to_measure(geometries):
    # A layer with no piece, or with a single one, has no distance to report. The caller
    # owns the message and the tool-specific unusable distance.
    assert min_element_distance(geometries, 2) is None


def test_reports_progress_against_the_total_pair_count():
    # Four pieces make six pairs. The caller drives a progress bar from these numbers and
    # must never have to recompute the total, which arrives with every callback.
    calls = []
    geometries = [box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1), box(9, 0, 10, 1)]

    min_element_distance(geometries, 2, on_pair=lambda processed, total: calls.append((processed, total)))

    assert [processed for processed, _ in calls] == [1, 2, 3, 4, 5, 6]
    assert {total for _, total in calls} == {6}
    assert calls[-1][0] == calls[-1][1]


def test_aborts_before_measuring_the_pair_that_asks_for_it():
    # A user abort arrives between pairs; nothing after it may be measured.
    processed = []
    geometries = [box(0, 0, 1, 1), box(3, 0, 4, 1), box(6, 0, 7, 1)]

    def abort_check():
        return len(processed) == 2

    with pytest.raises(GracefulException):
        min_element_distance(
            geometries,
            2,
            on_pair=lambda pair_nr, total: processed.append((pair_nr, total)),
            abort_check=abort_check,
        )

    # The two pairs measured before the abort are the only callbacks.
    assert processed == [(1, 3), (2, 3)]
