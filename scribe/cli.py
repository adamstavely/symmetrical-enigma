#!/usr/bin/env python3
"""
SCRIBE CLI: analyze a repo (or batch of repos) and optionally store in VAULT.
Usage:
  poetry run python cli.py analyze [--store] <path_or_url>
  poetry run python cli.py batch [--store] [--concurrency N] --repos <file> | repo1 [repo2 ...]
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Allow importing vault when run from scribe/ or project root
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scribe.analyzer import RepositoryAnalyzer


def _ensure_repo_path(path_or_url: str) -> Path:
    """If it looks like a URL, clone into /tmp/repos/<name>; else use as path."""
    path_or_url = path_or_url.strip()
    if path_or_url.startswith("http://") or path_or_url.startswith("https://") or path_or_url.startswith("git@"):
        try:
            import git
        except ImportError:
            print("GitPython required for clone: pip install gitpython", file=sys.stderr)
            sys.exit(1)
        clone_dir = Path(os.environ.get("SCRIBE_CLONE_DIR", "/tmp/repos"))
        clone_dir.mkdir(parents=True, exist_ok=True)
        name = path_or_url.rstrip("/").split("/")[-1].replace(".git", "")
        dest = clone_dir / name
        if dest.exists():
            return dest
        print(f"Cloning {path_or_url} -> {dest} ...")
        git.Repo.clone_from(path_or_url, dest)
        return dest
    p = Path(path_or_url).resolve()
    if not p.is_dir():
        print(f"Not a directory: {p}", file=sys.stderr)
        sys.exit(1)
    return p


async def run_analyze(path_or_url: str, store: bool) -> None:
    path = _ensure_repo_path(path_or_url)
    analyzer = RepositoryAnalyzer()
    print(f"Analyzing {path} (USE_MOCK_LLM={os.environ.get('USE_MOCK_LLM', 'true')}) ...")
    model = await analyzer.analyze_repository(path)
    print(f"System: {model.system.get('name')} ({model.system.get('id')})")
    print(f"Containers: {len(model.containers)}")
    print(f"Relationships: {len(model.relationships)}")

    if store:
        try:
            from vault.repository import ArchitectureRepository
        except ImportError:
            print("VAULT not found. Add project root to PYTHONPATH to use --store.", file=sys.stderr)
            sys.exit(1)
        vault = ArchitectureRepository()
        try:
            await vault.store_architecture(model.to_vault_dict())
            print("Stored in VAULT (Neo4j).")
        finally:
            await vault.close()
    else:
        import json
        print(json.dumps(model.to_vault_dict(), indent=2, default=str))


def _load_repo_list(repos_file: Path | None, positional: list[str]) -> list[str]:
    """Return list of repo URLs/paths: from file (one per line) or from positional args."""
    if repos_file and repos_file.exists():
        return [line.strip() for line in repos_file.read_text().splitlines() if line.strip()]
    return positional or []


async def _analyze_one(
    path_or_url: str,
    store: bool,
    vault: "ArchitectureRepository | None",
    index: int,
    total: int,
) -> bool:
    """Analyze one repo; return True if success."""
    try:
        path = _ensure_repo_path(path_or_url)
        analyzer = RepositoryAnalyzer()
        model = await analyzer.analyze_repository(path)
        print(f"[{index + 1}/{total}] {model.system.get('name', '?')} ({model.system.get('id')})")
        if store and vault:
            await vault.store_architecture(model.to_vault_dict())
        return True
    except Exception as e:
        print(f"[{index + 1}/{total}] FAILED {path_or_url}: {e}", file=sys.stderr)
        return False


async def run_batch(
    repo_list: list[str],
    store: bool,
    concurrency: int = 2,
) -> None:
    """Batch analyze repos with optional concurrency limit; store all in VAULT if --store."""
    vault = None
    if store:
        try:
            from vault.repository import ArchitectureRepository
            vault = ArchitectureRepository()
        except ImportError:
            print("VAULT not found. Add project root to PYTHONPATH to use --store.", file=sys.stderr)
            sys.exit(1)
    try:
        sem = asyncio.Semaphore(concurrency)
        total = len(repo_list)
        if total == 0:
            print("No repositories to analyze.")
            return

        async def limited_run(i: int, url: str) -> bool:
            async with sem:
                return await _analyze_one(url, store, vault, i, total)

        tasks = [limited_run(i, url) for i, url in enumerate(repo_list)]
        results = await asyncio.gather(*tasks)
        ok = sum(results)
        print(f"Done: {ok}/{total} succeeded.")
    finally:
        if vault:
            await vault.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="EDDA SCRIBE - analyze repositories")
    subparsers = parser.add_subparsers(dest="command", required=True)
    # analyze: single repo
    p_analyze = subparsers.add_parser("analyze", help="Analyze one repository")
    p_analyze.add_argument("path", nargs="?", default=".", help="Repository path or Git URL")
    p_analyze.add_argument("--store", action="store_true", help="Store result in VAULT (Neo4j)")
    # batch: multiple repos
    p_batch = subparsers.add_parser("batch", help="Batch analyze multiple repositories")
    p_batch.add_argument("--store", action="store_true", help="Store all results in VAULT")
    p_batch.add_argument("--concurrency", type=int, default=2, help="Max concurrent analyses (default 2)")
    p_batch.add_argument("--repos", type=Path, help="File with one repo URL/path per line")
    p_batch.add_argument("repos_positional", nargs="*", metavar="repo", help="Repo URLs or paths")
    args = parser.parse_args()

    if args.command == "analyze":
        asyncio.run(run_analyze(args.path, args.store))
    elif args.command == "batch":
        repo_list = _load_repo_list(getattr(args, "repos", None), getattr(args, "repos_positional", []))
        asyncio.run(run_batch(repo_list, args.store, args.concurrency))


if __name__ == "__main__":
    main()
