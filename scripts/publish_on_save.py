"""Publish Jupyter saves to the blog or to the matching book checkout."""

from contextlib import closing
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import select
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit

import psutil
import websocket
import yaml

from prepare_programming_bitcoin import BOOK_LINK, verify_fork

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".venv" / "workspace"
EVENT = "https://events.jupyter.org/jupyter_server/contents_service/v1"
PREFIX = "Publish Jupyter save: "


@dataclass(frozen=True)
class SavedFile:
    root: Path
    path: str
    branch: str

    def git(self, *args):
        result = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True, timeout=30,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if result.returncode:
            raise RuntimeError(f"git {args[0]} failed (exit {result.returncode})")
        return result.stdout.strip()

    def eligible(self):
        source = self.root / self.path
        if not source.is_file() or source.resolve() != self.root.resolve() / self.path:
            return False
        if self.root == BOOK_LINK:
            verify_fork(self.root)
            return True
        config = yaml.safe_load(self.git("show", "HEAD:_quarto.yml"))
        return (self.path in config["project"]["render"]
                and self.git("ls-tree", "--name-only", "HEAD", "--", self.path) == self.path)


def saved_file(path):
    prefix = "notebooks/programmingbitcoin/book/"
    if path.startswith(prefix):
        relative = path[len(prefix):]
        if re.fullmatch(r"code-ch(?:0[1-9]|1[0-3])/[^./][^/]*\.(?:py|ipynb)", relative):
            return SavedFile(BOOK_LINK, relative, "master")
        return None
    parts = PurePosixPath(path).parts
    if len(parts) == 3 and parts[0] == "notebooks" and parts[2].endswith(".ipynb"):
        return SavedFile(ROOT, path, "main")
    return None


def record_save(db, event):
    if event.get("schema_id") != EVENT or event.get("action") != "save":
        return
    path = event["path"]
    file = saved_file(path)
    if file and file.eligible() and file.git("branch", "--show-current") == file.branch:
        blob = file.git("hash-object", "--", file.path)
        with db:
            db.execute("INSERT OR REPLACE INTO saves VALUES (?, ?)", (path, blob))


def check_commit(file, commit, parent):
    return (file.git("show", "-s", "--format=%P", commit) == parent
            and file.git("show", "-s", "--format=%s", commit) == PREFIX + file.path
            and file.git("diff", "--name-only", parent, commit) == file.path)


def publish(db, path, blob):
    file = saved_file(path)
    if not file or not file.eligible():
        return "Skipped a file no longer listed for publication"
    git = file.git
    if git("branch", "--show-current") != file.branch:
        raise RuntimeError(f"waiting for the {file.branch} branch")
    git_dir = Path(git("rev-parse", "--absolute-git-dir"))
    if any((git_dir / state).exists() for state in (
        "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply",
    )):
        raise RuntimeError("waiting for the current Git operation to finish")

    path = file.path
    head = git("rev-parse", "HEAD")
    head_blob = git("ls-tree", "--format=%(objectname)", head, "--", path)
    remote_ref = "refs/heads/" + file.branch
    if head_blob == blob and head == git("rev-parse", "refs/remotes/origin/" + file.branch):
        return "Up to date"
    remote = git("ls-remote", "--exit-code", "origin", remote_ref).split()[0]
    table = "book_outgoing" if file.root == BOOK_LINK else "outgoing"
    if head != remote:
        intent = db.execute(f"SELECT parent, path, blob FROM {table}").fetchone()
        allowed = (intent and intent[:2] == (remote, path)
                   and head_blob in (intent[2], blob))
        if not allowed or not check_commit(file, head, remote):
            raise RuntimeError(f"local and remote {file.branch} differ; review git status before publishing")
        git("push", "origin", f"{head}:{remote_ref}")
    if head_blob == blob:
        return "Up to date"
    if git("hash-object", "--", path) != blob:
        return "Superseded by another edit; waiting for its save"

    # Each repository must retain its own pending push when a connection fails.
    with db:
        db.execute(f"DELETE FROM {table}")
        db.execute(f"INSERT INTO {table} VALUES (?, ?, ?)", (head, path, blob))
    if not head_blob:
        git("add", "--intent-to-add", "--", path)
    git("commit", "--only", "-m", PREFIX + path, "--", path)
    commit = git("rev-parse", "HEAD")
    if not check_commit(file, commit, head) or git("rev-parse", f"{commit}:{path}") != blob:
        raise RuntimeError("the saved file or branch changed during commit; review git status")
    git("push", "origin", f"{commit}:{remote_ref}")
    return f"Pushed {commit[:8]}"


def flush(db):
    delay = 5
    for path, blob in db.execute("SELECT path, blob FROM saves ORDER BY rowid").fetchall():
        try:
            status = publish(db, path, blob)
            with db:
                db.execute("DELETE FROM saves WHERE path = ? AND blob = ?", (path, blob))
            print(f"{status}: {path}", flush=True)
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
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
            db.execute("CREATE TABLE IF NOT EXISTS book_outgoing (parent TEXT, path TEXT, blob TEXT)")
        while psutil.pid_exists(server["pid"]) and runtime.is_file():
            try:
                with closing(websocket.create_connection(
                    url, header={"Authorization": "token " + server["token"]},
                    timeout=10, suppress_origin=True, http_no_proxy=["localhost", "127.0.0.1"],
                )) as stream:
                    ready.write_text(json.dumps({"pid": os.getpid(), "server_pid": server["pid"], "chapter_saves": True, "named_post_saves": True}))
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
            except (OSError, websocket.WebSocketException, subprocess.SubprocessError, RuntimeError) as error:
                print(f"Reconnecting to local Jupyter ({type(error).__name__})", flush=True)
                time.sleep(2)
            finally:
                ready.unlink(missing_ok=True)


if __name__ == "__main__":
    listen(Path(sys.argv[1]))
