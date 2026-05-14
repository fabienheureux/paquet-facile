#!/usr/bin/env -S uv run python
"""
release.py
Build a release branch on the sites-faciles fork from the namespaced sources
and open a single PR against numerique-gouv/sites-conformes:main.

The upstream tag and branch name are derived from the version in
sites_conformes/pyproject.toml — e.g. version "3.2.0rc1" clones tag v3.2.0
into a release branch v3.2.0rc1-namespaced-folder. Both can be overridden
with --tag and --branch.

The branch contains up to four commits:

Commit 1 — file-level namespacing:
  1. Clone numerique-gouv/sites-conformes @ <tag> into a temp dir.
  2. For each item in sites_conformes/sites_conformes/, delete the matching
     entry in the temp dir.
  3. Copy sites_conformes/sites_conformes/ into the temp dir.
  4. Copy sites_conformes/pyproject.toml into the temp dir.
  5. Copy our .github/workflows/{publish,ci-check-i18n,docs}.yml into the temp
     dir. The i18n workflow overrides upstream's so the locale-path checks
     point at the packaged sites_conformes/locale/ instead of repo-root
     locale/. The docs workflow rebuilds the Sphinx site on push-to-main.
  6. Copy git-tracked files under demo/ into the temp dir (a runnable example
     consumer of the package; sits at the release-branch repo root).

Commit 2 — folder namespacing:
  6. Move every entry from commit 1 into a new sites_conformes/ subdirectory
     (except Django project files listed in KEEP_AT_ROOT).

Commit 3 — pre-commit auto-fixes (skipped if nothing to fix):
  7. Run upstream's pre-commit hooks (ruff/black/uv-lock) on the namespaced
     tree. Our search-and-replace passes can produce lines that exceed the
     project's line length or otherwise diverge from black formatting; this
     pass normalizes them so CI's Quality job stays green.

Commit 4 — uv.lock refresh (skipped if already up to date):
  8. Run `uv lock` so the lockfile reflects the final layout and the editable
     install of the namespaced sites_conformes package.

Then: force-push to the fork and open a PR against main.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

UPSTREAM_REPO = "git@github.com:numerique-gouv/sites-conformes.git"
UPSTREAM_SLUG = "numerique-gouv/sites-conformes"
FORK_REPO = "git@github.com:fabienheureux/sites-faciles.git"
FORK_OWNER = "fabienheureux"
PACKAGE_DIR_NAME = "sites_conformes"
TEMP_DIR_NAME = "sites_conformes_temp"

# PEP 440 pre/post/dev suffix — everything after the base X.Y.Z that we strip
# to obtain the upstream tag. Matches rc1, rc2, a3, b1, .dev4, .post0, etc.
_VERSION_SUFFIX_RE = re.compile(r"(?:[._-]?(?:rc|a|b|alpha|beta|dev|post)\d*)+$", re.IGNORECASE)


def read_package_version(repo_root: Path) -> tuple[str, str]:
    """Return (full_version, base_version) read from sites_conformes/pyproject.toml.

    base_version drops any rc/dev/post/a/b suffix so it maps to the upstream
    git tag. E.g. "3.2.0rc1" -> ("3.2.0rc1", "3.2.0").
    """
    pyproject = repo_root / PACKAGE_DIR_NAME / "pyproject.toml"
    try:
        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError:
        logging.error("Cannot read package version: %s not found", pyproject)
        sys.exit(2)
    except tomllib.TOMLDecodeError as exc:
        logging.error("Failed to parse %s: %s", pyproject, exc)
        sys.exit(2)

    full = data.get("project", {}).get("version")
    if not isinstance(full, str) or not full:
        logging.error("No project.version in %s", pyproject)
        sys.exit(2)

    base = _VERSION_SUFFIX_RE.sub("", full)
    if not base:
        logging.error("Version %r has no base segment after stripping suffix", full)
        sys.exit(2)
    return full, base

# Upstream directories that the namespaced package renames (and therefore no
# longer ships under the same name). They must be explicitly deleted in
# phase_one_files — otherwise the upstream copy lingers next to the renamed
# version. Maps upstream-name → new-name (new-name is informational).
RENAMED_UPSTREAM_DIRS = {
    "content_manager": "core",
}

# Upstream files at the clone root that must be deleted before the release
# branch is committed. These are legacy/empty build artifacts that conflict
# with our pyproject.toml — setuptools.build_meta picks up an empty setup.py
# and fails uv sync with "No distribution was found".
STRAY_UPSTREAM_FILES = (
    "setup.py",
    "setup.cfg",
)

# Namespaced-package entries that must stay at release-branch ROOT rather than
# being moved into the sites_conformes/ subdir during phase_two_folder. These
# are Django project-glue files: the project lives at root and imports apps
# from the installable sites_conformes package.
#
# locale/ stays INSIDE the package — translations ship with sites_conformes so
# users who `pip install sites-conformes` get them automatically.
KEEP_AT_ROOT = frozenset({
    "config",     # Django project package (settings.py, urls.py, wsgi.py)
    "manage.py",  # Django entrypoint
})


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


def copy_git_tracked_dir(repo_root: Path, rel_dir: str, dest_root: Path) -> int:
    """Copy git-tracked files under <repo_root>/<rel_dir>/ into <dest_root>/<rel_dir>/.

    Uses `git ls-files` to enumerate so transient artifacts (`.venv/`,
    `__pycache__/`, `*.pyc`, etc.) never make it into the release branch even
    though there's no .gitignore in the source dir. Returns the number of
    files copied.
    """
    listing = subprocess.run(
        ["git", "ls-files", rel_dir],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    files = [line for line in listing.stdout.splitlines() if line]
    if not files:
        logging.warning("⚠️  No git-tracked files under %s/", rel_dir)
        return 0

    logging.info("📂 Copying %d git-tracked files from %s/ → %s/%s/", len(files), rel_dir, dest_root.name, rel_dir)
    for rel_path in files:
        src = repo_root / rel_path
        dst = dest_root / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return len(files)


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
    # Override upstream's i18n check workflow because it greps the wrong locale
    # path after packagification (upstream uses `git diff locale/` at repo root).
    source_i18n_yml = repo_root / ".github" / "workflows" / "ci-check-i18n.yml"
    # Ship our docs build workflow so the release branch's GitHub Pages stay
    # in sync with the docs/ content shipped in the same release.
    source_docs_yml = repo_root / ".github" / "workflows" / "docs.yml"
    # Demo project (runnable example consumer of the package). Lives at the
    # release-branch repo root, alongside the package and project glue.
    source_demo = repo_root / "demo"

    for required in (
        source_pkg,
        source_pyproject,
        source_publish_yml,
        source_i18n_yml,
        source_docs_yml,
        source_demo,
    ):
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

    logging.info("🧽 Deleting stray upstream build artifacts that conflict with our pyproject")
    for name in STRAY_UPSTREAM_FILES:
        stray = temp_dir / name
        if stray.exists():
            logging.info("🗑️  Removing %s", stray)
            stray.unlink()
        else:
            logging.debug("⏭️  %s not present, skipping", stray)

    logging.info("📦 Copying namespaced package into temp dir")
    copy_tree_contents(source_pkg, temp_dir)

    copy_file(source_pyproject, temp_dir / "pyproject.toml")
    copy_file(source_publish_yml, temp_dir / ".github" / "workflows" / "publish.yml")
    copy_file(source_i18n_yml, temp_dir / ".github" / "workflows" / "ci-check-i18n.yml")
    copy_file(source_docs_yml, temp_dir / ".github" / "workflows" / "docs.yml")

    copy_git_tracked_dir(repo_root, "demo", temp_dir)

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
        if name in KEEP_AT_ROOT:
            logging.info("📌 Keeping %s at release-branch root (Django project file)", name)
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


def _run_precommit(temp_dir: Path, *, check: bool) -> int:
    """Invoke `pre-commit run --all-files` non-interactively, streaming output.

    Stdout/stderr go to the terminal directly (not captured) so progress is
    visible and we don't accumulate large diffs in memory. Stdin is wired to
    /dev/null so no hook can stall on a prompt. Returns the exit code.
    """
    cmd = [
        "uv", "run", "--with", "pre-commit",
        "pre-commit", "run", "--all-files",
        "--show-diff-on-failure",  # noop when only auto-fixers run
        "--color", "never",
    ]
    logging.debug("$ %s (cwd=%s)", " ".join(cmd), temp_dir)
    with open(os.devnull, "rb") as devnull:
        result = subprocess.run(
            cmd,
            cwd=temp_dir,
            check=check,
            stdin=devnull,
            # stdout/stderr inherited — no PIPE, so output streams live and
            # large diffs don't balloon the parent's memory.
        )
    return result.returncode


def phase_three_precommit(temp_dir: Path, tag: str) -> None:
    """Run pre-commit hooks (ruff/black/uv-lock) and commit any auto-fixes.

    Upstream's CI Quality check runs the same hooks with `--check`-style
    semantics, so any unformatted output from our namespacing pipeline shows
    up as a CI failure (line-length overflows, slice spacing, etc.). Running
    pre-commit here normalizes the tree before the branch is pushed.

    All configured hooks are auto-fixers, so we run pre-commit twice:
      1. First pass: hooks may modify files and exit non-zero. That's expected;
         we ignore the exit code.
      2. Second pass: if hooks STILL fail, they're flagging something they
         couldn't auto-fix. That's a real lint error — fail the release.
    """
    if shutil.which("uv") is None:
        logging.error("`uv` not found on PATH — install it before running release.py")
        sys.exit(2)

    config = temp_dir / ".pre-commit-config.yaml"
    if not config.exists():
        logging.warning("⏭️  No .pre-commit-config.yaml in clone, skipping format step")
        return

    logging.info("🎨 Running pre-commit (first pass — may auto-fix)")
    _run_precommit(temp_dir, check=False)

    logging.info("🎨 Running pre-commit (verification pass)")
    _run_precommit(temp_dir, check=True)

    commit_all(temp_dir, f"Apply pre-commit auto-fixes for {tag}")


def phase_four_lock(temp_dir: Path, tag: str) -> None:
    """Regenerate uv.lock against the final layout and commit as the final commit.

    Runs `uv lock` from the release-branch root so the lockfile reflects:
      * the refreshed dep set from our pyproject template
      * the editable sites_conformes/ package (installed via the root pyproject)

    Fails the release if `uv` is missing or the lock step errors — a broken
    lockfile would silently propagate to CI and downstream consumers.
    """
    if shutil.which("uv") is None:
        logging.error("`uv` not found on PATH — install it before running release.py")
        sys.exit(2)

    logging.info("🔒 Running `uv lock` to refresh lockfile")
    run(["uv", "lock"], cwd=temp_dir)
    commit_all(temp_dir, f"Refresh uv.lock for {tag}")


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
    phase_three_precommit(temp_dir, tag)
    phase_four_lock(temp_dir, tag)
    force_push(temp_dir, "fork", branch)

    if skip_prs:
        logging.warning("⏭️  --skip-prs set; not opening PR")
    else:
        version_display = tag.lstrip("v")
        open_pr(
            temp_dir,
            target_slug=upstream_slug,
            head_branch=branch,
            base_branch=base_branch,
            head_owner=fork_owner,
            title=f"Packagification de Sites Conformes v{version_display}",
            body=(
                f"Packagification for `{tag}`.\n\n"
                f"Three commits:\n"
                f"1. File-level namespacing (rewrites existing files in place).\n"
                f"2. Move all namespaced sources into `{PACKAGE_DIR_NAME}/` so the package "
                f"lives in its own subdirectory.\n"
                f"3. Refresh `uv.lock` against the final layout and the editable "
                f"`{PACKAGE_DIR_NAME}` install."
            ),
        )

    if keep_temp:
        logging.info("📁 Leaving temp dir in place: %s", temp_dir)
    else:
        logging.info("🧹 Removing temp dir %s", temp_dir)
        shutil.rmtree(temp_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        default=None,
        help="Upstream tag to clone (default: v<base-version> from sites_conformes/pyproject.toml)",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Release branch name (default: v<full-version>-namespaced-folder)",
    )
    parser.add_argument("--upstream", default=UPSTREAM_REPO, help="Upstream repo URL")
    parser.add_argument("--upstream-slug", default=UPSTREAM_SLUG, help="Upstream repo slug for gh")
    parser.add_argument("--fork", default=FORK_REPO, help="Fork repo URL to push to")
    parser.add_argument("--fork-owner", default=FORK_OWNER, help="Fork owner used as PR head prefix")
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch on upstream for the PR (default: main)",
    )
    parser.add_argument("--skip-prs", action="store_true", help="Push branch but don't open a PR")
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temp clone after pushing")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (-v, -vv)")
    args = parser.parse_args()

    setup_logger(args.verbose)

    repo_root = Path(__file__).resolve().parent

    full_version, base_version = read_package_version(repo_root)
    tag = args.tag or f"v{base_version}"
    branch = args.branch or f"v{full_version}-namespaced-folder"
    logging.info("📌 Package version %s → upstream tag %s, branch %s", full_version, tag, branch)

    try:
        build_release(
            repo_root=repo_root,
            tag=tag,
            branch=branch,
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
