"""Unit conversion helpers.

Kept apart from the GUI and from the object model on purpose: converting a project is the one
operation in FlatCAM Plus that can quietly destroy a user's geometry, so the arithmetic is a pure
function that can be round-tripped in a test before anything live is touched.

The application stores coordinates in its current ``app_units``; nothing here guesses which one,
it always asks for both sides explicitly.
"""

from shapely import transform as shapely_transform_coords

MM_PER_INCH = 25.4

MM = "MM"
IN = "IN"


def normalize_units(units):
    """Return ``"MM"`` or ``"IN"`` for the spellings the application uses."""
    value = str(units).strip().upper()
    if value in (MM, "MILLIMETER", "MILLIMETERS", "MM)"):
        return MM
    if value in (IN, "INCH", "INCHES", "IN)"):
        return IN
    raise ValueError("Unsupported units: %r" % (units,))


def conversion_factor(from_units, to_units):
    """How much to multiply a length expressed in ``from_units`` to get ``to_units``."""
    source = normalize_units(from_units)
    target = normalize_units(to_units)

    if source == target:
        return 1.0
    if source == MM and target == IN:
        return 1.0 / MM_PER_INCH
    return MM_PER_INCH


def convert_length(value, from_units, to_units):
    return value * conversion_factor(from_units, to_units)


def convert_geometry(geometry, from_units, to_units):
    """Scale a shapely geometry between units, preserving its type and coordinates.

    Returns the same object when the units already match, so callers can compare identity to
    decide whether anything needs replacing.
    """
    factor = conversion_factor(from_units, to_units)
    if factor == 1.0:
        return geometry

    return shapely_transform_coords(geometry, lambda coords: coords * factor)


def convert_geometry_list(geometries, from_units, to_units):
    factor = conversion_factor(from_units, to_units)
    if factor == 1.0:
        return list(geometries)
    return [convert_geometry(geometry, from_units, to_units) for geometry in geometries]
