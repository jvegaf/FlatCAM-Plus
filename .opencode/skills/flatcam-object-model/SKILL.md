---
name: flatcam-object-model
description: "Trigger: document object, FlatCAMObj, serialization, project save/load, object collection, plot. Add or change FlatCAM Plus document objects safely."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Object Model

## Activation Contract

Load when adding a document type, changing persisted object state, touching `appObjects/`, or debugging project save/load, object creation, selection, or plotting.

## Hard Rules

- Base class is `FlatCAMObj` in `appObjects/AppObjectTemplate.py`. Subclasses set `kind`, `ui_type`, and the exact `ser_attrs` list that defines persisted state.
- `AppObject.new_object(kind, name, initialize, plot=..., callback=...)` is the only supported creation path. It copies app defaults whose keys start with `<kind>_`, stripping the prefix into `obj_options`.
- `obj_options` is a `LoudDict` with a change callback. Mutate it through the documented API; do not replace it.
- `from_dict()` updates `obj_options` in place for the `'options'` key and sets the other `ser_attrs` attributes. Missing keys from old projects are tolerated; never assume every attribute exists.
- Shapely geometry and `ApertureMacro` are serialized through `camlib.to_dict()`; any new non-JSON state must be added to `ser_attrs` and made serializable.
- `set_ui(ui)` asserts the declared `ui_type`. Keep the UI class and the object's `ui_type` in sync.
- Object signals (`object_created`, `object_changed`, `object_plotted`) drive collection updates and plotting; emit them through the existing `AppObject` flow.
- Collection operations live in `appObjects/ObjectCollection.py` (`append`, `get_active`, `get_selected`, `get_by_name`, `get_list`). Do not maintain a parallel object list.

## Decision Gates

| Change | Action |
| --- | --- |
| New persisted field | Add it to `ser_attrs`; update `from_dict` compatibility |
| New document type | Subclass `FlatCAMObj`, add `kind`/`ui_type`, register in `AppObject.classdict` |
| New default option | Add `<kind>_<name>` in `flatcam_plus/defaults.py`; read it from `obj_options` |
| Plot-only concern | Use the existing `plot()` and shape collection |

## Execution Steps

1. Read the closest object (`GeometryObject`, `GerberObject`, `DocumentObject`).
2. Define `kind`, `ui_type`, `ser_attrs`, and the UI class.
3. Register the kind in `AppObject.new_object`'s `classdict` when adding a type.
4. Add defaults with the correct `<kind>_` prefix.
5. Verify creation, project save/load, selection, and plotting.

## Output Contract

Report: object class and `kind`, `ser_attrs` changes, defaults added, creation path used, and save/load verification evidence.

## References

- `appObjects/AppObjectTemplate.py` — `FlatCAMObj` lifecycle and serialization.
- `appObjects/AppObject.py` — `new_object` and collection signals.
- `appObjects/ObjectCollection.py` — collection queries.
- `flatcam_plus/camlib.py` — `to_dict` / `dict2obj` serializers.
