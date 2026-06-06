import re
from collections import defaultdict

_bridge_results = []   # module-level list, reset each run


def pytest_configure(config):
    global _bridge_results
    _bridge_results = []


def pytest_runtest_logreport(report):
    if report.when != "call":
        return

    node = report.nodeid
    match = re.match(r"^(.*?)\[(.+)\]$", node)
    test_name  = match.group(1).split("::")[-1] if match else node.split("::")[-1]
    param_repr = match.group(2)                  if match else ""

    failure_reason = ""
    if report.failed:
        lines = [ln.strip() for ln in str(report.longrepr).splitlines() if ln.strip()]
        for ln in reversed(lines):
            if "AssertionError" in ln or "assert " in ln:
                failure_reason = ln[:200]
                break
        if not failure_reason and lines:
            failure_reason = lines[-1][:200]

    _bridge_results.append({
        "test_name": test_name,
        "params":    param_repr,
        "status":    report.outcome,
        "reason":    failure_reason,
    })


# ── Human-readable format description shown once per group ──────────────────
HEADERS = {
    "test_validate_span": (
        "span=<metres, float>  |  "
        "expect=VALID means validator must accept it, INVALID means it must reject it"
    ),
    "test_validate_carriageway_width": (
        "median=<Yes/No>  |  lanes=<int>  |  width=<metres, float>  |  "
        "expect=VALID/INVALID"
    ),
    "test_validate_skew_angle": (
        "angle=<degrees, float — valid range is SKEW_ANGLE_MIN..SKEW_ANGLE_MAX>  |  "
        "expect=VALID means accepted, INVALID means rejected"
    ),
    "test_validate_layout_equation": (
        "overall_w=<m>  |  girders=<count>  |  spacing=<m>  |  overhang=<m>  |  "
        "expect=OK means no layout_equation error, ERROR means layout_equation error raised"
    ),
    "test_validate_kerb_width": (
        "footpath=<None / Single Side / Both Sides>  |  kerb=<mm>  |  "
        "expect=OK means no kerb_width error, ERROR means kerb_width error raised  "
        "(rule: when footpath=None, kerb >= KEY_SAFETY_KERB_MIN_WIDTH)"
    ),
    "test_validate_footpath_width": (
        "footpath=<None / Single Side / Both Sides>  |  width=<metres>  |  "
        "expect=OK means no footpath_width error, ERROR means error raised  "
        "(rule: when footpath provided, width >= 1.5 m)"
    ),
    "test_validate_railing_height": (
        "footpath=<None / Single Side / Both Sides>  |  height=<mm>  |  "
        "expect=OK means no railing_height error, ERROR means error raised  "
        "(rule: when footpath provided, height >= KEY_RAILING_MIN_HEIGHT[0])"
    ),
    "test_validate_stud_height": (
        "stud_height=<mm>  |  "
        "expect=OK means no stud_height error, ERROR means error raised  "
        "(rule: stud_height >= MIN_STUD_HEIGHT_MM)"
    ),
    "test_validate_stud_diameter": (
        "stud_dia=<mm>  |  flange_t=<mm>  |  "
        "expect=OK means no stud_diameter error, ERROR means error raised  "
        "(rule: stud_dia <= MAX_STUD_DIAMETER_FACTOR * flange_t)"
    ),
    "test_validate_stud_edge_distance": (
        "edge_dist=<mm>  |  "
        "expect=OK means no stud_edge_distance error, ERROR means error raised  "
        "(rule: edge_dist >= MIN_EDGE_DISTANCE_MM)"
    ),
    "test_validate_additional_inputs_all_valid_combinations": (
        "footpath=<None/Single Side/Both Sides>  |  kerb=<mm>  |  "
        "fp_width=<m or None>  |  railing=<mm>  |  expect=OK"
    ),
    "test_cross_field_span_carriageway_interaction": (
        "span=<m>  |  cw=<m>  |  median=<Yes/No>  |  "
        "span_err=<True/False>  |  cw_err=<True/False>"
    ),
    "test_carriageway_median_cross_field": (
        "cw_width=<m>  |  median=<Yes/No>  |  expect=VALID/INVALID"
    ),
    "test_validate_additional_inputs_footpath_combinations_expanded": (
        "footpath=<None/Single Side/Both Sides>  |  kerb=<mm>  |  "
        "fp_width=<m or None>  |  railing=<mm>  |  expect=OK/FAIL"
    ),
}


