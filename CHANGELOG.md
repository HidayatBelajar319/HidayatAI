# Changelog

## [2026-09-05] - Ultron Sphere, Floating Orb, Portable Data Dir, EXE Build
- Added animated gold Ultron sphere centerpiece on dashboard (floating_orb.py)
- Added floating always-on-top corner orb with mini chat popup (no main window needed)
- Added central path resolver with user-configurable data dir (core/paths.py)
- Wired identity config to user data dir with legacy migration (core/identity.py)
- Added Data Location settings card (Change/Portable/Reset) in ui.py
- Swapped all logo references to assets/UltronJarvis_Logo.png/.ico
- Removed hardcoded user paths (dynamic detection via env vars)
- Fixed EXE build: removed --exclude-module=unittest (broke pyparsing chain)
- Added cleanup_ultronjarvis.bat (removes generated shortcuts, data dirs, firewall rules)

## [2026-09-04] - Initial Hidayat AI (Ultron Jarvis) Setup
- Rebranded from Brahma Echo to Ultron Jarvis (Hidayat AI)
- Added self-improvement system (core/self_improvement.py)
- Added self-editing system with backups (core/self_editor.py)
- Added anti-jailbreak security system (core/security_guard.py)
- Enhanced dashboard for LocalHost HTTP deployment
- Added proper credits per Suryaansh's format
- License and trademark preserved per original terms
