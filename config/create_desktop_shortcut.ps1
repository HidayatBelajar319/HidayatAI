<#
.SYNOPSIS
    Creates a desktop shortcut for Ultron Jarvis (Hidayat AI) with auto-detected paths.

.DESCRIPTION
    This script automatically detects:
    - The Hidayat AI installation directory (where this script is located)
    - The Python interpreter (prefers .venv\Scripts\pythonw.exe, falls back to system pythonw)
    - The user's Desktop folder (handles OneDrive, redirected folders, etc.)
    - The application icon

    No hardcoded paths - works on any Windows machine.
#>

# Get the directory where this script resides (Hidayat AI root)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$HidayatAIRoot = Split-Path -Parent $ScriptDir

# Auto-detect Python interpreter
$VenvPythonw = Join-Path $HidayatAIRoot ".venv\Scripts\pythonw.exe"
$SystemPythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source

if (Test-Path $VenvPythonw) {
    $PythonwPath = $VenvPythonw
} elseif ($SystemPythonw) {
    $PythonwPath = $SystemPythonw
} else {
    Write-Error "pythonw.exe not found. Please ensure Python is installed and in PATH, or create a virtual environment at .venv"
    exit 1
}

# Main script path
$MainPy = Join-Path $HidayatAIRoot "main.py"
if (-not (Test-Path $MainPy)) {
    Write-Error "main.py not found at $MainPy"
    exit 1
}

# Icon path
$IconPath = Join-Path $HidayatAIRoot "assets\Brahma_Lite_Logo.ico"
$IconArg = if (Test-Path $IconPath) { "$IconPath,0" } else { $null }

# Resolve user's Desktop folder (handles OneDrive, folder redirection, etc.)
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$ShortcutName = "Ultron Jarvis (Hidayat AI).lnk"
$ShortcutPath = Join-Path $DesktopPath $ShortcutName

# Create shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonwPath
$Shortcut.Arguments = "`"$MainPy`""
$Shortcut.WorkingDirectory = $HidayatAIRoot
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Description = "Launch Ultron Jarvis (Hidayat AI)"
if ($IconArg) { $Shortcut.IconLocation = $IconArg }
$Shortcut.Save()

Write-Host "Shortcut created at: $ShortcutPath"
Write-Host "Target: $PythonwPath"
Write-Host "Arguments: $MainPy"
Write-Host "Working Directory: $HidayatAIRoot"