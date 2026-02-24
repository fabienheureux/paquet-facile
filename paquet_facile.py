#!/usr/bin/env -S uv run python
"""
paquet_facile.py
A tool for syncing the sites-faciles codebase and applying transformations.

Clones a specific version from upstream and applies namespacing transformations.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# -- Logging ------------------------------------------------------------------


def setup_logger(verbose: int) -> None:
    """Configure logging verbosity based on verbosity level."""
    match verbose:
        case 0:
            level = logging.WARNING
        case 1:
            level = logging.INFO
        case _:
            level = logging.DEBUG

    logging.basicConfig(
        format="%(levelname)-8s %(message)s",
        level=level,
    )


# -- Git Integration ----------------------------------------------------------


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logging.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check,
            cwd=cwd,
        )
        return result
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed: %s", " ".join(cmd))
        logging.error("Error: %s", exc.stderr)
        raise


def git_ls_files(pattern: str | None = None) -> list[str]:
    """Return tracked files matching a git pathspec (pattern)."""
    cmd = ["git", "ls-files"] + ([pattern] if pattern else [])

    try:
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            logging.error("git ls-files failed: %s", result.stderr)
            return []
    except Exception as exc:
        logging.error("git ls-files failed: %s", exc)
        return []

    return [s for s in result.stdout.splitlines() if s]


def git_clone(repo_url: str, tag: str, target_dir: Path) -> None:
    """Clone a git repository at a specific tag."""
    logging.info("📥 Cloning %s @ %s", repo_url, tag)

    cmd = [
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
        str(target_dir),
    ]

    run_command(cmd)
    logging.info("✅ Clone completed")


# -- Configuration Loading ----------------------------------------------------


def load_config(path: Path) -> dict[str, Any]:
    """Load and parse YAML configuration file."""
    logging.info("📖 Loading rules from %s", path)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        logging.error("Config file not found: %s", path)
        sys.exit(2)
    except yaml.YAMLError as exc:
        logging.error("Failed to parse config: %s", exc)
        sys.exit(2)
    except Exception as exc:
        logging.error("Unexpected error loading config: %s", exc)
        sys.exit(2)


def expand_rules(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand {app}, {package_name}, and {package_name_upper} placeholders into concrete rules and validate minimal schema."""
    apps: list[str] = config.get("apps", [])
    package_name: str = config.get("package_name", "sites_faciles")
    package_name_upper: str = package_name.upper()
    raw_rules: list[dict[str, Any]] = config.get("rules", []) or []

    expanded: list[dict[str, Any]] = []
    for rule in raw_rules:
        search: str | None = rule.get("search")
        replace: str | None = rule.get("replace")

        if not search or replace is None:
            logging.warning("Skipping invalid rule (missing search/replace): %s", rule)
            continue

        # Replace {package_name} and {package_name_upper} placeholders first
        search = search.replace("{package_name}", package_name)
        replace = replace.replace("{package_name}", package_name)
        search = search.replace("{package_name_upper}", package_name_upper)
        replace = replace.replace("{package_name_upper}", package_name_upper)

        if "{app}" in (search + replace) and apps:
            for app in apps:
                expanded.append(
                    {
                        **rule,
                        "search": search.replace("{app}", app),
                        "replace": replace.replace("{app}", app),
                    }
                )
        else:
            expanded.append({**rule, "search": search, "replace": replace})

    logging.info(
        "🔧 Expanded %d rules into %d concrete rules", len(raw_rules), len(expanded)
    )
    return expanded


# -- File Classification ------------------------------------------------------


def is_text_file(path: Path, text_exts: set[str]) -> bool:
    """Check if file should be treated as text based on file extension."""
    return path.suffix in text_exts


def get_files_for_rule(rule: dict[str, Any], scopes: dict[str, str]) -> list[str]:
    """Get list of files that match a rule's scope or path_glob."""
    path_glob: str | None = rule.get("path_glob")

    if path_glob:
        return git_ls_files(path_glob)

    scope_name: str | None = rule.get("scope")
    if not scope_name:
        logging.warning("Rule missing both 'path_glob' and 'scope'; skipping: %s", rule)
        return []

    file_glob = scopes.get(scope_name)
    if not file_glob:
        logging.warning("Unknown scope %r in rule; skipping: %s", scope_name, rule)
        return []

    return git_ls_files(file_glob)


# -- File Processing ----------------------------------------------------------


