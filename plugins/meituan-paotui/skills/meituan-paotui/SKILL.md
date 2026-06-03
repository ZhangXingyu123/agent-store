---
name: meituan-paotui
description: Use when the user asks about Meituan Paotui runner-service tasks such as 跑腿, 美团跑腿, 同城配送, 帮取, 帮送, 帮买, 取号, 排队, 帮搬, 帮扔, or similar local errand workflows. This adapter does not handle ordinary food ordering or Meituan Waimai unless an authorized upstream food-ordering skill is provided.
---

# Meituan Paotui

This is a store adapter for the official Meituan Paotui Skill source:

- GitHub: `https://github.com/meituan/MT-Paotui-For-Client`
- ClawHub: `https://clawhub.ai/meituan-tech/mt-paotui-for-client`

The current adapter intentionally does not redistribute the upstream code. The upstream repository is public, but this store should only bundle the full upstream skill after the license or explicit authorization permits redistribution.

## What this adapter can do

- Explain how to install or verify the official Meituan Paotui Skill source.
- Route runner-service requests to the official source when it is installed locally.
- Enforce safety rules before any real-world order action.
- Prevent confusion with normal food-ordering skills.

## What this adapter cannot do

- It cannot place orders by itself.
- It cannot bypass Meituan account authorization.
- It cannot handle ordinary food delivery ordering unless an authorized Meituan Waimai or restaurant-ordering skill is provided.

## Safety rules

1. Treat runner-service requests as real spending and potentially irreversible.
2. Always show a preview before submission.
3. Require explicit user confirmation before any action that submits an order or spends money.
4. If estimated cost exceeds 100 CNY, ask for an additional confirmation.
5. Never expose tokens or private authorization URLs in logs.
6. If upstream source or authorization is missing, stop and explain what is missing.

## Workflow

1. Classify the request as runner-service, help-buy, queue/ticket-taking, or other local errand.
2. If the user asks for food delivery ordering, explain that this adapter is for Paotui, not Meituan Waimai ordering.
3. Run `scripts/check_meituan_upstream.py` from the plugin root to check whether the official source appears reachable.
4. If the official source is installed locally and authorized, use its documented workflow.
5. Before submission, show the service type, addresses, item/request, estimated fee, and expected time.
6. Wait for explicit confirmation.

