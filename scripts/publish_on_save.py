"""Publish saved, tracked blog notebooks from one local Jupyter server."""

from contextlib import closing
import json
import os
from pathlib import Path, PurePosixPath
import select
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit

import psutil
import websocket
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".venv" / "workspace"
EVENT = "https://events.jupyter.org/jupyter_server/contents_service/v1"
PREFIX = "Publish Jupyter save: "


def git(*args):
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode:
        # Keep credentials, remote URLs, and notebook contents out of the log.
        raise RuntimeError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout.strip()


def on_main():
    return git("rev-parse", "--abbrev-ref", "HEAD") == "main"


def is_post(path):
    parts = PurePosixPath(path).parts
    if len(parts) != 3 or parts[0] != "notebooks" or parts[2] != "index.ipynb":
        return False
    source = ROOT / path
    if not source.is_file() or source.resolve() != source:
        return False
    config = yaml.safe_load(git("show", "HEAD:_quarto.yml"))
    return (path in config["project"]["render"]
            and git("ls-tree", "--name-only", "HEAD", "--", path) == path)


def record_save(db, event):
    if event.get("schema_id") != EVENT or event.get("action") != "save":
        return
    path = event["path"]
    if on_main() and is_post(path):
        blob = git("hash-object", "--", path)
        with db:
            db.execute("INSERT OR REPLACE INTO saves VALUES (?, ?)", (path, blob))


def check_commit(commit, parent, path):
    # Also recognizes our single pending commit after an interrupted push.
    return (git("show", "-s", "--format=%P", commit) == parent
            and git("show", "-s", "--format=%s", commit) == PREFIX + path
            and git("diff", "--name-only", parent, commit) == path)


def publish(db, path, blob):
    if not on_main():
        raise RuntimeError("waiting for the main branch")
    if not is_post(path):
        return "Skipped a notebook no longer listed for publication"
    git_dir = Path(git("rev-parse", "--absolute-git-dir"))
    if any((git_dir / state).exists() for state in (
        "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply",
    )):
        raise RuntimeError("waiting for the current Git operation to finish")

    head = git("rev-parse", "HEAD")
    head_blob = git("rev-parse", f"{head}:{path}")
    if head_blob == blob and head == git("rev-parse", "refs/remotes/origin/main"):
        return "Up to date"
    remote = git("ls-remote", "--exit-code", "origin", "refs/heads/main").split()[0]
    if head != remote:
        intent = db.execute("SELECT parent, path, blob FROM outgoing").fetchone()
        # A second save can land while Git is reading the working file. It can
        # authorize that newer blob, but only for the same pending commit.
        allowed = (intent and intent[:2] == (remote, path)
                   and head_blob in (intent[2], blob))
        if not allowed or not check_commit(head, remote, path):
            raise RuntimeError("local and remote main differ; review git status before publishing")
        git("push", "origin", f"{head}:refs/heads/main")
    if head_blob == blob:
        return "Up to date"
    if git("hash-object", "--", path) != blob:
        return "Superseded by another edit; waiting for its save"

    # Remember the exact allowed change before committing. A lost network connection
    # or interrupted process can then retry its own commit without pushing other work.
    with db:
        db.execute("DELETE FROM outgoing")
        db.execute("INSERT INTO outgoing VALUES (?, ?, ?)", (head, path, blob))
    # --only leaves other staged work out of this commit.
    git("commit", "--only", "-m", PREFIX + path, "--", path)
    commit = git("rev-parse", "HEAD")
    if not check_commit(commit, head, path) or git("rev-parse", f"{commit}:{path}") != blob:
        raise RuntimeError("the notebook or branch changed during commit; review git status")
    git("push", "origin", f"{commit}:refs/heads/main")
    return f"Pushed {commit[:8]}"


def flush(db):
    delay = 5
    for path, blob in db.execute("SELECT path, blob FROM saves ORDER BY rowid").fetchall():
        try:
            status = publish(db, path, blob)
            with db:
                db.execute("DELETE FROM saves WHERE path = ? AND blob = ?", (path, blob))
            print(f"{status}: {path}", flush=True)
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            print(f"Save queued: {path} ({error})", flush=True)
            delay = 30
    return delay


def listen(runtime):
    server = json.loads(runtime.read_text())
    address = urlsplit(server["url"])
    if (Path(server["root_dir"]).resolve() != ROOT
            or address.hostname not in ("localhost", "127.0.0.1") or address.scheme != "http"):
        raise ValueError("Expected this checkout's local Jupyter server")
    url = f"ws://{address.netloc}{address.path.rstrip('/')}/api/events/subscribe"
    ready = STATE / "publish-ready.json"
    paused = STATE / "pause-publishing"
    with sqlite3.connect(STATE / "publish-queue.sqlite", timeout=0) as db:
        # Keep one subscriber per checkout, including concurrent workspace starts.
        db.execute("PRAGMA locking_mode=EXCLUSIVE")
        with db:
            db.execute("BEGIN EXCLUSIVE")
            db.execute("CREATE TABLE IF NOT EXISTS saves (path TEXT PRIMARY KEY, blob TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS outgoing (parent TEXT, path TEXT, blob TEXT)")
        while psutil.pid_exists(server["pid"]) and runtime.is_file():
            try:
                with closing(websocket.create_connection(
                    url, header={"Authorization": "token " + server["token"]},
                    timeout=10, suppress_origin=True, http_no_proxy=["localhost", "127.0.0.1"],
                )) as stream:
                    ready.write_text(json.dumps({"pid": os.getpid(), "server_pid": server["pid"]}))
                    print("Listening for notebook saves", flush=True)
                    retry_at = 0
                    while True:
                        if select.select([stream.sock], [], [], 1)[0]:
                            message = stream.recv()
                            if not message:
                                break
                            if not paused.exists():
                                record_save(db, json.loads(message))
                        if not paused.exists() and time.monotonic() >= retry_at:
                            delay = flush(db)
                            retry_at = time.monotonic() + delay
            except (OSError, websocket.WebSocketException, subprocess.TimeoutExpired, RuntimeError) as error:
                print(f"Reconnecting to local Jupyter ({type(error).__name__})", flush=True)
                time.sleep(2)
            finally:
                ready.unlink(missing_ok=True)


if __name__ == "__main__":
    listen(Path(sys.argv[1]))
