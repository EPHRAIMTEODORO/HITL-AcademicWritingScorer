"""Refresh the site's exact prompt text and source provenance without importing the app.

From the website folder:
    python scripts/sync_reference.py --source-root "C:/path/to/Rule-Based-AES"
The source path is optional when the site is directly inside the app repository.
Only writes files within HITL AES. The website itself needs no Python runtime.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
SOURCE_FILES = [
    "HITL/desktop/main.cjs",
    "HITL/desktop/preload.cjs",
    "HITL/desktop/package.json",
    "HITL/ui/index.html",
    "HITL/local_api_server.py",
    "HITL/app_backend.py",
    "HITL/hitl_processor.py",
    "HITL/hybrid_llm_aes.py",
    "HITL/llm_rubric_prompt.py",
    "aes_feature_extractor.py",
    "HITL/preflight.py",
    "HITL/desktop/scripts/build-python-sidecar.cjs",
    "HITL/desktop/scripts/build-windows-installer.ps1",
    "HITL/desktop/README.md",
    "docs/TECHNICAL_REFERENCE.md",
    "data/awl_word_forms.json",
]
PROMPT_NAMES = ["SYSTEM_PROMPT", "USER_PROMPT_TEMPLATE", "LEVEL_4_ANCHOR", "LEVEL_5_ANCHOR", "LEVEL_6_ANCHOR"]


def git(root: Path, *args: str) -> str | None:
    """Return optional Git provenance; source exports still support file hashes."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True, stderr=subprocess.PIPE
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def refresh(root: Path) -> None:
    prompt_source = (root / "HITL/llm_rubric_prompt.py").read_text(encoding="utf-8")
    tree = ast.parse(prompt_source)
    constants = {}
    prompt_lines = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in PROMPT_NAMES:
                    constants[target.id] = ast.literal_eval(node.value)
                    prompt_lines[target.id] = [node.lineno, node.end_lineno]
    if set(constants) != set(PROMPT_NAMES):
        raise RuntimeError("Prompt definitions changed; review the site before refreshing.")

    git_root = git(root, "rev-parse", "--show-toplevel")
    base_commit = git(root, "rev-parse", "HEAD") if git_root and Path(git_root).resolve() == root else None
    sources = []
    for relative in SOURCE_FILES:
        raw = (root / relative).read_bytes()
        status = git(root, "status", "--porcelain", "--", relative) if base_commit else None
        sources.append({
            "path": relative,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "lines": len(raw.splitlines()),
            "modified_from_head": bool(status) if status is not None else None,
        })
    package = json.loads((root / "HITL/desktop/package.json").read_text(encoding="utf-8"))
    manifest = {
        "scope": "HITL desktop app and its imported shared linguistic extractor only",
        "review_date": "2026-11-06",
        "desktop_version": package["version"],
        "base_commit": base_commit,
        "snapshot_note": "Current source snapshot. Modified files may differ from the base commit and GitHub main. Null Git fields mean provenance is unavailable, such as for a source export without Git history. Narrative content was manually reviewed; this script only refreshes exact prompts and provenance.",
        "prompt_locations": prompt_lines,
        "sources": sources,
    }
    prompt_bundle = "HITL DESKTOP APP — EXACT PROMPT REFERENCE\nSource: HITL/llm_rubric_prompt.py\n\n"
    prompt_bundle += "The user template substitutes all three full anchor essays, then target metadata and essay.\n\n"
    prompt_bundle += "\n\n".join(f"=== {name} ===\n{constants[name]}" for name in PROMPT_NAMES)

    labels = {
        "SYSTEM_PROMPT": ("System instruction", "Sets the assessor role, conservative scoring policy, and JSON-only response."),
        "USER_PROMPT_TEMPLATE": ("User prompt template", "Contains the complete six-level rubric, task, safeguards, required JSON keys, and substitution fields. The three anchor placeholders are expanded before inference."),
        "LEVEL_4_ANCHOR": ("Level 4 calibration essay", "Full anchor supplied to the model, preserved exactly as written in the source."),
        "LEVEL_5_ANCHOR": ("Level 5 calibration essay", "Full anchor supplied to the model, preserved exactly as written in the source."),
        "LEVEL_6_ANCHOR": ("Level 6 calibration essay", "Full anchor supplied to the model, preserved exactly as written in the source."),
    }
    blocks = []
    for name in PROMPT_NAMES:
        title, description = labels[name]
        start, end = prompt_lines[name]
        blocks.append(f'''<details class="prompt-block" id="prompt-{name.lower()}">
<summary><span>{html.escape(title)}</span><span class="mono prompt-kind">{name}</span></summary>
<div class="prompt-body"><p>{html.escape(description)}</p>
<div class="prompt-toolbar"><span class="source-label">llm_rubric_prompt.py · lines {start}–{end}</span><button type="button" class="copy-button" data-copy="text-{name.lower()}">Copy text</button></div>
<pre id="text-{name.lower()}" tabindex="0">{html.escape(constants[name])}</pre></div></details>''')
    index_path = SITE / "index.html"
    index = index_path.read_text(encoding="utf-8")
    index, count = re.subn(r"<!-- EXACT_PROMPTS_START -->.*?<!-- EXACT_PROMPTS_END -->", lambda _: "<!-- EXACT_PROMPTS_START -->\n" + "\n".join(blocks) + "\n<!-- EXACT_PROMPTS_END -->", index, flags=re.S)
    if count != 1:
        raise RuntimeError("Expected one exact-prompt insertion region.")
    source_rows = []
    for item in sources:
        path = item["path"]
        # These links intentionally track main; the local hash records this site's actual input.
        link = "https://github.com/EPHRAIMTEODORO/Rule-Based-AES/blob/main/" + path
        changed = "Git unavailable" if item["modified_from_head"] is None else ("Workspace edits" if item["modified_from_head"] else "Matches base commit")
        source_rows.append(f'<tr><th scope="row"><a href="{link}" target="_blank" rel="noopener noreferrer">{html.escape(path)}</a></th><td>{changed}</td><td><code title="{item["sha256"]}">{item["sha256"][:12]}</code></td></tr>')
    index, count = re.subn(r"<!-- SOURCE_ROWS_START -->.*?<!-- SOURCE_ROWS_END -->", lambda _: "<!-- SOURCE_ROWS_START -->\n" + "\n".join(source_rows) + "\n<!-- SOURCE_ROWS_END -->", index, flags=re.S)
    if count != 1:
        raise RuntimeError("Expected one source table insertion region.")
    index = re.sub(r'data-source-version>[^<]*', f'data-source-version>{package["version"]}', index)
    # Read and validate all inputs and template markers before changing outputs.
    assets = SITE / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (assets / "prompts.txt").write_text(prompt_bundle + "\n", encoding="utf-8")
    index_path.write_text(index, encoding="utf-8")
    print(f"Synced {len(constants)} exact prompt definitions and {len(sources)} source hashes; desktop {package['version']}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--source-root", type=Path, metavar="PATH",
        help="App source repository containing HITL/, aes_feature_extractor.py, docs/, and data/. Relative paths use the current working directory.",
    )
    args = parser.parse_args()
    root = (args.source_root.expanduser() if args.source_root else SITE.parent).resolve()
    missing = [relative for relative in SOURCE_FILES if not (root / relative).is_file()]
    if missing:
        parser.error(
            f"App source files not found under {root}.\n"
            'From the website folder, run: python scripts/sync_reference.py --source-root "C:/path/to/Rule-Based-AES"\n'
            "Supply the app source repository, not the standalone website folder. "
            "Existing website files have not been changed.\nMissing: " + ", ".join(missing)
        )
    try:
        refresh(root)
    except (OSError, SyntaxError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"Reference refresh failed: {exc}\n")


if __name__ == "__main__":
    main()
