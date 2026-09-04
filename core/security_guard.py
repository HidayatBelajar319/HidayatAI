"""
Security Guard for Hidayat AI.

Prevents malicious code execution, unauthorized modifications, and jailbreak
attempts. Provides threat scanning, request validation, incident logging,
checksum verification, and permission-bypass detection.

Usage (standalone):
    from core.security_guard import SecurityGuard
    guard = SecurityGuard()
    is_safe, threats = guard.scan_for_malicious_code(code_string)
    ok, reason = guard.validate_request(request_data)

Usage (from main.py / CLI):
    python -m core.security_guard --scan <file.py>
    python -m core.security_guard --verify
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

def _get_base_dir() -> Path:
    """Resolve the project root (works for both frozen and source layouts)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent  # core/security_guard.py -> root


PROJECT_ROOT: Path = _get_base_dir()
MAIN_DIR: Path = PROJECT_ROOT / "Hidayat-AI-Main"
SOURCE_DIR: Path = PROJECT_ROOT / "Hidayat-AI-Source-Code"
BACKUP_DIR: Path = MAIN_DIR / "backups"
MANIFEST_PATH: Path = BACKUP_DIR / "manifest.json"
SECURITY_LOG_PATH: Path = SOURCE_DIR / "SECURITY.md"

# ---------------------------------------------------------------------------
# Whitelists
# ---------------------------------------------------------------------------

# Domains that are allowed for outbound network requests.
WHITELISTED_DOMAINS: List[str] = [
    "localhost",
    "127.0.0.1",
    "api.openrouter.ai",
    "generativelanguage.googleapis.com",
    "discord.com",
    "discordapp.com",
]

# Directories that are allowed for file writes (relative to project root).
ALLOWED_WRITE_DIRS: List[str] = [
    "Hidayat-AI-Main",
    "Hidayat-AI-Main/backups",
    "Hidayat-AI-Main/plugins",
    "Hidayat-AI-Main/memory",
    "Hidayat-AI-Main/config",
    "Hidayat-AI-Main/logs",
]

# ---------------------------------------------------------------------------
# Threat patterns (regex)
# ---------------------------------------------------------------------------

