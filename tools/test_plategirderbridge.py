import pytest

from math import isclose
from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_INCLUDE_MEDIAN, KEY_SKEW_ANGLE, KEY_FOOTPATH,
    SPAN_MIN, SPAN_MAX,
    CARRIAGEWAY_WIDTH_MIN, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, CARRIAGEWAY_WIDTH_MAX_LIMIT,
    SKEW_ANGLE_MIN, SKEW_ANGLE_MAX,
    KEY_STRUCTURE_TYPE, KEY_PROJECT_LOCATION, KEY_DESIGN_MODE, KEY_GIRDER,
    KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC
)
from osdagbridge.core.utils.codes.keyfile import (
    KEY_SAFETY_KERB_MIN_WIDTH,
    KEY_RAILING_MIN_HEIGHT,
    MIN_STUD_HEIGHT_MM,
    MAX_STUD_DIAMETER_FACTOR,
    MIN_EDGE_DISTANCE_MM,
)
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015

DELTA = 0.1

@pytest.fixture
def validator():
    return BridgeInputValidator()

@pytest.fixture
def valid_basic_inputs():
    return {
        KEY_SPAN: str(SPAN_MIN + 5),
        KEY_CARRIAGEWAY_WIDTH: str(CARRIAGEWAY_WIDTH_MIN + 1),
        KEY_INCLUDE_MEDIAN: "No",
        KEY_SKEW_ANGLE: str((SKEW_ANGLE_MIN + SKEW_ANGLE_MAX) / 2),
        KEY_FOOTPATH: "None",
        KEY_STRUCTURE_TYPE: "Highway Bridge",
        KEY_PROJECT_LOCATION: "Mumbai",
        KEY_DESIGN_MODE: "Optimized",
        KEY_GIRDER: "E 250A",
        KEY_CROSS_BRACING: "X",
        KEY_END_DIAPHRAGM: "Cross Bracing",
        KEY_DECK_CONCRETE_GRADE_BASIC: "M30"
    }

@pytest.fixture
def valid_additional_inputs():
    return {
        "overall_bridge_width": 10.0,
        "girder_spacing": 2.5,
        "deck_overhang": 1.25,
        "no_of_girders": 4,
        "kerb_width": 800,
        "footpath_width": 1.6,
        "railing_height": 1150,
        "stud_height": 120,
        "stud_diameter": 22,
        "top_flange_thickness": 20,
        "stud_edge_distance": 30,
        KEY_FOOTPATH: "None"
    }


# ==========================================
# test_validate_span
# FORMAT: span=<metres, float>
#         expect=VALID → validator must accept it
#         expect=INVALID → validator must reject it
# ==========================================

@pytest.mark.parametrize("value, expected_valid", [
    # ── Large negatives (INVALID) ──────────────────────────────────────────
    (-200.0, False),
    (-100.0, False),
    (-50.0,  False),
    (-20.0,  False),
    (-10.0,  False),
    (-5.0,   False),
    (-2.0,   False),
    (-1.0,   False),
    # ── Zero (INVALID) ────────────────────────────────────────────────────
    (0.0,    False),
    # ── Positive but far below SPAN_MIN (INVALID) ─────────────────────────
    # (arbitrary midrange stress values to test a wide spread below the limit)
    (1.0,    False),
    (5.0,    False),
    (8.0,    False),
    (10.0,   False),
    (12.0,   False),
    (15.0,   False),
    (17.0,   False),
    # ── Just below SPAN_MIN (INVALID) ─────────────────────────────────────
    (SPAN_MIN - 10.0,  False),
    (SPAN_MIN - 5.0,   False),
    (SPAN_MIN - 2.0,   False),
    (SPAN_MIN - 1.0,   False),
    (SPAN_MIN - 0.5,   False),
    (SPAN_MIN - 0.1,   False),
    (SPAN_MIN - 0.01,  False),
    # ── Exact SPAN_MIN (VALID) ────────────────────────────────────────────
    (SPAN_MIN,         True),
    # ── Just above SPAN_MIN (VALID) ───────────────────────────────────────
    (SPAN_MIN + 0.01,  True),
    (SPAN_MIN + 0.1,   True),
    (SPAN_MIN + 0.5,   True),
    (SPAN_MIN + 1.0,   True),
    # ── Midrange values spread across the valid range (VALID) ─────────────
    (21.0,  True),
    (22.0,  True),
    (23.0,  True),
    (24.0,  True),
    (25.0,  True),
    (26.0,  True),
    (27.0,  True),
    (28.0,  True),
    (29.0,  True),
    (30.0,  True),
    (31.0,  True),
    (32.0,  True),
    (32.5,  True),
    (33.0,  True),
    (34.0,  True),
    (35.0,  True),
    (36.0,  True),
    (37.0,  True),
    (38.0,  True),
    (39.0,  True),
    (40.0,  True),
    (41.0,  True),
    (42.0,  True),
    (43.0,  True),
    (44.0,  True),
    # ── Just below SPAN_MAX (VALID) ───────────────────────────────────────
    (SPAN_MAX - 1.0,   True),
    (SPAN_MAX - 0.5,   True),
    (SPAN_MAX - 0.1,   True),
    (SPAN_MAX - 0.01,  True),
    # ── Exact SPAN_MAX (VALID) ────────────────────────────────────────────
    (SPAN_MAX,         True),
    # ── Just above SPAN_MAX (INVALID) ─────────────────────────────────────
    (SPAN_MAX + 0.01,  False),
    (SPAN_MAX + 0.1,   False),
    (SPAN_MAX + 0.5,   False),
    (SPAN_MAX + 1.0,   False),
    (SPAN_MAX + 5.0,   False),
    (SPAN_MAX + 10.0,  False),
    (SPAN_MAX + 100.0, False),
    # ── Type / edge-case errors (INVALID) ─────────────────────────────────
    (None,      False),
    ("",        False),
    ("abc",     False),
    ("20",      True),   # string of a valid number → valid (accepted by validator)
    ("20.0",    True),
    ([],        False),
    ({},        False),
])
def test_validate_span(validator, value, expected_valid):
    inputs = {KEY_SPAN: value}
    result = validator.validate_basic_inputs(KEY_SPAN, inputs)
    if expected_valid:
        assert result is None, f"Expected span {value} to be valid"
    else:
        assert result is not None, f"Expected span {value} to be invalid"


# ==========================================
# test_validate_carriageway_width
# FORMAT: median=<Yes/No>  lanes=<int>  width=<metres>
#         expect=VALID / INVALID
# ==========================================

