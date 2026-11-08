"""
Unit tests for CutOut._classify_contours()

Tests the automatic detection of interior vs exterior contours
for the Cutout Tool's auto-interior-detection feature.

A contour's role is decided by how many other filled contours contain it: even nesting
depth (0, 2, 4...) is material and gets the offset outside, odd depth (1, 3, 5...) is a
hole and gets the offset inside. The old "largest filled area is the exterior, anything
inside it is a hole" rule is gone, and so is the convex-hull guess for a contour that
has no exterior ring to rebuild a filled shape from (see the warning tests at the end).

Run with: uv run --with pytest pytest tests/test_classify_contours.py -v
Requires shapely and PyQt6 (the plugin module imports Qt); no QApplication is started.
"""

import pytest
from shapely import Polygon, LineString, LinearRing, Point

# Call the production code, not a copy of it. This module used to carry its own
# reimplementation, so the tests could not notice a change to the real one. `CutOut` is a
# QWidget subclass, but importing the class and reaching its staticmethod needs no
# QApplication.
import flatcam_plus.appPlugins.ToolCutOut as tool_cutout

_classify_contours = tool_cutout.CutOut._classify_contours


def make_gerber_band(coords, width=0.254):
    """Simulate a Gerber profile path: LineString buffered with aperture width/2."""
    line = LineString(coords)
    return line.buffer(width / 2)


def make_rectangular_outline(xmin, ymin, xmax, ymax, width=0.254):
    """Create a rectangular outline as a thin band (like Gerber profile)."""
    ring_coords = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)]
    return make_gerber_band(ring_coords, width)


def make_circular_outline(cx, cy, radius, width=0.254, segments=64):
    """Create a circular outline as a thin band."""
    import math
    coords = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        coords.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return make_gerber_band(coords, width)


def make_arc_band(cx, cy, radius, start_deg, end_deg, width=0.254, segments=16):
    """Create an open arc as a thin band, the shape a mouse-bite frame is drawn with."""
    import math
    coords = []
    for i in range(segments + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / segments)
        coords.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return make_gerber_band(coords, width)


class WarningRecorder:
    """Stand-in for ``app.log`` that keeps the warnings it was handed."""

    def __init__(self):
        self.messages = []

    def warning(self, message, *args, **kwargs):
        self.messages.append(message % args if args else message)


# ============================================================================
# TEST CASES
# ============================================================================

class TestSinglePolygon:
    """REQ-03: Zero regression for single polygon."""

    def test_single_polygon_returns_empty_set(self):
        """One polygon → no interior detected."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        result = _classify_contours([outline])
        assert result == set()

    def test_empty_list_returns_empty_set(self):
        """Empty input → empty set."""
        result = _classify_contours([])
        assert result == set()


class TestExteriorWithOneSlot:
    """REQ-01/REQ-02: Detect internal contour and classify correctly."""

    def test_rectangular_outline_with_internal_circle(self):
        """Rectangular outline + circular slot inside → slot is interior."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        slot = make_circular_outline(32, 20, 8)
        result = _classify_contours([outline, slot])
        assert result == {1}  # index 1 is the slot

    def test_slot_first_in_list(self):
        """Even if slot comes first in the list, the nesting depth still finds it."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        slot = make_circular_outline(32, 20, 8)
        result = _classify_contours([slot, outline])
        assert result == {0}  # index 0 is the slot (smaller)

    def test_rectangular_outline_with_rectangular_slot(self):
        """Rectangular outline + rectangular internal slot."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        slot = make_rectangular_outline(20, 10, 44, 30)
        result = _classify_contours([outline, slot])
        assert result == {1}


class TestExteriorWithMultipleSlots:
    """REQ-07: Support multiple internal cutouts."""

    def test_three_internal_slots(self):
        """Exterior + 3 slots → all 3 classified as interior."""
        outline = make_rectangular_outline(0, 0, 100, 60)
        slot1 = make_circular_outline(25, 30, 8)
        slot2 = make_circular_outline(50, 30, 8)
        slot3 = make_circular_outline(75, 30, 8)
        result = _classify_contours([outline, slot1, slot2, slot3])
        assert result == {1, 2, 3}


class TestPanelNoContainment:
    """REQ-04: Panel with multiple PCBs side by side → all exterior."""

    def test_two_boards_side_by_side(self):
        """Two PCBs next to each other (no containment) → both exterior."""
        board1 = make_rectangular_outline(0, 0, 30, 40)
        board2 = make_rectangular_outline(35, 0, 65, 40)
        result = _classify_contours([board1, board2])
        assert result == set()  # neither is inside the other

    def test_three_boards_in_panel(self):
        """Three PCBs in a row → all exterior."""
        board1 = make_rectangular_outline(0, 0, 20, 30)
        board2 = make_rectangular_outline(25, 0, 45, 30)
        board3 = make_rectangular_outline(50, 0, 70, 30)
        result = _classify_contours([board1, board2, board3])
        assert result == set()


