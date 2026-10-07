#!/usr/bin/env python3
"""Preflight the design sheets, then generate the Lua mod from them.

  python3 -I tools/build.py preflight   # list unfilled cells, broken references, unverified and unbuilt rows
  python3 -I tools/build.py generate    # preflight, then write reframework/autorun/*.lua (only if clean)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NA = "n/a"

# Columns a row of each kind must really fill (not "n/a") before it can be built.
KIND_REQUIRES = {
    "rage": ["hp_threshold_pct", "damage_mult", "chip_taken_reduction_pct"],
    "heat": ["damage_mult", "duration_ticks", "uses_per_round", "pause_while_opponent_in_hitstun", "chip_pct_of_max",
             "chip_can_ko", "recover_pct_of_max_per_landed_attack", "hit_trims_recoverable_pct", "heat_start_heals_pct_of_pool", "key_p1", "key_p2"],
    "heat_smash": ["armed_ticks", "bonus_pct_of_max"],
    "rage_art": ["armed_ticks", "bonus_pct_of_max", "uses_per_round", "key_p1", "key_p2"],
    "slowmo_fx": ["fx_speed_scale", "fx_frames", "fx_method"],
    "juggle_scaling": [],
    "hitstop_research": [],
}
# Hooks a kind writes to: the hook row must allow writing.
KIND_WRITES = {"rage": ["hp_now"], "heat": ["hp_now"], "heat_smash": ["hp_now"], "rage_art": ["hp_now"], "slowmo_fx": ["global_speed", "scene_time_scale", "max_fps"], "juggle_scaling": [], "hitstop_research": []}
STATUS_BUILT = "implemented"


def load(name):
    return json.loads((ROOT / "sheets" / f"{name}.json").read_text())


def blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "") or (isinstance(v, list) and len(v) == 0)


def preflight(hooks, mechs):
    errors, unverified, unbuilt = [], [], []
    hook_ids = {}

    for sheet_name, sheet in (("hooks", hooks), ("mechanics", mechs)):
        cols = sheet["columns"]
        seen = set()
        for row in sheet["rows"]:
            rid = row.get("id", "<no id>")
            if rid in seen:
                errors.append(f"{sheet_name}: duplicate id '{rid}'")
            seen.add(rid)
            extra = set(row) - set(cols)
            if extra:
                errors.append(f"{sheet_name}.{rid}: columns not in the sheet header: {sorted(extra)}")
            for c in cols:
                if c not in row or blank(row[c]):
                    errors.append(f"{sheet_name}.{rid}.{c}: unfilled cell")
    for row in hooks["rows"]:
        hook_ids[row["id"]] = row
        if row.get("kind") not in ("field", "api"):
            errors.append(f"hooks.{row['id']}.kind: must be 'field' or 'api'")
        if row.get("access") not in ("r", "w", "rw"):
            errors.append(f"hooks.{row['id']}.access: must be 'r', 'w' or 'rw'")

    used = set()
    for row in mechs["rows"]:
        rid = row["id"]
        kind = row.get("kind")
        if kind not in KIND_REQUIRES:
            errors.append(f"mechanics.{rid}.kind: unknown kind '{kind}'")
            continue
        if row.get("status") == STATUS_BUILT:
            for c in KIND_REQUIRES[kind]:
                if row.get(c) == NA:
                    errors.append(f"mechanics.{rid}.{c}: is 'n/a' but a built '{kind}' row needs a value")
        for hid in row.get("uses_hooks", []):
            used.add(hid)
            if hid not in hook_ids:
                errors.append(f"mechanics.{rid}.uses_hooks: '{hid}' does not exist in the hooks sheet")
        if kind == "slowmo_fx" and row.get("fx_method") not in hook_ids:
            errors.append(f"mechanics.{rid}.fx_method: '{row.get('fx_method')}' is not a hook in the hooks sheet")
        for hid in KIND_WRITES[kind]:
            if hid not in row.get("uses_hooks", []):
                errors.append(f"mechanics.{rid}: writes '{hid}' but does not list it in uses_hooks")
            elif hid in hook_ids and "w" not in hook_ids[hid].get("access", ""):
                errors.append(f"mechanics.{rid}: writes '{hid}' but that hook is read-only")
        if row.get("status") != STATUS_BUILT:
            unbuilt.append(f"mechanics.{rid} (status: {row.get('status')})")
        if row.get("verified") is not True:
            unverified.append(f"mechanics.{rid}")

    for hid, row in hook_ids.items():
        if hid not in used:
            errors.append(f"hooks.{hid}: no mechanics row uses it")
        if row.get("read_verified") not in (True, "n/a"):
            unverified.append(f"hooks.{hid} (read)")
        if "w" in row.get("access", "") and row.get("write_verified") is not True:
            unverified.append(f"hooks.{hid} (write)")
    return errors, unverified, unbuilt


def lua_value(v, indent=0):
    pad = "  " * indent
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=True)
    if isinstance(v, list):
        if not v:
            return "{}"
        inner = ",\n".join("  " * (indent + 1) + lua_value(x, indent + 1) for x in v)
        return "{\n" + inner + "\n" + pad + "}"
    if isinstance(v, dict):
        inner = ",\n".join(
            "  " * (indent + 1) + "[" + json.dumps(k) + "] = " + lua_value(x, indent + 1) for k, x in v.items()
        )
        return "{\n" + inner + "\n" + pad + "}"
    raise TypeError(f"cannot write {v!r} as Lua")


def generate(hooks, mechs):
    out_dir = ROOT / "reframework" / "autorun"
    out_dir.mkdir(parents=True, exist_ok=True)

    built = [r for r in mechs["rows"] if r["status"] == STATUS_BUILT]
    rows_lua = "local ROWS = " + lua_value({"mechanics": built, "hooks": hooks["rows"]})
    engine = (ROOT / "src" / "engine.lua.tpl").read_text().replace("--@@ROWS@@", rows_lua)
    (out_dir / "sf6_tekken_mode.lua").write_text(engine)

    probe_hooks = "local HOOKS = " + lua_value(hooks["rows"])
    probe = (ROOT / "src" / "probe.lua.tpl").read_text().replace("--@@HOOKS@@", probe_hooks)
    (out_dir / "sf6_tekken_probe.lua").write_text(probe)
    return [out_dir / "sf6_tekken_mode.lua", out_dir / "sf6_tekken_probe.lua"]


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preflight"
    hooks, mechs = load("hooks"), load("mechanics")
    errors, unverified, unbuilt = preflight(hooks, mechs)

    print(f"PREFLIGHT: {len(errors)} problem(s)")
    for e in errors:
        print("  FAIL ", e)
    if unbuilt:
        print(f"Not built yet ({len(unbuilt)}):")
        for u in unbuilt:
            print("  TODO ", u)
    print(f"Unverified in the real game ({len(unverified)}):")
    for u in unverified:
        print("  CHECK", u)

    if errors:
        print("Not building: fix the sheets first.")
        return 1
    if cmd == "generate":
        for p in generate(hooks, mechs):
            print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
