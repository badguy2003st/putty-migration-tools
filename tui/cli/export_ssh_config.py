#!/usr/bin/env python3
"""
Standalone CLI tool for exporting PuTTY sessions to SSH config.

Usage:
    python -m tui.cli.export_ssh_config [options]
    
Options:
    --ppk-dir DIR        Directory containing PPK files (default: ./ppk_keys)
    --ssh-dir DIR        SSH directory for keys (default: ~/.ssh)
    --output FILE        Output SSH config file (default: ~/.ssh/config)
    --no-backup          Don't backup existing SSH config
    --non-interactive    Don't prompt for Pageant matches
    --dry-run            Show what would be done without writing
"""

import sys
import argparse
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tui.core.ssh_config import SSHConfigGenerator, write_ssh_config
from tui.core.file_operations import ensure_ppk_directory
from tui.utils.platform import is_windows
from tui.utils.security import show_security_reminder


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for SSH config export command."""
    parser = argparse.ArgumentParser(
        description="Export PuTTY sessions to SSH config format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export with defaults
  python -m tui.cli.export_ssh_config
  
  # Custom PPK directory
  python -m tui.cli.export_ssh_config --ppk-dir ~/my_keys
  
  # Dry run (preview only)
  python -m tui.cli.export_ssh_config --dry-run
  
  # Non-interactive mode
  python -m tui.cli.export_ssh_config --non-interactive
        """
    )
    
    parser.add_argument(
        '--ppk-dir',
        default='./ppk_keys',
        help='Directory containing PPK files (default: ./ppk_keys)'
    )
    
    parser.add_argument(
        '--ssh-dir',
        default='~/.ssh',
        help='SSH directory for converted keys (default: ~/.ssh)'
    )
    
    parser.add_argument(
        '--output',
        default='~/.ssh/config',
        help='Output SSH config file (default: ~/.ssh/config)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help="Don't backup existing SSH config"
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help="Don't prompt for Pageant key matches"
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without writing files'
    )
    
    return parser


def main():
    """Main entry point for CLI tool."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Check if running on Windows
    if not is_windows():
        print("❌ This tool requires Windows to read PuTTY Registry")
        print("   (PuTTY sessions are stored in Windows Registry)")
        print()
        print("   If you're on Linux/macOS, you can:")
        print("   1. Use: putty-migrate convert")
        print("   2. Or manually create SSH config entries")
        return 1
    
    # Ensure ppk_keys directory exists (create if needed)
    ppk_dir = Path(args.ppk_dir).expanduser().resolve()
    check = ensure_ppk_directory(ppk_dir)
    if check['created']:
        print(check['cli_message'])
        return 0
    
    try:
        # Create generator
        generator = SSHConfigGenerator(
            ppk_keys_dir=args.ppk_dir,
            ssh_dir=args.ssh_dir,
            interactive=not args.non_interactive
        )
        
        # Generate SSH config entries
        entries = generator.generate()
        
        if not entries:
            print("\n⚠️  No SSH sessions found to export")
            return 0
        
        # Show summary
        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        
        stats = generator.registry.get_statistics()
        print(f"  Keys Processed:")
        print(f"    ✅ From ppk_keys/: {stats.get('ppk_keys_dir', 0)}")
        print(f"    🆕 From Registry:  {stats.get('putty_registry', 0)}")
        print(f"    📋 Total Unique:   {len(generator.registry)}")
        print()
        print(f"  Sessions Processed:")
        print(f"    📋 Total:         {len(entries)}")
        print("=" * 60)
        print()
        
        # Dry run or write
        if args.dry_run:
            print("🔍 DRY RUN MODE - Preview of SSH config:")
            print()
            for entry in entries:
                print(entry.to_ssh_config())
                print()
            
            print("ℹ️  Dry run complete. No files were modified.")
            print("   Remove --dry-run to write the SSH config.")
            
        else:
            # Write SSH config
            write_ssh_config(
                entries=entries,
                output_file=args.output,
                backup=not args.no_backup
            )
            
            print()
            show_security_reminder()
            
            print("\n📖 Next steps:")
            print("   1. Review the generated SSH config:")
            print(f"      cat {args.output}")
            print()
            print("   2. Test SSH connection:")
            print("      ssh <host-alias>")
            print()
            print("   3. Convert PPK keys if needed:")
            print("      putty-migrate convert")
            print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Security cleanup
        import gc
        gc.collect()


if __name__ == "__main__":
    sys.exit(main())
