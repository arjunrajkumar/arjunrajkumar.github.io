"""Connect the chapter notebooks to Arjun's editable copy of the book."""

from pathlib import Path
from dataclasses import dataclass
import os
import subprocess
import sys


BLOG = Path(__file__).resolve().parents[1]
BOOK_PREFIX = "notebooks/programmingbitcoin/book"
BOOK_LINK = BLOG / BOOK_PREFIX
DEFAULT_BOOK_NOTEBOOK = BOOK_PREFIX + "/code-ch01/Chapter1.ipynb"
FORK = "arjunrajkumar/programmingbitcoin"
FORK_URL = f"https://github.com/{FORK}.git"
INITIAL_REVIEW = "workspace-review-required"


def checkout_git(repo, *args):
    return subprocess.check_output(
        ["git", "--no-pager", "--literal-pathspecs", "-c", f"core.hooksPath={os.devnull}", "-C", str(repo), *args],
        text=True, timeout=40, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    ).strip()


def review_text(text):
    # Escape terminal controls and invisible Unicode in untrusted commit text.
    return "".join(character if character.isprintable() or character in "\n\t"
                   else ascii(character)[1:-1] for character in text)


@dataclass(frozen=True)
class CheckoutUpdate:
    repo: Path
    branch: str
    head: str
    target: str
    initial: bool = False


def check_update(update):
    repo = update.repo
    if (checkout_git(repo, "branch", "--show-current") != update.branch
            or checkout_git(repo, "rev-parse", "HEAD") != update.head):
        raise RuntimeError(f"{repo.name} changed during review. Start a new review.")
    if update.initial:
        if any(path.name != ".git" for path in repo.iterdir()):
            raise RuntimeError(f"{repo.name} contains local files. Review them before the first checkout.")
    elif checkout_git(repo, "status", "--porcelain"):
        raise RuntimeError(f"{repo.name} has local changes. Preserve them before updating.")


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


def review_checkout(repo, branch):
    """Fetch and review a fixed commit. Apply it only after all reviews finish."""
    if checkout_git(repo, "branch", "--show-current") != branch:
        raise RuntimeError(f"Use {branch} in {repo}. Inspect the current branch before switching.")
    initial = (repo / ".git" / INITIAL_REVIEW).exists()
    try:
        checkout_git(repo, "fetch", "--quiet", "origin", branch)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if initial:
            raise RuntimeError(f"Could not fetch {repo.name} for its first review.")
        print(f"Could not check GitHub for {repo.name}. Using the local copy. Check your connection and Git access.")
        return
    head = checkout_git(repo, "rev-parse", "HEAD")
    target = checkout_git(repo, "rev-parse", "FETCH_HEAD")
    ahead, behind = map(int, checkout_git(repo, "rev-list", "--left-right", "--count", f"{head}...{target}").split())
    if not behind and not initial:
        return
    if ahead:
        raise RuntimeError(f"{repo.name} has diverged from GitHub. Review both histories before updating.")
    update = CheckoutUpdate(repo, branch, head, target, initial)
    check_update(update)
    base = checkout_git(repo, "hash-object", "-t", "tree", os.devnull) if initial else head
    changed = set(checkout_git(
        repo, "diff", "--name-only", "--no-renames", "-z", base, target,
    ).split("\0"))
    if not initial:
        changed.update(checkout_git(
            repo, "log", "--format=", "--name-only", "-z", f"{head}..{target}",
        ).split("\0"))
    changed = sorted(path for path in changed if path)
    instructions = [path for path in changed if Path(path).name.lower() in (
        "agents.md", "agents.override.md", "agents.rb",
    )]
    startup = [path for path in changed if path.startswith(("scripts/", ".github/", ".codex/"))
               or Path(path).name in ("_quarto.yml", "requirements-preview.txt", "requirements.txt")]
    print(f"\nReview changes for {repo.name} on {branch}", flush=True)
    print(f"Current commit {head}\nProposed commit {target}")
    if instructions:
        print("INSTRUCTION FILE CHANGES REQUIRE YOUR APPROVAL")
        print(review_text("\n".join(instructions)))
    if startup:
        print("STARTUP, BUILD OR DEPENDENCY FILES CHANGED")
        print(review_text("\n".join(startup)))
    log_range = ["-1", target] if initial else [f"{head}..{target}"]
    print(review_text(checkout_git(repo, "log", "--format=fuller", "--date=iso-strict", *log_range)))
    print(review_text(checkout_git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-color", "--stat", base, target)))
    print(review_text(checkout_git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-color", "--no-renames", base, target)), flush=True)
    if instructions and not initial:
        print("Instruction changes in each incoming commit")
        print(review_text(checkout_git(
            repo, "log", "--format=oneline", "-p", "--no-ext-diff", "--no-textconv",
            "--no-color", f"{head}..{target}", "--", *instructions,
        )), flush=True)
    answer = f"approve instructions {target}" if instructions else f"approve {target}"
    print(f"End of review for {repo.name}. Approval covers this commit and its code execution.")
    if not sys.stdin.isatty():
        raise RuntimeError("Approval needs an interactive terminal. The agent must show this review and ask Arjun first.")
    try:
        approved = input(f"Type '{answer}' to continue, or press Enter to stop.\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        approved = ""
    if approved != answer:
        raise RuntimeError(f"Approval was not given for {repo.name}. Startup stopped.")
    return update


def apply_checkout_updates(updates, sessions_open):
    if not updates:
        return
    if sessions_open():
        raise RuntimeError("Save and close the open notebook sessions before applying updates. Startup stopped.")
    # Recheck every repository before the first mutation. Merge fixed reviewed IDs.
    for update in updates:
        check_update(update)
    for update in updates:
        check_update(update)
        if update.initial:
            # The initial clone has no working files. check_update enforces this.
            checkout_git(update.repo, "reset", "--hard", update.target)
            (update.repo / ".git" / INITIAL_REVIEW).unlink()
        else:
            checkout_git(update.repo, "merge", "--ff-only", update.target)
        if checkout_git(update.repo, "rev-parse", "HEAD") != update.target:
            raise RuntimeError(f"{update.repo.name} changed during the update. Review it before starting tools.")


def prepare_book():
    sibling = BLOG.parent / "programmingbitcoin"
    book = BOOK_LINK.resolve() if os.path.lexists(BOOK_LINK) else sibling
    if not book.exists():
        if book != sibling or os.path.lexists(sibling):
            raise RuntimeError("The existing book link is broken. Inspect it before changing its target.")
        subprocess.run(["git", "clone", "--no-checkout", FORK_URL, str(sibling)], check=True)
        (book / ".git" / INITIAL_REVIEW).touch()
    verify_fork(book)
    if not (book / ".git" / INITIAL_REVIEW).exists() and not (book / "code-ch01" / "ecc.py").is_file():
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
