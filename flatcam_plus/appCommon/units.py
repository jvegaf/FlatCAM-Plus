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


def geometry_fingerprint(obj):
    """A value that changes when an object's geometry is really converted.

    Used to catch an object that silently refuses: ``Gerber.convert_units`` returns early for
    files that declared their own units, so trusting the call would leave that object in the old
    unit while the application reports the new one.
    """
    geometries = getattr(obj, "solid_geometry", None)
    if geometries:
        try:
            return tuple(round(value, 6) for value in geometries[0].bounds)
        except (AttributeError, TypeError):
            return None
    return None


def convert_objects(objects, from_units, to_units):
    """Convert every object between units, all or nothing.

    Conversion is applied one object at a time, and every converted object is checked for an
    actual change: an object that refuses (or has no geometry) makes the whole operation roll
    back, because a project half in millimetres and half in inches is worse than an unconverted
    one, and the application would be reporting the wrong unit for the objects that refused.

    Returns ``(True, [])`` on success, or ``(False, [names])`` with the offenders after rolling
    back everything that had already been converted.
    """
    if conversion_factor(from_units, to_units) == 1.0:
        return True, []

    converted = []
    refused = []

    for obj in objects:
        before = geometry_fingerprint(obj)
        original_units = getattr(obj, "units", None) or from_units

        # ``convert_units`` owns setting ``obj.units``. Assigning it here would mark an object
        # that refused as converted, which is the exact failure this function exists to catch.
        obj.convert_units(to_units)

        after = geometry_fingerprint(obj)
        if before is not None and after == before:
            refused.append(getattr(obj, "obj_options", {}).get("name") or repr(obj))
            continue

        converted.append((obj, original_units))

    if not refused:
        return True, []

    for obj, original_units in converted:
        obj.convert_units(original_units)

    return False, refused
