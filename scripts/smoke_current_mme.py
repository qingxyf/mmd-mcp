"""Opt-in MME roundtrip on an explicitly selected EXISTING MMD, without launching MMD.

Exports a backup, writes a separate same-assignment EMM through MCP, imports it,
and re-exports to compare. Does not load PMM, seek frames, or modify model keys.
"""
import argparse
import asyncio
import base64
import json
import sys
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(hwnd, morph_model_index=None):
    output = Path(__file__).resolve().parents[1] / "local" / f"current-mme-smoke-{datetime.now():%Y%m%d-%H%M%S}"
    output.mkdir(parents=True)
    report = {"hwnd": hwnd, "steps": [], "output": str(output)}
    try:
        params = StdioServerParameters(command=sys.executable, args=["-m", "mmd_mcp.server"])
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()

                async def call(name, *, live=True, **arguments):
                    response = await session.call_tool(name, {**({"hwnd": hwnd} if live else {}), **arguments})
                    assert not response.isError, (name, response)
                    result = response.structuredContent
                    assert result is not None, (name, response)
                    assert result.get("status", "completed") == "completed", (name, result)
                    report["steps"].append({"tool": name, "result": result})
                    print(f"OK {name}", flush=True)
                    return result

                before = await call("mmd_get_ui_state")
                settings_before = await call("mmd_get_scene_settings")
                baseline = await call("mmd_transfer_effect_assignments", operation="export", path=str(output / "before.emm"))
                assignments = baseline["assignments"]
                encoding = baseline["encoding"]
                assert assignments["objects"], "No objects available for a same-scene import"
                assert all(Path(p).is_file() for p in assignments["objects"].values()), "Decoded object paths must resolve"
                await call("mmd_read_effect_assignments", live=False, emm_path=str(output / "before.emm"), encoding=encoding)
                same = assignments["effect_sections"]["Effect"]["assignments"]
                assert same, "No explicit Main assignments available"
                key = next(iter(same))
                await call("mmd_write_effect_assignments", live=False, emm_path=str(output / "before.emm"),
                           output_path=str(output / "same-assignments.emm"), assignments={key: same[key]}, encoding=encoding)
                assert (output / "before.emm").read_bytes() == (output / "same-assignments.emm").read_bytes()
                await call("mmd_transfer_effect_assignments", operation="import", path=str(output / "same-assignments.emm"), encoding=encoding)
                after = await call("mmd_transfer_effect_assignments", operation="export", path=str(output / "after.emm"))
                assert after["assignments"]["objects"] == assignments["objects"]
                assert after["assignments"]["effect_sections"] == assignments["effect_sections"]
                if morph_model_index is not None:
                    try:
                        await call("mmd_select_model", selector_index=morph_model_index)
                        model = await call("mmd_get_ui_state")
                        category, panel = next((category, panel) for category, panel in model["morph_panels"].items()
                            if panel and panel["selected_name"] is not None and panel["displayed_weight"] is not None)
                        # Reapply the displayed value only, with no key registration
                        # and no frame evaluation on this morph-only path.
                        adjusted = await call("mmd_batch_bone_keys", items=[{
                            "frame": model["displayed_frame"]["value"], "register_key": False,
                            "morphs": [{"category": category, "name": panel["selected_name"],
                                        "weight": float(panel["displayed_weight"])}]}])
                        assert adjusted["bone_keys"] == 0
                        report["morph_ui_verified"] = True
                    finally:
                        await call("mmd_select_model", selector_index=before["model_selector"]["selected_index"])
                final = await call("mmd_get_ui_state")
                settings_final = await call("mmd_get_scene_settings")
                for field in ("displayed_frame", "model_selector"):
                    assert final[field] == before[field], field
                assert settings_before["settings"] == settings_final["settings"]
                response = await session.call_tool("mmd_capture_window", {"hwnd": hwnd})
                assert not response.isError, response
                png = next(block for block in response.content if block.type == "image")
                (output / "current.png").write_bytes(base64.b64decode(png.data))
                report["status"] = "passed"
                report["encoding"] = encoding
                print(f"PASS current MMD MME roundtrip: {output}", flush=True)
    finally:
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--hwnd", type=int, required=True)
    parser.add_argument("--morph-model-index", type=int,
                        help="Also reapply one existing morph's displayed weight without keying it")
    args = parser.parse_args()
    asyncio.run(check(args.hwnd, args.morph_model_index))