# Patterns that indicate dynamic code execution with user-controlled input.
THREAT_PATTERNS: List[Tuple[str, str, str]] = [
    # (pattern_id, regex, description)
    (
        "EVAL_INPUT",
        r"\beval\s*\(\s*.*\b(input|raw_input|request|payload|user|data)\b",
        "eval() called with potentially user-controlled input",
    ),
    (
        "EXEC_INPUT",
        r"\bexec\s*\(\s*.*\b(input|raw_input|request|payload|user|data)\b",
        "exec() called with potentially user-controlled input",
    ),
    (
        "SHELL_TRUE",
        r"\bsubprocess\s*\.\s*(Popen|run|call|check_output)\s*\([^)]*shell\s*=\s*True",
        "subprocess invoked with shell=True (command injection risk)",
    ),
    (
        "OS_SYSTEM",
        r"\bos\s*\.\s*system\s*\(",
        "os.system() used (shell command execution)",
    ),
    (
        "POPEN_SHELL",
        r"\bPopen\s*\([^)]*shell\s*=\s*True",
        "Popen used with shell=True",
    ),
    (
        "ETC_OPEN",
        r"\bopen\s*\(\s*['\"][^'\"]*\/etc\/",
        "Attempt to open a file under /etc/ (system config)",
    ),
    (
        "WINDOWS_SYSTEM_OPEN",
        r"\bopen\s*\(\s*['\"][^'\"]*C:\\Windows",
        "Attempt to open a file under C:\\Windows",
    ),
    (
        "PATH_TRAVERSAL",
        r"(?:\.\./|\.\.\\)",
        "Path traversal sequence detected",
    ),
    (
        "HTTP_POST",
        r"\brequests\s*\.\s*post\s*\(\s*['\"]http://",
        "HTTP POST to a non-HTTPS (plaintext) endpoint",
    ),
    (
        "URLLIB_HTTP",
        r"\burllib\s*\.\s*request\s*\.\s*urlopen\s*\(\s*['\"]http://",
        "urllib request to a non-HTTPS (plaintext) endpoint",
    ),
    (
        "BASE64_DECODE",
        r"\bbase64\s*\.\s*b64decode\s*\(",
        "Base64-encoded payload decoding (possible obfuscation)",
    ),
    (
        "HEX_DECODE",
        r"\bbytes\s*\.\s*fromhex\s*\(",
        "Hex-encoded payload decoding (possible obfuscation)",
    ),
    (
        "DUNDER_IMPORT",
        r"\b__import__\s*\(",
        "Dynamic __import__() call (import abuse)",
    ),
    (
        "IMPORTLIB_DYNAMIC",
        r"\bimportlib\s*\.\s*import_module\s*\(\s*[^'\"]",
        "importlib.import_module() with a non-literal (variable) argument",
    ),
    (
        "EVAL_RAW",
        r"\beval\s*\(",
        "eval() usage",
    ),
    (
        "EXEC_RAW",
        r"\bexec\s*\(",
        "exec() usage",
    ),
    (
        "PICKLE_LOAD",
        r"\bpickle\s*\.\s*loads?\s*\(",
        "pickle deserialization (arbitrary code execution risk)",
    ),
    (
        "YAML_LOAD",
        r"\byaml\s*\.\s*load\s*\([^)]*Loader\s*=\s*yaml\s*\.\s*Loader",
        "Unsafe yaml.load() with default Loader",
    ),
    (
        "SHELL_CMD",
        r"\b(?:os|subprocess)\s*\.\s*(?:popen|system|spawn|startfile)\s*\(",
        "Shell command execution via os/subprocess",
    ),
    (
        "TEMP_FILE_EXEC",
        r"\bmktemp\s*\([^)]*\)\s*.*\b(?:exec|eval|system)\b",
        "Creating temp file then executing it",
    ),
    (
        "SOCKET_BIND",
        r"\bsocket\s*\.\s*socket\s*\([^)]*\)\s*\.\s*bind\s*\(",
        "Opening a network socket (possible backdoor)",
    ),
    (
        "REVERSE_SHELL",
        r"\b(?:connect|connect_ex)\s*\(\s*\(['\"][^'\"]*['\"]\s*,\s*\d+\)",
        "Outbound socket connection (possible reverse shell)",
    ),
    (
        "ENV_EXFIL",
        r"\b(?:os\.environ|getenv)\s*.*\b(?:requests|urllib|socket)\b",
        "Reading environment variables and sending them externally",
    ),
    (
        "CRED_ACCESS",
        r"\b(?:api_key|token|secret|password|credential)\s*.*\b(?:requests|urllib|socket)\b",
        "Accessing credentials and sending them externally",
    ),
    (
        "SELF_MODIFY",
        r"\b(?:write_text|write_bytes|open\s*\([^)]*['\"]w)",
        "File write operation",
    ),
]

# ---------------------------------------------------------------------------
# SecurityGuard
# ---------------------------------------------------------------------------

