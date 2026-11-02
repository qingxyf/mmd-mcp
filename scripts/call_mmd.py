"""Call a source checkout's stdio MCP server without changing client configuration."""
import argparse
import asyncio
import base64
import json
import sys
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def invoke(tool, arguments, output_dir=None):
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "mmd_mcp.server"])
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            if tool == "list-tools":
                result = await session.list_tools()
                return {"tools": [entry.model_dump(mode="json") for entry in result.tools]}, False
            response = await session.call_tool(tool, arguments)
            result = {"is_error": bool(response.isError), "result": response.structuredContent}
            if response.structuredContent is None:
                result["text"] = [entry.text for entry in response.content if entry.type == "text"]
            images = [entry for entry in response.content if entry.type == "image"]
            if images:
                destination = output_dir or (Path(__file__).resolve().parents[1] / "local" / "captures" /
                                             datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
                destination.mkdir(parents=True, exist_ok=True)
                result["images"] = []
                for index, entry in enumerate(images):
                    if entry.mimeType != "image/png":
                        raise ValueError(f"Unexpected capture type: {entry.mimeType}")
                    path = destination / f"capture-{index}.png"
                    with path.open("xb") as stream:
                        stream.write(base64.b64decode(entry.data, validate=True))
                    result["images"].append(str(path.resolve()))
            return result, bool(response.isError)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", help="MCP tool name, or list-tools for current schemas")
    parser.add_argument("--arguments", type=Path, help="UTF-8 JSON object containing tool arguments")
    parser.add_argument("--output-dir", type=Path, help="Directory for PNG responses")
    args = parser.parse_args()
    arguments = json.loads(args.arguments.read_text(encoding="utf-8-sig")) if args.arguments else {}
    if not isinstance(arguments, dict):
        parser.error("--arguments must contain a JSON object")
    result, failed = asyncio.run(invoke(args.tool, arguments, args.output_dir))
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failed else 0)
