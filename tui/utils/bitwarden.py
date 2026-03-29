"""
Bitwarden import utilities.

Handles prompting the user to import exported Bitwarden files.
Shared by both CLI and TUI modes.
"""

import subprocess
import shutil
from pathlib import Path


def prompt_for_import() -> bool:
    """
    Ask user if they want to import to Bitwarden.
    
    Returns:
        True if user wants to import, False otherwise
    """
    try:
        answer = input("\n📥 Import to Bitwarden now? [y/N]: ").strip().lower()
        return answer in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        return False


def do_bitwarden_import(export_file: Path) -> bool:
    """
    Import to Bitwarden using bw CLI.
    
    Args:
        export_file: Path to bitwarden-export.json
        
    Returns:
        True if import successful, False otherwise
    """
    # Check bw CLI available
    if not shutil.which('bw'):
        print()
        print("❌ Bitwarden CLI (bw) not found!")
        print("   Download from: https://bitwarden.com/download/")
        print("   Or use: winget install Bitwarden.CLI")
        print()
        print("   Manual import:")
        print(f"   bw import bitwardenjson {export_file.name}")
        return False
    
    print()
    print("🔄 Importing to Bitwarden...")
    print()
    
    try:
        # Import to Bitwarden (bw will prompt for unlock if needed)
        result = subprocess.run(
            ['bw', 'import', 'bitwardenjson', str(export_file)],
            capture_output=False  # Show bw prompts directly to user
        )
        
        if result.returncode == 0:
            # Sync with web vault
            print()
            print("🔄 Syncing with web vault...")
            subprocess.run(['bw', 'sync'])
            
            print()
            print("=" * 60)
            print("✅ Import successful!")
            print("=" * 60)
            print()
            print("Your SSH keys are now in Bitwarden vault!")
            print("Use Bitwarden SSH Agent to access them.")
            print()
            return True
        else:
            print()
            print("=" * 60)
            print("⚠️  Import failed or cancelled")
            print("=" * 60)
            print()
            print("You can import manually:")
            print(f"  bw import bitwardenjson {export_file.name}")
            print()
            return False
    
    except FileNotFoundError:
        print()
        print("❌ Bitwarden CLI not found in PATH!")
        return False
    except Exception as e:
        print()
        print(f"❌ Import error: {e}")
        return False


def prompt_bitwarden_import(export_file: str) -> None:
    """
    Prompt user to import to Bitwarden and execute if confirmed.
    
    This is a convenience function that combines prompting and importing.
    Used by TUI main.py after app exits.
    
    Args:
        export_file: Path to the bitwarden-export.json file (as string)
    """
    print()
    print("=" * 60)
    print("  Bitwarden Import")
    print("=" * 60)
    print()
    print(f"📦 Export file: {Path(export_file).name}")
    print()
    
    # Check if bw CLI is available
    if not shutil.which('bw'):
        print("⚠️  Bitwarden CLI (bw) not found!")
        print("   Download from: https://bitwarden.com/download/")
        print()
        print("   Manual import:")
        print(f"   bw import bitwardenjson {Path(export_file).name}")
        return
    
    # Ask user
    if prompt_for_import():
        do_bitwarden_import(Path(export_file))
    else:
        print()
        print("ℹ️  Import skipped. You can import later:")
        print(f"   bw import bitwardenjson {Path(export_file).name}")
        print()