@pytest.mark.parametrize("median, num_lanes, value, expected_valid", [
    # ════════════════════════════════════════════════════════════════════════
    # No Median  (min = CARRIAGEWAY_WIDTH_MIN,  max = CARRIAGEWAY_WIDTH_MAX_LIMIT)
    # ════════════════════════════════════════════════════════════════════════

    # Far below min (INVALID)
    ("No", 1, 0.5,  False),
    ("No", 1, 1.0,  False),
    ("No", 1, 2.0,  False),
    ("No", 1, 2.5,  False),
    ("No", 1, 3.0,  False),
    ("No", 1, 3.5,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.25, False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.01, False),

    # Just below CARRIAGEWAY_WIDTH_MIN (INVALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 1.0,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.5,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.1,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.01, False),

    # Exact CARRIAGEWAY_WIDTH_MIN (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MIN,         True),

    # Just above CARRIAGEWAY_WIDTH_MIN (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.01,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.1,   True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.25,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.0000001, True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.05,      True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.25,      True),

    # Midrange (arbitrary midrange stress values to test a wide spread) (VALID)
    ("No", 1, 5.0,  True),
    ("No", 1, 5.5,  True),
    ("No", 1, 6.0,  True),
    ("No", 1, 6.5,  True),
    ("No", 1, 7.0,  True),
    ("No", 1, 8.0,  True),
    ("No", 1, 9.0,  True),
    ("No", 1, 10.0, True),
    ("No", 1, 11.0, True),
    ("No", 1, 12.0, True),
    ("No", 1, 13.0, True),
    ("No", 1, 15.0, True),
    ("No", 1, 17.0, True),
    ("No", 1, 19.0, True),
    ("No", 1, 20.0, True),
    ("No", 1, 21.0, True),
    ("No", 1, 22.0, True),
    ("No", 1, 23.0, True),

    # Just below CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 1.0,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.5,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.1,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.01, True),

    # Exact CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT,         True),

    # Just above CARRIAGEWAY_WIDTH_MAX_LIMIT (INVALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.01,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,   False),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.5,   False),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 1.0,   False),
    ("No", 1, 25.0,  False),
    ("No", 1, 30.0,  False),

    # Type / edge-case errors (INVALID)
    ("No", 1, None,    False),
    ("No", 1, "",      False),
    ("No", 1, "abc",   False),
    ("No", 1, str(CARRIAGEWAY_WIDTH_MIN),  True),

    # ════════════════════════════════════════════════════════════════════════
    # Yes Median  (min = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, max = CARRIAGEWAY_WIDTH_MAX_LIMIT)
    # ════════════════════════════════════════════════════════════════════════

    # Far below min (INVALID)
    ("Yes", 2, 0.5,  False),
    ("Yes", 2, 1.0,  False),
    ("Yes", 2, 2.0,  False),
    ("Yes", 2, 3.0,  False),
    ("Yes", 2, 4.0,  False),
    ("Yes", 2, 5.0,  False),
    ("Yes", 2, 6.0,  False),
    ("Yes", 2, 7.0,  False),

    # Just below CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN (INVALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 1.0,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.5,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.1,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.01, False),

    # Exact CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,         True),

    # Just above CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN + 0.01,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN + 0.1,   True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN + 0.5,   True),

    # Midrange (arbitrary midrange stress values to test a wide spread) (VALID)
    ("Yes", 2, 8.0,  True),
    ("Yes", 2, 9.0,  True),
    ("Yes", 2, 10.0, True),
    ("Yes", 2, 11.0, True),
    ("Yes", 2, 12.0, True),
    ("Yes", 2, 14.0, True),
    ("Yes", 2, 15.0, True),
    ("Yes", 2, 17.0, True),
    ("Yes", 2, 19.0, True),
    ("Yes", 2, 20.0, True),
    ("Yes", 2, 21.0, True),
    ("Yes", 2, 22.0, True),
    ("Yes", 2, 23.0, True),

    # Just below CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 1.0,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.5,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.1,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.01, True),

    # Exact CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT,         True),

    # Just above CARRIAGEWAY_WIDTH_MAX_LIMIT (INVALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.01,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,   False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 1.0,   False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 2.0,   False),
    ("Yes", 2, 25.0,  False),
    ("Yes", 2, 30.0,  False),

    # Type / edge-case errors (INVALID)
    ("Yes", 2, None,   False),
    ("Yes", 2, "",     False),
    ("Yes", 2, "abc",  False),
    ("Yes", 2, str(CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN),  True),
])
def test_validate_carriageway_width(validator, median, num_lanes, value, expected_valid):
    inputs = {KEY_CARRIAGEWAY_WIDTH: value, KEY_INCLUDE_MEDIAN: median}
    result = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)

    val_as_float = None
    if value is not None:
        try:
            val_as_float = float(value)
        except (ValueError, TypeError):
            pass

    required_width = IRC5_2015.cl_104_3_1_carriageway_width(
        val_as_float if val_as_float is not None else 0, num_lanes
    )

    if expected_valid and val_as_float is not None \
            and val_as_float >= required_width and val_as_float <= CARRIAGEWAY_WIDTH_MAX_LIMIT:
        assert result is None, f"Expected carriageway width {value} with median {median} to be valid"
    elif expected_valid:
        assert result is not None
    else:
        assert result is not None, f"Expected carriageway width {value} with median {median} to be invalid"


# ==========================================
# test_validate_skew_angle
# FORMAT: angle=<degrees, float>   valid range SKEW_ANGLE_MIN..SKEW_ANGLE_MAX
#         expect=VALID / INVALID
# ==========================================

@pytest.mark.parametrize("value, expected_valid", [
    # ── Large negatives way below SKEW_ANGLE_MIN (INVALID) ────────────────
    (-100.0, False),
    (-50.0,  False),
    (-30.0,  False),
    (-20.0,  False),
    (-16.0,  False),

    # ── Just below SKEW_ANGLE_MIN (INVALID) ───────────────────────────────
    (SKEW_ANGLE_MIN - 10.0,  False),
    (SKEW_ANGLE_MIN - 5.0,   False),
    (SKEW_ANGLE_MIN - 1.0,   False),
    (SKEW_ANGLE_MIN - 0.5,   False),
    (SKEW_ANGLE_MIN - 0.1,   False),
    (SKEW_ANGLE_MIN - 0.01,  False),

    # ── Exact SKEW_ANGLE_MIN (VALID) ──────────────────────────────────────
    (SKEW_ANGLE_MIN,          True),

    # ── Just above SKEW_ANGLE_MIN (VALID) ─────────────────────────────────
    (SKEW_ANGLE_MIN + 0.01,   True),
    (SKEW_ANGLE_MIN + 0.1,    True),
    (SKEW_ANGLE_MIN + 0.5,    True),

    # ── Step through negative portion of valid range (VALID) ──────────────
    (-14.0, True),
    (-13.0, True),
    (-12.0, True),
    (-11.0, True),
    (-10.0, True),
    (-9.0,  True),
    (-8.0,  True),
    (-7.0,  True),
    (-6.0,  True),
    (-5.0,  True),
    (-4.0,  True),
    (-3.0,  True),
    (-2.0,  True),
    (-1.0,  True),

    # ── Zero (VALID) ──────────────────────────────────────────────────────
    (0.0,   True),

    # ── Step through positive portion of valid range (VALID) ──────────────
    (1.0,   True),
    (2.0,   True),
    (3.0,   True),
    (4.0,   True),
    (5.0,   True),
    (6.0,   True),
    (7.0,   True),
    (8.0,   True),
    (9.0,   True),
    (10.0,  True),
    (11.0,  True),
    (12.0,  True),
    (13.0,  True),
    (14.0,  True),

    # ── Just below SKEW_ANGLE_MAX (VALID) ─────────────────────────────────
    (SKEW_ANGLE_MAX - 0.5,   True),
    (SKEW_ANGLE_MAX - 0.1,   True),
    (SKEW_ANGLE_MAX - 0.01,  True),

    # ── Exact SKEW_ANGLE_MAX (VALID) ──────────────────────────────────────
    (SKEW_ANGLE_MAX,          True),

    # ── Just above SKEW_ANGLE_MAX (INVALID) ───────────────────────────────
    (SKEW_ANGLE_MAX + 0.01,   False),
    (SKEW_ANGLE_MAX + 0.1,    False),
    (SKEW_ANGLE_MAX + 0.5,    False),
    (SKEW_ANGLE_MAX + 1.0,    False),
    (SKEW_ANGLE_MAX + 5.0,    False),
    (SKEW_ANGLE_MAX + 10.0,   False),

    # ── Large positives way above SKEW_ANGLE_MAX (INVALID) ────────────────
    (20.0,  False),
    (25.0,  False),
    (30.0,  False),
    (50.0,  False),
    (100.0, False),

    # ── Type / edge-case errors (INVALID) ─────────────────────────────────
    (None,    False),
    ("",      False),
    ("abc",   False),
    ("0",     True),
    ("15",    True),
])
def test_validate_skew_angle(validator, value, expected_valid):
    inputs = {KEY_SKEW_ANGLE: value}
    result = validator.validate_basic_inputs(KEY_SKEW_ANGLE, inputs)
    if expected_valid:
        assert result is None, f"Expected skew angle {value} to be valid"
    else:
        assert result is not None, f"Expected skew angle {value} to be invalid"


# ==========================================
# test_validate_layout_equation  (parametrized)
# FORMAT: overall_w  girders  spacing  overhang
#         rule: overall_w == (girders-1)*spacing + 2*overhang
#         expect=OK → no layout_equation error
#         expect=ERROR → layout_equation error raised
# ==========================================

