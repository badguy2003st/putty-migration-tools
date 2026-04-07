"""
Export All CLI - Windows command for complete package export

Creates a portable ZIP package for Linux migration.

Usage:
    putty-migrate export-all [OPTIONS]

v1.1.1: Complete export/import workflow
"""

import sys
import asyncio
import argparse
from pathlib import Path

from ..core.export_package import create_export_package, generate_default_zip_filename
from ..core.file_operations import load_password_file


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for export-all command."""
    parser = argparse.ArgumentParser(
        prog='putty-migrate export-all',
        description='Export all PuTTY data to a portable ZIP package',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export with auto-generated filename
  putty-migrate export-all

  # Export to specific file
  putty-migrate export-all -o my-export.zip

  # Export with custom password file
  putty-migrate export-all --password-file custom-passwords.txt

  # Dry run (preview only)
  putty-migrate export-all --dry-run

The export package includes:
  • Converted OpenSSH keys
  • SSH configuration
  • Tabby terminal config
  • Bitwarden vault export
  • MANIFEST.json and README.txt
"""
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output ZIP file (default: auto-generated with timestamp)'
    )
    
    parser.add_argument(
        '--password-file',
        default='./ppk_keys/passwords.txt',
        help='Password file for encrypted PPKs (default: ./ppk_keys/passwords.txt)'
    )
    
    parser.add_argument(
        '--ppk-dir',
        default='./ppk_keys',
        help='Directory containing PPK files (default: ./ppk_keys)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without creating ZIP (shows what would be exported)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (show detailed progress)'
    )
    
    return parser


async def run_export_all(args) -> int:
    """
    Execute the export-all command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 = success, non-zero = error)
    """
    ppk_dir = Path(args.ppk_dir).resolve()
    passwords_file = Path(args.password_file).resolve()
    
    # Determine output file
    if args.output:
        output_zip = Path(args.output).resolve()
    else:
        output_zip = Path.cwd() / generate_default_zip_filename()
    
    print("=" * 60)
    print("  PuTTY Migration Tools - Export All")
    print("=" * 60)
    print()
    
    # Check ppk_dir exists
    if not ppk_dir.exists():
        print(f"❌ Error: PPK directory not found: {ppk_dir}")
        print()
        print("Create it with:")
        print(f"  mkdir {ppk_dir}")
        print(f"  # Then copy your .ppk files to {ppk_dir}/")
        return 1
    
    # Count PPK files
    ppk_files = list(ppk_dir.glob("*.ppk"))
    if not ppk_files:
        print(f"❌ Error: No .ppk files found in {ppk_dir}")
        print()
        print("Copy your PuTTY private keys (.ppk files) to this directory.")
        return 1
    
    print(f"📁 PPK Directory: {ppk_dir}")
    print(f"📦 Output ZIP:    {output_zip}")
    print(f"🔑 PPK Files:     {len(ppk_files)} found")
    print()
    
    # Load passwords
    passwords = []
    if passwords_file.exists():
        passwords = load_password_file(passwords_file)
        print(f"🔐 Passwords:     {len(passwords)} loaded from {passwords_file.name}")
    else:
        print(f"⚠️  No passwords file (will only convert unencrypted keys)")
    
    print()
    
    if args.dry_run:
        print("[DRY RUN MODE - No files will be created]")
        print()
        print("Would export:")
        for ppk in ppk_files[:10]:  # Show first 10
            print(f"  • {ppk.name}")
        if len(ppk_files) > 10:
            print(f"  ... and {len(ppk_files) - 10} more")
        print()
        print(f"Output file: {output_zip}")
        return 0
    
    # Progress callback
    def on_progress(current: int, total: int, message: str):
        if args.verbose:
            percent = int((current / total) * 100)
            print(f"[{percent:3d}%] {message}")
        else:
            # Simple progress dots
            print(".", end="", flush=True)
    
    print("🚀 Starting export...")
    if not args.verbose:
        print("Progress: ", end="", flush=True)
    
    # Run export
    result = await create_export_package(
        output_zip,
        ppk_dir,
        passwords=passwords,
        progress_callback=on_progress
    )
    
    if not args.verbose:
        print()  # Newline after progress dots
    
    print()
    
    if result.success:
        print("=" * 60)
        print("✅ Export Complete!")
        print("=" * 60)
        print()
        print(f"📦 ZIP File:  {result.zip_file}")
        print(f"💾 Size:      {_format_size(result.size_bytes)}")
        print()
        
        if result.manifest:
            counts = result.manifest.get('counts', {})
            print("📋 Contents:")
            print(f"   • {counts.get('ssh_keys_exported', 0)} SSH keys")
            print(f"   • {counts.get('sessions_ssh', 0)} session configurations")
            print(f"   • Tabby terminal config")
            print(f"   • Bitwarden vault export")
            print()
            
            enc_status = result.manifest.get('encryption_status', {})
            if enc_status.get('encrypted_keys', 0) > 0:
                print(f"🔐 {enc_status['encrypted_keys']} encrypted keys preserved")
            
            errors = result.manifest.get('errors', [])
            if errors:
                print()
                print(f"⚠️  {len(errors)} keys could not be converted:")
                for error in errors[:5]:
                    print(f"   • {error['file']}: {error['error']}")
                if len(errors) > 5:
                    print(f"   ... and {len(errors) - 5} more")
        
        print()
        print("=" * 60)
        print("📋 Next Steps:")
        print("=" * 60)
        print()
        print("1. Copy ZIP to your Linux machine:")
        print(f"   scp {output_zip.name} user@linux-host:~")
        print()
        print("2. On Linux, import with:")
        print(f"   putty-migrate import-all --zip {output_zip.name}")
        print()
        print("3. Or extract manually (see README.txt in ZIP)")
        print()
        
        return 0
    else:
        print("=" * 60)
        print("❌ Export Failed")
        print("=" * 60)
        print()
        print(f"Error: {result.error}")
        print()
        return 1


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def main(argv=None) -> int:
    """
    Main entry point for export-all command.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Check platform
    from ..utils.platform import is_windows
    if not is_windows():
        print("❌ Error: export-all is only available on Windows")
        print()
        print("This command exports PuTTY data from Windows Registry.")
        print("On Linux, use: putty-migrate import-all")
        return 1
    
    # Run async export
    try:
        return asyncio.run(run_export_all(args))
    except KeyboardInterrupt:
        print()
        print("⚠️  Export cancelled by user")
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
