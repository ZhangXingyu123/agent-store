# Feishu Connector

This plugin adds an agent skill and MCP configuration for the official Feishu/Lark OpenAPI MCP server.

Before using it, create a Feishu/Lark app and set:

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

For user OAuth mode:

```bash
export FEISHU_MCP_EXTRA_ARGS="--oauth --token-mode user_access_token"
```

Then install the plugin from `Agent Store` in the host agent and ask your agent to use `feishu-connector`.