@pytest.mark.parametrize("overall_w, no_girders, spacing, overhang, expected_error", [
    # ── Valid cases: overall_w == (no_girders-1)*spacing + 2*overhang ─────
    (10.0,  4,  2.5,  1.25,  False),   # (4-1)*2.5  + 2*1.25  = 10.0
    (7.5,   3,  2.5,  1.25,  False),   # (3-1)*2.5  + 2*1.25  =  7.5
    (12.5,  5,  2.5,  1.25,  False),   # (5-1)*2.5  + 2*1.25  = 12.5
    (15.0,  6,  2.5,  1.25,  False),   # (6-1)*2.5  + 2*1.25  = 15.0
    (17.5,  7,  2.5,  1.25,  False),   # (7-1)*2.5  + 2*1.25  = 17.5
    (20.0,  8,  2.5,  1.25,  False),   # (8-1)*2.5  + 2*1.25  = 20.0
    (12.0,  4,  3.0,  1.5,   False),   # (4-1)*3.0  + 2*1.5   = 12.0
    (8.0,   3,  2.0,  2.0,   False),   # (3-1)*2.0  + 2*2.0   =  8.0
    (16.0,  5,  3.0,  2.0,   False),   # (5-1)*3.0  + 2*2.0   = 16.0
    (6.0,   2,  2.0,  2.0,   False),   # (2-1)*2.0  + 2*2.0   =  6.0
    (10.0,  10, 1.0,  0.5,   False),   # (10-1)*1.0 + 2*0.5   = 10.0
    (14.0,  4,  4.0,  1.0,   False),   # (4-1)*4.0  + 2*1.0   = 14.0

    # ── Invalid cases: overall_w does NOT match formula ───────────────────
    (10.2,  4,  2.5,  1.25,  True),    # off by +0.2
    (9.8,   4,  2.5,  1.25,  True),    # off by -0.2
    (11.0,  4,  2.5,  1.25,  True),    # off by +1.0
    (8.0,   4,  2.5,  1.25,  True),    # too small for given params
    (0.0,   4,  2.5,  1.25,  True),    # zero width
    (7.4,   3,  2.5,  1.25,  True),    # should be 7.5
    (7.6,   3,  2.5,  1.25,  True),    # should be 7.5
    (15.2,  6,  2.5,  1.25,  True),    # off by +0.2
    (20.5,  8,  2.5,  1.25,  True),    # off by +0.5
    (25.0,  4,  2.5,  1.25,  True),    # completely wrong
    (2.5,   1,  0.0,  1.25,  False),   # 1 girder: (1-1)*0 + 2*1.25 = 2.5 -> OK
    (3.0,   1,  0.0,  1.25,  True),    # 1 girder: should be 2.5 -> ERROR
])
def test_validate_layout_equation(validator, valid_additional_inputs,
                                  overall_w, no_girders, spacing, overhang, expected_error):
    # overall_bridge_width == (no_of_girders - 1) * girder_spacing + 2 * deck_overhang
    inputs = valid_additional_inputs.copy()
    inputs["overall_bridge_width"] = overall_w
    inputs["no_of_girders"]        = no_girders
    inputs["girder_spacing"]       = spacing
    inputs["deck_overhang"]        = overhang

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "layout_equation" in res["errors"]
    else:
        assert "layout_equation" not in res["errors"]


# ==========================================
# test_validate_kerb_width
# FORMAT: footpath  kerb(mm)
#         rule (when footpath=None): kerb >= KEY_SAFETY_KERB_MIN_WIDTH
#         when footpath is provided: clause does not apply → always OK
#         expect=OK / ERROR
# ==========================================

@pytest.mark.parametrize("footpath, kerb, expected_error", [
    # ── footpath = None: kerb must be >= KEY_SAFETY_KERB_MIN_WIDTH ─────────
    # Far below min → ERROR
    ("None", 0,   True),
    ("None", 50,  True),
    ("None", 100, True),
    ("None", 150, True),
    ("None", 200, True),
    ("None", 250, True),
    ("None", 300, True),
    ("None", 400, True),
    ("None", 500, True),
    ("None", 550, True),
    ("None", 600, True),
    ("None", 725, True),
    ("None", 740, True),

    # Just below KEY_SAFETY_KERB_MIN_WIDTH → ERROR
    ("None", KEY_SAFETY_KERB_MIN_WIDTH - 100, True),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH - 50,  True),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH - 10,  True),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH - 5,   True),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH - 1,   True),

    # Exact KEY_SAFETY_KERB_MIN_WIDTH → OK
    ("None", KEY_SAFETY_KERB_MIN_WIDTH,         False),

    # Just above KEY_SAFETY_KERB_MIN_WIDTH → OK
    ("None", KEY_SAFETY_KERB_MIN_WIDTH + 1,     False),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH + 10,    False),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH + 50,    False),
    ("None", KEY_SAFETY_KERB_MIN_WIDTH + 100,   False),

    # Larger values → OK
    ("None", 900,  False),
    ("None", 1000, False),
    ("None", 1100, False),
    ("None", 1200, False),
    ("None", 1500, False),
    ("None", 2000, False),

    # ── footpath = Single Side: clause not applicable → always OK ──────────
    ("Single Side", 0,   False),
    ("Single Side", 100, False),
    ("Single Side", 200, False),
    ("Single Side", 400, False),
    ("Single Side", 500, False),
    ("Single Side", 700, False),
    ("Single Side", 749, False),
    ("Single Side", KEY_SAFETY_KERB_MIN_WIDTH,       False),
    ("Single Side", KEY_SAFETY_KERB_MIN_WIDTH + 100, False),
    ("Single Side", 1000, False),
    ("Single Side", 1500, False),

    # ── footpath = Both Sides: clause not applicable → always OK ──────────
    ("Both Sides", 0,   False),
    ("Both Sides", 100, False),
    ("Both Sides", 300, False),
    ("Both Sides", 500, False),
    ("Both Sides", 600, False),
    ("Both Sides", 749, False),
    ("Both Sides", KEY_SAFETY_KERB_MIN_WIDTH,       False),
    ("Both Sides", KEY_SAFETY_KERB_MIN_WIDTH + 200, False),
    ("Both Sides", 1000, False),
])
def test_validate_kerb_width(validator, valid_additional_inputs, footpath, kerb, expected_error):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH]   = footpath
    inputs["kerb_width"]   = kerb

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "kerb_width" in res["errors"]
    else:
        assert "kerb_width" not in res["errors"]


# ==========================================
# test_validate_footpath_width
# FORMAT: footpath  width(m)
#         rule (when footpath provided): width >= 1.5 m
#         when footpath=None: clause does not apply → always OK
#         expect=OK / ERROR
# ==========================================

