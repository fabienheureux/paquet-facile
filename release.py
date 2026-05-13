#!/usr/bin/env -S uv run python
"""
release.py
Build a release branch on the sites-faciles fork from the namespaced sources
and open a single PR against numerique-gouv/sites-conformes:production.

The branch contains two commits:

Commit 1 — file-level namespacing:
  1. Clone numerique-gouv/sites-conformes @ v3.1.1 into a temp dir.
  2. For each item in sites_conformes/sites_conformes/, delete the matching
     entry in the temp dir.
  3. Copy sites_conformes/sites_conformes/ into the temp dir.
  4. Copy sites_conformes/pyproject.toml into the temp dir.
  5. Copy .github/workflows/publish.yml into the temp dir's .github/workflows/.

Commit 2 — folder namespacing:
  6. Move every entry from commit 1 into a new sites_conformes/ subdirectory.

Then: force-push to the fork and open a PR against production.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

UPSTREAM_REPO = "git@github.com:numerique-gouv/sites-conformes.git"
UPSTREAM_SLUG = "numerique-gouv/sites-conformes"
FORK_REPO = "git@github.com:fabienheureux/sites-faciles.git"
FORK_OWNER = "fabienheureux"
DEFAULT_TAG = "v3.1.1"
DEFAULT_BRANCH = "v3.1.1-namespaced"
PACKAGE_DIR_NAME = "sites_conformes"
TEMP_DIR_NAME = "sites_conformes_temp"

# Upstream directories that the namespaced package renames (and therefore no
# longer ships under the same name). They must be explicitly deleted in
# phase_one_files — otherwise the upstream copy lingers next to the renamed
# version. Maps upstream-name → new-name (new-name is informational).
RENAMED_UPSTREAM_DIRS = {
    "content_manager": "core",
}


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


def remove_matching_entries(source_dir: Path, target_dir: Path) -> list[str]:
    """For each top-level entry in source_dir, delete the matching entry in target_dir.

    Returns the list of top-level names processed (used later for the folder move).
    """
    names: list[str] = []
    for entry in sorted(source_dir.iterdir()):
        names.append(entry.name)
        dest = target_dir / entry.name
        if not dest.exists() and not dest.is_symlink():
            logging.debug("⏭️  Nothing to remove for %s", entry.name)
            continue
        logging.info("🗑️  Removing %s", dest)
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    return names


def copy_tree_contents(source_dir: Path, target_dir: Path) -> None:
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


def ensure_remote(temp_dir: Path, name: str, url: str) -> None:
    existing = run(["git", "remote"], cwd=temp_dir).stdout.split()
    if name in existing:
        run(["git", "remote", "set-url", name, url], cwd=temp_dir)
    else:
        run(["git", "remote", "add", name, url], cwd=temp_dir)


def has_changes(temp_dir: Path) -> bool:
    status = run(["git", "status", "--porcelain"], cwd=temp_dir)
    return bool(status.stdout.strip())


def commit_all(temp_dir: Path, message: str) -> bool:
    run(["git", "add", "-A"], cwd=temp_dir)
    if not has_changes(temp_dir):
        logging.warning("⚠️  No changes to commit for %r", message)
        return False
    run(["git", "commit", "-m", message], cwd=temp_dir)
    return True


def force_push(temp_dir: Path, remote: str, branch: str) -> None:
    logging.info("🚀 Force-pushing %s → %s", branch, remote)
    run(["git", "push", "-f", remote, f"{branch}:{branch}"], cwd=temp_dir)


def open_pr(
    temp_dir: Path,
    target_slug: str,
    head_branch: str,
    base_branch: str,
    head_owner: str | None,
    title: str,
    body: str,
) -> None:
    """Open (or update) a PR using the gh CLI.

    ``target_slug`` is the repo the PR is opened on. If ``head_owner`` is set,
    the head is qualified as ``owner:branch`` (cross-repo PR); otherwise the
    head is assumed to live on ``target_slug`` itself.
    """
    head = f"{head_owner}:{head_branch}" if head_owner else head_branch
    logging.info("🔗 Opening PR %s → %s:%s", head, target_slug, base_branch)
    try:
        run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                target_slug,
                "--base",
                base_branch,
                "--head",
                head,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=temp_dir,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").lower()
        if "already exists" in stderr or "a pull request for branch" in stderr:
            logging.warning("ℹ️  PR already exists for %s; skipping create", head)
            return
        raise


def phase_one_files(
    repo_root: Path,
    temp_dir: Path,
    tag: str,
    branch: str,
) -> list[str]:
    """Apply file-level namespacing and commit. Returns top-level package entry names."""
    source_pkg = repo_root / "sites_conformes" / "sites_conformes"
    source_pyproject = repo_root / "sites_conformes" / "pyproject.toml"
    source_publish_yml = repo_root / ".github" / "workflows" / "publish.yml"

    for required in (source_pkg, source_pyproject, source_publish_yml):
        if not required.exists():
            logging.error("Required path missing: %s", required)
            sys.exit(2)

    logging.info("🌿 Creating branch %s from %s", branch, tag)
    run(["git", "checkout", "-B", branch], cwd=temp_dir)

    logging.info("🧽 Deleting upstream entries that the namespaced package overrides")
    package_entries = remove_matching_entries(source_pkg, temp_dir)

    logging.info("🧽 Deleting upstream dirs renamed by namespacing")
    for upstream_name, new_name in RENAMED_UPSTREAM_DIRS.items():
        renamed = temp_dir / upstream_name
        if renamed.exists():
            logging.info("🗑️  Removing %s (renamed to %s in namespaced pkg)", renamed, new_name)
            shutil.rmtree(renamed)
        else:
            logging.debug("⏭️  Upstream %s not present, skipping", renamed)

    logging.info("📦 Copying namespaced package into temp dir")
    copy_tree_contents(source_pkg, temp_dir)

    copy_file(source_pyproject, temp_dir / "pyproject.toml")
    copy_file(source_publish_yml, temp_dir / ".github" / "workflows" / "publish.yml")

    commit_all(temp_dir, f"Namespaced release for {tag} (files)")
    return package_entries


def phase_two_folder(
    temp_dir: Path,
    package_entries: list[str],
    tag: str,
) -> None:
    """Move the entries copied in phase one into a sites_conformes/ subdir and commit."""
    package_dir = temp_dir / PACKAGE_DIR_NAME
    if package_dir.exists():
        logging.warning(
            "⚠️  %s already exists in the clone — skipping move (likely upstream conflict)",
            package_dir,
        )
    else:
        package_dir.mkdir()

    for name in package_entries:
        if name == PACKAGE_DIR_NAME:
            logging.debug("⏭️  Skipping move of %s into itself", name)
            continue
        src = temp_dir / name
        if not src.exists():
            logging.debug("⏭️  %s not present in clone, skipping", src)
            continue
        dst = package_dir / name
        logging.info("📂 Moving %s → %s", src, dst)
        # Use `git mv` so the rename is recorded cleanly when possible.
        try:
            run(["git", "mv", name, f"{PACKAGE_DIR_NAME}/{name}"], cwd=temp_dir)
        except subprocess.CalledProcessError:
            logging.debug("git mv failed for %s, falling back to shutil.move", name)
            shutil.move(str(src), str(dst))

    commit_all(temp_dir, f"Move namespaced sources into {PACKAGE_DIR_NAME}/ for {tag}")


def build_release(
    repo_root: Path,
    tag: str,
    branch: str,
    upstream: str,
    upstream_slug: str,
    fork: str,
    fork_owner: str,
    base_branch: str,
    keep_temp: bool,
    skip_prs: bool,
) -> None:
    temp_dir = repo_root / TEMP_DIR_NAME

    clone_upstream(upstream, tag, temp_dir)
    ensure_remote(temp_dir, "fork", fork)

    package_entries = phase_one_files(repo_root, temp_dir, tag, branch)
    phase_two_folder(temp_dir, package_entries, tag)
    force_push(temp_dir, "fork", branch)

    if skip_prs:
        logging.warning("⏭️  --skip-prs set; not opening PR")
    else:
        open_pr(
            temp_dir,
            target_slug=upstream_slug,
            head_branch=branch,
            base_branch=base_branch,
            head_owner=fork_owner,
            title=f"Namespaced release for {tag}",
            body=(
                f"Namespacing for `{tag}`.\n\n"
                f"Two commits:\n"
                f"1. File-level namespacing (rewrites existing files in place).\n"
                f"2. Move all namespaced sources into `{PACKAGE_DIR_NAME}/` so the package "
                f"lives in its own subdirectory."
            ),
        )

    if keep_temp:
        logging.info("📁 Leaving temp dir in place: %s", temp_dir)
    else:
        logging.info("🧹 Removing temp dir %s", temp_dir)
        shutil.rmtree(temp_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=DEFAULT_TAG, help=f"Upstream tag (default: {DEFAULT_TAG})")
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Release branch name (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument("--upstream", default=UPSTREAM_REPO, help="Upstream repo URL")
    parser.add_argument("--upstream-slug", default=UPSTREAM_SLUG, help="Upstream repo slug for gh")
    parser.add_argument("--fork", default=FORK_REPO, help="Fork repo URL to push to")
    parser.add_argument("--fork-owner", default=FORK_OWNER, help="Fork owner used as PR head prefix")
    parser.add_argument(
        "--base-branch",
        default="production",
        help="Base branch on upstream for the PR (default: production)",
    )
    parser.add_argument("--skip-prs", action="store_true", help="Push branch but don't open a PR")
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
            upstream_slug=args.upstream_slug,
            fork=args.fork,
            fork_owner=args.fork_owner,
            base_branch=args.base_branch,
            keep_temp=args.keep_temp,
            skip_prs=args.skip_prs,
        )
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed: %s", " ".join(exc.cmd))
        if exc.stderr:
            logging.error("stderr: %s", exc.stderr.strip())
        sys.exit(exc.returncode or 1)


if __name__ == "__main__":
    main()
