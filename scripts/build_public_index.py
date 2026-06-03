#!/usr/bin/env python3
"""Build public discovery artifacts for the Codex plugin marketplace."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from marketplace_lib import build_public_catalog, write_json
from validate_marketplace import validate_marketplace


def render_badge(text: str, class_name: str) -> str:
    return f'<span class="badge {class_name}">{html.escape(text)}</span>'


def render_plugin(plugin: dict) -> str:
    pricing = plugin["pricing"]
    governance = plugin["governance"]
    verification = plugin["verification"]
    distribution = plugin["distribution"]
    capabilities = "".join(f"<li>{html.escape(item)}</li>" for item in plugin.get("capabilities", []))
    price = "Free"
    if pricing["model"] == "one_time":
        price = f"{pricing.get('currency', 'USD')} {pricing.get('priceCents', 0) / 100:.2f}"
    elif pricing["model"] == "subscription":
        price = f"{pricing.get('currency', 'USD')} {pricing.get('priceCents', 0) / 100:.2f} / period"
    elif pricing["model"] == "usage":
        price = "Usage based"
    elif pricing["model"] == "external":
        price = "External"

    install_command = distribution.get("codexInstallCommand", "codex plugin marketplace add <source>")
    risk_class = f"risk-{governance.get('riskTier', 'low')}"
    status_class = "status-ok" if plugin["status"] == "listed" else "status-muted"
    verification_class = "status-ok" if verification.get("state") == "passed" else "status-warn"
    return f"""
    <article class="plugin">
      <div class="plugin-icon" aria-hidden="true">{html.escape(plugin["displayName"][:1].upper())}</div>
      <div class="plugin-main">
        <div class="plugin-top">
          <div>
            <h2>{html.escape(plugin["displayName"])}</h2>
            <p class="plugin-name">{html.escape(plugin["name"])}@{html.escape(plugin["version"])}</p>
          </div>
          <div class="badges">
            {render_badge(plugin["status"], status_class)}
            {render_badge("verified " + verification.get("state", "unknown"), verification_class)}
            {render_badge("risk " + governance.get("riskTier", "unknown"), risk_class)}
          </div>
        </div>
        <p class="summary">{html.escape(plugin["summary"])}</p>
        <ul class="capabilities">{capabilities}</ul>
        <div class="meta-grid">
          <div><span>Category</span><strong>{html.escape(plugin["category"])}</strong></div>
          <div><span>Developer</span><strong>{html.escape(plugin["developer"].get("name", ""))}</strong></div>
          <div><span>Price</span><strong>{html.escape(price)}</strong></div>
          <div><span>Review</span><strong>{html.escape(governance.get("reviewState", ""))}</strong></div>
        </div>
        <div class="command-row">
          <code>{html.escape(install_command)}</code>
        </div>
      </div>
    </article>
    """


def render_html(catalog: dict) -> str:
    plugin_cards = "\n".join(render_plugin(plugin) for plugin in catalog["plugins"])
    categories = sorted({plugin["category"] for plugin in catalog["plugins"]})
    category_text = " / ".join(categories)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(catalog["displayName"])}</title>
  <style>
    :root {{
      --bg: #f7f7f4;
      --ink: #1c2321;
      --muted: #68706d;
      --line: #d9ded9;
      --panel: #ffffff;
      --green: #2d6a4f;
      --blue: #2457a6;
      --amber: #9a5f00;
      --red: #a03a2f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }}
    .wrap {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
    }}
    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 0;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }}
    .mark {{
      width: 40px;
      height: 40px;
      display: grid;
      place-items: center;
      background: var(--green);
      color: #ffffff;
      font-weight: 800;
      border-radius: 8px;
      flex: 0 0 auto;
    }}
    h1 {{
      margin: 0;
      font-size: 22px;
      line-height: 1.15;
    }}
    .brand p {{
      margin: 2px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .install {{
      min-width: 280px;
      max-width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fafbf9;
      overflow-x: auto;
      white-space: nowrap;
    }}
    code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 13px;
    }}
    main {{
      padding: 28px 0 44px;
    }}
    .summary-band {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 84px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 20px;
    }}
    .plugins {{
      display: grid;
      gap: 14px;
    }}
    .plugin {{
      display: grid;
      grid-template-columns: 56px minmax(0, 1fr);
      gap: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .plugin-icon {{
      width: 56px;
      height: 56px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: #dbe9e2;
      color: var(--green);
      font-weight: 800;
      font-size: 22px;
    }}
    .plugin-top {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: start;
    }}
    h2 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
    }}
    .plugin-name {{
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .summary {{
      margin: 12px 0;
      color: #33403b;
    }}
    .badges {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
    }}
    .badge {{
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 4px 8px;
      font-size: 12px;
      white-space: nowrap;
      background: #f9faf8;
    }}
    .status-ok {{ color: var(--green); border-color: #9fc7b5; }}
    .status-muted {{ color: var(--muted); }}
    .status-warn, .risk-high, .risk-critical {{ color: var(--red); border-color: #e0a097; }}
    .risk-medium {{ color: var(--amber); border-color: #d6b36b; }}
    .risk-low {{ color: var(--blue); border-color: #9fb6da; }}
    .capabilities {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 0;
      margin: 0 0 12px;
      list-style: none;
    }}
    .capabilities li {{
      padding: 5px 8px;
      border-radius: 6px;
      background: #f1f4f1;
      color: #33403b;
      font-size: 13px;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }}
    .meta-grid div {{
      border-top: 1px solid var(--line);
      padding-top: 8px;
      min-width: 0;
    }}
    .meta-grid span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
    }}
    .meta-grid strong {{
      display: block;
      margin-top: 2px;
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    .command-row {{
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 8px;
      background: #f8f8f4;
      border: 1px solid var(--line);
      overflow-x: auto;
      white-space: nowrap;
    }}
    footer {{
      padding: 24px 0;
      color: var(--muted);
      border-top: 1px solid var(--line);
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      .topbar {{
        align-items: stretch;
        flex-direction: column;
      }}
      .summary-band, .meta-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .plugin-top {{
        flex-direction: column;
      }}
      .badges {{
        justify-content: flex-start;
      }}
    }}
    @media (max-width: 560px) {{
      .wrap {{
        width: min(100% - 20px, 1120px);
      }}
      .summary-band, .meta-grid {{
        grid-template-columns: 1fr;
      }}
      .plugin {{
        grid-template-columns: 1fr;
      }}
      .plugin-icon {{
        width: 48px;
        height: 48px;
      }}
      h1 {{ font-size: 20px; }}
      h2 {{ font-size: 18px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap topbar">
      <div class="brand">
        <div class="mark">CS</div>
        <div>
          <h1>{html.escape(catalog["displayName"])}</h1>
          <p>{html.escape(category_text)}</p>
        </div>
      </div>
      <div class="install"><code>{html.escape(catalog["installCommand"])}</code></div>
    </div>
  </header>
  <main class="wrap">
    <section class="summary-band" aria-label="Marketplace metrics">
      <div class="metric"><span>Plugins</span><strong>{len(catalog["plugins"])}</strong></div>
      <div class="metric"><span>Verified</span><strong>{sum(1 for p in catalog["plugins"] if p["verification"].get("state") == "passed")}</strong></div>
      <div class="metric"><span>Paid SKUs</span><strong>{sum(1 for p in catalog["plugins"] if p["pricing"].get("model") not in {"free", "external"})}</strong></div>
      <div class="metric"><span>Risk tiers</span><strong>{html.escape(", ".join(sorted({p["governance"].get("riskTier", "unknown") for p in catalog["plugins"]})))}</strong></div>
    </section>
    <section class="plugins" aria-label="Plugins">
      {plugin_cards}
    </section>
  </main>
  <footer>
    <div class="wrap">Generated from .agents/plugins/marketplace.json and marketplace/listings/*.json.</div>
  </footer>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build public marketplace artifacts.")
    parser.add_argument("--root", default=".", help="Marketplace repository root.")
    parser.add_argument("--output-dir", default="public", help="Output directory for generated artifacts.")
    parser.add_argument("--marketplace-source", default="<marketplace-source>", help="Source shown in install commands.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = validate_marketplace(root)
    if report["errors"]:
        print("Cannot build public index; validation failed.")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        return 1

    catalog = build_public_catalog(root)
    catalog["installCommand"] = f"codex plugin marketplace add {args.marketplace_source}"
    for plugin in catalog["plugins"]:
        plugin["distribution"]["codexInstallCommand"] = catalog["installCommand"]

    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "marketplace.json", catalog)
    (output_dir / "index.html").write_text(render_html(catalog), encoding="utf-8")
    print(f"Wrote {output_dir / 'marketplace.json'}")
    print(f"Wrote {output_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