@pytest.mark.parametrize("footpath, footpath_width, expected_error", [
    # ── Single Side: min width = 1.5 m ────────────────────────────────────
    # Far below min → ERROR
    ("Single Side", 0.0,  True),
    ("Single Side", 0.1,  True),
    ("Single Side", 0.2,  True),
    ("Single Side", 0.3,  True),
    ("Single Side", 0.4,  True),
    ("Single Side", 0.5,  True),
    ("Single Side", 0.6,  True),
    ("Single Side", 0.7,  True),
    ("Single Side", 0.8,  True),
    ("Single Side", 0.9,  True),
    ("Single Side", 1.0,  True),
    ("Single Side", 1.1,  True),
    ("Single Side", 1.2,  True),
    ("Single Side", 1.3,  True),
    ("Single Side", 1.4,  True),

    # Just below 1.5 → ERROR
    ("Single Side", 1.49,   True),
    ("Single Side", 1.499,  True),
    ("Single Side", 1.4999, True),

    # Exact 1.5 → OK
    ("Single Side", 1.5,    False),

    # Just above 1.5 → OK
    ("Single Side", 1.501,  False),
    ("Single Side", 1.51,   False),
    ("Single Side", 1.6,    False),

    # Larger values → OK
    ("Single Side", 2.0,    False),
    ("Single Side", 2.5,    False),
    ("Single Side", 3.0,    False),
    ("Single Side", 4.0,    False),
    ("Single Side", 5.0,    False),
    ("Single Side", 10.0,   False),
    ("Single Side", 50.0,   False),

    # Missing width when footpath provided → ERROR
    ("Single Side", None,   True),

    # ── Both Sides: same minimum rule ─────────────────────────────────────
    ("Both Sides", 0.5,   True),
    ("Both Sides", 1.0,   True),
    ("Both Sides", 1.3,   True),
    ("Both Sides", 1.4,   True),
    ("Both Sides", 1.49,  True),

    # Exact 1.5 → OK
    ("Both Sides", 1.5,   False),

    # Above min → OK
    ("Both Sides", 1.6,   False),
    ("Both Sides", 2.0,   False),
    ("Both Sides", 2.5,   False),
    ("Both Sides", 3.0,   False),
    ("Both Sides", 5.0,   False),
    ("Both Sides", 10.0,  False),
    ("Both Sides", 50.0,  False),

    # Missing width → ERROR
    ("Both Sides", None,  True),

    # ── None footpath: clause not applicable → always OK ──────────────────
    ("None", 0.0,   False),
    ("None", 0.5,   False),
    ("None", 1.0,   False),
    ("None", 1.4,   False),
    ("None", 1.5,   False),
    ("None", 2.0,   False),
    ("None", 5.0,   False),
    ("None", 10.0,  False),
    ("None", 50.0,  False),
    ("None", None,  False),
])
def test_validate_footpath_width(validator, valid_additional_inputs, footpath, footpath_width, expected_error):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH]      = footpath
    inputs["footpath_width"]  = footpath_width

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "footpath_width" in res["errors"]
    else:
        assert "footpath_width" not in res["errors"]


# ==========================================
# test_validate_railing_height
# FORMAT: footpath  height(mm)
#         rule (when footpath provided): height >= KEY_RAILING_MIN_HEIGHT[0]
#         when footpath=None: clause does not apply → always OK
#         expect=OK / ERROR
# ==========================================

@pytest.mark.parametrize("footpath, railing_height, expected_error", [
    # ── Single Side: min = KEY_RAILING_MIN_HEIGHT[0] ──────────────────────
    # Far below min → ERROR
    ("Single Side", 100,  True),
    ("Single Side", 200,  True),
    ("Single Side", 300,  True),
    ("Single Side", 400,  True),
    ("Single Side", 500,  True),
    ("Single Side", 600,  True),
    ("Single Side", 700,  True),
    ("Single Side", 800,  True),
    ("Single Side", 900,  True),
    ("Single Side", 950,  True),
    ("Single Side", 1000, True),
    ("Single Side", 1050, True),

    # Just below KEY_RAILING_MIN_HEIGHT[0] → ERROR
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] - 100, True),
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] - 50,  True),
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] - 10,  True),
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] - 5,   True),
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] - 1,   True),

    # Exact KEY_RAILING_MIN_HEIGHT[0] → OK
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0],         False),

    # Just above KEY_RAILING_MIN_HEIGHT[0] → OK
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] + 1,     False),
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] + 10,    False),
    ("Single Side", KEY_RAILING_MIN_HEIGHT[0] + 50,    False),

    # Larger values → OK
    ("Single Side", 1150, False),
    ("Single Side", 1200, False),
    ("Single Side", 1250, False),
    ("Single Side", 1300, False),
    ("Single Side", 1400, False),
    ("Single Side", 1500, False),
    ("Single Side", 1600, False),
    ("Single Side", 1700, False),
    ("Single Side", 1800, False),
    ("Single Side", 1900, False),
    ("Single Side", 2000, False),
    ("Single Side", 3000, False),

    # ── None footpath: clause does not apply → always OK ──────────────────
    ("None", 100,  True),
    ("None", 300,  True),
    ("None", 500,  True),
    ("None", 700,  True),
    ("None", 1000, True),
    ("None", KEY_RAILING_MIN_HEIGHT[0] - 1,   True),
    ("None", KEY_RAILING_MIN_HEIGHT[0],        False),
    ("None", KEY_RAILING_MIN_HEIGHT[0] + 100,  False),
    ("None", 1500, False),
    ("None", 2000, False),
    ("None", 3000, False),
])
def test_validate_railing_height(validator, valid_additional_inputs, footpath, railing_height, expected_error):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH]      = footpath
    inputs["railing_height"]  = railing_height

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "railing_height" in res["errors"]
    else:
        assert "railing_height" not in res["errors"]


# ==========================================
# test_validate_stud_height
# FORMAT: stud_height(mm)
#         rule: stud_height >= MIN_STUD_HEIGHT_MM
#         expect=OK / ERROR
# ==========================================

@pytest.mark.parametrize("stud_h, expected_error", [
    # ── Negative values (ERROR) ────────────────────────────────────────────
    (-200, True),
    (-100, True),
    (-50,  True),
    (-20,  True),
    (-10,  True),
    (-1,   True),

    # ── Zero (ERROR) ──────────────────────────────────────────────────────
    (0,    True),

    # ── Positive but below MIN_STUD_HEIGHT_MM (ERROR) ─────────────────────
    (1,    True),
    (5,    True),
    (10,   True),
    (20,   True),
    (25,   True),
    (30,   True),
    (40,   True),
    (60,   True),
    (70,   True),
    (85,   True),

    # Just below MIN_STUD_HEIGHT_MM → ERROR
    (MIN_STUD_HEIGHT_MM - 50,  True),
    (MIN_STUD_HEIGHT_MM - 20,  True),
    (MIN_STUD_HEIGHT_MM - 10,  True),
    (MIN_STUD_HEIGHT_MM - 5,   True),
    (MIN_STUD_HEIGHT_MM - 1,   True),

    # Exact MIN_STUD_HEIGHT_MM → OK
    (MIN_STUD_HEIGHT_MM,        False),

    # Just above MIN_STUD_HEIGHT_MM → OK
    (MIN_STUD_HEIGHT_MM + 1,    False),
    (MIN_STUD_HEIGHT_MM + 5,    False),
    (MIN_STUD_HEIGHT_MM + 10,   False),
    (MIN_STUD_HEIGHT_MM + 25,   False),
    (MIN_STUD_HEIGHT_MM + 50,   False),

    # Larger values → OK
    # Larger values (arbitrary midrange stress values to test a wide spread) → OK
    (110,  False),
    (115,  False),
    (120,  False),
    (130,  False),
    (140,  False),
    (150,  False),
    (160,  False),
    (175,  False),
    (200,  False),
    (250,  False),
    (300,  False),
    (500,  False),
    (None, False),
])
def test_validate_stud_height(validator, valid_additional_inputs, stud_h, expected_error):
    inputs = valid_additional_inputs.copy()
    inputs["stud_height"] = stud_h

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "stud_height" in res["errors"]
    else:
        assert "stud_height" not in res["errors"]


# ==========================================
# test_validate_stud_diameter
# FORMAT: stud_dia(mm)  flange_t(mm)
#         rule: stud_dia <= MAX_STUD_DIAMETER_FACTOR * flange_t
#         expect=OK / ERROR
# ==========================================