def _fmt(test_name: str, raw: str) -> str:
    """Convert raw pytest param-id string into a labelled, human-readable line."""
    parts = raw.split("-")

    def _clean(v: str) -> str:
        return re.sub(r"\d+$", "", v).lower()

    def _bool(v: str) -> str:   # True/False → VALID/INVALID
        return "VALID" if _clean(v) == "true" else "INVALID"

    def _err(v: str) -> str:    # True/False → ERROR/OK
        return "ERROR" if _clean(v) == "true" else "OK"

    def _unit(v: str, unit: str) -> str:
        clean_val = str(v).strip()
        if clean_val.lower() in ("none", "null"):
            return "None"
        return f"{clean_val}{unit}"

    try:
        def _span_reason(val_str: str) -> str:
            if val_str.startswith("value") or val_str in ("None", "", "abc", "(type-error: list)", "(type-error: dict)"):
                return " (type error)"
            try:
                val = float(val_str)
                if val < 20.0:
                    return " (span < 20.0)"
                if val > 45.0:
                    return " (span > 45.0)"
            except ValueError:
                return " (type error)"
            return ""

        def _cw_reason(median: str, width_str: str) -> str:
            if width_str in ("None", "", "abc") or "value" in width_str:
                return " (type error)"
            try:
                w = float(width_str)
                if w > 23.6:
                    return " (width > 23.6)"
                if median == "Yes" and w < 7.5:
                    return " (width < 7.5 with median)"
                if median == "No" and w < 4.25:
                    return " (width < 4.25 without median)"
            except ValueError:
                return " (type error)"
            return ""

        def _skew_reason(val_str: str) -> str:
            if val_str in ("None", "", "abc") or "value" in val_str:
                return " (type error)"
            try:
                val = float(val_str)
                if val < -15.0:
                    return " (angle < -15.0)"
                if val > 15.0:
                    return " (angle > 15.0)"
            except ValueError:
                return " (type error)"
            return ""

        if test_name == "test_validate_span":
            # format: <value>-<True/False>   (value may be negative)
            val = "-".join(parts[:-1])
            is_valid = _clean(parts[-1]) == "true"
            exp = "VALID" if is_valid else "INVALID"
            if not is_valid:
                exp += _span_reason(val)
            if val == "value70":
                val = "(type-error: list)"
            elif val == "value71":
                val = "(type-error: dict)"
            return f"span={val}  |  expect={exp}"

        if test_name == "test_validate_carriageway_width":
            # format: <median>-<lanes>-<width>-<True/False>
            if len(parts) >= 4:
                median = parts[0]
                lanes  = parts[1]
                width  = "-".join(parts[2:-1])
                is_valid = _clean(parts[-1]) == "true"
                exp = "VALID" if is_valid else "INVALID"
                if not is_valid:
                    exp += _cw_reason(median, width)
                return (f"median={median}  |  lanes={lanes}  |  "
                        f"width={width}m  |  expect={exp}")

        if test_name == "test_validate_skew_angle":
            # format: <value>-<True/False>   (value may be negative)
            val = "-".join(parts[:-1])
            is_valid = _clean(parts[-1]) == "true"
            exp = "VALID" if is_valid else "INVALID"
            if not is_valid:
                exp += _skew_reason(val)
            return f"angle={val}°  |  expect={exp}"

        if test_name == "test_validate_layout_equation":
            # format: <overall_w>-<girders>-<spacing>-<overhang>-<True/False>
            if len(parts) == 5:
                ow, g, sp, oh, err_raw = parts
                exp = _err(err_raw)
                if _clean(err_raw) == "true":
                    exp += " (overall_w != (girders-1)*spacing + 2*overhang)"
                return (f"overall_w={ow}m  |  girders={g}  |  "
                        f"spacing={sp}m  |  overhang={oh}m  |  expect={exp}")

        if test_name in (
            "test_validate_kerb_width",
            "test_validate_footpath_width",
            "test_validate_railing_height",
        ):
            # format: <footpath>-<value>-<True/False>
            if len(parts) == 3:
                footpath, val, err_raw = parts
                exp = _err(err_raw)
                if _clean(err_raw) == "true":
                    if test_name == "test_validate_kerb_width":
                        exp += " (kerb < 750)"
                    elif test_name == "test_validate_footpath_width":
                        exp += " (width < 1.5 or None)"
                    elif test_name == "test_validate_railing_height":
                        exp += " (height < 1100)"
                if test_name == "test_validate_kerb_width":
                    return f"footpath={footpath}  |  kerb={_unit(val, 'mm')}  |  expect={exp}"
                if test_name == "test_validate_footpath_width":
                    return f"footpath={footpath}  |  width={_unit(val, 'm')}  |  expect={exp}"
                # railing
                return f"footpath={footpath}  |  height={_unit(val, 'mm')}  |  expect={exp}"

        if test_name == "test_validate_stud_height":
            # format: <value>-<True/False>   (value may be negative)
            val = "-".join(parts[:-1])
            exp = _err(parts[-1])
            if _clean(parts[-1]) == "true":
                exp += " (height < 100)"
            return f"stud_height={_unit(val, 'mm')}  |  expect={exp}"

        if test_name == "test_validate_stud_diameter":
            # format: <stud_d>-<flange_t>-<True/False>
            if len(parts) == 3:
                stud_d, flange_t, err_raw = parts
                exp = _err(err_raw)
                if _clean(err_raw) == "true":
                    exp += " (stud_dia > 2 * flange_t)"
                return (f"stud_dia={_unit(stud_d, 'mm')}  |  flange_t={_unit(flange_t, 'mm')}  |  "
                        f"expect={exp}")

        if test_name == "test_validate_stud_edge_distance":
            # format: <value>-<True/False>   (value may be negative)
            val = "-".join(parts[:-1])
            exp = _err(parts[-1])
            if _clean(parts[-1]) == "true":
                exp += " (edge_dist < 25)"
            return f"edge_dist={_unit(val, 'mm')}  |  expect={exp}"

        if test_name == "test_validate_additional_inputs_all_valid_combinations":
            # format: footpath-kerb-fp_width-railing
            if len(parts) >= 4:
                return (f"footpath={parts[0]}  |  kerb={_unit(parts[1], 'mm')}  |  "
                        f"fp_width={_unit(parts[2], 'm')}  |  railing={_unit(parts[3], 'mm')}  |  expect=OK")

        if test_name == "test_validate_additional_inputs_footpath_combinations_expanded":
            # format: footpath-kerb-fp_width-railing-expected_status
            if len(parts) >= 5:
                footpath = parts[0]
                kerb_str = parts[1]
                fp_width_str = parts[2]
                railing_str = parts[3]
                
                # Parse numeric values
                def to_val(s):
                    if s.strip().lower() in ("none", "null", ""):
                        return None
                    try:
                        return float(s)
                    except ValueError:
                        return None
                
                kerb = to_val(kerb_str)
                fp_width = to_val(fp_width_str)
                railing = to_val(railing_str)
                
                invalid_fields = []
                if footpath == "None":
                    if kerb is not None and kerb < 750:
                        invalid_fields.append("kerb")
                    if railing is not None and railing < 1100:
                        invalid_fields.append("railing")
                else:
                    if fp_width is not None and fp_width < 1.5:
                        invalid_fields.append("fp_width")
                    if railing is not None and railing < 1100:
                        invalid_fields.append("railing")
                
                exp_status = _clean(parts[-1]) == "true"
                exp = "OK" if exp_status else "FAIL"
                if not exp_status and invalid_fields:
                    exp += f" (invalid: {', '.join(invalid_fields)})"
                
                return (f"footpath={footpath}  |  kerb={_unit(kerb_str, 'mm')}  |  "
                        f"fp_width={_unit(fp_width_str, 'm')}  |  railing={_unit(railing_str, 'mm')}  |  expect={exp}")

        if test_name == "test_cross_field_span_carriageway_interaction":
            # format: span-cw-median-span_err-cw_err
            if len(parts) >= 5:
                return (f"span={parts[0]}m  |  cw={parts[1]}m  |  median={parts[2]}  |  "
                        f"span_err={parts[3]}  |  cw_err={parts[4]}")

        if test_name == "test_carriageway_median_cross_field":
            # format: cw_width-median-expect_error
            if len(parts) >= 3:
                exp = "INVALID" if _clean(parts[-1]) == "true" else "VALID"
                return (f"cw_width={parts[0]}m  |  median={parts[1]}  |  "
                        f"expect={exp}")

    except Exception:
        pass

    return raw   # fallback: show raw param string unchanged


