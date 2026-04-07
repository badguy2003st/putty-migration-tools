"""
Import All CLI - Linux command for importing migration packages

Imports Windows-generated export packages with selective options.

Usage:
    putty-migrate import-all ZIP_FILE [OPTIONS]

v1.1.1: Complete export/import workflow
"""

import sys
import asyncio
import argparse
from pathlib import Path

from ..core.import_package import import_package, ImportOptions, validate_zip_structure, get_import_summary


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for import-all command."""
    parser = argparse.ArgumentParser(
        prog='putty-migrate import-all',
        description='Import PuTTY migration package from ZIP file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import everything with default options
  putty-migrate import-all export.zip --all

  # Import only SSH keys
  putty-migrate import-all export.zip --ssh-keys

  # Import with specific conflict mode
  putty-migrate import-all export.zip --ssh-keys --conflict overwrite

  # Auto-import to Bitwarden
  putty-migrate import-all export.zip --bitwarden --bw-auto-import

  # Dry run (preview only)
  putty-migrate import-all export.zip --all --dry-run

The package may contain:
  • OpenSSH keys (private and public)
  • SSH configuration
  • Tabby terminal config
  • Bitwarden vault export
"""
    )
    
    parser.add_argument(
        'zip_file',
        help='ZIP file created on Windows'
    )
    
    parser.add_argument(
        '--ssh-keys',
        action='store_true',
        help='Import SSH keys to ~/.ssh'
    )
    
    parser.add_argument(
        '--ssh-config',
        action='store_true',
        help='Import SSH config to ~/.ssh/config'
    )
    
    parser.add_argument(
        '--bitwarden',
        action='store_true',
        help='Handle Bitwarden export'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Import everything (implies all above options)'
    )
    
    parser.add_argument(
        '--conflict',
        choices=['rename', 'overwrite', 'skip'],
        default='rename',
        help='Conflict handling mode for SSH keys (default: rename)'
    )
    
    parser.add_argument(
        '--bw-auto-import',
        action='store_true',
        help='Automatically run "bw import" command (requires bw CLI)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without importing (shows what would be imported)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (show detailed progress)'
    )
    
    return parser


async def run_import_all(args) -> int:
    """
    Execute the import-all command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 = success, non-zero = error)
    """
    zip_file = Path(args.zip_file).resolve()
    
    print("=" * 60)
    print("  PuTTY Migration Tools - Import All")
    print("=" * 60)
    print()
    
    # Validate ZIP file
    if not zip_file.exists():
        print(f"❌ Error: ZIP file not found: {zip_file}")
        return 1
    
    print(f"📦 ZIP File: {zip_file}")
    print()
    
    # Validate ZIP structure
    print("🔍 Validating package...")
    valid, message = validate_zip_structure(zip_file)
    
    if not valid:
        print(f"❌ Invalid package: {message}")
        return 1
    
    print(f"✅ {message}")
    print()
    
    # Determine import options
    if args.all:
        opt_ssh_keys = True
        opt_ssh_config = True
        opt_bitwarden = True
    else:
        opt_ssh_keys = args.ssh_keys
        opt_ssh_config = args.ssh_config
        opt_bitwarden = args.bitwarden
    
    # Check if anything is selected
    if not (opt_ssh_keys or opt_ssh_config or opt_bitwarden):
        print("❌ Error: No import options specified")
        print()
        print("Use --all to import everything, or specify:")
        print("  --ssh-keys       Import SSH keys")
        print("  --ssh-config     Import SSH configuration")
        print("  --bitwarden      Import Bitwarden export")
        print()
        print("Example: putty-migrate import-all export.zip --all")
        return 1
    
    # Create import options
    options = ImportOptions(
        ssh_keys=opt_ssh_keys,
        ssh_config=opt_ssh_config,
        bitwarden=opt_bitwarden,
        conflict_mode=args.conflict,
        bitwarden_auto_import=args.bw_auto_import
    )
    
    # Show what will be imported
    print("📋 Import Plan:")
    if opt_ssh_keys:
        print(f"   ✓ SSH Keys (conflict mode: {args.conflict})")
    if opt_ssh_config:
        print("   ✓ SSH Config")
    if opt_bitwarden:
        mode = "auto-import" if args.bw_auto_import else "manual"
        print(f"   ✓ Bitwarden ({mode})")
    print()
    
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]")
        print()
        print("✅ Dry run complete. Use without --dry-run to perform actual import.")
        return 0
    
    # Progress callback
    def on_progress(current: int, total: int, message: str):
        if args.verbose:
            percent = int((current / total) * 100)
            print(f"[{percent:3d}%] {message}")
        else:
            # Simple progress dots
            print(".", end="", flush=True)
    
    print("🚀 Starting import...")
    if not args.verbose:
        print("Progress: ", end="", flush=True)
    
    # Run import
    result = await import_package(
        zip_file,
        options,
        progress_callback=on_progress
    )
    
    if not args.verbose:
        print()  # Newline after progress dots
    
    print()
    
    if result.success:
        print("=" * 60)
        print("✅ Import Complete!")
        print("=" * 60)
        print()
        
        # Show detailed summary
        summary = get_import_summary(result)
        print(summary)
        
        # Additional context from manifest
        if result.manifest:
            counts = result.manifest.get('counts', {})
            print("📊 Package Info:")
            print(f"   • Version: {result.manifest.get('version', 'unknown')}")
            print(f"   • Exported: {result.manifest.get('exported_at', 'unknown')}")
            print(f"   • Platform: {result.manifest.get('platform', 'unknown')}")
            print()
        
        return 0
    else:
        print("=" * 60)
        print("❌ Import Failed")
        print("=" * 60)
        print()
        print(f"Error: {result.error}")
        print()
        return 1


def main(argv=None) -> int:
    """
    Main entry point for import-all command.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Run async import
    try:
        return asyncio.run(run_import_all(args))
    except KeyboardInterrupt:
        print()
        print("⚠️  Import cancelled by user")
        return 1
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
