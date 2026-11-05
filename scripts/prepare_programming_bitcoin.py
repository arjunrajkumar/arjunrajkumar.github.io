"""Connect the chapter notebooks to Arjun's editable copy of the book."""

from pathlib import Path
import os
import subprocess


BLOG = Path(__file__).resolve().parents[1]
BOOK_PREFIX = "notebooks/programmingbitcoin/book"
BOOK_LINK = BLOG / BOOK_PREFIX
DEFAULT_BOOK_NOTEBOOK = BOOK_PREFIX + "/code-ch01/Chapter1.ipynb"
FORK = "arjunrajkumar/programmingbitcoin"
FORK_URL = f"https://github.com/{FORK}.git"


def verify_fork(book):
    if Path(subprocess.check_output(
        ["git", "-C", book, "rev-parse", "--show-toplevel"], text=True
    ).strip()).resolve() != book.resolve():
        raise RuntimeError("The book folder must be the root of a Git checkout.")
    allowed = {prefix + FORK + suffix for prefix in (
        "https://github.com/", "git@github.com:", "ssh://git@github.com/"
    ) for suffix in ("", ".git")}
    for options in ([], ["--push"]):
        urls = subprocess.check_output(
            ["git", "-C", book, "remote", "get-url", "--all", *options, "origin"], text=True
        ).splitlines()
        if not urls or any(url not in allowed for url in urls):
            raise RuntimeError(f"The book's origin must point to {FORK}. Inspect its remotes and local work.")


def update_checkout(repo, branch, sessions_open):
    def git(*args):
        return subprocess.check_output(
            ["git", "-C", repo, *args], text=True, timeout=40,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        ).strip()

    if git("branch", "--show-current") != branch:
        raise RuntimeError(f"Use {branch} in {repo}. Inspect the current branch before switching.")
    try:
        git("fetch", "--quiet", "origin")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"Could not check GitHub for {repo.name}. Using the local copy. Check your connection and Git access.")
        return
    remote = f"origin/{branch}"
    ahead, behind = map(int, git("rev-list", "--left-right", "--count", f"HEAD...{remote}").split())
    if behind:
        if ahead or git("status", "--porcelain") or sessions_open():
            raise RuntimeError(f"{repo.name} has new commits on GitHub. Review local changes and open work before updating.")
        git("merge", "--ff-only", remote)


def prepare_book():
    sibling = BLOG.parent / "programmingbitcoin"
    book = BOOK_LINK.resolve() if os.path.lexists(BOOK_LINK) else sibling
    if not book.exists():
        if book != sibling or os.path.lexists(sibling):
            raise RuntimeError("The existing book link is broken. Inspect it before changing its target.")
        subprocess.run(["git", "clone", FORK_URL, str(sibling)], check=True)
    verify_fork(book)
    if not (book / "code-ch01" / "ecc.py").is_file():
        raise RuntimeError("The book checkout is missing the Chapter 1 starter file.")
    if not os.path.lexists(BOOK_LINK):
        BOOK_LINK.parent.mkdir(parents=True, exist_ok=True)
        try:
            BOOK_LINK.symlink_to(os.path.relpath(book, BOOK_LINK.parent), target_is_directory=True)
        except FileExistsError:
            if BOOK_LINK.resolve() != book:
                raise RuntimeError("The book link changed during startup.")
        except OSError:
            if os.name != "nt":
                raise
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "New-Item -ErrorAction Stop -ItemType Junction -Path $env:WORKBOOK_LINK -Target $env:WORKBOOK_FORK | Out-Null"],
                env={**os.environ, "WORKBOOK_LINK": str(BOOK_LINK), "WORKBOOK_FORK": str(book)}, check=True,
            )
    return book
