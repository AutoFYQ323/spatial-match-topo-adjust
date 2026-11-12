# -*- coding: utf-8 -*-
"""Language-stable error codes for batch classification.

Do not classify failures by translating or substring-matching visible error text.
"""

NO_TARGET_LAYER = 'no_target_layer'
NO_REF_LAYER = 'no_ref_layer'
NO_TARGET_FEATURES = 'no_target_features'
NO_REF_FEATURES = 'no_ref_features'
CANCELLED = 'cancelled'
INVALID_MODE = 'invalid_mode'
GEOM_MISMATCH = 'geom_mismatch'

EMPTY_FEATURES = frozenset({
    NO_TARGET_FEATURES,
    NO_REF_FEATURES,
})
