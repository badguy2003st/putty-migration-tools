#!/usr/bin/env python3
"""
CLI tool for converting PPK keys to OpenSSH format.

Usage:
    putty-migrate convert [OPTIONS]
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Optional

from ..core.converter import batch_convert_ppk_files, copy_key_to_ssh
from ..core.file_operations import ensure_ppk_directory
from ..utils.platform import is_linux


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for convert command."""
    parser = argparse.ArgumentParser(
        prog='putty-migrate convert',
        description='Convert PPK keys to OpenSSH format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all PPK files from default directory
  putty-migrate convert
  
  # Convert from custom directory
  putty-migrate convert -i /path/to/ppk_keys -o /path/to/output
  
  # Convert and copy to ~/.ssh (Linux only)
  putty-migrate convert --to-ssh
  
  # Handle conflicts with rename mode
  putty-migrate convert --to-ssh --conflict rename
  
  # Dry run (preview only)
  putty-migrate convert --dry-run
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        metavar='DIR',
        default='./ppk_keys',
        help='PPK keys directory (default: ./ppk_keys)'
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='DIR',
        default='./openssh_keys',
        help='Output directory (default: ./openssh_keys)'
    )
    
    parser.add_argument(
        '--to-ssh',
        action='store_true',
        help='Copy converted keys to ~/.ssh (Linux only)'
    )
    
    parser.add_argument(
        '--conflict',
        choices=['rename', 'overwrite', 'skip'],
        default='rename',
        help='Conflict resolution mode when copying to ~/.ssh (default: rename)'
    )
    
    parser.add_argument(
        '--password',
        metavar='PASS',
        help='Password for encrypted PPK files'
    )
    
    parser.add_argument(
        '--password-file',
        metavar='FILE',
        help='File containing passwords (one per line) to try (v1.1.0)'
    )
    
    parser.add_argument(
        '--no-encryption',
        action='store_true',
        help='Do not re-encrypt keys (v1.1.0: default keeps original encryption)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without writing files'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser


def load_password_file(password_file: Path) -> list[str]:
    """
    Load passwords from file (v1.1.0 format: no comments).
    
    One password per line, empty lines ignored.
    All characters including # are part of the password.
    
    Args:
        password_file: Path to password file
        
    Returns:
        List of passwords (preserves leading/trailing spaces)
    """
    try:
        content = password_file.read_text(encoding='utf-8')
        passwords = [
            line.rstrip('\r\n')  # Preserve leading/trailing spaces
            for line in content.splitlines()
            if line.strip()  # Skip only empty lines
        ]
        return passwords
    except Exception as e:
        raise ValueError(f"Failed to load password file: {e}")


async def run_convert(args: argparse.Namespace) -> int:
    """
    Execute PPK conversion with provided arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    ppk_dir = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    
    # Handle password file (v1.1.0)
    passwords_list = None
    
    # Auto-load passwords.txt from input directory (like TUI does)
    auto_passwords_file = ppk_dir / "passwords.txt"
    
    if args.password_file:
        # Explicit password file provided
        password_file = Path(args.password_file).expanduser().resolve()
        if not password_file.exists():
            print(f"❌ Password file not found: {password_file}")
            return 1
        
        try:
            passwords_list = load_password_file(password_file)
            print(f"✅ Loaded {len(passwords_list)} password(s) from {password_file.name}")
            print()
        except ValueError as e:
            print(f"❌ {e}")
            return 1
    
    elif not args.password and auto_passwords_file.exists():
        # Auto-load from ppk_keys/passwords.txt (if no explicit password given)
        try:
            passwords_list = load_password_file(auto_passwords_file)
            print(f"✅ Auto-loaded {len(passwords_list)} password(s) from {auto_passwords_file.name}")
            print()
        except ValueError as e:
            print(f"⚠️  Warning: Could not load {auto_passwords_file.name}: {e}")
            print()
    
    # Ensure ppk_keys directory exists (create if needed)
    check = ensure_ppk_directory(ppk_dir)
    if check['created']:
        print(check['cli_message'])
        return 0
    
    # Validate input directory (should exist now)
    if not ppk_dir.exists():
        print(f"❌ PPK directory not found: {ppk_dir}")
        return 1
    
    # Find PPK files
    ppk_files = list(ppk_dir.glob("*.ppk"))
    
    if not ppk_files:
        print(f"⚠️  No .ppk files found in {ppk_dir}")
        return 0
    
    print(f"🔍 Found {len(ppk_files)} PPK file(s)")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - Preview:")
        print()
        for ppk_file in ppk_files:
            output_file = output_dir / ppk_file.stem
            print(f"  {ppk_file.name} → {output_file}")
        print()
        print(f"ℹ️  Files would be written to: {output_dir}")
        if args.to_ssh:
            print(f"ℹ️  Would copy to ~/.ssh with conflict mode: {args.conflict}")
        print()
        print("Remove --dry-run to perform actual conversion")
        return 0
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert PPK files
    print("🔄 Converting PPK files...")
    print()
    
    # v1.1.0: Re-encryption enabled by default (secure!)
    keep_enc = not args.no_encryption
    
    results = await batch_convert_ppk_files(
        ppk_files=ppk_files,
        output_dir=output_dir,
        password=args.password,
        passwords=passwords_list,  # v1.1.0: Multi-password support
        progress_callback=lambda cur, tot, name: print(f"  [{cur}/{tot}] {name}"),
        keep_encryption=keep_enc  # v1.1.0: Re-encryption support
    )
    if successful:
        print(f"✅ Successful: {len(successful)}/{len(results)}")
        if args.verbose:
            for r in successful:
                name = Path(r.ppk_file).name
                # Show which password worked (v1.1.0)
                if r.password_index is not None:
                    if r.password_index == 0:
                        print(f"   ✓ {name} (unencrypted)")
                    else:
                        print(f"   ✓ {name} (password #{r.password_index})")
                else:
                    print(f"   ✓ {name}")
    
    if failed:
        print(f"❌ Failed: {len(failed)}/{len(results)}")
        for r in failed:
            print(f"   ✗ {Path(r.ppk_file).name}: {r.error}")
    
    print("=" * 60)
    print()
    
    # Copy to ~/.ssh if requested
    if args.to_ssh and successful:
        if not is_linux():
            print("⚠️  --to-ssh is only supported on Linux")
            print("   Keys have been converted to: {output_dir}")
            return 0
        
        print(f"📁 Copying keys to ~/.ssh (conflict mode: {args.conflict})...")
        print()
        
        ssh_copies = []
        for result in successful:
            # Copy private key
            source_file = Path(result.output_file)
            copy_result = await copy_key_to_ssh(source_file, mode=args.conflict)
            ssh_copies.append(copy_result)
            
            # Copy public key if exists
            pub_file = source_file.with_suffix('.pub')
            if pub_file.exists():
                pub_copy = await copy_key_to_ssh(pub_file, mode=args.conflict)
                ssh_copies.append(pub_copy)
        
        # Show copy summary
        print()
        print("📋 SSH Copy Results:")
        for copy in ssh_copies:
            action = copy['action']
            dest = Path(copy['destination']).name
            
            if action == 'copied':
                print(f"   ✓ {dest} (copied)")
            elif action == 'renamed':
                print(f"   ✓ {dest} (renamed)")
            elif action == 'overwritten':
                print(f"   ✓ {dest} (overwritten, backup created)")
            elif action == 'skipped':
                print(f"   - {dest} (skipped)")
        
        print()
        print("✅ Keys are now in ~/.ssh/")
        print()
    
    elif successful:
        print(f"✅ Converted keys saved to: {output_dir}")
        print()
        if is_linux():
            print("💡 Tip: Use --to-ssh to copy keys to ~/.ssh")
            print()
    
    # Return success if at least one file converted successfully
    # Only fail if ALL files failed (and there were files to process)
    if successful:
        return 0  # At least one success
    elif not results:
        return 0  # No files to process (non-error)
    else:
        return 1  # All files failed


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for convert command.
    
    Args:
        args: Optional argument list (for testing)
        
    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    try:
        return asyncio.run(run_convert(parsed_args))
    except KeyboardInterrupt:
        print("\n⚠️  Conversion cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
