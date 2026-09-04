"""
Self-Improvement Engine for Hidayat AI.

Enables the AI to propose, request permission, and implement UI/UX/system
improvements — but ONLY inside Hidayat-AI-Main/ and with explicit user approval.

Usage (standalone):
    from core.self_improvement import SelfImprovementEngine
    engine = SelfImprovementEngine()
    engine.analyze_current_state()
    proposals = engine.propose_improvements()
    for p in proposals:
        print(f"[{p.id}] {p.title} ({p.risk_level})")

Usage (from main.py / CLI):
    python -m core.self_improvement          # runs interactive mode
    python -m core.self_improvement --list    # just list proposals
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def _get_base_dir() -> Path:
    """Resolve the project root (works for both frozen and source layouts)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent  # core/self_improvement.py -> root


PROJECT_ROOT: Path = _get_base_dir()
MAIN_DIR: Path = PROJECT_ROOT / "Hidayat-AI-Main"
SOURCE_DIR: Path = PROJECT_ROOT / "Hidayat-AI-Source-Code"
BACKUP_DIR: Path = MAIN_DIR / "backups"
CHANGELOG_PATH: Path = MAIN_DIR / "CHANGELOG.md"

# Files/folders that must NEVER be touched
PROTECTED_PATHS: List[str] = [
    "main.py",
    "core/identity.py",
    "core/prompt.txt",
    "LICENSE",
    "TRADEMARK.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    ".gitignore",
    "config/__init__.py",
]