@pytest.mark.parametrize("stud_d, flange_t, expected_error", [
    # ── flange_t = 10 → boundary at MAX_STUD_DIAMETER_FACTOR * 10 = 20 ───
    (5,                                          10, False),
    (10,                                         10, False),
    (15,                                         10, False),
    (19,                                         10, False),
    (MAX_STUD_DIAMETER_FACTOR * 10,              10, False),   # = 20 → OK
    (MAX_STUD_DIAMETER_FACTOR * 10 + 0.1,        10, True),    # = 20.1 → ERROR
    (21,                                         10, True),
    (25,                                         10, True),
    (30,                                         10, True),

    # ── flange_t = 12 → boundary at 24 ───────────────────────────────────
    (10,                                         12, False),
    (20,                                         12, False),
    (23,                                         12, False),
    (MAX_STUD_DIAMETER_FACTOR * 12,              12, False),   # = 24 → OK
    (MAX_STUD_DIAMETER_FACTOR * 12 + 0.1,        12, True),    # = 24.1 → ERROR
    (25,                                         12, True),
    (30,                                         12, True),

    # ── flange_t = 15 → boundary at 30 ───────────────────────────────────
    (5,                                          15, False),
    (10,                                         15, False),
    (20,                                         15, False),
    (25,                                         15, False),
    (29,                                         15, False),
    (MAX_STUD_DIAMETER_FACTOR * 15,              15, False),   # = 30 → OK
    (MAX_STUD_DIAMETER_FACTOR * 15 + 0.1,        15, True),    # = 30.1 → ERROR
    (31,                                         15, True),
    (35,                                         15, True),
    (45,                                         15, True),

    # ── flange_t = 20 → boundary at 40 ───────────────────────────────────
    (10,                                         20, False),
    (20,                                         20, False),
    (25,                                         20, False),
    (30,                                         20, False),
    (39,                                         20, False),
    (MAX_STUD_DIAMETER_FACTOR * 20,              20, False),   # = 40 → OK
    (MAX_STUD_DIAMETER_FACTOR * 20 + 0.1,        20, True),    # = 40.1 → ERROR
    (41,                                         20, True),
    (50,                                         20, True),
    (60,                                         20, True),

    # ── flange_t = 25 → boundary at 50 ───────────────────────────────────
    (10,                                         25, False),
    (25,                                         25, False),
    (40,                                         25, False),
    (49,                                         25, False),
    (MAX_STUD_DIAMETER_FACTOR * 25,              25, False),   # = 50 → OK
    (MAX_STUD_DIAMETER_FACTOR * 25 + 0.1,        25, True),    # = 50.1 → ERROR
    (51,                                         25, True),
    (60,                                         25, True),
    (70,                                         25, True),

    # ── flange_t = 30 → boundary at 60 ───────────────────────────────────
    (10,                                         30, False),
    (30,                                         30, False),
    (50,                                         30, False),
    (59,                                         30, False),
    (MAX_STUD_DIAMETER_FACTOR * 30,              30, False),   # = 60 → OK
    (MAX_STUD_DIAMETER_FACTOR * 30 + 0.1,        30, True),    # = 60.1 → ERROR
    (61,                                         30, True),
    (70,                                         30, True),
    (80,                                         30, True),
    (None,                                       20, False),
    (0,                                          20, False),
])
def test_validate_stud_diameter(validator, valid_additional_inputs, stud_d, flange_t, expected_error):
    inputs = valid_additional_inputs.copy()
    inputs["stud_diameter"]      = stud_d
    inputs["top_flange_thickness"] = flange_t

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "stud_diameter" in res["errors"]
    else:
        assert "stud_diameter" not in res["errors"]

# ==========================================
# test_validate_stud_edge_distance
# FORMAT: edge_dist(mm)
#         rule: edge_dist >= MIN_EDGE_DISTANCE_MM
#         expect=OK / ERROR
# ==========================================

@pytest.mark.parametrize("edge_d, expected_error", [
    # ── Negative values (ERROR) ────────────────────────────────────────────
    (-100, True),
    (-50,  True),
    (-20,  True),
    (-10,  True),
    (-5,   True),
    (-1,   True),

    # ── Zero (ERROR) ──────────────────────────────────────────────────────
    (0,    True),

    # ── Positive but below MIN_EDGE_DISTANCE_MM (ERROR) ───────────────────
    (1,    True),
    (3,    True),
    (5,    True),
    (8,    True),
    (10,   True),
    (12,   True),
    (18,   True),
    (22,   True),

    # Just below MIN_EDGE_DISTANCE_MM → ERROR
    (MIN_EDGE_DISTANCE_MM - 10,  True),
    (MIN_EDGE_DISTANCE_MM - 5,   True),
    (MIN_EDGE_DISTANCE_MM - 2,   True),
    (MIN_EDGE_DISTANCE_MM - 1,   True),
    (MIN_EDGE_DISTANCE_MM - 0.5, True),
    (MIN_EDGE_DISTANCE_MM - 0.1, True),

    # Exact MIN_EDGE_DISTANCE_MM → OK
    (MIN_EDGE_DISTANCE_MM,        False),

    # Just above MIN_EDGE_DISTANCE_MM → OK
    (MIN_EDGE_DISTANCE_MM + 0.1,  False),
    (MIN_EDGE_DISTANCE_MM + 0.5,  False),
    (MIN_EDGE_DISTANCE_MM + 1,    False),
    (MIN_EDGE_DISTANCE_MM + 5,    False),
    (MIN_EDGE_DISTANCE_MM + 10,   False),

    # Larger values (arbitrary midrange stress values to test a wide spread) → OK
    (40,   False),
    (50,   False),
    (60,   False),
    (75,   False),
    (100,  False),
    (125,  False),
    (150,  False),
    (200,  False),
    (300,  False),
    (500,  False),
    (None, False),
])
def test_validate_stud_edge_distance(validator, valid_additional_inputs, edge_d, expected_error):
    inputs = valid_additional_inputs.copy()
    inputs["stud_edge_distance"] = edge_d

    res = validator.validate_additional_inputs(inputs)
    if expected_error:
        assert "stud_edge_distance" in res["errors"]
    else:
        assert "stud_edge_distance" not in res["errors"]

# ==========================================
# TEST FULL PLATEGIRDERBRIDGE CREATION
# ==========================================

def test_plategirderbridge_creation_valid(valid_basic_inputs, valid_additional_inputs):
    bridge = PlateGirderBridge()

    full_inputs = valid_basic_inputs.copy()
    full_inputs.update(valid_additional_inputs)

    bridge.set_input(full_inputs)

    assert bridge.basic_inputs[KEY_SPAN] == str(SPAN_MIN + 5)
    assert bridge.additional_inputs["overall_bridge_width"] == 10.0

def test_plategirderbridge_creation_invalid():
    bridge = PlateGirderBridge()
    bridge.set_input({})

    parsed = bridge._parse_basic_inputs()
    assert parsed["span"] > 0
    assert parsed["cw_width"] > 0
    assert parsed["skew_angle"] == 0.0

# ==========================================
# TEST MISSING REQUIRED FIELDS AND UNVALIDATED BASIC INPUTS
# ==========================================

def test_validate_basic_inputs_missing_and_unvalidated_keys(validator):
    # Span missing entirely
    res_span = validator.validate_basic_inputs(KEY_SPAN, {})
    assert res_span is not None
    assert res_span[0] == SPAN_MIN

    # Carriageway width missing entirely
    res_cw = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, {})
    assert res_cw is not None
    assert res_cw[0] == CARRIAGEWAY_WIDTH_MIN

    # Skew angle missing entirely
    res_skew = validator.validate_basic_inputs(KEY_SKEW_ANGLE, {})
    assert res_skew is not None
    assert res_skew[0] == SKEW_ANGLE_MIN

    # Unvalidated / string-enum basic inputs (should always return None)
    for key in [KEY_STRUCTURE_TYPE, KEY_DESIGN_MODE, KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC]:
        assert validator.validate_basic_inputs(key, {}) is None
        assert validator.validate_basic_inputs(key, {key: "TestValue"}) is None

# ==========================================
# TEST MISSING ADDITIONAL INPUTS
# ==========================================

def test_validate_additional_inputs_missing_keys(validator, valid_additional_inputs):
    # Test when all fields are absent
    res_empty = validator.validate_additional_inputs({})
    assert res_empty["status"] is False
    assert "footpath_width" in res_empty["errors"]

    # Test when overall_bridge_width key is completely missing from an otherwise valid dict
    inputs = valid_additional_inputs.copy()
    inputs.pop("overall_bridge_width", None)
    res_missing_width = validator.validate_additional_inputs(inputs)
    assert "layout_equation" not in res_missing_width["errors"]

# ==========================================
# NEW GENERALLY IMPROVED SCENARIO TESTS
# ==========================================

