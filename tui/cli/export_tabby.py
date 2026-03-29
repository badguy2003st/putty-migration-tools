#!/usr/bin/env python3
"""
CLI tool for exporting PuTTY sessions to Tabby terminal.

Usage:
    putty-migrate tabby [OPTIONS]
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional

from ..core.registry import read_putty_sessions
from ..core.tabby_export import generate_tabby_config, validate_tabby_config
from ..utils.platform import is_windows


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for tabby command."""
    parser = argparse.ArgumentParser(
        prog='putty-migrate tabby',
        description='Export PuTTY sessions to Tabby terminal format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export to default file
  putty-migrate tabby
  
  # Export to custom file
  putty-migrate tabby -o my-tabby-config.json
  
  # Merge with existing Tabby config
  putty-migrate tabby --merge ~/.config/tabby/config.json
  
Import to Tabby:
  1. Open Tabby terminal
  2. Settings → Profiles & connections
  3. Import → Select the generated JSON file
        """
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        default='tabby-config.json',
        help='Output JSON file (default: tabby-config.json)'
    )
    
    parser.add_argument(
        '--merge',
        metavar='FILE',
        help='Merge with existing Tabby config file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser


def run_tabby_export(args: argparse.Namespace) -> int:
    """
    Execute Tabby export with provided arguments.
    
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
    
    print("=" * 60)
    print("  PuTTY → Tabby Terminal Export")
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
    
    # Filter to SSH sessions only
    ssh_sessions = [s for s in sessions if s.is_ssh]
    
    if not ssh_sessions:
        print("⚠️  No SSH sessions found")
        print("   Only SSH sessions can be exported to Tabby")
        return 0
    
    print(f"🔍 Found {len(ssh_sessions)} SSH session(s)")
    print()
    
    # Step 2: Generate Tabby config
    print("📦 Generating Tabby configuration...")
    
    try:
        json_config = generate_tabby_config(
            sessions=ssh_sessions,
            converted_keys=None,  # CLI doesn't track converted keys
            pretty=True
        )
    except Exception as e:
        print(f"❌ Export generation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Step 3: Validate
    valid, message = validate_tabby_config(json_config)
    
    if not valid:
        print(f"❌ Validation failed: {message}")
        return 1
    
    if args.verbose:
        print(f"   ✓ {message}")
    
    # Step 4: Merge with existing config if requested
    if args.merge:
        merge_file = Path(args.merge).expanduser().resolve()
        
        if not merge_file.exists():
            print(f"⚠️  Merge file not found: {merge_file}")
            print("   Creating new config instead")
        else:
            print(f"🔀 Merging with existing config: {merge_file}")
            
            try:
                existing_config = json.loads(merge_file.read_text(encoding='utf-8'))
                new_config = json.loads(json_config)
                
                # Merge hosts arrays
                existing_hosts = existing_config.get('hosts', [])
                new_hosts = new_config.get('hosts', [])
                
                # Add new hosts (avoid duplicates by name)
                existing_names = {h.get('name') for h in existing_hosts}
                for host in new_hosts:
                    if host.get('name') not in existing_names:
                        existing_hosts.append(host)
                
                existing_config['hosts'] = existing_hosts
                
                # Update config
                json_config = json.dumps(existing_config, indent=2, ensure_ascii=False)
                
                print(f"   ✓ Merged {len(new_hosts)} new host(s)")
                print()
                
            except Exception as e:
                print(f"⚠️  Merge failed: {e}")
                print("   Creating new config instead")
                print()
    
    # Step 5: Write to file
    output_file.write_text(json_config, encoding='utf-8')
    
    file_size = output_file.stat().st_size / 1024  # KB
    
    print()
    print("=" * 60)
    print("  EXPORT COMPLETE")
    print("=" * 60)
    print(f"  File: {output_file}")
    print(f"  Size: {file_size:.1f} KB")
    print(f"  Sessions: {len(ssh_sessions)}")
    print("=" * 60)
    print()
    
    # Step 6: Show import instructions
    print("📥 Import to Tabby:")
    print()
    print("  1. Open Tabby terminal")
    print("  2. Go to Settings → Profiles & connections")
    print("  3. Click 'Import' button")
    print(f"  4. Select: {output_file}")
    print()
    print("✅ Your PuTTY sessions will appear in Tabby!")
    print()
    
    # Show notes about SSH keys
    key_sessions = [s for s in ssh_sessions if s.public_key_file]
    if key_sessions:
        print("📝 Note: SSH Keys")
        print(f"   {len(key_sessions)} session(s) use SSH keys")
        print("   → Convert PPK keys: putty-migrate convert")
        print("   → Then configure key paths in Tabby manually")
        print()
    
    return 0


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for tabby command.
    
    Args:
        args: Optional argument list (for testing)
        
    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    try:
        return run_tabby_export(parsed_args)
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
