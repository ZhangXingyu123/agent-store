---
name: feishu-connector
description: Use when the user wants Codex to work with Feishu or Lark documents, messages, calendars, contacts, groups, tasks, bitables, or Open Platform APIs through the official Feishu/Lark OpenAPI MCP server. Trigger on 飞书, Lark, Feishu, 飞书文档, 飞书群, 多维表格, 日历, 会议, IM, bitable, and approval workflow requests.
---

# Feishu Connector

Use this skill to connect Codex to Feishu/Lark through the official `@larksuiteoapi/lark-mcp` MCP server.

## Required setup

The user must create a Feishu/Lark app and provide credentials through environment variables:

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

Optional extra MCP flags can be passed with:

```bash
export FEISHU_MCP_EXTRA_ARGS="--oauth --token-mode user_access_token"
```

For Lark international tenants, set:

```bash
export FEISHU_MCP_EXTRA_ARGS="--domain https://open.larksuite.com"
```

## Use cases

- Search or summarize Feishu/Lark documents.
- Draft or send Feishu/Lark group messages after user confirmation.
- Read calendar context and help schedule meetings.
- Read or write allowed bitable records.
- Find Feishu Open Platform API docs for integration work.

## Safety rules

1. Ask the user which Feishu/Lark resources and scopes are needed before requesting broad permissions.
2. Never send messages, write bitable records, create calendar events, or modify documents without a clear preview and explicit confirmation.
3. Prefer read-only operations unless the user explicitly asks for a write action.
4. Do not store or print `FEISHU_APP_SECRET`.
5. If MCP credentials are missing, explain the required environment variables instead of guessing.

## Workflow

1. Identify whether the task is read-only or write/action-taking.
2. Check whether the `lark-mcp` MCP server is available.
3. If not available, run `scripts/check_feishu_setup.py` from the plugin root to explain missing setup.
4. Use MCP tools for Feishu/Lark operations.
5. For write actions, show a concise preview and wait for explicit confirmation.

