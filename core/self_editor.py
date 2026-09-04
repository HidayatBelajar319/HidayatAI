"""
Self-Editing System for Hidayat AI.

Enables the AI to edit its own code inside Hidayat-AI-Main/ with explicit
user permission, automatic backups, and integrity verification.

Usage (standalone):
    from core.self_editor import SelfEditor
    editor = SelfEditor()
    editor.request_edit("ui.py", new_content, "Fix dashboard layout")

Usage (from main.py / CLI):
    python -m core.self_editor          # runs interactive mode
    python -m core.self_editor --list-backups
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def _get_base_dir() -> Path:
    """Resolve the project root (works for both frozen and source layouts)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent  # core/self_editor.py -> root


PROJECT_ROOT: Path = _get_base_dir()
MAIN_DIR: Path = PROJECT_ROOT / "Hidayat-AI-Main"
SOURCE_DIR: Path = PROJECT_ROOT / "Hidayat-AI-Source-Code"
BACKUP_DIR: Path = MAIN_DIR / "backups"
MANIFEST_PATH: Path = BACKUP_DIR / "manifest.json"
SECURITY_LOG_PATH: Path = SOURCE_DIR / "SECURITY.md"

# ---------------------------------------------------------------------------
# Protected paths — NEVER editable, even with explicit user permission.
# ---------------------------------------------------------------------------

# The entire Hidayat-AI-Source-Code/ folder is off-limits.
SOURCE_DIR_NAME: str = "Hidayat-AI-Source-Code"

# Files/folders that must NEVER be touched inside Hidayat-AI-Main/.
PROTECTED_PATHS: List[str] = [
    # Legal / governance
    "LICENSE",
    "TRADEMARK.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    # Credentials
    "config/api_keys.json",
    "config/brahma_connect.json",
    "config/discord_bot.json",
    # Entry point
    "main.py",
    # Core systems
    "core/identity.py",
    "core/self_editor.py",
    "core/security_guard.py",
    "core/self_improvement.py",
]

# ---------------------------------------------------------------------------
# SelfEditor
# ---------------------------------------------------------------------------