class TestSlotTouchingBorder:
    """Edge case: slot that is clearly outside the outline."""

    def test_slot_completely_outside(self):
        """Slot completely outside the exterior → not classified as interior."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        # Slot entirely outside the outline bounds
        slot = make_rectangular_outline(70, 15, 80, 25)
        result = _classify_contours([outline, slot])
        assert 1 not in result

    def test_slot_crossing_the_outline_is_material(self):
        """A slot that starts inside and runs out past the board edge is not nested.

        Its filled shape is not contained by the outline, so its depth is 0 and it is
        cut from the outside like any other material contour. The old rule looked at the
        representative point alone, which sits inside the board and called it a hole.
        """
        outline = make_rectangular_outline(0, 0, 64, 40)
        slot = make_rectangular_outline(60, 15, 70, 25)
        result = _classify_contours([outline, slot])
        assert result == set()


class TestNestingDepth:
    """S1: the role comes from the nesting depth, not from which polygon is biggest."""

    def test_pad_inside_a_slot_is_material(self):
        """Board outline → slot → pad: the pad is depth 2, so it is material again."""
        outline = make_rectangular_outline(0, 0, 100, 60)
        slot = make_circular_outline(50, 30, 20)
        pad = make_circular_outline(50, 30, 5)
        result = _classify_contours([outline, slot, pad])
        assert result == {1}

    def test_hole_drilled_in_a_pad_inside_a_slot_is_a_hole(self):
        """Depth 3 is a hole again: outline → slot → pad → hole in the pad."""
        outline = make_rectangular_outline(0, 0, 100, 60)
        slot = make_circular_outline(50, 30, 20)
        pad = make_circular_outline(50, 30, 10)
        hole = make_circular_outline(50, 30, 3)
        result = _classify_contours([outline, slot, pad, hole])
        assert result == {1, 3}

    def test_panel_boards_of_different_sizes_keep_their_own_slot(self):
        """Two boards of different sizes, each with a slot.

        Classification must not depend on which board is the biggest: the small board's
        slot is a hole of the small board, even though it sits outside the largest contour.
        """
        big_board = make_rectangular_outline(0, 0, 100, 60)
        big_slot = make_circular_outline(50, 30, 10)
        small_board = make_rectangular_outline(120, 0, 150, 40)
        small_slot = make_circular_outline(135, 20, 5)
        result = _classify_contours([big_board, big_slot, small_board, small_slot])
        assert result == {1, 3}

    def test_mouse_bite_frame_around_the_board_is_material(self):
        """A mouse-bite frame is a set of arcs around the board: all of it is material.

        The arcs sit outside the board, so no contour contains another and nothing is a hole.
        """
        board = make_circular_outline(0, 0, 10)
        arcs = [
            make_arc_band(0, 0, 11, start, start + 80)
            for start in (10, 100, 190, 280)
        ]
        result = _classify_contours([board] + arcs)
        assert result == set()


class TestDegenerateGeometries:
    """Edge cases with unusual geometries."""

    def test_point_like_geometry(self):
        """Very small geometry that could cause issues."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        tiny = Point(32, 20).buffer(0.01)  # tiny circle inside
        result = _classify_contours([outline, tiny])
        assert result == {1}


class TestRealWorldGerberSimulation:
    """Simulate the actual user's case: gear-shaped outline + triangular slot."""

    def test_gear_outline_with_triangular_slot(self):
        """
        Simulates a gear-like PCB outline (large irregular polygon)
        with a rounded triangular internal slot.
        The Gerber produces both as thin bands (buffered LineStrings).
        """
        import math

        # Gear-like exterior (simplified: circle with bumps)
        gear_coords = []
        for i in range(60):
            angle = 2 * math.pi * i / 60
            r = 32 + 4 * math.sin(6 * angle)  # 6-bump gear
            gear_coords.append((r * math.cos(angle), r * math.sin(angle)))
        gear_coords.append(gear_coords[0])  # close
        gear_outline = make_gerber_band(gear_coords, width=0.254)

        # Rounded triangle inside (simplified: 3-point smoothed)
        tri_coords = []
        for i in range(36):
            angle = 2 * math.pi * i / 36
            r = 10 + 3 * math.cos(3 * angle)  # 3-lobe shape
            tri_coords.append((r * math.cos(angle), r * math.sin(angle)))
        tri_coords.append(tri_coords[0])
        tri_slot = make_gerber_band(tri_coords, width=0.254)

        result = _classify_contours([gear_outline, tri_slot])
        assert result == {1}  # triangular slot is interior


class TestWarnings:
    """S3: a contour that cannot be classified is reported, then treated as exterior."""

    def test_open_linestring_is_reported_and_treated_as_exterior(self):
        """A LineString has no exterior ring, so no filled shape can be rebuilt from it.

        It used to be guessed at with a convex hull; now it is reported and left on the
        exterior path, which is the safe direction.
        """
        outline = make_rectangular_outline(0, 0, 64, 40)
        open_line = LineString([(10, 10), (50, 10)])
        warnings = WarningRecorder()
        result = _classify_contours([outline, open_line], logger=warnings)

        assert result == set()
        assert len(warnings.messages) == 1
        assert "1" in warnings.messages[0]
        assert "treating it as exterior" in warnings.messages[0]

    def test_empty_polygon_is_reported_and_treated_as_exterior(self):
        """An empty contour encloses no area, so it cannot take part in a depth count."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        warnings = WarningRecorder()
        result = _classify_contours([outline, Polygon()], logger=warnings)

        assert result == set()
        assert len(warnings.messages) == 1
        assert "1" in warnings.messages[0]
        assert "treating it as exterior" in warnings.messages[0]

    def test_a_classifiable_run_reports_nothing(self):
        """The happy path stays silent, so a warning in the log always means something."""
        outline = make_rectangular_outline(0, 0, 64, 40)
        slot = make_circular_outline(32, 20, 8)
        warnings = WarningRecorder()
        result = _classify_contours([outline, slot], logger=warnings)

        assert result == {1}
        assert warnings.messages == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
