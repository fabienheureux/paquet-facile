#!/usr/bin/env -S uv run python
"""
release.py
Build a release branch on the sites-faciles fork from the namespaced sources.

Steps:
  1. Clone numerique-gouv/sites-conformes @ v3.1.1 into a temp dir.
  2. For each item in sites_conformes/sites_conformes/, delete the matching
     entry in the temp dir.
  3. Copy sites_conformes/sites_conformes/ into the temp dir.
  4. Copy sites_conformes/pyproject.toml into the temp dir.
  5. Copy .github/workflows/publish.yml into the temp dir's .github/workflows/.
  6. Commit everything and force-push to a new branch on the fork.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

UPSTREAM_REPO = "git@github.com:numerique-gouv/sites-conformes.git"
FORK_REPO = "git@github.com:fabienheureux/sites-faciles.git"
DEFAULT_TAG = "v3.1.1"
DEFAULT_BRANCH = "v3.1.1-namespaced"
TEMP_DIR_NAME = "sites_conformes_temp"


def setup_logger(verbose: int) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(format="%(levelname)-8s %(message)s", level=level)


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    logging.debug("$ %s (cwd=%s)", " ".join(cmd), cwd or ".")
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def clone_upstream(repo_url: str, tag: str, target: Path) -> None:
    if target.exists():
        logging.info("🧹 Removing existing %s", target)
        shutil.rmtree(target)
    logging.info("📥 Cloning %s @ %s into %s", repo_url, tag, target)
    run(
        [
            "git",
            "clone",
            "--quiet",
            "-c",
            "advice.detachedHead=false",
            "--branch",
            tag,
            "--depth",
            "1",
            repo_url,
            str(target),
        ]
    )


def remove_matching_entries(source_dir: Path, target_dir: Path) -> None:
    """For each top-level entry in source_dir, delete the matching entry in target_dir."""
    for entry in sorted(source_dir.iterdir()):
        dest = target_dir / entry.name
        if not dest.exists() and not dest.is_symlink():
            logging.debug("⏭️  Nothing to remove for %s", entry.name)
            continue
        logging.info("🗑️  Removing %s", dest)
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink()


def copy_tree_contents(source_dir: Path, target_dir: Path) -> None:
    """Copy each top-level entry of source_dir into target_dir."""
    for entry in sorted(source_dir.iterdir()):
        dest = target_dir / entry.name
        logging.info("📂 Copying %s → %s", entry, dest)
        if entry.is_dir():
            shutil.copytree(entry, dest)
        else:
            shutil.copy2(entry, dest)


def copy_file(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    logging.info("📄 Copying %s → %s", source, dest)
    shutil.copy2(source, dest)


def push_release_branch(
    temp_dir: Path, fork_url: str, branch: str, tag: str
) -> None:
    logging.info("🌿 Preparing branch %s in %s", branch, temp_dir)
    run(["git", "checkout", "-B", branch], cwd=temp_dir)
    run(["git", "add", "-A"], cwd=temp_dir)

    status = run(["git", "status", "--porcelain"], cwd=temp_dir)
    if not status.stdout.strip():
        logging.warning("⚠️  No changes to commit — skipping commit")
    else:
        run(
            ["git", "commit", "-m", f"Namespaced release for {tag}"],
            cwd=temp_dir,
        )

    logging.info("📡 Setting fork remote to %s", fork_url)
    # Reset 'origin' to point at the fork, or add as a new remote.
    existing = run(["git", "remote"], cwd=temp_dir).stdout.split()
    if "fork" in existing:
        run(["git", "remote", "set-url", "fork", fork_url], cwd=temp_dir)
    else:
        run(["git", "remote", "add", "fork", fork_url], cwd=temp_dir)

    logging.info("🚀 Force-pushing %s to fork", branch)
    run(["git", "push", "-f", "fork", f"{branch}:{branch}"], cwd=temp_dir)
    logging.warning("✅ Pushed %s to %s", branch, fork_url)


def build_release(
    repo_root: Path,
    tag: str,
    branch: str,
    upstream: str,
    fork: str,
    keep_temp: bool,
) -> None:
    source_pkg = repo_root / "sites_conformes" / "sites_conformes"
    source_pyproject = repo_root / "sites_conformes" / "pyproject.toml"
    source_publish_yml = repo_root / ".github" / "workflows" / "publish.yml"

    for required in (source_pkg, source_pyproject, source_publish_yml):
        if not required.exists():
            logging.error("Required path missing: %s", required)
            sys.exit(2)

    temp_dir = repo_root / TEMP_DIR_NAME

    clone_upstream(upstream, tag, temp_dir)

    logging.info("🧽 Deleting upstream entries that the namespaced package overrides")
    remove_matching_entries(source_pkg, temp_dir)

    logging.info("📦 Copying namespaced package into temp dir")
    copy_tree_contents(source_pkg, temp_dir)

    copy_file(source_pyproject, temp_dir / "pyproject.toml")
    copy_file(source_publish_yml, temp_dir / ".github" / "workflows" / "publish.yml")

    push_release_branch(temp_dir, fork, branch, tag)

    if keep_temp:
        logging.info("📁 Leaving temp dir in place: %s", temp_dir)
    else:
        logging.info("🧹 Removing temp dir %s", temp_dir)
        shutil.rmtree(temp_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=DEFAULT_TAG, help=f"Upstream tag (default: {DEFAULT_TAG})")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help=f"Branch to push (default: {DEFAULT_BRANCH})")
    parser.add_argument("--upstream", default=UPSTREAM_REPO, help="Upstream repo URL")
    parser.add_argument("--fork", default=FORK_REPO, help="Fork repo URL to push to")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temp clone after pushing")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-v, -vv)")
    args = parser.parse_args()

    setup_logger(args.verbose)

    repo_root = Path(__file__).resolve().parent

    try:
        build_release(
            repo_root=repo_root,
            tag=args.tag,
            branch=args.branch,
            upstream=args.upstream,
            fork=args.fork,
            keep_temp=args.keep_temp,
        )
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed: %s", " ".join(exc.cmd))
        if exc.stderr:
            logging.error("stderr: %s", exc.stderr.strip())
        sys.exit(exc.returncode or 1)


if __name__ == "__main__":
    main()