# ── Terminal summary hook ────────────────────────────────────────────────────
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _bridge_results:
        return

    groups = defaultdict(list)
    for r in _bridge_results:
        groups[r["test_name"]].append(r)

    total_all  = len(_bridge_results)
    passed_all = sum(1 for r in _bridge_results if r["status"] == "passed")
    failed_all = total_all - passed_all

    terminalreporter.write_sep("=", "Detailed Test Summary (per value)")

    for test_name, entries in groups.items():
        grp_passed = [e for e in entries if e["status"] == "passed"]
        grp_failed = [e for e in entries if e["status"] == "failed"]

        if not grp_failed:
            status_label = f"  ALL PASS ({len(grp_passed)}/{len(entries)})"
        else:
            status_label = f"  FAIL  {len(grp_failed)} failed / {len(entries)} total"

        terminalreporter.write_line(f"\n{test_name}{status_label}")
        terminalreporter.write_line("  " + "-" * 70)

        # Print the human-readable format description for this group
        if test_name in HEADERS:
            terminalreporter.write_line(f"  FORMAT: {HEADERS[test_name]}")
            terminalreporter.write_line("  " + "-" * 70)

        for e in entries:
            icon   = "PASS" if e["status"] == "passed" else "FAIL"
            params = _fmt(test_name, e["params"]) if e["params"] else "(no params)"
            line   = f"  [{icon}]  {params}"
            if e["reason"]:
                line += f"\n         -> {e['reason']}"
            terminalreporter.write_line(line)

    terminalreporter.write_sep("=", "End of Detailed Summary")
    terminalreporter.write_line("============================================================")
    terminalreporter.write_line(f"  TOTAL: {total_all}   PASSED: {passed_all}   FAILED: {failed_all}")
    terminalreporter.write_line("============================================================")
