#!/usr/bin/env python3
"""
CLI tool for exporting PuTTY sessions to Bitwarden.

Usage:
    putty-migrate bitwarden [OPTIONS]
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

from ..core.registry import read_putty_sessions
from ..core.bitwarden_export import generate_bitwarden_export, validate_bitwarden_export
from ..core.auth_detection import detect_auth_method
from ..core.converter import batch_convert_ppk_files
from ..core.file_operations import ensure_ppk_directory
from ..utils.platform import is_windows
from ..utils.bitwarden import prompt_for_import, do_bitwarden_import


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for bitwarden command."""
    parser = argparse.ArgumentParser(
        prog='putty-migrate bitwarden',
        description='Export PuTTY sessions to Bitwarden SSH Key format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export to default file
  putty-migrate bitwarden
  
  # Export to custom file
  putty-migrate bitwarden -o my-export.json
  
  # Auto-convert PPK files first
  putty-migrate bitwarden --auto-convert
  
  # Specify custom directories
  putty-migrate bitwarden --ppk-dir ./keys --openssh-dir ./converted
  
Import to Bitwarden:
  bw login
  bw unlock
  bw import bitwardenjson bitwarden-export.json
        """
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        default='bitwarden-export.json',
        help='Output JSON file (default: bitwarden-export.json)'
    )
    
    parser.add_argument(
        '--ppk-dir',
        metavar='DIR',
        default='./ppk_keys',
        help='PPK directory (default: ./ppk_keys)'
    )
    
    parser.add_argument(
        '--openssh-dir',
        metavar='DIR',
        default='./openssh_keys',
        help='OpenSSH directory (default: ./openssh_keys)'
    )
    
    parser.add_argument(
        '--auto-convert',
        action='store_true',
        help='Auto-convert PPK files to OpenSSH before export'
    )
    
    parser.add_argument(
        '--auto-import',
        action='store_true',
        help='Automatically import to Bitwarden after export'
    )
    
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='No prompts - export only (skip import prompt)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser


async def run_bitwarden_export(args: argparse.Namespace) -> int:
    """
    Execute Bitwarden export with provided arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Check if running on Windows
    if not is_windows():
        print("❌ This tool requires Windows to read PuTTY Registry")
        print("   (PuTTY sessions are stored in Windows Registry)")
        return 1
    
    output_file = Path(args.output).expanduser().resolve()
    ppk_dir = Path(args.ppk_dir).expanduser().resolve()
    openssh_dir = Path(args.openssh_dir).expanduser().resolve()
    
    # Ensure ppk_keys directory exists (create if needed)
    check = ensure_ppk_directory(ppk_dir)
    if check['created']:
        print(check['cli_message'])
        return 0
    
    print("=" * 60)
    print("  PuTTY → Bitwarden SSH Key Export")
    print("=" * 60)
    print()
    
    # Step 1: Read PuTTY sessions
    print("📖 Reading PuTTY sessions from Registry...")
    
    try:
        sessions = read_putty_sessions()
    except Exception as e:
        print(f"❌ Failed to read PuTTY sessions: {e}")
        return 1
    
    if not sessions:
        print("⚠️  No PuTTY sessions found")
        return 0
    
    print(f"   Found {len(sessions)} session(s)")
    print()
    
    # Step 2: Filter to SSH key sessions
    print("🔍 Filtering sessions with SSH key authentication...")
    
    key_sessions = []
    for session in sessions:
        auth_info = detect_auth_method(session.raw_data)
        if auth_info.method == "key":
            key_sessions.append(session)
            if args.verbose:
                print(f"   ✓ {session.name} ({auth_info.key_file or 'Pageant'})")
    
    if not key_sessions:
        print("⚠️  No sessions using SSH key authentication found")
        print("   Only sessions with SSH keys can be exported to Bitwarden")
        return 0
    
    print(f"   {len(key_sessions)} session(s) with SSH keys")
    print()
    
    # Step 3: Auto-convert PPK files if requested
    if args.auto_convert:
        if not ppk_dir.exists():
            print(f"⚠️  PPK directory not found: {ppk_dir}")
            print("   Skipping auto-conversion")
        else:
            ppk_files = list(ppk_dir.glob("*.ppk"))
            
            if ppk_files:
                print(f"🔄 Auto-converting {len(ppk_files)} PPK file(s)...")
                print()
                
                openssh_dir.mkdir(parents=True, exist_ok=True)
                
                results = await batch_convert_ppk_files(
                    ppk_files=ppk_files,
                    output_dir=openssh_dir,
                    progress_callback=lambda cur, tot, name: print(f"  [{cur}/{tot}] {name}")
                )
                
                successful = sum(1 for r in results if r.success)
                print(f"   ✅ Converted: {successful}/{len(results)}")
                print()
            else:
                print(f"⚠️  No PPK files found in {ppk_dir}")
                print()
    
    # Step 4: Check OpenSSH directory exists
    if not openssh_dir.exists():
        print(f"❌ OpenSSH directory not found: {openssh_dir}")
        print()
        print("💡 Tips:")
        print("   1. Convert PPK files first: putty-migrate convert")
        print("   2. Or use --auto-convert flag")
        return 1
    
    # Step 5: Generate Bitwarden export
    print("📦 Generating Bitwarden export...")
    
    try:
        json_export = generate_bitwarden_export(
            sessions=key_sessions,
            openssh_keys_dir=openssh_dir,
            ppk_keys_dir=ppk_dir,
            include_standalone_keys=True
        )
    except Exception as e:
        print(f"❌ Export generation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Step 6: Validate export
    valid, message = validate_bitwarden_export(json_export)
    
    if not valid:
        print(f"❌ Validation failed: {message}")
        return 1
    
    if args.verbose:
        print(f"   ✓ {message}")
    
    # Step 7: Write to file
    output_file.write_text(json_export, encoding='utf-8')
    
    file_size = output_file.stat().st_size / 1024  # KB
    
    print()
    print("=" * 60)
    print("  EXPORT COMPLETE")
    print("=" * 60)
    print(f"  File: {output_file}")
    print(f"  Size: {file_size:.1f} KB")
    print("=" * 60)
    print()
    
    # Step 8: Show import instructions
    print("📥 Import to Bitwarden:")
    print()
    print("  1. Login to Bitwarden CLI:")
    print("     bw login")
    print()
    print("  2. Unlock vault:")
    print("     bw unlock")
    print()
    print("  3. Import the file:")
    print(f"     bw import bitwardenjson {output_file.name}")
    print()
    print("  4. Sync with web vault:")
    print("     bw sync")
    print()
    print("✅ Your SSH keys will be available in Bitwarden SSH Agent!")
    print()
    
    # Step 9: Auto-import or prompt for import
    if not args.non_interactive:
        if args.auto_import:
            # Auto-import without asking
            do_bitwarden_import(output_file)
        else:
            # Ask user if they want to import
            if prompt_for_import():
                do_bitwarden_import(output_file)
    
    return 0


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for bitwarden command.
    
    Args:
        args: Optional argument list (for testing)
        
    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    try:
        return asyncio.run(run_bitwarden_export(parsed_args))
    except KeyboardInterrupt:
        print("\n⚠️  Export cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
