# -*- coding: utf-8 -*-
"""Read new settings keys first, then fall back to older keys.

Writes always go to SpatialMatchTopoAdjust/. Saved schemes and language
from previous versions remain readable and are copied once to the new
keys. Never uses the KMZ language settings key.
"""

NEW_PREFIX = "SpatialMatchTopoAdjust/"
MID_PREFIX = "layer_snap_check/"
OLD_PREFIX = "cdet/"

_MIGRATE_FLAG = "SpatialMatchTopoAdjust/_migrated_from_legacy"
_LANG_NEW = "SpatialMatchTopoAdjust/ui_language"
_LANG_OLD = "LayerSnapCheck/ui_language"

# Stored sentinel values that identify "layer title" / "element count"
# as the reference source. New writes use the new tokens; reads accept both.
LAYER_TITLE_NEW = "__lsc_layer_title__"
LAYER_TITLE_OLD = "__cdet_layer_title__"
ELEMENT_COUNT_NEW = "__lsc_element_count__"
ELEMENT_COUNT_OLD = "__cdet_element_count__"

FIELD_SCHEME_KIND = "spatial_match_topo_adjust_field_schemes"
FIELD_SCHEME_KIND_MID = "layer_snap_check_field_schemes"
FIELD_SCHEME_KIND_OLD = "cdet_field_schemes"
MOVE_SCHEME_KIND = "spatial_match_topo_adjust_move_schemes"
MOVE_SCHEME_KIND_MID = "layer_snap_check_move_schemes"
MOVE_SCHEME_KIND_OLD = "cdet_move_schemes"
SNAP_SCHEME_KIND = "spatial_match_topo_adjust_snap_schemes"
SNAP_SCHEME_KIND_MID = "layer_snap_check_snap_schemes"


def _migrate_language_key(settings):
    if settings is None:
        return
    try:
        new_val = str(settings.value(_LANG_NEW, "") or "").strip()
        if new_val:
            return
        old_val = str(settings.value(_LANG_OLD, "") or "").strip()
        if old_val:
            settings.setValue(_LANG_NEW, old_val)
    except Exception:
        pass


def migrate_legacy_settings(settings):
    """Copy layer_snap_check/ and cdet/ keys into SpatialMatchTopoAdjust/ once.

    Existing destination values are left unchanged. Language is copied from
    LayerSnapCheck/ui_language when the new key is still empty.
    """
    if settings is None:
        return
    try:
        already = settings.value(_MIGRATE_FLAG, False)
        flag_on = already in (True, "true", "True", "1", 1)
    except Exception:
        flag_on = False
    if not flag_on:
        try:
            keys = list(settings.allKeys())
        except Exception:
            keys = []
        for key in keys:
            for prefix in (MID_PREFIX, OLD_PREFIX):
                if key.startswith(prefix):
                    suffix = key[len(prefix):]
                    new_key = NEW_PREFIX + suffix
                    try:
                        if not settings.contains(new_key):
                            settings.setValue(new_key, settings.value(key))
                    except Exception:
                        pass
                    break
    _migrate_language_key(settings)
    try:
        settings.setValue(_MIGRATE_FLAG, True)
    except Exception:
        pass


def settings_value(settings, suffix, default=None, typ=None, **kwargs):
    if typ is None:
        typ = kwargs.pop("type", None)
    kwargs = {} if typ is None else {"type": typ}
    for prefix in (NEW_PREFIX, MID_PREFIX, OLD_PREFIX):
        key = prefix + suffix
        try:
            if settings.contains(key):
                return settings.value(key, default, **kwargs)
        except Exception:
            pass
    try:
        return settings.value(OLD_PREFIX + suffix, default, **kwargs)
    except Exception:
        return default


def settings_set(settings, suffix, value):
    settings.setValue(NEW_PREFIX + suffix, value)


def is_layer_title_token(value):
    return value in (LAYER_TITLE_NEW, LAYER_TITLE_OLD)


def is_element_count_token(value):
    return value in (ELEMENT_COUNT_NEW, ELEMENT_COUNT_OLD)


def is_field_scheme_kind(value):
    return value in (FIELD_SCHEME_KIND, FIELD_SCHEME_KIND_MID, FIELD_SCHEME_KIND_OLD)


def is_move_scheme_kind(value):
    return value in (MOVE_SCHEME_KIND, MOVE_SCHEME_KIND_MID, MOVE_SCHEME_KIND_OLD)


def is_snap_scheme_kind(value):
    return value in (SNAP_SCHEME_KIND, SNAP_SCHEME_KIND_MID)
