#!/usr/bin/env python3
"""
Main launcher for the TUI GUI mode.

This launches the Textual-based interactive UI.
For CLI mode, use: python -m tui COMMAND (e.g., python -m tui convert)
"""

import sys
import os
import shutil

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_terminal_compatibility():
    """
    Check if terminal supports Textual.
    
    Returns:
        Tuple of (compatible: bool, reason: str)
    """
    # Check terminal size
    cols, rows = shutil.get_terminal_size((80, 24))
    if cols < 80 or rows < 24:
        return False, f"Terminal too small (min 80x24, current {cols}x{rows})"
    
    # Check UTF-8 support
    try:
        "🔧".encode('utf-8')
    except Exception:
        return False, "No UTF-8 support"
    
    return True, "OK"


def main():
    """Launch the TUI application."""
    # Check compatibility
    compatible, reason = check_terminal_compatibility()
    
    if not compatible:
        print(f"⚠️  {reason}")
        print("   Falling back to CLI mode...")
        print()
        from tui.cli.export_ssh_config import main as cli_main
        return cli_main()
    
    # Try to launch TUI
    try:
        from tui.ui.app import PuttyMigrationApp
        from tui.utils.bitwarden import prompt_bitwarden_import
        
        app = PuttyMigrationApp()
        app.run()
        
        # After TUI exits: Check for Bitwarden import
        if app.bitwarden_export_file:
            prompt_bitwarden_import(app.bitwarden_export_file)
        
        return 0
        
    except ImportError as e:
        print(f"⚠️  Textual not installed: {e}")
        print("   Install with: pip install textual rich")
        print()
        print("   Falling back to CLI mode...")
        print()
        from tui.cli.export_ssh_config import main as cli_main
        return cli_main()
    
    except Exception as e:
        print(f"❌ TUI failed to start: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("   Falling back to CLI mode...")
        print()
        from tui.cli.export_ssh_config import main as cli_main
        return cli_main()


if __name__ == "__main__":
    sys.exit(main())
