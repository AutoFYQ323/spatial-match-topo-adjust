# -*- coding: utf-8 -*-
"""Own scheme-bundle format for Spatial Match & Topo Adjust import/export.

The three function libraries stay separate. This module only describes the
combined packet used when exporting or importing all three at once.
It does not use KMZ file formats, asset names, or QSettings keys.
"""

BUNDLE_KIND = "spatial_match_topo_adjust_scheme_bundle"
BUNDLE_FORMAT = "spatial_match_topo_adjust_scheme_bundle_v1"
BUNDLE_KIND_OLD = "layer_snap_check_scheme_bundle"
BUNDLE_FORMAT_OLD = "layer_snap_check_scheme_bundle_v1"
BUNDLE_SCHEMA_VERSION = 1
PLUGIN_VERSION = "1.0.0"

# Libraries stored under payload["libraries"]
LIB_SNAP = "snap"
LIB_FIELD = "field"
LIB_MOVE = "move"


def is_scheme_bundle(payload):
    if not isinstance(payload, dict):
        return False
    kind = payload.get("kind")
    fmt = payload.get("format")
    if kind in (BUNDLE_KIND, BUNDLE_KIND_OLD) or fmt in (BUNDLE_FORMAT, BUNDLE_FORMAT_OLD):
        return True
    return False


def empty_libraries():
    return {
        LIB_SNAP: {"schemes": {}, "group_orders": {}},
        LIB_FIELD: {"schemes": {}},
        LIB_MOVE: {"schemes": {}},
    }


def make_bundle(snap_schemes, snap_group_orders, field_schemes, move_schemes, plugin_version=None):
    """Build a forward-identifiable bundle. Values are already library dicts."""
    import time
    if not plugin_version:
        plugin_version = PLUGIN_VERSION
    return {
        "kind": BUNDLE_KIND,
        "format": BUNDLE_FORMAT,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "generator": "Spatial Match & Topo Adjust",
        "plugin_version": plugin_version,
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "libraries": {
            LIB_SNAP: {
                "schemes": dict(snap_schemes or {}),
                "group_orders": dict(snap_group_orders or {}),
            },
            LIB_FIELD: {"schemes": dict(field_schemes or {})},
            LIB_MOVE: {"schemes": dict(move_schemes or {})},
        },
    }


def bundle_libraries(payload):
    """Return the libraries dict, or None if not a bundle."""
    if not is_scheme_bundle(payload):
        return None
    libs = payload.get("libraries")
    if not isinstance(libs, dict):
        return None
    return libs