def test_validate_multiple_basic_input_errors(validator):
    # Pass an inputs dict where span, carriageway width, and skew angle are all invalid at once
    inputs = {
        KEY_SPAN: "10.0",                 # SPAN_MIN is 20, so 10.0 is invalid
        KEY_CARRIAGEWAY_WIDTH: "2.0",    # CARRIAGEWAY_WIDTH_MIN is 4.25, so 2.0 is invalid
        KEY_INCLUDE_MEDIAN: "No",
        KEY_SKEW_ANGLE: "30.0"           # SKEW_ANGLE_MAX is 15.0, so 30.0 is invalid
    }

    res_span = validator.validate_basic_inputs(KEY_SPAN, inputs)
    res_cw = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)
    res_skew = validator.validate_basic_inputs(KEY_SKEW_ANGLE, inputs)

    # Confirm all three return errors/corrections
    assert res_span is not None
    assert res_cw is not None
    assert res_skew is not None

def test_validate_additional_inputs_multiple_errors(validator, valid_additional_inputs):
    # Set both stud_height and stud_edge_distance to invalid values
    inputs = valid_additional_inputs.copy()
    inputs["stud_height"] = 50                 # MIN_STUD_HEIGHT_MM is 100, so 50 is invalid
    inputs["stud_edge_distance"] = 10         # MIN_EDGE_DISTANCE_MM is 25, so 10 is invalid

    res = validator.validate_additional_inputs(inputs)
    # Confirm both errors are returned and present in the errors dictionary
    assert res["status"] is False
    assert "stud_height" in res["errors"]
    assert "stud_edge_distance" in res["errors"]

def test_validate_enum_fields(validator):
    # If the validator doesn't check these basic enum/dropdown inputs,
    # document with a test confirming they pass through freely (return None).
    enum_keys = [
        KEY_STRUCTURE_TYPE, KEY_DESIGN_MODE, KEY_GIRDER,
        KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC
    ]
    for key in enum_keys:
        # Valid value should pass
        assert validator.validate_basic_inputs(key, {key: "Highway Bridge"}) is None
        # Garbage value should also pass freely
        assert validator.validate_basic_inputs(key, {key: "Invalid Garbage Value"}) is None

def test_plategirderbridge_partial_inputs(valid_basic_inputs):
    bridge = PlateGirderBridge()
    # Pass only basic inputs without additional inputs, confirm set_input does not crash
    bridge.set_input(valid_basic_inputs)
    assert len(bridge.basic_inputs) > 0
    assert len(bridge.additional_inputs) == 0

    # Confirm set_input handles unexpected keys gracefully by storing them in additional_inputs
    inputs = valid_basic_inputs.copy()
    inputs["unexpected_test_key_xyz"] = "random_value"
    bridge.set_input(inputs)
    assert bridge.additional_inputs["unexpected_test_key_xyz"] == "random_value"

@pytest.mark.parametrize("footpath, kerb_width, footpath_width, railing_height", [
    ("None", 800, None, 1200),
    ("None", 750, 0.0, 1100),
    ("Single Side", 0, 1.5, 1150),
    ("Single Side", 500, 2.0, 1200),
    ("Both Sides", 100, 1.5, 1100),
    ("Both Sides", 600, 1.8, 1300),
])
def test_validate_additional_inputs_all_valid_combinations(validator, valid_additional_inputs,
                                                          footpath, kerb_width, footpath_width, railing_height):
    # Parametrized test covering different valid combinations of footpath type crossed with all the footpath-dependent fields
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH] = footpath
    inputs["kerb_width"] = kerb_width
    inputs["footpath_width"] = footpath_width
    inputs["railing_height"] = railing_height

    res = validator.validate_additional_inputs(inputs)
    assert res["status"] is True, f"Expected valid combination for footpath={footpath}, errors: {res.get('errors')}"
    assert len(res["errors"]) == 0

# ==============================================================================
# GROUP A — FULL BASIC-INPUT VALIDATION LOOP (Gap #2)
#
# Real usage calls validate_basic_inputs() for EVERY key in sequence.
# These two tests confirm:
#   (a) a fully-valid dict produces zero errors across all keys, and
#   (b) an all-invalid dict surfaces exactly the three numeric errors while
#       the enum/dropdown fields remain silent.
# ==============================================================================

def test_validate_basic_inputs_full_loop_all_valid(validator, valid_basic_inputs):
    """
    Simulate the real call-site loop: iterate over every key in
    PlateGirderBridge._BASIC_INPUT_KEYS and validate against a fully-valid
    input dict.  Every key must return None (no correction required).
    """
    all_keys = list(PlateGirderBridge._BASIC_INPUT_KEYS)
    errors = {}
    for key in all_keys:
        res = validator.validate_basic_inputs(key, valid_basic_inputs)
        if res is not None:
            errors[key] = res
    assert errors == {}, (
        f"Expected no validation errors with fully-valid inputs, "
        f"but got errors on: {list(errors.keys())}"
    )

def test_validate_basic_inputs_full_loop_collects_all_errors(validator):
    """
    Simulate the real call-site loop with all three numeric fields out of range.
    Confirms the loop collects span + carriageway_width + skew_angle errors
    while enum/dropdown keys remain silent — proving the loop does not
    short-circuit on the first failure.
    """
    bad_inputs = {
        KEY_SPAN:                      str(SPAN_MIN - 5),
        KEY_CARRIAGEWAY_WIDTH:         str(CARRIAGEWAY_WIDTH_MIN - 1),
        KEY_INCLUDE_MEDIAN:            "No",
        KEY_SKEW_ANGLE:                str(SKEW_ANGLE_MAX + 10),
        KEY_STRUCTURE_TYPE:            "Highway Bridge",
        KEY_PROJECT_LOCATION:          "Mumbai",
        KEY_DESIGN_MODE:               "Optimized",
        KEY_GIRDER:                    "E 250A",
        KEY_CROSS_BRACING:             "E 250A",
        KEY_END_DIAPHRAGM:             "E 250A",
        KEY_DECK_CONCRETE_GRADE_BASIC: "M30",
    }
    all_keys = list(PlateGirderBridge._BASIC_INPUT_KEYS)
    errors = {}
    for key in all_keys:
        res = validator.validate_basic_inputs(key, bad_inputs)
        if res is not None:
            errors[key] = res

    assert KEY_SPAN in errors,              "SPAN out-of-range must produce an error"
    assert KEY_CARRIAGEWAY_WIDTH in errors, "CARRIAGEWAY_WIDTH out-of-range must produce an error"
    assert KEY_SKEW_ANGLE in errors,        "SKEW_ANGLE out-of-range must produce an error"

    # Enum / dropdown fields must be completely silent
    for silent_key in [KEY_STRUCTURE_TYPE, KEY_DESIGN_MODE, KEY_GIRDER,
                        KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC]:
        assert silent_key not in errors, (
            f"{silent_key!r} should NOT produce an error "
            f"(not validated by BridgeInputValidator)"
        )

# ==============================================================================
# GROUP B — CROSS-FIELD INTERACTION: span × carriageway_width (Gap #1)
#
# Both fields live in the same inputs dict.  The tests confirm:
#   - Each field is evaluated independently (neither suppresses the other).
#   - The KEY_INCLUDE_MEDIAN flag in the SAME dict shifts the carriageway floor.
# ==============================================================================