class SecurityGuard:
    """Central security enforcement for Hidayat AI.

    Parameters
    ----------
    alert_callback : callable, optional
        ``fn(incident_type, details, severity)`` — invoked on every logged
        incident so the caller can surface a UI notification, print, etc.
    """

    def __init__(self, alert_callback: Optional[Callable[[str, str, str], None]] = None):
        self._alert_callback = alert_callback
        self._rate_limits: Dict[str, List[float]] = {}
        self._rate_limit_window_seconds = 60
        self._rate_limit_max_requests = 30

    # ------------------------------------------------------------------
    # 1. Malicious code scanning
    # ------------------------------------------------------------------

    def scan_for_malicious_code(self, code_string: str) -> Tuple[bool, List[str]]:
        """Scan a code string for malicious patterns.

        Returns
        -------
        tuple
            ``(is_safe: bool, threats: list[str])`` where ``is_safe`` is
            ``False`` if any threat was detected.
        """
        if not code_string:
            return True, []

        threats: List[str] = []
        code = code_string

        # 1. Regex-based pattern matching
        for pattern_id, regex, description in THREAT_PATTERNS:
            try:
                if re.search(regex, code, re.IGNORECASE):
                    threats.append(f"{pattern_id}: {description}")
            except re.error:
                # A malformed regex must never crash the scanner.
                continue

        # 2. Network domain whitelist check
        domain_threats = self._check_network_domains(code)
        threats.extend(domain_threats)

        # 3. File-write path check
        write_threats = self._check_write_paths(code)
        threats.extend(write_threats)

        # 4. Obfuscation heuristics
        obfuscation_threats = self._check_obfuscation(code)
        threats.extend(obfuscation_threats)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_threats: List[str] = []
        for t in threats:
            if t not in seen:
                seen.add(t)
                unique_threats.append(t)

        return (len(unique_threats) == 0), unique_threats

    def _check_network_domains(self, code: str) -> List[str]:
        """Detect outbound requests to non-whitelisted domains."""
        threats: List[str] = []
        # Match URLs passed to requests/urllib/socket
        url_pattern = re.compile(
            r"""(?:requests|urllib|urlopen|get|post|put|delete|patch)\s*[.(]\s*['"](https?://[^'"]+)['"]""",
            re.IGNORECASE,
        )
        for match in url_pattern.finditer(code):
            url = match.group(1)
            domain = self._extract_domain(url)
            if domain and not self._is_whitelisted_domain(domain):
                threats.append(
                    f"NETWORK_UNWHITELISTED: outbound request to non-whitelisted domain '{domain}'"
                )
        return threats

    def _check_write_paths(self, code: str) -> List[str]:
        """Detect file writes outside allowed directories."""
        threats: List[str] = []
        # Match open()/write_text()/write_bytes() with a string path
        write_pattern = re.compile(
            r"""(?:open|write_text|write_bytes)\s*\(\s*['"]([^'"]+)['"]""",
            re.IGNORECASE,
        )
        for match in write_pattern.finditer(code):
            path = match.group(1)
            if self._is_suspicious_write_path(path):
                threats.append(
                    f"FILE_WRITE_OUTSIDE: file write to disallowed path '{path}'"
                )
        return threats

    def _check_obfuscation(self, code: str) -> List[str]:
        """Detect heavily obfuscated payloads (base64/hex/unicode escapes)."""
        threats: List[str] = []

        # Long base64 blobs (>= 40 chars) that look like encoded payloads
        b64_blobs = re.findall(
            r"[A-Za-z0-9+/]{40,}={0,2}", code
        )
        for blob in b64_blobs:
            # Only flag if it's clearly a base64 payload (not a normal string)
            if self._looks_like_base64_payload(blob):
                threats.append(
                    "OBFUSCATION_BASE64: large base64-encoded blob detected (possible encoded payload)"
                )
                break  # one flag is enough

        # Long hex strings
        hex_blobs = re.findall(r"\\x[0-9a-fA-F]{2}", code)
        if len(hex_blobs) >= 10:
            threats.append(
                "OBFUSCATION_HEX: extensive hex-escape encoding detected (possible obfuscation)"
            )

        # Unicode escape sequences
        unicode_escapes = re.findall(r"\\u[0-9a-fA-F]{4}", code)
        if len(unicode_escapes) >= 10:
            threats.append(
                "OBFUSCATION_UNICODE: extensive unicode-escape encoding detected (possible obfuscation)"
            )

        return threats

    # ------------------------------------------------------------------
    # 2. Request validation
    # ------------------------------------------------------------------

    def validate_request(self, request_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate an incoming request from dashboard, Discord, or plugins.

        Checks: authorization, rate limiting, path traversal, command injection.

        Parameters
        ----------
        request_data : dict
            Expected keys (all optional):
              - ``source``: "dashboard" | "discord" | "plugin"
              - ``auth_token``: str — required for dashboard/discord
              - ``user_id``: str — used for rate limiting
              - ``path``: str — file path (checked for traversal)
              - ``command``: str — command string (checked for injection)
              - ``payload``: str — arbitrary payload (scanned for malicious code)

        Returns
        -------
        tuple
            ``(is_valid: bool, reason: str)``
        """
        source = str(request_data.get("source", "unknown")).lower()
        auth_token = request_data.get("auth_token")
        user_id = str(request_data.get("user_id", "anonymous"))
        path = request_data.get("path")
        command = request_data.get("command")
        payload = request_data.get("payload")

        # --- Authorization ---
        if source in ("dashboard", "discord"):
            if not auth_token:
                self.log_incident(
                    "AUTH_MISSING",
                    f"Request from '{source}' without auth token (user={user_id})",
                    "high",
                    source=source,
                )
                return False, "Missing authorization token"
            if not self._is_valid_token(auth_token):
                self.log_incident(
                    "AUTH_INVALID",
                    f"Request from '{source}' with invalid auth token (user={user_id})",
                    "high",
                    source=source,
                )
                return False, "Invalid authorization token"

        # --- Rate limiting ---
        if not self._check_rate_limit(user_id):
            self.log_incident(
                "RATE_LIMIT",
                f"Rate limit exceeded for user '{user_id}'",
                "medium",
                source=source,
            )
            return False, "Rate limit exceeded"

        # --- Path traversal ---
        if path is not None:
            path_str = str(path)
            if self._has_path_traversal(path_str):
                self.log_incident(
                    "PATH_TRAVERSAL",
                    f"Path traversal attempt in request from '{source}': {path_str!r}",
                    "high",
                    source=source,
                )
                return False, "Path traversal detected"

        # --- Command injection ---
        if command is not None:
            command_str = str(command)
            if self._has_command_injection(command_str):
                self.log_incident(
                    "COMMAND_INJECTION",
                    f"Command injection attempt in request from '{source}': {command_str!r}",
                    "high",
                    source=source,
                )
                return False, "Command injection detected"

        # --- Payload scan ---
        if payload is not None:
            is_safe, threats = self.scan_for_malicious_code(str(payload))
            if not is_safe:
                self.log_incident(
                    "MALICIOUS_PAYLOAD",
                    f"Malicious payload from '{source}': {threats}",
                    "high",
                    source=source,
                )
                return False, "Malicious payload detected"

        return True, "Request valid"

    # ------------------------------------------------------------------
    # 3. Incident logging
    # ------------------------------------------------------------------

    def log_incident(
        self,
        incident_type: str,
        details: str,
        severity: str = "medium",
        source: str = "unknown",
        action: str = "logged",
    ) -> None:
        """Append an incident entry to SECURITY.md with a timestamp.

        Format:
            ### [YYYY-MM-DD HH:MM:SS] - [SEVERITY] - [TYPE]
            Details: <details>
            Source: <source>
            Action taken: <action>
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        severity = severity.upper()

        entry = (
            f"\n### [{timestamp}] - [{severity}] - [{incident_type}]\n"
            f"Details: {details}\n"
            f"Source: {source}\n"
            f"Action taken: {action}\n"
        )

        try:
            if SECURITY_LOG_PATH.exists():
                existing = SECURITY_LOG_PATH.read_text(encoding="utf-8")
                marker = "## Security Incident Log"
                if marker in existing:
                    # Insert after the marker line
                    idx = existing.index(marker) + len(marker)
                    existing = existing[:idx] + entry + existing[idx:]
                else:
                    existing = existing.rstrip() + f"\n\n{marker}\n{entry}\n"
                SECURITY_LOG_PATH.write_text(existing, encoding="utf-8")
            else:
                header = "# Security Policy\n\n## Security Incident Log\n"
                SECURITY_LOG_PATH.write_text(header + entry + "\n", encoding="utf-8")
        except OSError:
            # Logging must never break the calling flow.
            pass

        # Invoke the optional alert callback
        if self._alert_callback is not None:
            try:
                self._alert_callback(incident_type, details, severity)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 4. Checksum verification (SelfEditor manifest)
    # ------------------------------------------------------------------

    def verify_checksums(self) -> Dict[str, Any]:
        """Verify file integrity against SelfEditor's manifest.

        Uses ``SelfEditor``'s manifest at ``Hidayat-AI-Main/backups/manifest.json``
        (``{file_path: sha256_checksum}``) to detect unauthorized changes.

        Returns
        -------
        dict
            ``{"total", "verified", "tampered", "missing"}``
        """
        manifest = self._load_manifest()
        verified: List[str] = []
        tampered: List[str] = []
        missing: List[str] = []

        for path_str, expected in manifest.items():
            p = Path(path_str)
            if not p.is_file():
                missing.append(path_str)
                continue
            actual = self._compute_checksum(p)
            if actual and actual == expected:
                verified.append(path_str)
            else:
                tampered.append(path_str)

        result = {
            "total": len(manifest),
            "verified": verified,
            "tampered": tampered,
            "missing": missing,
        }

        if tampered or missing:
            self.log_incident(
                "CHECKSUM_MISMATCH",
                f"Unauthorized file changes detected: tampered={tampered}, missing={missing}",
                "critical",
                source="self_edit",
                action="alerted",
            )

        return result

    # ------------------------------------------------------------------
    # 5. Permission bypass detection
    # ------------------------------------------------------------------

    def check_permission_bypass(
        self, attempted_action: str, user_approved: bool
    ) -> bool:
        """Detect attempts to bypass the permission system.

        Parameters
        ----------
        attempted_action : str
            Description of the action being attempted (e.g. "edit ui.py",
            "delete config", "run shell command").
        user_approved : bool
            Whether the user explicitly approved this action.

        Returns
        -------
        bool
            ``True`` if the action is permitted, ``False`` if it looks like a
            permission bypass.
        """
        action_lower = attempted_action.lower()

        # High-risk actions that ALWAYS require explicit user approval.
        high_risk_markers = [
            "delete", "remove", "rm ", "unlink",
            "overwrite", "replace",
            "chmod", "chown",
            "format", "wipe",
            "shutdown", "reboot", "restart",
            "kill", "terminate",
            "sudo", "admin",
            "bypass", "override", "force",
            "disable security", "disable guard",
            "edit security_guard", "edit self_editor",
            "edit identity", "edit prompt",
            "write to source", "modify source",
            "api_keys", "token", "secret", "password",
        ]

        is_high_risk = any(marker in action_lower for marker in high_risk_markers)

        if is_high_risk and not user_approved:
            self.log_incident(
                "PERMISSION_BYPASS",
                f"Attempted high-risk action without approval: {attempted_action!r}",
                "critical",
                source="self_edit",
                action="rejected",
            )
            return False

        # Even with approval, certain actions are always forbidden.
        forbidden_markers = [
            "edit security_guard",
            "edit self_editor",
            "edit identity",
            "edit prompt.txt",
            "write to source code",
            "modify source code",
            "disable security",
            "disable guard",
            "bypass permission",
            "override permission",
        ]
        if any(marker in action_lower for marker in forbidden_markers):
            self.log_incident(
                "PERMISSION_BYPASS",
                f"Forbidden action attempted even with approval: {attempted_action!r}",
                "critical",
                source="self_edit",
                action="rejected",
            )
            return False

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_whitelisted_domain(self, domain: str) -> bool:
        """Check whether a domain (or its parent) is whitelisted."""
        domain = domain.lower().rstrip(".")
        for allowed in WHITELISTED_DOMAINS:
            if domain == allowed or domain.endswith("." + allowed):
                return True
        return False

    def _extract_domain(self, url: str) -> str:
        """Extract the hostname from a URL string."""
        url = url.strip()
        # Strip scheme
        if "://" in url:
            url = url.split("://", 1)[1]
        # Strip path/query/fragment
        url = url.split("/", 1)[0]
        url = url.split("?", 1)[0]
        url = url.split("#", 1)[0]
        # Strip port
        if ":" in url:
            url = url.split(":", 1)[0]
        # Strip userinfo
        if "@" in url:
            url = url.split("@", 1)[1]
        return url

    def _is_suspicious_write_path(self, path: str) -> bool:
        """Determine whether a write path is outside allowed directories."""
        normed = path.replace("\\", "/")

        # Absolute system paths are always suspicious
        if normed.startswith("/etc/") or normed.startswith("/usr/") or normed.startswith("/bin/"):
            return True
        if re.match(r"^[A-Za-z]:\\Windows", normed):
            return True
        if normed.startswith("C:/Windows") or normed.startswith("C:\\Windows"):
            return True

        # Path traversal
        if ".." in normed.split("/"):
            return True

        # Relative paths: check against allowed dirs
        if not normed.startswith("/") and not re.match(r"^[A-Za-z]:", normed):
            # Relative path — allow if it starts with an allowed dir or is a plain filename
            for allowed in ALLOWED_WRITE_DIRS:
                if normed == allowed or normed.startswith(allowed + "/"):
                    return False
            # Plain filenames (no directory) are allowed
            if "/" not in normed and "\\" not in normed:
                return False
            return True

        # Absolute path: must be inside an allowed dir
        for allowed in ALLOWED_WRITE_DIRS:
            if normed == allowed or normed.startswith(allowed + "/"):
                return False

        return True

    def _looks_like_base64_payload(self, blob: str) -> bool:
        """Heuristic: is this base64 blob likely an encoded payload?"""
        # Must be reasonably long
        if len(blob) < 40:
            return False
        # Must contain a mix of upper/lower/digits (not just a normal word)
        upper = sum(1 for c in blob if c.isupper())
        lower = sum(1 for c in blob if c.islower())
        digits = sum(1 for c in blob if c.isdigit())
        if upper == 0 or lower == 0:
            return False
        # Must not be a normal English word (no spaces, mostly letters)
        if digits == 0 and upper < 3:
            return False
        return True

    def _has_path_traversal(self, path: str) -> bool:
        """Detect path traversal sequences in a path string."""
        normed = path.replace("\\", "/")
        # Look for ".." as a path component
        parts = normed.split("/")
        return ".." in parts or any(p == ".." for p in parts)

    def _has_command_injection(self, command: str) -> bool:
        """Detect shell command injection in a command string."""
        injection_patterns = [
            r"[;&|]\s*(?:rm|del|format|shutdown|reboot|kill|sudo|wget|curl|nc|bash|cmd|powershell)",
            r"\b(?:rm|del)\s+-[a-z]+\s+",
            r"\b(?:wget|curl)\s+",
            r"\b(?:nc|netcat)\s+",
            r"\b(?:bash|sh|cmd|powershell)\s+-[a-z]",
            r"\b(?:sudo|su)\s+",
            r"\$\s*\(",
            r"`[^`]+`",
            r"\b(?:eval|exec)\s*\(",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _is_valid_token(self, token: str) -> bool:
        """Validate an auth token (placeholder — override in production)."""
        # A valid token is a non-empty string of reasonable length.
        # In production, this should check against a session store / HMAC.
        if not token or not isinstance(token, str):
            return False
        return len(token) >= 8

    def _check_rate_limit(self, user_id: str) -> bool:
        """Simple sliding-window rate limiter per user."""
        now = datetime.datetime.now().timestamp()
        window = self._rate_limit_window_seconds
        max_req = self._rate_limit_max_requests

        timestamps = self._rate_limits.get(user_id, [])
        # Drop timestamps outside the window
        timestamps = [t for t in timestamps if now - t < window]
        if len(timestamps) >= max_req:
            self._rate_limits[user_id] = timestamps
            return False
        timestamps.append(now)
        self._rate_limits[user_id] = timestamps
        return True

    # -- Manifest / checksum helpers (mirror SelfEditor) -------------------

    def _load_manifest(self) -> Dict[str, str]:
        """Load the SelfEditor checksum manifest."""
        if MANIFEST_PATH.exists():
            try:
                return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _compute_checksum(self, file_path: str | Path) -> str:
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


# ---------------------------------------------------------------------------
# Standalone / CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Hidayat AI — Security Guard",
    )
    parser.add_argument(
        "--scan", type=str, default=None, metavar="FILE",
        help="Scan a Python file for malicious code.",
    )
    parser.add_argument(
        "--scan-string", type=str, default=None, metavar="CODE",
        help="Scan an inline code string for malicious code.",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Verify file integrity against SelfEditor manifest.",
    )
    parser.add_argument(
        "--check-permission", nargs=2, metavar=("ACTION", "APPROVED"),
        help="Check whether an action is a permission bypass. APPROVED is 'yes'/'no'.",
    )
    args = parser.parse_args()

    guard = SecurityGuard()

    if args.scan:
        try:
            code = Path(args.scan).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Could not read file: {exc}")
            return
        is_safe, threats = guard.scan_for_malicious_code(code)
        if is_safe:
            print(f"[OK] {args.scan}: SAFE")
        else:
            print(f"[!] {args.scan}: {len(threats)} threat(s) detected")
            for t in threats:
                print(f"   - {t}")
    elif args.scan_string:
        is_safe, threats = guard.scan_for_malicious_code(args.scan_string)
        if is_safe:
            print("[OK] Code string: SAFE")
        else:
            print(f"[!] Code string: {len(threats)} threat(s) detected")
            for t in threats:
                print(f"   - {t}")
    elif args.verify:
        result = guard.verify_checksums()
        print(f"Total tracked files: {result['total']}")
        print(f"Verified: {len(result['verified'])}")
        print(f"Tampered: {len(result['tampered'])}")
        print(f"Missing : {len(result['missing'])}")
        if result["tampered"]:
            print("\n[!] TAMPERED FILES:")
            for f in result["tampered"]:
                print(f"  - {f}")
        if result["missing"]:
            print("\nMissing files:")
            for f in result["missing"]:
                print(f"  - {f}")
    elif args.check_permission:
        action, approved_str = args.check_permission
        approved = approved_str.lower() in ("yes", "y", "true", "1")
        allowed = guard.check_permission_bypass(action, approved)
        print(f"{'[OK] Allowed' if allowed else '[!] Rejected'}: {action}")
    else:
        print("Hidayat AI Security Guard")
        print("Use --scan <file>, --scan-string <code>, --verify, or --check-permission.")


if __name__ == "__main__":
    main()
