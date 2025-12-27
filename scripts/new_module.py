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
category: ${category}
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
from universe.settings import shared_templates_dir

app = FastAPI(title="${title}")

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parents[2]
BRAND_DIR = ROOT_DIR / "brand"
SHARED_TEMPLATES = shared_templates_dir(ROOT_DIR)

templates = Jinja2Templates(
    directory=[str(BASE_DIR / "templates"), str(SHARED_TEMPLATES)]
)
templates.env.auto_reload = True
templates.env.cache = {}

if BRAND_DIR.exists():
    app.mount("/brand", StaticFiles(directory=BRAND_DIR), name="brand")

FLOW_BASE_URL = os.getenv("SPARKY_FLOW_BASE_URL")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_path = request.url.path.rstrip("/")
    flow_links = resolve_flow_links("${name}", base_url=FLOW_BASE_URL)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "flow_links": flow_links, "base_path": base_path},
    )


@app.post("/run")
def run(input_text: str | None = Form(None)):
    return {"ok": True, "input": input_text}
"""
)

HTML_TEMPLATE = Template(
    """{% extends "module_base.html" %}

{% block title %}${title}{% endblock %}
{% block heading %}${title}{% endblock %}
{% block description %}${description}{% endblock %}

{% block form %}
<form id="module-form" action="{{ base_path }}/run" method="post">
  <label for="input_text">Input</label>
  <input id="input_text" name="input_text" placeholder="Type here">
  <button type="submit">Run</button>
</form>
{% endblock %}

{% block result %}
<section id="result" class="result">
  <div class="result-title">Result</div>
  <pre id="output">-</pre>
</section>
{% endblock %}

{% block meta %}
<span>Fast utility, zero accounts.</span>
<a href="/docs" target="_blank" rel="noreferrer">Open API docs</a>
{% endblock %}

{% block scripts %}
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

  const basePath = "{{ base_path }}";

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);

    try {
      const response = await fetch(`$${basePath}/run`, { method: "POST", body: formData });
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
{% endblock %}
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
    parser.add_argument("--category", help="Category label")
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
    category = args.category or "Utilities"

    module_yaml = MODULE_YAML_TEMPLATE.substitute(
        name=name,
        title=title,
        description=description,
        mount=mount,
        category=category,
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