@pytest.mark.parametrize(
    "span, carriageway_width, median, expect_span_error, expect_cw_error",
    [
        # Both at exact minimum — both valid
        (SPAN_MIN,       CARRIAGEWAY_WIDTH_MIN,              "No",  False, False),
        # Span at minimum, carriageway just below minimum
        (SPAN_MIN,       CARRIAGEWAY_WIDTH_MIN - 0.5,        "No",  False, True),
        # Span just below minimum, carriageway at minimum
        (SPAN_MIN - 1.0, CARRIAGEWAY_WIDTH_MIN,              "No",  True,  False),
        # Both below minimum — each must fail independently
        (SPAN_MIN - 5.0, CARRIAGEWAY_WIDTH_MIN - 1.0,        "No",  True,  True),
        # Median "Yes" raises the carriageway floor; span valid, cw passes
        (30.0,           CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,  "Yes", False, False),
        # Median "Yes"; carriageway below the higher median minimum
        (30.0,           CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 1.0, "Yes", False, True),
        # Both at their respective maxima — both valid
        (SPAN_MAX,       CARRIAGEWAY_WIDTH_MAX_LIMIT,        "No",  False, False),
        # Span over max, carriageway valid — only span fails
        (SPAN_MAX + 1.0, CARRIAGEWAY_WIDTH_MIN,              "No",  True,  False),
    ],
)
def test_cross_field_span_carriageway_interaction(
        validator, span, carriageway_width, median,
        expect_span_error, expect_cw_error):
    """
    Cross-field interaction: span and carriageway_width in the SAME inputs dict.
    Validates that neither field's error suppresses the other, and that the
    median flag correctly shifts the carriageway floor.
    """
    inputs = {
        KEY_SPAN:              span,
        KEY_CARRIAGEWAY_WIDTH: carriageway_width,
        KEY_INCLUDE_MEDIAN:    median,
    }
    span_res = validator.validate_basic_inputs(KEY_SPAN, inputs)
    cw_res   = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)

    if expect_span_error:
        assert span_res is not None, (
            f"span={span} should fail validation but returned None"
        )
    else:
        assert span_res is None, (
            f"span={span} should pass validation but returned {span_res}"
        )

    if expect_cw_error:
        assert cw_res is not None, (
            f"carriageway_width={carriageway_width} (median={median!r}) "
            f"should fail but returned None"
        )
    else:
        assert cw_res is None, (
            f"carriageway_width={carriageway_width} (median={median!r}) "
            f"should pass but returned {cw_res}"
        )

@pytest.mark.parametrize("carriageway_width, median, expect_error", [
    # Width valid for no-median but below the median minimum
    (CARRIAGEWAY_WIDTH_MIN,                    "No",  False),  # no median: at floor → OK
    (CARRIAGEWAY_WIDTH_MIN,                    "Yes", True),   # with median: 4.25 < 7.5 → FAIL
    (CARRIAGEWAY_WIDTH_MIN + 1.0,              "No",  False),  # no median: above floor → OK
    (CARRIAGEWAY_WIDTH_MIN + 1.0,              "Yes", True),   # with median: still < 7.5 → FAIL
    # At the median minimum
    (CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,        "No",  False),  # no median: fine
    (CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,        "Yes", False),  # with median: exactly at floor → OK
    (CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.01, "Yes", True),   # just below median floor → FAIL
    # Shared upper cap
    (CARRIAGEWAY_WIDTH_MAX_LIMIT,              "No",  False),
    (CARRIAGEWAY_WIDTH_MAX_LIMIT,              "Yes", False),
    (CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,        "No",  True),   # over cap regardless of median
    (CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,        "Yes", True),
])
def test_carriageway_median_cross_field(validator, carriageway_width, median, expect_error):
    """
    Documents that KEY_INCLUDE_MEDIAN in the SAME dict changes which floor
    validate_basic_inputs enforces for KEY_CARRIAGEWAY_WIDTH.  A value valid
    without a median can be invalid with one.
    """
    inputs = {KEY_CARRIAGEWAY_WIDTH: carriageway_width, KEY_INCLUDE_MEDIAN: median}
    res = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)
    if expect_error:
        assert res is not None, (
            f"width={carriageway_width} with median={median!r} should be invalid"
        )
    else:
        assert res is None, (
            f"width={carriageway_width} with median={median!r} should be valid, got {res}"
        )

# ==============================================================================
# GROUP C — ADDITIONAL INPUTS: THREE SIMULTANEOUS ERRORS (Gap #4 extended)
#
# Extends the existing two-error test by adding a third simultaneous failure
# (layout_equation) to prove the validator collects ALL errors in one pass.
# ==============================================================================

def test_validate_additional_inputs_three_simultaneous_errors(
        validator, valid_additional_inputs):
    """
    Sets stud_height, stud_edge_distance, AND overall_bridge_width all to
    invalid values at once.  All three keys must appear in res["errors"] —
    the validator does not short-circuit on the first failure.
    """
    inputs = valid_additional_inputs.copy()
    inputs["stud_height"]          = MIN_STUD_HEIGHT_MM - 10   # too short
    inputs["stud_edge_distance"]   = MIN_EDGE_DISTANCE_MM - 5  # too close
    inputs["overall_bridge_width"] = 99.0                      # breaks layout equation

    res = validator.validate_additional_inputs(inputs)

    assert res["status"] is False
    assert "stud_height"        in res["errors"], "stud_height error must be reported"
    assert "stud_edge_distance" in res["errors"], "stud_edge_distance error must be reported"
    assert "layout_equation"    in res["errors"], "layout_equation error must be reported"
    assert len(res["errors"]) >= 3, (
        f"Expected at least 3 errors, got {len(res['errors'])}: "
        f"{list(res['errors'].keys())}"
    )

# ==============================================================================
# GROUP D — ENUM / DROPDOWN FIELDS PARAMETRIZED (Gap #3)
#
# The validator intentionally does NOT validate enum fields; the UI combobox
# constrains them.  Two parametrized tests document this design decision:
#   (d1) Genuine valid values  → None
#   (d2) Garbage values        → None (silent pass)
# Any future change that starts rejecting these keys will break these tests.
# ==============================================================================

@pytest.mark.parametrize("key, value", [
    (KEY_STRUCTURE_TYPE,            "Highway Bridge"),
    (KEY_STRUCTURE_TYPE,            "Other"),
    (KEY_DESIGN_MODE,               "Optimized"),
    (KEY_DESIGN_MODE,               "Custom"),
    (KEY_GIRDER,                    "E 250A"),
    (KEY_CROSS_BRACING,             "E 250A"),
    (KEY_END_DIAPHRAGM,             "E 250A"),
    (KEY_DECK_CONCRETE_GRADE_BASIC, "M30"),
])
def test_validate_enum_fields_valid_values_pass(validator, key, value):
    """
    Valid dropdown values for every enum-only basic-input key return None.
    The validator deliberately does not re-validate what the UI combobox
    already constrains.
    """
    result = validator.validate_basic_inputs(key, {key: value})
    assert result is None, (
        f"Key {key!r} with valid value {value!r}: expected None, got {result}"
    )


@pytest.mark.parametrize("key, garbage", [
    (KEY_STRUCTURE_TYPE,            "not_a_real_type"),
    (KEY_DESIGN_MODE,               "UNKNOWN_MODE_XYZ"),
    (KEY_GIRDER,                    ""),
    (KEY_CROSS_BRACING,             None),
    (KEY_END_DIAPHRAGM,             12345),
    (KEY_DECK_CONCRETE_GRADE_BASIC, []),
])
def test_validate_enum_fields_garbage_values_pass_silently(validator, key, garbage):
    """
    Documents the design decision: validate_basic_inputs silently ignores
    enum/dropdown fields even with garbage input.  If the validator ever
    starts rejecting these keys this test will fail and alert the developer.
    """
    result = validator.validate_basic_inputs(key, {key: garbage})
    assert result is None, (
        f"Key {key!r} with garbage {garbage!r}: "
        f"expected None (silent pass), got {result}"
    )

# ==============================================================================
# GROUP E — PlateGirderBridge.set_input ROBUSTNESS (Gap #5 extended)
#
# The existing tests only cover valid + empty inputs.  Four new tests cover:
#   (e1) set_input() must be idempotent (no state accumulation between calls).
#   (e2) An empty dict must produce empty basic + additional dicts.
#   (e3) Every key in basic_inputs must be a member of _BASIC_INPUT_KEYS.
#   (e4) No key in additional_inputs must be a member of _BASIC_INPUT_KEYS.
# ==============================================================================

def test_plategirderbridge_set_input_idempotent(valid_basic_inputs, valid_additional_inputs):
    """
    Calling set_input() twice with the same dict must yield the same split
    as calling it once — no state accumulates between calls.
    """
    bridge = PlateGirderBridge()
    full = {**valid_basic_inputs, **valid_additional_inputs}

    bridge.set_input(full)
    basic_first = dict(bridge.basic_inputs)
    addl_first  = dict(bridge.additional_inputs)

    bridge.set_input(full)
    assert bridge.basic_inputs      == basic_first, \
        "basic_inputs changed on second set_input() call — state is leaking"
    assert bridge.additional_inputs == addl_first, \
        "additional_inputs changed on second set_input() call — state is leaking"


