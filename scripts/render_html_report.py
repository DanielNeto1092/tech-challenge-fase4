from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip()
        if not line:
            close_ul()
            continue
        if line.startswith("# "):
            close_ul()
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            close_ul()
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            close_ul()
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            text = html.escape(line[2:])
            text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
            out.append(f"<li>{text}</li>")
        elif line.startswith("&gt; ") or line.startswith("> "):
            close_ul()
            text = html.escape(line[2:])
            out.append(f"<blockquote>{text}</blockquote>")
        else:
            close_ul()
            text = html.escape(line)
            text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
            out.append(f"<p>{text}</p>")
    close_ul()
    return "\n".join(out)


def render_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ margin: 0; background: #f5f7f7; color: #17211f; font-family: Arial, Helvetica, sans-serif; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 32px 22px 56px; }}
    h1 {{ font-size: 32px; margin: 0 0 18px; }}
    h2 {{ margin-top: 28px; border-top: 1px solid #d8dfde; padding-top: 20px; }}
    h3 {{ margin-top: 18px; color: #405652; }}
    p, li {{ line-height: 1.55; }}
    code {{ background: #eef6f4; border-radius: 4px; padding: 1px 5px; }}
    blockquote {{ border-left: 4px solid #0f766e; margin: 20px 0; padding: 10px 16px; background: #eef6f4; }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a simple HTML page from a Markdown report.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="Sentinela AI")
    args = parser.parse_args()

    md = Path(args.input).read_text(encoding="utf-8")
    body = markdown_to_html(md)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_page(args.title, body), encoding="utf-8")
    print(f"Wrote HTML -> {out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
