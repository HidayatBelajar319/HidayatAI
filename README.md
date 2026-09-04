<div align="center">
  <h1>Ultron Jarvis (Hidayat AI)</h1>

  <p><strong>Self-improving AI assistant derived from Brahma Echo</strong></p>
  <p>Voice-first automation · self-improvement · self-editing · anti-jailbreak security</p>
</div>

---

## Overview

Ultron Jarvis (Hidayat AI) is a self-improving Windows desktop AI assistant derived from the original Brahma Echo project. It combines voice and text control with automated workflows, screen-aware intelligence, and rich content generation — now enhanced with a self-improvement system, self-editing capabilities, and an anti-jailbreak security layer.

Designed for advanced desktop productivity, Hidayat AI delivers:

- Voice-first command and desktop automation
- Application control, browser workflows, and file handling
- Contextual screen inspection and adaptive task execution
- Presentation, document, and report generation
- Self-improvement and self-editing systems
- Anti-jailbreak security and request validation
- LocalHost HTTP dashboard deployment

## Quick Highlights

| Core capability | Why it matters |
|---|---|
| Voice-first assistant | Speak commands naturally and stay hands-free |
| Self-improvement system | Continuously learns and refines its own behavior |
| Self-editing with backups | Safely modifies its own code with mandatory backups |
| Anti-jailbreak security | Validates and sanitizes requests before execution |
| Screen-aware context | Ask about visible windows and on-screen content |
| Document automation | Create presentations, docs, spreadsheets, and PDFs |
| Plugin-ready | Extend features with lightweight Python plugins |

## Features

### Intelligent Assistant

- Unified voice and typed command handling
- Wake-word listening and responsive assistant activation
- Dynamic screen inspection for context-aware answers
- Automatic briefings with Edge TTS playback
- Gemini-first AI with OpenRouter fallback resilience

### Self-Improvement & Self-Editing

- Self-improvement system (`core/self_improvement.py`)
- Self-editing system with automatic backups (`core/self_editor.py`)
- All self-edits restricted to the Hidayat-AI-Main/ folder
- Protected files: LICENSE, TRADEMARK.md, main.py, core/*, config/*.json
- User permission required for every change

### Security & Anti-Jailbreak

- Request validation and sanitization (`core/security_guard.py`)
- Malicious code scanning before execution
- Path traversal prevention
- Command injection prevention
- Rate limiting on API endpoints
- Checksum-based file integrity verification
- Permission bypass detection

### Productivity & Automation

- Open and control Windows apps, windows, files, and system actions
- Browser automation with Playwright-driven workflows
- Contextual automation based on screen content and notifications
- Reminder, meeting assistance, and notification management

### Content & Office Tools

- Generate presentation decks, summaries, and slide content
- Create Word documents and spreadsheets from prompts
- Export polished reports and deliverables as PDF
- Build landing pages and website workspaces locally

### Integrations

- Discord bridge for remote commands and collaboration
- OpenRouter fallback for uninterrupted AI access
- Configurable voice, UI, startup, and notification settings
- LocalHost HTTP dashboard deployment

## Getting Started

### Prerequisites

- Windows 10 or Windows 11
- Python 3.11 or Python 3.12
- Git installed
- Gemini API key
- OpenRouter API key (optional but recommended)

### 1. Clone the repository

```powershell
git clone https://github.com/titechprabhasolutions/Brahma-Echo.git
cd Hidayat-AI-Source-Code
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
playwright install
```

### 4. Configure API credentials

Create `config/api_keys.json` with your keys:

```json
{
  "gemini_api_key": "YOUR_GEMINI_API_KEY",
  "openrouter_api_key": "YOUR_OPENROUTER_API_KEY"
}
```

#### Gemini API Key

1. Create a Google Cloud or Gemini account.
2. Enable Gemini API access for your project.
3. Add the generated key to `gemini_api_key`.

#### OpenRouter API Key

1. Register at https://openrouter.ai.
2. Generate an `sk-or-` API key.
3. Add the key to `openrouter_api_key`.

### 5. Optional: Configure Discord integration

If you want Discord remote control, populate `config/discord_bot.json` with your bot credentials and connection settings.

### 6. Launch Hidayat AI

```powershell
python main.py
```

For a cleaner startup experience on Windows:

```powershell
start_brahma.vbs
```

## Configuration

Core configuration files:

- `config/api_keys.json` — Gemini and OpenRouter credentials
- `config/app_settings.json` — voice, UI, startup, and automation preferences
- `config/brahma_connect.json` — device pairing, gateway, and discovery settings
- `config/discord_bot.json` — Discord bridge configuration

## Project Structure

- `main.py` — application startup, AI orchestration, and command routing
- `ui.py` — Qt-based desktop interface and live assistant controls
- `core/` — self-improvement, self-editing, and security systems
- `actions/` — modular automation, document, and assistant tools
- `brahma_connect/` — local gateway, pairing, and remote routing
- `config/` — local settings, credentials, and runtime configuration
- `plugins/` — optional plugin extensions
- `tests/` — integration and validation tests

## Plugin System

Extend Hidayat AI with custom Python plugins by adding files to `plugins/`.

Supported hooks:

- `on_brahma_created(brahma)` — called when the assistant instance is initialized
- `on_startup(brahma)` — called after startup when plugins are registered
- `on_text_command(text, source, brahma=None)` — called for each incoming text command; return `True` to indicate the command was handled

## Best Practices

- Keep credentials in `config/api_keys.json` and avoid committing secrets.
- Use the virtual environment for all development and runtime sessions.
- Restart the app after changing config or adding plugins.
- Review `config/app_settings.json` to tune voice, UI, and automation behavior.
- Review `SECURITY.md` for the anti-jailbreak and security protocol.

## Original Project

This project is derived from the original Brahma Echo project:

- Original repository: https://github.com/titechprabhasolutions/Brahma-Echo

## Credits

Original Project: Brahma AI
Original Creator: Suryaansh Tiwari

This project is a modified/customized version of the original Brahma AI project.
Modifications and additional work by: Hidayat

Licensed under the MIT License.

> Preserve attribution and keep credentials secure when building on top of Hidayat AI.
