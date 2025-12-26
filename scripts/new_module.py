#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from string import Template

ROOT_DIR = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT_DIR / "modules"

MODULE_YAML_TEMPLATE = Template(
    """name: ${name}
title: ${title}
version: 0.0.1
description: ${description}
public: true
entrypoints:
  api: modules.${name}.tool.app:app
mount: ${mount}
flows:
  after_success: []
"""
)

APP_TEMPLATE = Template(
    """from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from universe.flows import resolve_flow_links

app = FastAPI(title="${title}")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = ROOT_DIR / "universe" / "templates"

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    flow_links = resolve_flow_links("${name}", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links},
    )


@app.post("/run")
def run(input_text: str | None = Form(None)):
    return {"ok": True, "input": input_text}
"""
)

HTML_TEMPLATE = Template(
    """{% from "partials/ads.html" import ad_layout %}
{% from "partials/flow.html" import flow_section %}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${title}</title>
    <style>
      :root {
        --bg: #0f1116;
        --card: #171b22;
        --text: #f5f7fb;
        --muted: #9aa6bf;
        --accent: #5ac8fa;
        --border: rgba(255, 255, 255, 0.08);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background: radial-gradient(circle at 20% 10%, rgba(90, 200, 250, 0.2), transparent 40%),
          radial-gradient(circle at 80% 20%, rgba(131, 89, 255, 0.2), transparent 45%),
          var(--bg);
        color: var(--text);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px 20px;
      }

      .panel {
        width: min(640px, 100%);
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
      }

      .brand-mark {
        position: absolute;
        top: 18px;
        right: 18px;
        width: 56px;
        height: 56px;
        object-fit: contain;
        opacity: 0.2;
        filter: drop-shadow(0 6px 16px rgba(90, 200, 250, 0.4));
        pointer-events: none;
      }

      .brand-label {
        position: absolute;
        right: 20px;
        bottom: 20px;
        font-size: 0.75rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(245, 247, 251, 0.45);
        pointer-events: none;
      }

      h1 {
        margin: 0 0 8px;
        font-size: 2rem;
        letter-spacing: -0.02em;
      }

      p {
        margin: 0 0 24px;
        color: var(--muted);
        line-height: 1.5;
      }

      label {
        display: block;
        margin-bottom: 6px;
        font-weight: 600;
        font-size: 0.95rem;
      }

      input {
        width: 100%;
        padding: 12px 14px;
        border-radius: 10px;
        border: 1px solid var(--border);
        background: #0e1218;
        color: var(--text);
        margin-bottom: 16px;
        font-size: 1rem;
      }

      input:focus {
        outline: 2px solid rgba(90, 200, 250, 0.4);
        border-color: rgba(90, 200, 250, 0.6);
      }

      button {
        width: 100%;
        padding: 12px 16px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #3cc9ff, #7b5cff);
        color: #0a0f14;
        font-weight: 700;
        font-size: 1rem;
        cursor: pointer;
      }

      .result {
        margin-top: 20px;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid var(--border);
        background: rgba(14, 18, 24, 0.7);
        display: none;
      }

      .result.visible {
        display: block;
      }

      .result-title {
        font-size: 0.8rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(245, 247, 251, 0.6);
        margin-bottom: 10px;
      }

      pre {
        margin: 0;
        padding: 12px;
        border-radius: 10px;
        background: rgba(10, 14, 19, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #dfe6f4;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .meta {
        margin-top: 16px;
        font-size: 0.9rem;
        color: var(--muted);
        display: flex;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
      }

      .ad-block {
        margin: 16px 0 22px;
      }

      .ad-block.inline {
        margin: 12px 0 18px;
      }

      .ad-block.footer {
        margin-top: 26px;
      }

      .ad-label {
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(245, 247, 251, 0.55);
        margin-bottom: 8px;
      }

      .ad-slot {
        width: 100%;
        min-height: 180px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        background: linear-gradient(160deg, rgba(17, 22, 30, 0.9), rgba(10, 14, 19, 0.6));
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
      }

      .ad-slot.inline {
        min-height: 120px;
      }

      .ad-placeholder {
        font-size: 0.85rem;
        color: rgba(167, 179, 199, 0.7);
        border: 1px dashed rgba(255, 255, 255, 0.18);
        border-radius: 999px;
        padding: 6px 14px;
        pointer-events: none;
      }

      .sparky-flow {
        margin-top: 18px;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid rgba(90, 200, 250, 0.25);
        background: linear-gradient(140deg, rgba(13, 18, 26, 0.92), rgba(16, 22, 32, 0.7));
        box-shadow: inset 0 0 0 1px rgba(123, 92, 255, 0.15);
        display: none;
      }

      .sparky-flow.visible {
        display: block;
      }

      .flow-title {
        display: block;
        font-size: 0.8rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(245, 247, 251, 0.6);
        margin-bottom: 12px;
      }

      .sparky-flow ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 10px;
      }

      .sparky-flow a {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(14, 18, 24, 0.7);
        color: var(--text);
        text-decoration: none;
      }

      .sparky-flow a::after {
        content: "->";
        color: rgba(90, 200, 250, 0.8);
      }

      a {
        color: var(--accent);
        text-decoration: none;
      }
    </style>
  </head>
  <body>
    <main class="panel">
      <img class="brand-mark" src="/brand/logo/sparky-universe.icon.png" alt="">
      <span class="brand-label">Sparky Universe</span>
      <h1>${title}</h1>
      <p>${description}</p>
      {% call ad_layout() %}
      <form id="module-form" action="/run" method="post">
        <label for="input_text">Input</label>
        <input id="input_text" name="input_text" placeholder="Type here">
        <button type="submit">Run</button>
      </form>
      <section id="result" class="result">
        <div class="result-title">Result</div>
        <pre id="output">-</pre>
      </section>
      {{ flow_section(flow_links) }}
      <div class="meta">
        <span>Fast utility, zero accounts.</span>
        <a href="/docs" target="_blank" rel="noreferrer">Open API docs</a>
      </div>
      {% endcall %}
    </main>
    <script>
      const form = document.getElementById("module-form");
      const result = document.getElementById("result");
      const output = document.getElementById("output");
      const flow = document.getElementById("sparky-flow");

      const showFlow = () => {
        if (flow && flow.dataset.hasLinks === "true") {
          flow.classList.add("visible");
        }
      };

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(form);

        try {
          const response = await fetch(form.action, { method: "POST", body: formData });
          const data = await response.json();
          result.classList.add("visible");
          output.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
          result.classList.add("visible");
          output.textContent = "Request failed";
        } finally {
          showFlow();
        }
      });
    </script>
  </body>
</html>
"""
)


