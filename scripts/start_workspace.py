"""Prepare local tools, start or reuse the servers, and open a problem notebook."""

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
BIN = VENV / ("Scripts" if os.name == "nt" else "bin")
PYTHON = BIN / ("python.exe" if os.name == "nt" else "python")
LOG_DIR = VENV / "workspace"
DEFAULT_NOTEBOOK = "notebooks/verifying-bitcoin-transaction-signature/index.ipynb"


def prepare_tools():
    if not PYTHON.exists():
        if VENV.exists():
            raise RuntimeError("The existing .venv is incomplete. Preserve it and repair it before starting.")
        python = shutil.which("python3.13")
        if not python and sys.version_info[:2] == (3, 13):
            python = sys.executable
        if not python:
            raise RuntimeError("Install Python 3.13, then run this command again. See AGENTS.md.")
        subprocess.run([python, "-m", "venv", str(VENV)], check=True)

    check = subprocess.run(
        [str(PYTHON), "-c", "import sys; sys.exit(sys.version_info[:2] != (3, 13))"],
        check=False,
    )
    if check.returncode:
        raise RuntimeError("This .venv does not use Python 3.13. Preserve it and repair the environment.")

    # Check the pinned tools without contacting the package registry on every start.
    check_packages = """
import importlib.metadata as metadata
import sys
from pathlib import Path
for line in Path(sys.argv[1]).read_text().splitlines():
    if not line.strip() or line.startswith('#'):
        continue
    name, expected = line.strip().split('==')
    try:
        if metadata.version(name) != expected:
            sys.exit(1)
    except metadata.PackageNotFoundError:
        sys.exit(1)
"""
    requirements = ROOT / "requirements-preview.txt"
    check = subprocess.run([str(PYTHON), "-c", check_packages, str(requirements)], check=False)
    if check.returncode:
        subprocess.run([str(PYTHON), "-m", "pip", "install", "-r", str(requirements)], check=True)
    if Path(sys.prefix).resolve() != VENV.resolve():
        os.execv(str(PYTHON), [str(PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])


def available_port(preferred):
    for port in range(preferred, min(preferred + 20, 65536)):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free local port near {preferred}. Other services were left running.")


def spawn(command, name, port):
    LOG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{name}-{port}.log"
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    environment = os.environ.copy()
    environment["PATH"] = str(BIN) + os.pathsep + environment.get("PATH", "")
    options = {"start_new_session": True} if os.name != "nt" else {
        "creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    }
    with os.fdopen(fd, "a") as log:
        process = subprocess.Popen(
            command, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, **options,
        )
    return process, log_path


def wait_until(check, process=None, log_path=None):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"A server stopped during startup. Check {log_path}; do not share login tokens.")
        result = check()
        if result:
            return result
        time.sleep(0.5)
    raise RuntimeError(f"The server did not become ready. Check {log_path or 'the existing server'}.")


def local_jupyter_servers():
    from jupyter_server.serverapp import list_running_servers
    return [server for server in list_running_servers()
            if Path(server.get("root_dir", "")).resolve() == ROOT
            and urlsplit(server["url"]).hostname in ("127.0.0.1", "localhost")]


def ensure_jupyter(preferred):
    servers = sorted(local_jupyter_servers(), key=lambda s: s["port"] != preferred)
    if servers:
        print("Reusing JupyterLab for this repository.")
        return servers[0]
    port = available_port(preferred)
    process, log = spawn([
        str(BIN / "jupyter"), "lab", "--no-browser", "--ip=127.0.0.1",
        f"--port={port}", "--ServerApp.port_retries=0", f"--ServerApp.root_dir={ROOT}",
    ], "jupyter", port)
    server = wait_until(
        lambda: next((s for s in local_jupyter_servers() if s["pid"] == process.pid), None),
        process, log,
    )
    print("Started JupyterLab for this repository.")
    return server


def request_json(server, path, data=None):
    headers = {"Authorization": "token " + server.get("token", "")}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(server["url"] + path, headers=headers,
                      data=json.dumps(data).encode() if data is not None else None)
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def check_notebook(server, notebook):
    model = request_json(server, "api/contents/" + quote(notebook) + "?content=0")
    if model.get("type") != "notebook":
        raise RuntimeError("Jupyter did not find the requested notebook.")
    try:
        result = request_json(server, "nbdime/api/isgit", {"path": notebook})
    except Exception as error:
        raise RuntimeError(
            "The running Jupyter server has not loaded nbdime. Save your work, "
            "restart that Jupyter server, and run start again. No server was stopped."
        ) from error
    if not result.get("is_git"):
        raise RuntimeError("The notebook is not inside a Git repository; its Git diff would be unavailable.")


def responding(url):
    try:
        # Quarto can take several seconds to prepare a page on its first request.
        with urlopen(url, timeout=10) as response:
            return response.status == 200
    except OSError:
        return False


def ensure_preview(preferred):
    import psutil
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = process.info["cmdline"] or []
            if "preview" not in args or not any(Path(arg).name in ("quarto", "quarto.exe") for arg in args):
                continue
            if Path(process.cwd()).resolve() != ROOT:
                continue
            if "--host" not in args or args[args.index("--host") + 1] != "127.0.0.1":
                continue
            port = int(args[args.index("--port") + 1])
        except (psutil.AccessDenied, psutil.NoSuchProcess, ValueError, IndexError):
            continue
        url = f"http://127.0.0.1:{port}/"
        if any(responding(url) for _ in range(3)):
            print("Reusing the Quarto preview for this repository.")
            return {"url": url, "pid": process.pid}
        # Only stop a confirmed preview for this checkout. It runs no notebook code.
        owned = process.children(recursive=True) + [process]
        for child in owned:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(owned, timeout=5)
        print("Restarting the unresponsive Quarto preview for this repository.")
        break
    port = available_port(preferred)
    process, log = spawn([
        str(BIN / "quarto"), "preview", "--host", "127.0.0.1", "--port", str(port), "--no-browser",
    ], "quarto", port)
    url = f"http://127.0.0.1:{port}/"
    wait_until(lambda: responding(url), process, log)
    print("Started the Quarto preview for this repository.")
    return {"url": url, "pid": process.pid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", nargs="?", default=DEFAULT_NOTEBOOK)
    parser.add_argument("--no-browser", action="store_true", help="Let the chat agent open and verify the browser.")
    args = parser.parse_args()
    os.chdir(ROOT)
    notebook_path = (ROOT / args.notebook).resolve()
    if not notebook_path.is_relative_to(ROOT) or not notebook_path.is_file() or notebook_path.suffix != ".ipynb":
        raise RuntimeError("Choose an existing .ipynb file inside this repository.")
    if not (ROOT / ".git").exists():
        raise RuntimeError("Use a Git clone of the website repository, not a downloaded folder.")
    prepare_tools()
    import nbformat
    from jupyter_core.paths import jupyter_runtime_dir
    nbformat.validate(nbformat.read(notebook_path, as_version=4))
    notebook = notebook_path.relative_to(ROOT).as_posix()
    server = ensure_jupyter(8889)
    check_notebook(server, notebook)
    preview = ensure_preview(8765)
    notebook_url = server["url"] + "lab/tree/" + quote(notebook)
    state = {
        "notebook_url": notebook_url, "preview_url": preview["url"],
        "jupyter_pid": server["pid"], "preview_pid": preview["pid"],
        "jupyter_runtime_file": str(Path(jupyter_runtime_dir()) / f"jpserver-{server['pid']}.json"),
    }
    LOG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(LOG_DIR / "state.json", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump(state, output, indent=2)
    print(json.dumps(state, indent=2))  # Contains no login token.
    if not args.no_browser:
        token = server.get("token")
        url = notebook_url + ("?" + urlencode({"token": token}) if token else "")
        if not webbrowser.open_new_tab(url):
            raise RuntimeError("Servers are ready, but the browser did not open. See .venv/workspace/state.json.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError) as error:
        print(f"Startup stopped: {error}", file=sys.stderr)
        sys.exit(1)
