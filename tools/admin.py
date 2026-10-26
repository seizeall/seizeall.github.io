#!/usr/bin/env python3
"""Local content editor for the academic homepage.

    python tools/admin.py            # http://127.0.0.1:8099/admin
    python tools/admin.py --port 8100 --no-browser

Everything runs on your machine: a small HTTP server (stdlib only) that

  * serves the built site at  /
  * serves the editor at      /admin
  * reads / writes            content.json  and rebuilds index.html
  * stores uploads under      assets/
  * runs git commit / push / revert for you

The server binds to 127.0.0.1 only and every /api call needs the random
token that is injected into the editor page, so other browser tabs or
websites cannot drive it.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ADMIN_HTML = Path(__file__).resolve().parent / "admin.html"
CONTENT = ROOT / "content.json"

TOKEN = secrets.token_urlsafe(18)
BUILD_LOCK = threading.Lock()

ALLOWED_UPLOADS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".zip"}
MAX_UPLOAD = 60 * 1024 * 1024  # 60 MB


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def log(message: str) -> None:
    print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), message), flush=True)


def git(*args: str) -> subprocess.CompletedProcess:
    # Inherit the full environment: git needs HOME / USERPROFILE to find
    # ~/.gitconfig, otherwise every commit fails with "Author identity unknown".
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    return subprocess.run(
        ["git", "-C", str(ROOT)] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def git_out(*args: str) -> str:
    return git(*args).stdout.strip()


def branch() -> str:
    name = git_out("rev-parse", "--abbrev-ref", "HEAD")
    return name or "main"


def is_dirty() -> bool:
    return bool(git_out("status", "--porcelain"))



def rebuild() -> int:
    """Render index.html from content.json. Returns the output size."""
    with BUILD_LOCK:
        out = build.build(write=True)
        return len(out)


def save_content(data: dict) -> int:
    """Validate by rendering first, then persist both files."""
    with BUILD_LOCK:
        html_text = build.render(data)          # raises on a broken document
        CONTENT.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (ROOT / "index.html").write_text(html_text, encoding="utf-8", newline="\n")
        return len(html_text)


def read_content() -> dict:
    return json.loads(CONTENT.read_text(encoding="utf-8"))


def slugify(text: str, fallback: str = "file") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").lower()).strip("-")
    return text[:60] or fallback


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------
def api_status() -> dict:
    ahead = behind = 0
    counts = git_out("rev-list", "--left-right", "--count", "@{u}...HEAD")
    if counts and "\t" in counts:
        try:
            behind, ahead = (int(x) for x in counts.split("\t"))
        except ValueError:
            pass
    last = git_out("log", "-1", "--pretty=format:%h %s (%ad)", "--date=format:%Y-%m-%d %H:%M")
    return {
        "ok": True,
        "branch": branch(),
        "dirty": is_dirty(),
        "ahead": ahead,
        "behind": behind,
        "last_commit": last,
        "has_upstream": bool(git_out("rev-parse", "--abbrev-ref", "@{u}")),
    }


def api_history(limit: int = 20) -> dict:
    raw = git_out(
        "log", "-n", str(limit), "--pretty=format:%h\x1f%ad\x1f%s", "--date=format:%Y-%m-%d %H:%M"
    )
    items = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            items.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return {"ok": True, "items": items}


def api_publish() -> dict:
    if not is_dirty():
        return {"ok": True, "changed": False, "message": "没有需要发布的改动"}

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    add = git("add", "-A")
    if add.returncode != 0:
        return {"ok": False, "error": "git add 失败", "log": add.stderr}

    commit = git("commit", "-m", "site: update content (%s)" % stamp)
    if commit.returncode != 0:
        return {"ok": False, "error": "git commit 失败", "log": (commit.stdout + commit.stderr).strip()}

    sha = git_out("rev-parse", "--short", "HEAD")
    push = git("push", "origin", branch())
    if push.returncode != 0:
        return {
            "ok": False,
            "committed": sha,
            "pushed": False,
            "error": "已提交到本地，但推送失败（检查网络或 GitHub 凭据）",
            "log": (push.stdout + push.stderr).strip(),
        }

    return {
        "ok": True,
        "changed": True,
        "committed": sha,
        "pushed": True,
        "message": "已推送 %s，约 30 秒后线上生效" % sha,
        "log": (push.stdout + push.stderr).strip()[-400:],
    }


def api_rollback(sha: str | None) -> dict:
    if is_dirty():
        return {"ok": False, "error": "有未发布的改动，请先点「发布」再回退"}
    target = sha or "HEAD"
    revert = git("revert", "--no-edit", target)
    if revert.returncode != 0:
        git("revert", "--abort")
        return {
            "ok": False,
            "error": "回退失败（可能有冲突），已撤销本次操作",
            "log": (revert.stdout + revert.stderr).strip()[-600:],
        }

    rebuild()
    new_sha = git_out("rev-parse", "--short", "HEAD")
    push = git("push", "origin", branch())
    return {
        "ok": push.returncode == 0,
        "message": "已回退，生成新的提交 %s" % new_sha if push.returncode == 0
        else "已本地回退（%s），但推送失败" % new_sha,
        "pushed": push.returncode == 0,
        "log": (push.stdout + push.stderr).strip()[-400:] if push.returncode != 0 else "",
    }


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "academic-home-admin/1.0"

    # -- plumbing ---------------------------------------------------------
    def log_message(self, fmt, *args):  # quieter default logging
        log("%s %s" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str = "application/octet-stream"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload: dict, code: int = 200):
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _authorised(self) -> bool:
        return self.headers.get("X-Admin-Token", "") == TOKEN

    def _safe_path(self, rel: str) -> Path | None:
        rel = urllib.parse.unquote(rel).lstrip("/")
        if not rel or rel.endswith("/"):
            rel += "index.html"
        candidate = (ROOT / rel).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            return None
        return candidate

    def _body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_UPLOAD:
            raise ValueError("文件太大（上限 60 MB）")
        return self.rfile.read(length) if length else b""

    # -- GET --------------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            if not self._authorised():
                return self._json({"ok": False, "error": "unauthorised"}, 401)
            try:
                if path == "/api/status":
                    return self._json(api_status())
                if path == "/api/content":
                    return self._json({"ok": True, "content": read_content()})
                if path == "/api/history":
                    return self._json(api_history())
                return self._json({"ok": False, "error": "unknown endpoint"}, 404)
            except Exception as exc:  # noqa: BLE001
                log(traceback.format_exc())
                return self._json({"ok": False, "error": str(exc)}, 500)

        if path in ("/admin", "/admin/"):
            html_text = ADMIN_HTML.read_text(encoding="utf-8")
            html_text = html_text.replace("__TOKEN__", TOKEN)
            return self._send(200, html_text.encode("utf-8"), "text/html; charset=utf-8")

        if path == "/favicon.ico":
            fav = ROOT / "assets" / "img" / "favicon.svg"
            return self._send(200, fav.read_bytes(), "image/svg+xml")

        target = self._safe_path(path)
        if not target or not target.is_file():
            return self._send(404, b"Not found", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        return self._send(200, target.read_bytes(), ctype)

    # -- POST -------------------------------------------------------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/"):
            return self._json({"ok": False, "error": "not found"}, 404)
        if not self._authorised():
            return self._json({"ok": False, "error": "unauthorised"}, 401)

        try:
            if path == "/api/content":
                payload = json.loads(self._body().decode("utf-8") or "{}")
                data = payload.get("content")
                if not isinstance(data, dict):
                    return self._json({"ok": False, "error": "缺少 content 字段"}, 400)
                size = save_content(data)
                log("content saved, index.html rebuilt (%d bytes)" % size)
                return self._json({"ok": True, "bytes": size})

            if path == "/api/upload":
                rel = (query.get("path") or [""])[0]
                if not rel:
                    return self._json({"ok": False, "error": "缺少 path 参数"}, 400)
                rel = urllib.parse.unquote(rel)
                suffix = Path(rel).suffix.lower()
                if suffix not in ALLOWED_UPLOADS:
                    return self._json({"ok": False, "error": "不支持的文件类型 %s" % suffix}, 400)
                target = self._safe_path(rel)
                if not target or not str(target).startswith(str(ROOT / "assets")):
                    return self._json({"ok": False, "error": "只能上传到 assets/ 目录"}, 400)
                target.parent.mkdir(parents=True, exist_ok=True)
                body = self._body()
                target.write_bytes(body)
                log("uploaded %s (%d bytes)" % (rel, len(body)))
                return self._json({"ok": True, "path": rel.replace("\\", "/"), "size": len(body)})

            if path == "/api/publish":
                result = api_publish()
                log("publish -> %s" % result.get("message") or result.get("error"))
                return self._json(result)

            if path == "/api/rollback":
                payload = json.loads(self._body().decode("utf-8") or "{}")
                result = api_rollback(payload.get("sha"))
                log("rollback -> %s" % (result.get("message") or result.get("error")))
                return self._json(result)

            if path == "/api/rebuild":
                size = rebuild()
                return self._json({"ok": True, "bytes": size})

            return self._json({"ok": False, "error": "unknown endpoint"}, 404)

        except Exception as exc:  # noqa: BLE001
            log(traceback.format_exc())
            return self._json({"ok": False, "error": str(exc)}, 500)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local editor for the academic homepage")
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    url = "http://127.0.0.1:%d/admin?t=%s" % (args.port, TOKEN)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)

    print()
    print("  个人主页 · 本地编辑器")
    print("  ------------------------------------------------")
    print("  编辑页面 : %s" % url)
    print("  站点预览 : http://127.0.0.1:%d/" % args.port)
    print("  停止     : Ctrl+C")
    print()
    log("serving %s" % ROOT)

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        log("bye")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