class SelfEditor:
    """Handles permission-gated, backup-protected edits to Hidayat-AI-Main/.

    Parameters
    ----------
    approval_callback : callable, optional
        ``fn(file_path, reason) -> bool``.  When *None*, interactive ``input()``
        is used to request user permission.
    """

    def __init__(self, approval_callback: Optional[Callable[[str, str], bool]] = None):
        self._approval_callback = approval_callback
        self._ensure_backup_dir()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_edit(self, file_path: str, new_content: str, reason: str) -> Dict[str, Any]:
        """Validate path, request permission, create backup, and apply change.

        Parameters
        ----------
        file_path : str
            Path to the target file. May be absolute or relative to
            Hidayat-AI-Main/.
        new_content : str
            The full new content to write to the file.
        reason : str
            Human-readable explanation of why the edit is being made.

        Returns
        -------
        dict
            ``{"success": bool, "message": str, ...}`` with details about the
            outcome (backup path, checksum, etc.).
        """
        # 1. Validate the path
        resolved = self.validate_path(file_path)
        if resolved is None:
            self._log_attempt(file_path, reason, approved=False, detail="path validation failed")
            return {
                "success": False,
                "message": (
                    f"Path '{file_path}' is invalid: it is either outside "
                    "Hidayat-AI-Main/ or in the protected list."
                ),
            }

        if not resolved.is_file():
            self._log_attempt(file_path, reason, approved=False, detail="target is not a file")
            return {
                "success": False,
                "message": f"Target '{resolved}' does not exist or is not a regular file.",
            }

        # 2. Request user permission
        approved = self._request_permission(str(resolved), reason)
        if not approved:
            self._log_attempt(file_path, reason, approved=False, detail="user denied")
            return {
                "success": False,
                "message": "Edit denied by user.",
            }

        # 3. Create a backup of the current content
        backup_path = self.create_backup(resolved)
        if backup_path is None:
            self._log_attempt(file_path, reason, approved=False, detail="backup creation failed")
            return {
                "success": False,
                "message": "Failed to create a backup before editing.",
            }

        # 4. Apply the change
        try:
            resolved.write_text(new_content, encoding="utf-8")
        except OSError as exc:
            self._log_attempt(file_path, reason, approved=False, detail=f"write failed: {exc}")
            return {
                "success": False,
                "message": f"Failed to write file: {exc}",
                "backup_path": str(backup_path),
            }

        # 5. Update the integrity manifest
        checksum = self.compute_checksum(resolved)
        self._update_manifest(str(resolved), checksum)

        self._log_attempt(file_path, reason, approved=True, detail="edit applied")
        return {
            "success": True,
            "message": f"Edit applied to '{resolved}'.",
            "backup_path": str(backup_path),
            "checksum": checksum,
        }

    def validate_path(self, file_path: str) -> Optional[Path]:
        """Ensure *file_path* is inside Hidayat-AI-Main/ and NOT protected.

        Returns the resolved :class:`pathlib.Path` if valid, otherwise ``None``.
        """
        # Normalise separators
        normed = file_path.replace("\\", "/")

        # Reject anything that points into the Source-Code folder
        if SOURCE_DIR_NAME in Path(normed).parts:
            return None

        # Resolve relative to MAIN_DIR if not absolute
        candidate = Path(file_path)
        if not candidate.is_absolute():
            candidate = MAIN_DIR / candidate

        resolved = candidate.resolve()

        # Path-traversal guard: must stay inside MAIN_DIR
        try:
            resolved.relative_to(MAIN_DIR.resolve())
        except ValueError:
            return None

        # Protected-path check (relative to MAIN_DIR)
        rel = resolved.relative_to(MAIN_DIR.resolve()).as_posix()
        if self._is_protected(rel):
            return None

        return resolved

    def create_backup(self, file_path: str | Path) -> Optional[Path]:
        """Copy *file_path* to ``Hidayat-AI-Main/backups/{timestamp}_{filename}``.

        Returns the destination :class:`pathlib.Path`, or ``None`` on failure.
        """
        src = Path(file_path)
        if not src.is_file():
            return None

        self._ensure_backup_dir()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        dst = BACKUP_DIR / f"{timestamp}_{src.name}"

        try:
            shutil.copy2(src, dst)
        except OSError:
            return None
        return dst

    def compute_checksum(self, file_path: str | Path) -> str:
        """Return the SHA-256 hex digest of a file's content."""
        path = Path(file_path)
        hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
        except OSError:
            return ""
        return hasher.hexdigest()

    def verify_integrity(self, file_path: str | Path, expected_checksum: str) -> bool:
        """Detect unauthorized changes by comparing current checksum to expected."""
        actual = self.compute_checksum(file_path)
        if not actual or not expected_checksum:
            return False
        return actual == expected_checksum

    def list_backups(self) -> List[Dict[str, str]]:
        """Return a list of backup files with metadata.

        Each entry: ``{"filename": str, "path": str, "size": int, "modified": str}``
        """
        self._ensure_backup_dir()
        backups: List[Dict[str, str]] = []
        for f in sorted(BACKUP_DIR.iterdir(), key=lambda p: p.name):
            if f.is_file() and f.name != "manifest.json":
                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "modified": datetime.datetime.fromtimestamp(
                        stat.st_mtime
                    ).isoformat(),
                })
        return backups

    def restore_backup(self, backup_filename: str) -> Dict[str, Any]:
        """Restore a file from a backup, with user permission.

        Parameters
        ----------
        backup_filename : str
            The backup file name (e.g. ``20260101_120000_123456_ui.py``).

        Returns
        -------
        dict
            ``{"success": bool, "message": str, ...}``
        """
        backup_path = BACKUP_DIR / backup_filename
        if not backup_path.is_file():
            return {"success": False, "message": f"Backup '{backup_filename}' not found."}

        # Derive the original filename from the backup name.
        # Format: {timestamp}_{original_filename} where timestamp is
        # YYYYMMDD_HHMMSS_ffffff (three underscore-separated parts).
        parts = backup_filename.split("_", 3)
        if len(parts) < 4:
            return {
                "success": False,
                "message": f"Cannot determine original path from backup name '{backup_filename}'.",
            }
        original_name = parts[3]

        # We don't know the original directory, so ask the user for the target.
        reason = f"Restore file from backup '{backup_filename}'"
        approved = self._request_permission(f"restore:{backup_filename}", reason)
        if not approved:
            self._log_attempt(backup_filename, reason, approved=False, detail="restore denied")
            return {"success": False, "message": "Restore denied by user."}

        # Search for the original file by name across MAIN_DIR (excluding backups).
        matches: List[Path] = []
        for candidate in MAIN_DIR.rglob("*"):
            if "backups" in candidate.parts:
                continue
            if candidate.name == original_name and candidate.is_file():
                matches.append(candidate)

        if not matches:
            return {
                "success": False,
                "message": (
                    f"Could not locate original file '{original_name}' in Hidayat-AI-Main/. "
                    "Please specify the target path manually."
                ),
            }

        # If multiple matches, pick the first (or ask). For simplicity, use first.
        target = matches[0]
        if not self.validate_path(str(target)):
            return {
                "success": False,
                "message": f"Target '{target}' is protected or invalid.",
            }

        # Backup the current state before overwriting
        pre_backup = self.create_backup(target)

        try:
            shutil.copy2(backup_path, target)
        except OSError as exc:
            self._log_attempt(backup_filename, reason, approved=True, detail=f"restore failed: {exc}")
            return {"success": False, "message": f"Restore failed: {exc}"}

        checksum = self.compute_checksum(target)
        self._update_manifest(str(target), checksum)
        self._log_attempt(backup_filename, reason, approved=True, detail="restore applied")

        return {
            "success": True,
            "message": f"Restored '{target}' from '{backup_filename}'.",
            "target": str(target),
            "pre_restore_backup": str(pre_backup) if pre_backup else None,
            "checksum": checksum,
        }

    # ------------------------------------------------------------------
    # Integration with SelfImprovementEngine
    # ------------------------------------------------------------------

    def apply_improvement(self, file_path: str, new_content: str, reason: str) -> Dict[str, Any]:
        """Apply an approved improvement proposal from SelfImprovementEngine.

        This is a thin wrapper around :meth:`request_edit` that can be called
        by ``SelfImprovementEngine`` once a proposal has been approved.
        """
        return self.request_edit(file_path, new_content, reason)

    # ------------------------------------------------------------------
    # Manifest / integrity helpers
    # ------------------------------------------------------------------

    def load_manifest(self) -> Dict[str, str]:
        """Load the checksum manifest (``{file: checksum}``)."""
        if MANIFEST_PATH.exists():
            try:
                return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save_manifest(self, manifest: Dict[str, str]) -> None:
        """Persist the checksum manifest to ``backups/manifest.json``."""
        self._ensure_backup_dir()
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _update_manifest(self, file_path: str, checksum: str) -> None:
        """Add/update a file's checksum in the manifest."""
        manifest = self.load_manifest()
        manifest[str(file_path)] = checksum
        self.save_manifest(manifest)

    def verify_all(self) -> Dict[str, Any]:
        """Verify integrity of all files tracked in the manifest.

        Returns a dict with ``verified`` and ``tampered`` lists.
        """
        manifest = self.load_manifest()
        verified: List[str] = []
        tampered: List[str] = []
        missing: List[str] = []

        for path_str, expected in manifest.items():
            p = Path(path_str)
            if not p.is_file():
                missing.append(path_str)
                continue
            if self.verify_integrity(p, expected):
                verified.append(path_str)
            else:
                tampered.append(path_str)

        return {
            "total": len(manifest),
            "verified": verified,
            "tampered": tampered,
            "missing": missing,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_protected(self, rel: str) -> bool:
        """Check whether a MAIN_DIR-relative path is protected."""
        normed = rel.replace("\\", "/")
        for prot in PROTECTED_PATHS:
            if normed == prot or normed.startswith(prot.rstrip("*")):
                return True
        return False

    def _ensure_backup_dir(self) -> Path:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return BACKUP_DIR

    def _request_permission(self, target: str, reason: str) -> bool:
        """Ask the user (or callback) for approval."""
        if self._approval_callback is not None:
            return bool(self._approval_callback(target, reason))

        print("\n" + "=" * 60)
        print("  SELF-EDIT PERMISSION REQUEST")
        print("=" * 60)
        print(f"  Target : {target}")
        print(f"  Reason : {reason}")
        answer = input("  Approve this edit? [y/N] ").strip().lower()
        return answer in ("y", "yes")

    def _log_attempt(self, target: str, reason: str, approved: bool, detail: str = "") -> None:
        """Log an edit attempt (approved/denied) to SECURITY.md."""
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        status = "APPROVED" if approved else "DENIED"
        entry = (
            f"- `{timestamp}` **{status}** — target: `{target}` | reason: {reason}"
            + (f" | detail: {detail}" if detail else "")
        )

        try:
            if SECURITY_LOG_PATH.exists():
                existing = SECURITY_LOG_PATH.read_text(encoding="utf-8")
                # Append under a dedicated section if present, else at the end.
                marker = "## Self-Edit Audit Log"
                if marker in existing:
                    # Insert after the marker line
                    idx = existing.index(marker) + len(marker)
                    existing = existing[:idx] + "\n" + entry + existing[idx:]
                else:
                    existing = existing.rstrip() + f"\n\n{marker}\n\n{entry}\n"
                SECURITY_LOG_PATH.write_text(existing, encoding="utf-8")
            else:
                header = "# Security Policy\n\n## Self-Edit Audit Log\n\n"
                SECURITY_LOG_PATH.write_text(header + entry + "\n", encoding="utf-8")
        except OSError:
            # Logging must never break the edit flow.
            pass


# ---------------------------------------------------------------------------
# Standalone / CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Hidayat AI — Self-Editing System",
    )
    parser.add_argument(
        "--list-backups", action="store_true",
        help="List all backup files.",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Verify integrity of all manifest-tracked files.",
    )
    parser.add_argument(
        "--edit", nargs=3, metavar=("FILE", "CONTENT_FILE", "REASON"),
        help="Request an edit: FILE path, CONTENT_FILE (file containing new content), REASON.",
    )
    parser.add_argument(
        "--restore", type=str, default=None,
        help="Restore a file from a backup by backup filename.",
    )
    args = parser.parse_args()

    editor = SelfEditor()

    if args.list_backups:
        backups = editor.list_backups()
        if not backups:
            print("No backups found.")
        else:
            print(f"Found {len(backups)} backup(s):\n")
            for b in backups:
                print(f"  {b['filename']}  ({b['size']} bytes, {b['modified']})")
    elif args.verify:
        result = editor.verify_all()
        print(f"Total tracked files: {result['total']}")
        print(f"Verified: {len(result['verified'])}")
        print(f"Tampered: {len(result['tampered'])}")
        print(f"Missing : {len(result['missing'])}")
        if result["tampered"]:
            print("\n⚠️  TAMPERED FILES:")
            for f in result["tampered"]:
                print(f"  - {f}")
        if result["missing"]:
            print("\nMissing files:")
            for f in result["missing"]:
                print(f"  - {f}")
    elif args.edit:
        file_path, content_file, reason = args.edit
        try:
            new_content = Path(content_file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Could not read content file: {exc}")
            return
        result = editor.request_edit(file_path, new_content, reason)
        print(json.dumps(result, indent=2, default=str))
    elif args.restore:
        result = editor.restore_backup(args.restore)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Hidayat AI Self-Editing System")
        print("Use --list-backups, --verify, --edit, or --restore.")


if __name__ == "__main__":
    main()