def test_plategirderbridge_set_input_empty_dict_does_not_crash():
    """set_input({}) must not raise and must leave all split dicts empty."""
    bridge = PlateGirderBridge()
    bridge.set_input({})
    assert bridge.input_dict        == {}
    assert bridge.basic_inputs      == {}
    assert bridge.additional_inputs == {}


def test_plategirderbridge_basic_inputs_only_contains_basic_keys(valid_basic_inputs):
    """
    Every key stored in basic_inputs after set_input() must appear in
    PlateGirderBridge._BASIC_INPUT_KEYS.
    """
    bridge = PlateGirderBridge()
    bridge.set_input(valid_basic_inputs)
    for k in bridge.basic_inputs:
        assert k in PlateGirderBridge._BASIC_INPUT_KEYS, (
            f"Key {k!r} ended up in basic_inputs but is not in _BASIC_INPUT_KEYS"
        )


def test_plategirderbridge_additional_inputs_contains_no_basic_keys(
        valid_basic_inputs, valid_additional_inputs):
    """
    No key in additional_inputs after set_input() should be a member of
    _BASIC_INPUT_KEYS — every basic key must be routed exclusively to
    basic_inputs.
    """
    bridge = PlateGirderBridge()
    full = {**valid_basic_inputs, **valid_additional_inputs}
    bridge.set_input(full)
    for k in bridge.additional_inputs:
        assert k not in PlateGirderBridge._BASIC_INPUT_KEYS, (
            f"Key {k!r} is in additional_inputs but also belongs to _BASIC_INPUT_KEYS"
        )


# ==============================================================================
# GROUP F — FOOTPATH × DEPENDENT-FIELDS EXPANDED MATRIX (Gap #5 + both sides)
#
# The existing 6-case test only covers all-valid combinations.
# This expanded matrix adds boundary-crossing cases so the test documents
# BOTH the passing and failing sides of every rule:
#
#   footpath="None"        → kerb_width >= KEY_SAFETY_KERB_MIN_WIDTH (750 mm)
#   footpath="Single/Both" → footpath_width >= 1.5 m; kerb rule NOT applicable
#   any footpath value     → if railing_height is supplied, must be >= 1100 mm
# ==============================================================================

@pytest.mark.parametrize(
    "footpath, kerb_width, footpath_width, railing_height, expected_status",
    [
        # ── footpath = None: kerb_width and (if supplied) railing checked ─────
        # kerb at exact minimum, no railing supplied → OK
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, None,                          True),
        # kerb above minimum → OK
        ("None", KEY_SAFETY_KERB_MIN_WIDTH + 100, None, None,                          True),
        # kerb OK, footpath_width supplied but not applicable → OK
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       0.0,  None,                          True),
        # kerb OK, railing at exact minimum → OK
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, KEY_RAILING_MIN_HEIGHT[0],     True),
        # kerb OK, railing one above minimum → OK
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, KEY_RAILING_MIN_HEIGHT[0] + 1, True),
        # kerb one below minimum → FAIL
        ("None", KEY_SAFETY_KERB_MIN_WIDTH - 1,   None, 1200,                          False),
        # kerb OK, railing one below minimum → FAIL
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, KEY_RAILING_MIN_HEIGHT[0] - 1, False),
        # both kerb and railing invalid → FAIL (both errors collected)
        ("None", KEY_SAFETY_KERB_MIN_WIDTH - 1,   None, KEY_RAILING_MIN_HEIGHT[0] - 1, False),

        # ── footpath = Single Side: footpath_width + railing apply ────────────
        # all at exact minimums → OK
        ("Single Side", 0, 1.5,  KEY_RAILING_MIN_HEIGHT[0],      True),
        # railing comfortably above minimum → OK
        ("Single Side", 0, 1.5,  KEY_RAILING_MIN_HEIGHT[0] + 50, True),
        # wider footpath, higher railing → OK
        ("Single Side", 0, 2.0,  1200,                            True),
        ("Single Side", 0, 3.0,  1500,                            True),
        # railing one below minimum → FAIL
        ("Single Side", 0, 1.5,  KEY_RAILING_MIN_HEIGHT[0] - 1,  False),
        # footpath_width one tenth below minimum → FAIL
        ("Single Side", 0, 1.4,  1200,                            False),
        # both footpath_width and railing below minimum → FAIL
        ("Single Side", 0, 0.5,  KEY_RAILING_MIN_HEIGHT[0] - 1,  False),

        # ── footpath = Both Sides: same rules as Single Side ─────────────────
        ("Both Sides", 0, 1.5,  KEY_RAILING_MIN_HEIGHT[0],      True),
        ("Both Sides", 0, 2.5,  1300,                            True),
        ("Both Sides", 0, 5.0,  2000,                            True),
        # footpath_width just below minimum → FAIL
        ("Both Sides", 0, 1.49, 1200,                            False),
        # railing just below minimum → FAIL
        ("Both Sides", 0, 1.5,  KEY_RAILING_MIN_HEIGHT[0] - 1,  False),
    ],
)
def test_validate_additional_inputs_footpath_combinations_expanded(
        validator, valid_additional_inputs,
        footpath, kerb_width, footpath_width, railing_height, expected_status):
    """
    Expanded parametrized matrix: every footpath option (None / Single Side /
    Both Sides) crossed with edge-case values of kerb_width, footpath_width,
    and railing_height.  Both the valid and invalid sides of each boundary are
    included so the test fully documents which combinations pass and which fail.
    """
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH]     = footpath
    inputs["kerb_width"]     = kerb_width
    inputs["footpath_width"] = footpath_width
    inputs["railing_height"] = railing_height

    res = validator.validate_additional_inputs(inputs)
    assert res["status"] is expected_status, (
        f"footpath={footpath!r}, kerb={kerb_width}, "
        f"fp_width={footpath_width}, railing={railing_height} → "
        f"expected status={expected_status}, got status={res['status']}, "
        f"errors={res.get('errors')}"
    )


# ==============================================================================
# GROUP G — VALIDATOR RETURN VALUE STRUCTURES (Gap #2 & #3 extended)
#
# Asserts the return structure and content:
#   - validate_basic_inputs returns (corrected_value, non-empty error message)
#   - validate_additional_inputs returns non-empty string errors
# ==============================================================================

def test_validate_basic_inputs_span_error_return_structure(validator):
    res = validator.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: SPAN_MIN - 1})
    assert res is not None
    assert res[0] == SPAN_MIN          # corrected value is the boundary constant
    assert isinstance(res[1], str)
    assert len(res[1]) > 0

def test_validate_basic_inputs_carriageway_error_return_structure(validator):
    res = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
          {KEY_CARRIAGEWAY_WIDTH: CARRIAGEWAY_WIDTH_MIN - 1, KEY_INCLUDE_MEDIAN: "No"})
    assert res is not None
    assert res[0] == CARRIAGEWAY_WIDTH_MIN
    assert isinstance(res[1], str)
    assert len(res[1]) > 0

def test_validate_basic_inputs_skew_angle_error_return_structure(validator):
    res = validator.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: SKEW_ANGLE_MAX + 1})
    assert res is not None
    assert res[0] == SKEW_ANGLE_MAX
    assert isinstance(res[1], str)
    assert len(res[1]) > 0

def test_validate_additional_inputs_error_messages_are_nonempty_strings(validator, valid_additional_inputs):
    inputs = valid_additional_inputs.copy()
    inputs["stud_height"] = MIN_STUD_HEIGHT_MM - 10
    inputs["stud_edge_distance"] = MIN_EDGE_DISTANCE_MM - 5
    res = validator.validate_additional_inputs(inputs)
    assert res["status"] is False
    for key, msg in res["errors"].items():
        assert isinstance(msg, str), f"Error for {key!r} must be a string"
        assert len(msg) > 0, f"Error message for {key!r} must be non-empty"