# Relative dirs inside MAIN_DIR that are safe to scan
SCANNABLE_EXTENSIONS: Tuple[str, ...] = (
    ".py", ".json", ".css", ".js", ".html", ".md", ".txt", ".yaml", ".yml", ".toml",
)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ImprovementProposal:
    """Describes a single proposed improvement."""
    id: str
    title: str
    description: str
    category: str          # "ui" | "ux" | "feature" | "performance"
    risk_level: str        # "low" | "medium" | "high"
    estimated_effort: str  # e.g. "5 min", "30 min"
    files_affected: List[str] = field(default_factory=list)

    # runtime helpers -------------------------------------------------------
    def summary(self) -> str:
        risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(self.risk_level, "⚪")
        cat_icon = {"ui": "🎨", "ux": "🖱️", "feature": "🧩", "performance": "⚡"}.get(self.category, "📋")
        files_str = ", ".join(self.files_affected) if self.files_affected else "(none)"
        return (
            f"{risk_icon} {cat_icon} [{self.id}] {self.title}\n"
            f"   Category : {self.category}\n"
            f"   Risk     : {self.risk_level}\n"
            f"   Effort   : {self.estimated_effort}\n"
            f"   Files    : {files_str}\n"
            f"   Desc     : {self.description}\n"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImprovementProposal":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Safe path helpers
# ---------------------------------------------------------------------------

def _resolve_main_path(rel: str) -> Optional[Path]:
    """Resolve a relative path inside Hidayat-AI-Main/, returning None if
    it escapes the directory (path-traversal guard)."""
    target = (MAIN_DIR / rel).resolve()
    try:
        target.relative_to(MAIN_DIR.resolve())
    except ValueError:
        return None
    return target


def _is_protected(rel: str) -> bool:
    """Check whether *rel* matches any protected path entry."""
    normed = rel.replace("\\", "/")
    for prot in PROTECTED_PATHS:
        if normed == prot or normed.startswith(prot.rstrip("*")):
            return True
    return False


def _safe_rel(path: Path) -> str:
    """Return a POSIX-style relative path string under MAIN_DIR."""
    try:
        return path.resolve().relative_to(MAIN_DIR.resolve()).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def _ensure_backup_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def _backup_file(rel: str) -> Optional[Path]:
    """Copy a file to backups/<hash>_<basename>.  Returns destination path."""
    src = _resolve_main_path(rel)
    if src is None or not src.is_file():
        return None
    dst_dir = _ensure_backup_dir()
    file_hash = hashlib.md5(rel.encode()).hexdigest()[:8]
    dst = dst_dir / f"{file_hash}_{src.name}"
    shutil.copy2(src, dst)
    return dst


def _backup_files(rels: List[str]) -> Dict[str, Optional[str]]:
    """Backup multiple files. Returns mapping rel -> backup path str."""
    result: Dict[str, Optional[str]] = {}
    for r in rels:
        bp = _backup_file(r)
        result[r] = str(bp) if bp else None
    return result


# ---------------------------------------------------------------------------
# CHANGELOG writer
# ---------------------------------------------------------------------------

def _log_to_changelog(proposal: ImprovementProposal, changes_made: List[str]) -> None:
    """Append an entry to Hidayat-AI-Main/CHANGELOG.md."""
    today = datetime.date.today().isoformat()
    files_list = "\n".join(f"  - {f}" for f in changes_made) if changes_made else "  - (none)"
    entry = (
        f"\n## [{today}] - Improvement: {proposal.title}\n"
        f"- Description: {proposal.description}\n"
        f"- Category: {proposal.category}\n"
        f"- Risk level: {proposal.risk_level}\n"
        f"- Files changed:\n{files_list}\n"
        f"- Approved by: User\n"
    )

    if CHANGELOG_PATH.exists():
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
        CHANGELOG_PATH.write_text(existing.rstrip() + "\n" + entry + "\n", encoding="utf-8")
    else:
        header = "# Changelog\n\nAll notable improvements to Hidayat AI are documented here.\n"
        CHANGELOG_PATH.write_text(header + entry + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Scanning / heuristic analysis
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _scan_ui_files() -> List[Tuple[str, str]]:
    """Yield (rel_path, content) for scannable files under MAIN_DIR."""
    results: List[Tuple[str, str]] = []
    for root, _dirs, files in os.walk(MAIN_DIR):
        # skip backups, .git, node_modules, __pycache__
        rel_root = Path(root).resolve().relative_to(MAIN_DIR.resolve()).as_posix()
        skip_dirs = {"backups", ".git", "node_modules", "__pycache__", "brahma-connect-android"}
        if any(part in skip_dirs for part in rel_root.split("/")):
            continue
        for fname in files:
            if any(fname.endswith(ext) for ext in SCANNABLE_EXTENSIONS):
                full = Path(root) / fname
                rel = _safe_rel(full)
                if not _is_protected(rel):
                    results.append((rel, _read_text(full)))
    return results


# ---------------------------------------------------------------------------
# Built-in heuristic rules
# ---------------------------------------------------------------------------

def _heuristic_analyze(files: List[Tuple[str, str]]) -> List[ImprovementProposal]:
    """Apply heuristic rules to the scanned files and return proposals."""
    proposals: List[ImprovementProposal] = []
    _id_counter = 0

    def _next_id(prefix: str) -> str:
        nonlocal _id_counter
        _id_counter += 1
        return f"{prefix}-{_id_counter:03d}"

    rel_map = {r: c for r, c in files}

    # ---- Rule 1: Missing docstrings in Python files ----
    py_files = [(r, c) for r, c in files if r.endswith(".py")]
    for rel, content in py_files:
        lines = content.splitlines()
        if not lines:
            continue
        # Find functions / classes without docstrings
        missing_docs = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                # Check if next non-blank, non-comment line is a docstring
                j = i + 1
                while j < len(lines) and (lines[j].strip() == "" or lines[j].strip().startswith("#")):
                    j += 1
                if j < len(lines):
                    next_line = lines[j].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        missing_docs += 1
        if missing_docs >= 3:
            proposals.append(ImprovementProposal(
                id=_next_id("DOC"),
                title=f"Add missing docstrings in {Path(rel).name}",
                description=(
                    f"Found {missing_docs} functions/classes without docstrings. "
                    "Adding docstrings improves IDE support and maintainability."
                ),
                category="ux",
                risk_level="low",
                estimated_effort="10 min",
                files_affected=[rel],
            ))

    # ---- Rule 2: Large CSS files without minification hints ----
    css_files = [(r, c) for r, c in files if r.endswith(".css")]
    for rel, content in css_files:
        line_count = len(content.splitlines())
        if line_count > 300:
            proposals.append(ImprovementProposal(
                id=_next_id("CSS"),
                title=f"Optimise large stylesheet ({Path(rel).name}, {line_count} lines)",
                description=(
                    f"The file has {line_count} lines. Consider splitting into "
                    "component-level stylesheets or adding comments for sections."
                ),
                category="performance",
                risk_level="low",
                estimated_effort="20 min",
                files_affected=[rel],
            ))

    # ---- Rule 3: Hardcoded strings that should be constants ----
    js_files = [(r, c) for r, c in files if r.endswith(".js")]
    for rel, content in js_files:
        # Look for repeated literal strings (appear 3+ times)
        literals = re.findall(r"""['"]([^'"]{3,40})['"]""", content)
        freq: Dict[str, int] = {}
        for lit in literals:
            freq[lit] = freq.get(lit, 0) + 1
        repeated = {k: v for k, v in freq.items() if v >= 3}
        if repeated:
            top = list(repeated.items())[:3]
            examples = ", ".join(f'"{k}" ({v}x)' for k, v in top)
            proposals.append(ImprovementProposal(
                id=_next_id("JS"),
                title=f"Extract repeated string literals in {Path(rel).name}",
                description=(
                    f"Found repeated string literals: {examples}. "
                    "Consider extracting to a constants object."
                ),
                category="performance",
                risk_level="low",
                estimated_effort="15 min",
                files_affected=[rel],
            ))

    # ---- Rule 4: HTML pages without meta viewport (mobile) ----
    html_files = [(r, c) for r, c in files if r.endswith(".html")]
    for rel, content in html_files:
        if "viewport" not in content.lower() and "<head" in content.lower():
            proposals.append(ImprovementProposal(
                id=_next_id("MOB"),
                title=f"Add responsive viewport meta tag in {Path(rel).name}",
                description=(
                    "This HTML file is missing a viewport meta tag. Adding it "
                    "improves mobile rendering."
                ),
                category="ui",
                risk_level="low",
                estimated_effort="2 min",
                files_affected=[rel],
            ))

    # ---- Rule 5: Python files with bare except ----
    for rel, content in py_files:
        if re.search(r"except\s*:", content):
            proposals.append(ImprovementProposal(
                id=_next_id("ERR"),
                title=f"Replace bare 'except:' in {Path(rel).name}",
                description=(
                    "Bare 'except:' catches all exceptions including SystemExit "
                    "and KeyboardInterrupt. Replace with specific exception types."
                ),
                category="ux",
                risk_level="medium",
                estimated_effort="10 min",
                files_affected=[rel],
            ))

    # ---- Rule 6: Missing __init__.py in Python packages ----
    package_dirs: Dict[str, bool] = {}
    for root, dirs, fnames in os.walk(MAIN_DIR):
        rel_root = Path(root).resolve().relative_to(MAIN_DIR.resolve()).as_posix()
        skip = {"backups", ".git", "node_modules", "__pycache__", "brahma-connect-android"}
        if any(part in skip for part in rel_root.split("/")):
            continue
        has_py = any(f.endswith(".py") for f in fnames)
        has_init = "__init__.py" in fnames
        if has_py and not has_init and rel_root:
            package_dirs[rel_root] = True
    for pkg in package_dirs:
        proposals.append(ImprovementProposal(
            id=_next_id("PKG"),
            title=f"Add __init__.py to '{pkg}/'",
            description=(
                f"The directory '{pkg}' contains Python files but no __init__.py. "
                "Adding one makes it a proper package."
            ),
            category="feature",
            risk_level="low",
            estimated_effort="1 min",
            files_affected=[f"{pkg}/__init__.py"],
        ))

    # ---- Rule 7: Very long Python functions (>80 lines) ----
    for rel, content in py_files:
        in_func = False
        func_name = ""
        func_start = 0
        func_indent = 0
        for i, line in enumerate(content.splitlines(), 1):
            match = re.match(r"^(\s*)(def |async def )(\w+)", line)
            if match:
                if in_func and (i - func_start) > 80:
                    proposals.append(ImprovementProposal(
                        id=_next_id("LONG"),
                        title=f"Refactor long function '{func_name}' in {Path(rel).name}",
                        description=(
                            f"Function '{func_name}' spans {i - func_start} lines. "
                            "Consider breaking it into smaller helpers."
                        ),
                        category="ux",
                        risk_level="medium",
                        estimated_effort="30 min",
                        files_affected=[rel],
                    ))
                in_func = True
                func_name = match.group(3)
                func_start = i
                func_indent = (len(match.group(1)) // 4) if match.group(1) else 0

    return proposals


# ---------------------------------------------------------------------------
# SelfImprovementEngine
# ---------------------------------------------------------------------------

class SelfImprovementEngine:
    """Orchestrates the propose → approve → implement cycle for Hidayat-AI-Main/."""

    def __init__(self, approval_callback: Optional[Callable[[ImprovementProposal], bool]] = None):
        """
        Parameters
        ----------
        approval_callback : callable, optional
            ``fn(proposal) -> bool``.  When *None*, interactive ``input()`` is used.
        """
        self._approval_callback = approval_callback
        self._proposals: List[ImprovementProposal] = []
        self._analyzed: bool = False
        self._applied: set[str] = set()  # proposal ids already applied this session

    # -- validation helpers -------------------------------------------------

    def _validate_main_dir(self) -> bool:
        return MAIN_DIR.is_dir()

    def _validate_path(self, rel: str) -> Optional[Path]:
        resolved = _resolve_main_path(rel)
        if resolved is None:
            return None
        if _is_protected(rel):
            return None
        return resolved

    # -- public API ---------------------------------------------------------

    def analyze_current_state(self) -> Dict[str, Any]:
        """Scan Hidayat-AI-Main/ and return a summary dict."""
        if not self._validate_main_dir():
            return {"error": f"Hidayat-AI-Main/ not found at {MAIN_DIR}"}

        files = _scan_ui_files()
        stats = {
            "total_files_scanned": len(files),
            "by_extension": {},
            "main_dir": str(MAIN_DIR),
        }
        for rel, _ in files:
            ext = Path(rel).suffix or "(none)"
            stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1

        self._proposals = _heuristic_analyze(files)
        self._analyzed = True
        stats["proposals_generated"] = len(self._proposals)
        return stats

    def propose_improvements(self) -> List[ImprovementProposal]:
        """Return the list of proposals from the last analysis."""
        if not self._analyzed:
            self.analyze_current_state()
        return list(self._proposals)

    def request_permission(self, proposal_id: str) -> bool:
        """Ask the user (or callback) for approval on a specific proposal."""
        proposal = self._find_proposal(proposal_id)
        if proposal is None:
            print(f"[!] Unknown proposal id: {proposal_id}")
            return False

        print("\n" + "=" * 60)
        print("  IMPROVEMENT PROPOSAL")
        print("=" * 60)
        print(proposal.summary())

        if self._approval_callback is not None:
            approved = self._approval_callback(proposal)
        else:
            answer = input("  Approve this improvement? [y/N] ").strip().lower()
            approved = answer in ("y", "yes")

        if approved:
            print("  ✅ Approved.\n")
        else:
            print("  ❌ Rejected.\n")
        return approved

    def implement_approved(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Apply an approved proposal's changes to Hidayat-AI-Main/.

        Returns a result dict with ``success``, ``backup_paths``, ``changes_made``,
        or ``None`` if the proposal is not found / rejected.
        """
        proposal = self._find_proposal(proposal_id)
        if proposal is None:
            return None

        if not self._validate_main_dir():
            return {"success": False, "error": "Hidayat-AI-Main/ not found"}

        # Double-check path safety
        for rel in proposal.files_affected:
            resolved = self._validate_path(rel)
            if resolved is None:
                return {
                    "success": False,
                    "error": f"Path validation failed for '{rel}' — protected or escapes MAIN_DIR",
                }

        # Backup
        backup_map = _backup_files(proposal.files_affected)

        # --- Apply changes by category ---
        changes_made: List[str] = []
        results = self._apply_by_category(proposal, changes_made)

        if results["success"]:
            self._applied.add(proposal_id)
            _log_to_changelog(proposal, changes_made)

        return {
            "success": results["success"],
            "backup_paths": backup_map,
            "changes_made": changes_made,
            "details": results.get("details", ""),
        }

    def log_to_changelog(self, proposal_id: str, changes_made: List[str]) -> None:
        """Public wrapper: append to CHANGELOG.md."""
        proposal = self._find_proposal(proposal_id)
        if proposal:
            _log_to_changelog(proposal, changes_made)

    # -- internal -----------------------------------------------------------

    def _find_proposal(self, pid: str) -> Optional[ImprovementProposal]:
        for p in self._proposals:
            if p.id == pid:
                return p
        return None

    def _apply_by_category(
        self, proposal: ImprovementProposal, changes_made: List[str]
    ) -> Dict[str, Any]:
        """Dispatch to category-specific applicators."""
        applicator = {
            "ui": self._apply_ui,
            "ux": self._apply_ux,
            "feature": self._apply_feature,
            "performance": self._apply_performance,
        }.get(proposal.category, self._apply_generic)
        return applicator(proposal, changes_made)

    # -- per-category applicators -------------------------------------------
    # Each returns {"success": bool, ...}

    def _apply_ui(self, p: ImprovementProposal, changes: List[str]) -> Dict[str, Any]:
        """Apply UI improvements (viewport meta, CSS splits, etc.)."""
        for rel in p.files_affected:
            resolved = self._validate_path(rel)
            if resolved is None:
                return {"success": False, "error": f"Cannot resolve {rel}"}

            if rel.endswith(".html") and "viewport" not in _read_text(resolved).lower():
                content = _read_text(resolved)
                # Insert viewport meta after <head> or <meta charset...>
                viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
                insertion_point = content.lower().find("<head")
                if insertion_point != -1:
                    # find the closing >
                    gt_pos = content.find(">", insertion_point)
                    if gt_pos != -1:
                        content = content[: gt_pos + 1] + "\n    " + viewport_tag + content[gt_pos + 1 :]
                        resolved.write_text(content, encoding="utf-8")
                        changes.append(rel)
            else:
                # Generic pass-through: flag for manual review
                changes.append(f"{rel} (flagged — manual review needed)")
        return {"success": True, "details": "UI changes applied."}

    def _apply_ux(self, p: ImprovementProposal, changes: List[str]) -> Dict[str, Any]:
        """Apply UX improvements (docstrings, bare-except fixes)."""
        for rel in p.files_affected:
            resolved = self._validate_path(rel)
            if resolved is None:
                return {"success": False, "error": f"Cannot resolve {rel}"}

            if rel.endswith(".py") and "bare" in p.description.lower() or "except:" in p.description.lower():
                content = _read_text(resolved)
                new_content = content.replace("except:", "except Exception:")
                if new_content != content:
                    resolved.write_text(new_content, encoding="utf-8")
                    changes.append(rel)
                else:
                    changes.append(f"{rel} (no bare excepts found)")
            elif rel.endswith(".py") and "docstring" in p.description.lower():
                # Add module-level docstring if missing
                content = _read_text(resolved)
                lines = content.splitlines(keepends=True)
                if lines and not lines[0].strip().startswith('"""') and not lines[0].strip().startswith("'''"):
                    name = Path(rel).stem
                    docstring = f'"""{name} module for Hidayat AI."""\n\n'
                    new_content = docstring + content
                    resolved.write_text(new_content, encoding="utf-8")
                    changes.append(rel)
                else:
                    changes.append(f"{rel} (already has docstring)")
            else:
                changes.append(f"{rel} (flagged — manual review needed)")
        return {"success": True, "details": "UX changes applied."}

    def _apply_feature(self, p: ImprovementProposal, changes: List[str]) -> Dict[str, Any]:
        """Apply feature improvements (missing __init__.py, etc.)."""
        for rel in p.files_affected:
            resolved = self._validate_path(rel)
            if resolved is None:
                # __init__.py might not exist yet — create the parent dir
                parent_rel = str(Path(rel).parent)
                parent = self._validate_path(parent_rel)
                if parent is not None and parent.is_dir():
                    target = MAIN_DIR / rel
                    if not target.exists():
                        target.write_text("", encoding="utf-8")
                        changes.append(rel)
                    else:
                        changes.append(f"{rel} (already exists)")
                else:
                    return {"success": False, "error": f"Parent dir for {rel} not found"}
            else:
                changes.append(f"{rel} (already exists)")
        return {"success": True, "details": "Feature changes applied."}

    def _apply_performance(self, p: ImprovementProposal, changes: List[str]) -> Dict[str, Any]:
        """Apply performance improvements (flag for manual review mostly)."""
        for rel in p.files_affected:
            changes.append(f"{rel} (flagged — requires manual optimisation)")
        return {"success": True, "details": "Performance improvements flagged."}

    def _apply_generic(self, p: ImprovementProposal, changes: List[str]) -> Dict[str, Any]:
        """Fallback: flag everything for manual review."""
        for rel in p.files_affected:
            changes.append(f"{rel} (flagged — manual review needed)")
        return {"success": True, "details": "Generic pass-through."}

    # -- convenience --------------------------------------------------------

    def run_full_cycle(self) -> Dict[str, Any]:
        """Interactive: scan → list → ask → implement. Returns summary."""
        stats = self.analyze_current_state()
        proposals = self.propose_improvements()

        if not proposals:
            return {"message": "No improvement proposals found.", "stats": stats}

        print(f"\n🔍 Found {len(proposals)} improvement proposals for Hidayat-AI-Main/:\n")
        for p in proposals:
            print(p.summary())

        applied: List[str] = []
        skipped: List[str] = []
        for p in proposals:
            approved = self.request_permission(p.id)
            if approved:
                result = self.implement_approved(p.id)
                if result and result.get("success"):
                    applied.append(p.id)
                else:
                    skipped.append(p.id)
                    print(f"  ⚠️  Failed to implement {p.id}: {result}")
            else:
                skipped.append(p.id)

        return {
            "stats": stats,
            "total_proposals": len(proposals),
            "applied": applied,
            "skipped": skipped,
        }


# ---------------------------------------------------------------------------
# Standalone / CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Hidayat AI — Self-Improvement Engine",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Only list proposals (no interactive approval).",
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Run full interactive cycle (scan → approve → implement).",
    )
    parser.add_argument(
        "--approve", type=str, default=None,
        help="Auto-approve a specific proposal id (e.g. DOC-001).",
    )
    args = parser.parse_args()

    engine = SelfImprovementEngine()

    if args.list:
        engine.analyze_current_state()
        proposals = engine.propose_improvements()
        if not proposals:
            print("No improvement proposals found.")
        else:
            print(f"Found {len(proposals)} proposal(s):\n")
            for p in proposals:
                print(p.summary())
    elif args.approve:
        engine.analyze_current_state()
        engine.request_permission = lambda pid: True  # type: ignore[assignment]
        result = engine.implement_approved(args.approve)
        if result:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Proposal {args.approve} not found.")
    elif args.run:
        summary = engine.run_full_cycle()
        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(json.dumps(summary, indent=2, default=str))
    else:
        # Default: just analyse and list
        stats = engine.analyze_current_state()
        proposals = engine.propose_improvements()
        print(f"\nHidayat AI Self-Improvement Engine")
        print(f"Scanned {stats.get('total_files_scanned', 0)} files in Hidayat-AI-Main/")
        print(f"Generated {len(proposals)} proposals.\n")
        for p in proposals:
            print(p.summary())
        print("Run with --run for interactive mode, or --list for listing.")


if __name__ == "__main__":
    main()