def apply_rule_to_text(text: str, rule: dict[str, Any]) -> tuple[str, int]:
    """
    Apply a single rule to text content.
    Returns tuple of (modified_text, replacement_count).
    """
    search: str = rule["search"]
    replace: str = rule["replace"]
    literal: bool = bool(rule.get("literal", False))
    filter_pattern: str | None = rule.get("filter")

    if literal:
        count = text.count(search)
        if count <= 0:
            return text, 0
        return text.replace(search, replace), count

    # Regex mode
    try:
        if filter_pattern:
            # Apply replacement only within sections matching the filter
            matches = re.findall(filter_pattern, text, re.DOTALL)
            new_text = text
            total_count = 0

            for match in matches:
                replaced_text, count = re.subn(search, replace, match)
                new_text = new_text.replace(match, replaced_text, 1)
                total_count += count

            return new_text, total_count
        else:
            new_text, count = re.subn(search, replace, text)
            return new_text, count

    except re.error as exc:
        logging.error("Invalid regex pattern %r in rule: %s", search, exc)
        return text, 0


def apply_rule_to_file(path: Path, rule: dict[str, Any], dry_run: bool) -> bool:
    """
    Apply a single rule to a single file.
    Returns True if file would be/was changed.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.error("❌ Failed to read %s: %s", path, exc)
        return False

    new_text, count = apply_rule_to_text(text, rule)

    if count <= 0:
        return False

    search = rule["search"]
    replace = rule["replace"]
    logging.info("✏️  %s — %d replacement(s) for %r → %r", path, count, search, replace)

    if dry_run:
        logging.debug("DRY-RUN: not writing changes to %s", path)
        return True

    try:
        path.write_text(new_text, encoding="utf-8")
    except Exception as exc:
        logging.error("Failed to write %s: %s", path, exc)
        return False

    return True


# -- Directory Operations -----------------------------------------------------


def rename_template_dirs(
    apps: list[str], package_name: str, dry_run: bool = False
) -> None:
    """Move {app}/templates/{app} → {app}/templates/{package_name}_{app}."""
    for app in apps:
        src = Path(app) / "templates" / app
        dst = Path(app) / "templates" / f"{package_name}_{app}"

        if not src.exists():
            logging.debug("⏭️  No template dir to move for app %r: %s", app, src)
            continue

        if dst.exists():
            logging.warning("⚠️  Destination already exists, skipping: %s", dst)
            continue

        if dry_run:
            logging.info("[DRY-RUN] Would move: %s → %s", src, dst)
        else:
            logging.info("📂 Moving: %s → %s", src, dst)
            try:
                shutil.move(str(src), str(dst))
            except Exception as exc:
                logging.error("❌ Failed to move %s → %s: %s", src, dst, exc)


def rename_app_dirs(
    app_renames: dict[str, str], package_name: str, dry_run: bool = False
) -> None:
    """Rename app directories: {old_app}/ → {new_app}/, including template subdirs.

    Also renames the namespaced template subdir inside the new app:
    {new_app}/templates/{package_name}_{old_app}/ → {new_app}/templates/{package_name}_{new_app}/
    """
    for old_app, new_app in app_renames.items():
        src = Path(old_app)
        dst = Path(new_app)

        if not src.exists():
            logging.debug("⏭️  No app dir to rename for %r: %s", old_app, src)
            continue

        if dst.exists():
            logging.warning("⚠️  Destination already exists, skipping: %s", dst)
            continue

        if dry_run:
            logging.info("[DRY-RUN] Would rename app dir: %s → %s", src, dst)
        else:
            logging.info("📂 Renaming app dir: %s → %s", src, dst)
            try:
                shutil.move(str(src), str(dst))
            except Exception as exc:
                logging.error("❌ Failed to rename %s → %s: %s", src, dst, exc)
                continue

        # Also rename the namespaced template subdir inside the (now-moved) app
        old_tpl = dst / "templates" / f"{package_name}_{old_app}"
        new_tpl = dst / "templates" / f"{package_name}_{new_app}"
        if old_tpl.exists():
            if dry_run:
                logging.info("[DRY-RUN] Would rename template dir: %s → %s", old_tpl, new_tpl)
            else:
                logging.info("📂 Renaming template dir: %s → %s", old_tpl, new_tpl)
                try:
                    shutil.move(str(old_tpl), str(new_tpl))
                except Exception as exc:
                    logging.error("❌ Failed to rename %s → %s: %s", old_tpl, new_tpl, exc)


# -- Refactoring Logic --------------------------------------------------------


def _apply_transformations(config_path: Path, dry_run: bool, jobs: int | None) -> None:
    """Apply transformation rules to the current directory."""
    # Load configuration
    config = load_config(config_path)
    scopes: dict[str, str] = config.get("scopes", {})
    text_extensions_from_cfg: list[str] = config.get("text_extensions", [])

    # Set up text file extensions
    DEFAULT_TEXT_EXTENSIONS: set[str] = {
        ".py",
        ".html",
        ".htm",
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".yaml",
        ".yml",
        ".po",
        ".ini",
        ".cfg",
        ".rst",
        ".xml",
        ".js",
        ".ts",
        ".css",
        ".scss",
    }
    text_exts = set(text_extensions_from_cfg) or DEFAULT_TEXT_EXTENSIONS
    logging.debug("Text extensions: %s", sorted(text_exts))

    # Expand rules
    expanded_rules = expand_rules(config)

    # Process files: apply each rule to all matching files
    total_files_changed = 0
    scanned_files = 0
    all_files_processed = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures: list[concurrent.futures.Future[bool]] = []

        for rule in expanded_rules:
            files = get_files_for_rule(rule, scopes)

            for f in files:
                path = Path(f)
                if not is_text_file(path, text_exts):
                    continue

                all_files_processed.add(path)
                future = executor.submit(apply_rule_to_file, path, rule, dry_run)
                futures.append(future)

        scanned_files = len(all_files_processed)

        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    total_files_changed += 1
            except Exception as exc:
                logging.error("Worker failed: %s", exc)

    logging.warning(
        "🎬 Finished replacements %s: scanned %d files, %d file(s) changed",
        "(dry-run)" if dry_run else "",
        scanned_files,
        total_files_changed,
    )

    # Rename template directories
    apps: list[str] = config.get("apps", [])
    package_name: str = config.get("package_name", "sites_faciles")
    if apps:
        rename_template_dirs(apps, package_name, dry_run)

    # Rename app directories (e.g. content_manager → core)
    app_renames: dict[str, str] = config.get("app_renames", {})
    if app_renames:
        rename_app_dirs(app_renames, package_name, dry_run)


# -- Sync Command -------------------------------------------------------------


def _cleanup_package_dir(package_dir: Path) -> None:
    """Remove unwanted directories and build files from the package."""
    unwanted = [
        # Version control & CI
        ".git",
        ".github",
        ".pre-commit-config.yaml",
        # Upstream project docs / housekeeping
        "ONBOARDING.md",
        "DOD.md",
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        # Deployment / runtime artefacts
        "Makefile",
        "Dockerfile",
        "Procfile",
        "Aptfile",
        # Upstream dependency lock (not ours)
        "uv.lock",
        # Python version pin (upstream-specific)
        ".python-version",
        # Upstream environment files
        ".env",
        ".env.example",
        ".env.template",
        ".env.test",
        # Locale config at project root
        ".locales",
        # Upstream build files (we generate our own via templates)
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
    ]
    for rel in unwanted:
        full_path = package_dir / rel
        if full_path.exists():
            logging.debug("Removing %s", full_path)
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()


def _process_templates(
    package_dir: Path,
    package_root: Path,
    package_name: str,
    tag: str,
    config: dict[str, Any],
) -> None:
    """Process all template files and create package structure.

    This function walks through the templates directory and replicates its structure
    in the target package, processing all template files by replacing placeholders.
    """
    # Transform placeholders for templates
    package_name_title = package_name.replace("_", " ").title()
    package_name_kebab = package_name.replace("_", "-")
    class_name = "".join(word.capitalize() for word in package_name.split("_"))
    package_name_upper = package_name.upper()

    # Extract version from tag (remove leading 'v' if present)
    version = tag.lstrip("v")

    # Get apps list from config and format it as a Python list
    apps: list[str] = config.get("apps", [])
    apps_list = "[" + ", ".join([f'"{app}"' for app in apps]) + "]"

    # Define all available placeholders
    placeholders = {
        "{package_name}": package_name,
        "{PackageName}": class_name,
        "{package_verbose_name}": package_name_title,
        "{package_name_kebab}": package_name_kebab,
        "{package_name_upper}": package_name_upper,
        "{version}": version,
        "{apps_list}": apps_list,
    }

    templates_dir = Path("templates")
    if not templates_dir.exists():
        logging.warning("⚠️  Templates directory not found: %s", templates_dir)
        return

    logging.info("📝 Processing template files from %s", templates_dir)

    # Walk through all files in templates directory
    for template_file in templates_dir.rglob("*"):
        # Skip directories
        if template_file.is_dir():
            continue

        # Skip files that don't have .template. in their name
        if ".template." not in template_file.name:
            logging.debug("⏭️  Skipping non-template file: %s", template_file)
            continue

        # Calculate relative path from templates directory
        relative_path = template_file.relative_to(templates_dir)

        # Determine the output filename (remove .template. from the name)
        output_filename = template_file.name.replace(".template.", ".")

        # Determine the base directory for output based on file location
        # Files at root level go to package_root, others go to package_dir
        relative_dir = relative_path.parent

        if str(relative_dir) == ".":
            # Root level template files
            if output_filename in ["pyproject.toml", "README.md", "publish.yml"]:
                # These go to package_root
                output_dir = package_root
            else:
                # Other root level files go to package_dir
                output_dir = package_dir
        else:
            # Nested template files go to package_dir with their directory structure
            output_dir = package_dir / relative_dir

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Define output file path
        output_file = output_dir / output_filename

        # Read template content
        try:
            template_content = template_file.read_text(encoding="utf-8")
        except Exception as exc:
            logging.error("❌ Failed to read template %s: %s", template_file, exc)
            continue

        # Replace all placeholders
        processed_content = template_content
        for placeholder, value in placeholders.items():
            processed_content = processed_content.replace(placeholder, value)

        # Write processed content to output file
        try:
            output_file.write_text(processed_content, encoding="utf-8")
            logging.debug("  Created: %s", output_file.relative_to(package_root))
        except Exception as exc:
            logging.error("❌ Failed to write %s: %s", output_file, exc)

    logging.info("✅ Template processing completed")


def _create_release_branch(
    package_root: Path,
    tag: str,
    config: dict[str, Any],
    repo_url: str,
    fork_url: str,
    dry_run: bool = False,
) -> None:
    """Clone upstream main, inject the built package, and push a release branch to fork."""
    branch_name = f"{tag}-release"
    release_dir = Path("release_temp")

    if dry_run:
        logging.warning(
            "🎬 DRY-RUN: Would clone %s@main into %s", repo_url, release_dir
        )
        logging.warning(
            "🎬 DRY-RUN: Would remove app dirs: %s", config.get("apps", [])
        )
        logging.warning(
            "🎬 DRY-RUN: Would copy %s into %s/%s",
            package_root,
            release_dir,
            package_root.name,
        )
        logging.warning(
            "🎬 DRY-RUN: Would patch pyproject.toml with editable source for ./%s",
            package_root.name,
        )
        logging.warning(
            "🎬 DRY-RUN: Would create branch %s, commit, and force-push to %s",
            branch_name,
            fork_url,
        )
        return

    # 1. Clone upstream main into a fresh temp dir
    if release_dir.exists():
        shutil.rmtree(release_dir)
    logging.info("📥 Cloning %s@main into %s", repo_url, release_dir)
    run_command(
        ["git", "clone", "--depth", "1", "--branch", "main", repo_url, str(release_dir)]
    )

    # 2. Remove raw app directories from the clone
    for app in config.get("apps", []):
        app_dir = release_dir / app
        if app_dir.exists():
            logging.debug("🗑️  Removing app dir %s", app_dir)
            shutil.rmtree(app_dir)

    # 3. Copy the fully-built package into the clone root
    # Strip inner .git dir first to avoid git treating it as a submodule
    inner_git = package_root / package_root.name / ".git"
    if inner_git.exists():
        shutil.rmtree(inner_git)
    dest = release_dir / package_root.name
    logging.info("📂 Copying %s → %s", package_root, dest)
    shutil.copytree(str(package_root), str(dest))

    # 4. Add editable uv dependency via `uv add --editable`.
    # The clone's pyproject.toml name was already transformed to match the package
    # name, so temporarily rename it to avoid a self-dependency error.
    package_name_kebab = package_root.name.replace("_", "-")
    clone_pyproject = release_dir / "pyproject.toml"
    pyproject_text = clone_pyproject.read_text(encoding="utf-8")

    temp_name = "sites-faciles-release"
    clone_pyproject.write_text(
        pyproject_text.replace(f'name = "{package_name_kebab}"', f'name = "{temp_name}"', 1),
        encoding="utf-8",
    )

    logging.info("📦 Adding editable dependency for ./%s", package_root.name)
    run_command(["uv", "add", "--editable", f"./{package_root.name}"], cwd=release_dir)

    # Restore original project name
    final_text = clone_pyproject.read_text(encoding="utf-8")
    clone_pyproject.write_text(
        final_text.replace(f'name = "{temp_name}"', f'name = "{package_name_kebab}"', 1),
        encoding="utf-8",
    )

    # 5. Create branch, commit, and force-push to fork
    logging.info("🌿 Creating branch %s", branch_name)
    run_command(["git", "checkout", "-b", branch_name], cwd=release_dir)
    run_command(["git", "add", "-A"], cwd=release_dir)
    run_command(
        ["git", "commit", "-m", f"Add sites_conformes package for {tag}"],
        cwd=release_dir,
    )
    logging.info("📡 Adding fork remote: %s", fork_url)
    run_command(["git", "remote", "add", "fork", fork_url], cwd=release_dir)
    logging.info("🚀 Force-pushing branch %s to fork", branch_name)
    run_command(["git", "push", "-f", "fork", branch_name], cwd=release_dir)

    # 6. Cleanup
    shutil.rmtree(release_dir)
    logging.info("✅ Release branch %s pushed successfully", branch_name)


def run_sync(
    tag: str,
    config_path: Path,
    dry_run: bool,
    jobs: int | None,
    repo_url: str = "git@github.com:numerique-gouv/sites-faciles.git",
    fork_url: str = "git@github.com:fabienheureux/sites-faciles.git",
) -> None:
    """Sync sites-faciles from upstream and apply refactoring."""
    # Load config to get package_name
    config = load_config(config_path)
    package_name: str = config.get("package_name", "sites_faciles")

    temp_dir = Path(f"{package_name}_temp")
    package_root = Path(package_name)
    package_dir = package_root / package_name

    # Clean up temp directory if it exists
    if temp_dir.exists():
        logging.info("🧹 Removing existing temp directory")
        shutil.rmtree(temp_dir)

    # Clone repository
    git_clone(repo_url, tag, temp_dir)

    # Change to temp directory and apply transformations
    original_dir = Path.cwd()
    try:
        os.chdir(temp_dir)
        logging.info("🔧 Applying transformations...")

        # Adjust config path to be relative to temp dir
        config_path_adjusted = Path("..") / config_path
        _apply_transformations(config_path_adjusted, dry_run, jobs)

    finally:
        os.chdir(original_dir)

    if dry_run:
        logging.warning("🎬 DRY-RUN: Would create nested structure in %s", package_root)
        return

    # Create package structure: package_name/package_name/
    logging.info("📦 Creating nested package structure")
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True)

    # Move cloned content into nested directory
    shutil.move(str(temp_dir), str(package_dir))

    # Process all templates to create package files
    _process_templates(package_dir, package_root, package_name, tag, config)

    # Create release branch, commit changes, and push (must be done before cleanup)
    _create_release_branch(package_root, tag, config, repo_url, fork_url, dry_run)

    # Cleanup unwanted files and directories
    _cleanup_package_dir(package_dir)

    logging.warning("✅ Sync completed successfully!")


# -- Main ---------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync sites-faciles from upstream and apply transformations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "tag",
        help="Git tag or branch to sync (e.g., v2.1.0)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("search-and-replace.yml"),
        help="Path to YAML config (default: search-and-replace.yml)",
    )
    parser.add_argument(
        "--repo",
        default="git@github.com:numerique-gouv/sites-faciles.git",
        help="Repository URL to clone from",
    )
    parser.add_argument(
        "--fork",
        default="git@github.com:fabienheureux/sites-faciles.git",
        help="Fork URL to push the release branch to (default: fabienheureux/sites-faciles)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Number of worker threads (default: CPU count)",
    )

    args = parser.parse_args()

    setup_logger(args.verbose)

    run_sync(
        tag=args.tag,
        config_path=args.config,
        dry_run=args.dry_run,
        jobs=args.jobs,
        repo_url=args.repo,
        fork_url=args.fork,
    )


if __name__ == "__main__":
    main()
