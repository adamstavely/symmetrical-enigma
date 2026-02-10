"""
Extract dependency and build info from pom.xml, package.json, requirements.txt, go.mod, build.gradle.
"""
from pathlib import Path


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _extract_maven(path: Path) -> dict:
    text = _read_text(path)
    if not text:
        return {}
    out: dict = {"file": str(path.name), "type": "maven", "dependencies": []}
    # Minimal: artifactId, groupId, packaging
    for line in text.splitlines():
        line = line.strip()
        if "<artifactId>" in line:
            out["artifact"] = line.replace("<artifactId>", "").replace("</artifactId>", "").strip()
        if "<groupId>" in line and "dependencies" not in line.lower():
            out["group"] = line.replace("<groupId>", "").replace("</groupId>", "").strip()
        if "<packaging>" in line:
            out["packaging"] = line.replace("<packaging>", "").replace("</packaging>", "").strip()
        if "<dependency>" in line or "<groupId>" in line:
            # Simplified: collect groupId/artifactId from dependency blocks
            if "<groupId>" in line and "dependencies" in line or out.get("in_dep"):
                g = line.replace("<groupId>", "").replace("</groupId>", "").strip()
                if g and not g.startswith("$"):
                    out.setdefault("dep_groups", []).append(g)
    return out


def _extract_npm(path: Path) -> dict:
    text = _read_text(path)
    if not text:
        return {}
    import json
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"file": str(path.name), "type": "npm", "error": "invalid json"}
    deps = dict(data.get("dependencies", {}))
    dev = dict(data.get("devDependencies", {}))
    return {
        "file": str(path.name),
        "type": "npm",
        "name": data.get("name"),
        "version": data.get("version"),
        "dependencies": deps,
        "devDependencies": dev,
    }


def _extract_python(path: Path) -> dict:
    text = _read_text(path)
    if not text:
        return {}
    deps = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            deps.append(line.split("==")[0].split(">=")[0].split("[")[0].strip())
    return {"file": str(path.name), "type": "python", "dependencies": deps}


def _extract_go(path: Path) -> dict:
    text = _read_text(path)
    if not text:
        return {}
    modules = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("require "):
            parts = line.replace("require ", "").strip().split()
            if len(parts) >= 1:
                modules.append(parts[0])
        elif " " in line and not line.startswith("//") and not line.startswith("module"):
            modules.append(line.split()[0])
    return {"file": str(path.name), "type": "go", "modules": modules}


def _extract_gradle(path: Path) -> dict:
    text = _read_text(path)
    if not text:
        return {}
    return {"file": str(path.name), "type": "gradle", "raw": text[:2000]}


def extract_dependencies(repo_path: Path) -> dict[str, dict]:
    """Extract from build files under repo_path. Returns map filename -> extracted dict."""
    results: dict[str, dict] = {}
    extractors = {
        "pom.xml": _extract_maven,
        "package.json": _extract_npm,
        "requirements.txt": _extract_python,
        "go.mod": _extract_go,
        "build.gradle": _extract_gradle,
    }
    for filename, extractor in extractors.items():
        p = repo_path / filename
        if p.exists():
            results[filename] = extractor(p)
    return results
