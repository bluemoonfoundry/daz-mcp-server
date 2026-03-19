# vangard-daz-mcp

[![Security Scan](https://img.shields.io/endpoint?url=https://mcpampel.com/badge/bluemoonfoundry/vangard-daz-mcp.json)](https://mcpampel.com/repo/bluemoonfoundry/vangard-daz-mcp)

MCP server wrapping the [DazScriptServer](https://github.com/bluemoonfoundry/vangard-daz-script-server) HTTP plugin for DAZ Studio.

## Tools

| Tool | Description |
|------|-------------|
| `daz_status` | Check DAZ Studio connectivity and version |
| `daz_execute` | Execute inline DazScript (JavaScript) code |
| `daz_execute_file` | Execute a `.dsa`/`.ds` script file on the DAZ Studio machine |

## Configuration

Set environment variables to override defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `DAZ_HOST` | `localhost` | DazScriptServer hostname |
| `DAZ_PORT` | `18811` | DazScriptServer port |
| `DAZ_TIMEOUT` | `30.0` | Request timeout in seconds |

## Usage

```bash
uv run vangard-daz-mcp
```

Or install and run:

```bash
uv pip install .
vangard-daz-mcp
```