def slugify(name: str) -> str:
    return name.replace("_", "-")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a Sparky Universe module.")
    parser.add_argument("name", help="Module package name, e.g. qr_batch")
    parser.add_argument("--title", help="Display title")
    parser.add_argument("--description", help="One-line description")
    parser.add_argument("--mount", help="Mount path, e.g. /qr/batch")
    args = parser.parse_args()

    name = args.name.strip()
    if not name:
        raise SystemExit("Module name is required.")

    module_dir = MODULES_DIR / name
    if module_dir.exists():
        raise SystemExit(f"Module already exists: {module_dir}")

    slug = slugify(name)
    title = args.title or name.replace("_", " ").title()
    description = args.description or "One-line purpose of the module."
    mount = args.mount or f"/{slug}"

    module_yaml = MODULE_YAML_TEMPLATE.substitute(
        name=name,
        title=title,
        description=description,
        mount=mount,
    )
    app_py = APP_TEMPLATE.substitute(name=name, title=title)
    html = HTML_TEMPLATE.substitute(title=title, description=description)
    story = f"# {title}\n\n{description}\n"

    write_file(module_dir / "module.yaml", module_yaml)
    write_file(module_dir / "__init__.py", "")
    write_file(module_dir / "core" / "__init__.py", "")
    write_file(module_dir / "tool" / "app.py", app_py)
    write_file(module_dir / "tool" / "templates" / "index.html", html)
    write_file(module_dir / "story.md", story)

    print(f"Created module at {module_dir}")


if __name__ == "__main__":
    main()
