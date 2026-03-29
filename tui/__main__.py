#!/usr/bin/env python3
"""
PuTTY Migration Tools - Unified CLI/TUI Entry Point

Usage:
    putty-migrate              # Launch interactive TUI
    putty-migrate COMMAND      # Run CLI command
    putty-migrate --help       # Show help
    
Commands:
    convert       Convert PPK keys to OpenSSH format
    bitwarden     Export PuTTY sessions to Bitwarden
    tabby         Export PuTTY sessions to Tabby terminal
    ssh-config    Generate SSH config from PuTTY sessions
    
For more information on each command:
    putty-migrate COMMAND --help
"""

import sys
import argparse

__version__ = "1.0.0"


def create_global_parser() -> argparse.ArgumentParser:
    """Create main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='putty-migrate',
        description='PuTTY Migration Tools - Migrate PuTTY sessions to modern SSH tools',
        epilog='For more information: https://github.com/yourusername/putty-migration-tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'putty-migrate {__version__}'
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest='command',
        metavar='COMMAND',
        help='Command to execute'
    )
    
    # Import CLI parsers
    from .cli.convert_ppk import create_parser as convert_parser
    from .cli.export_bitwarden import create_parser as bitwarden_parser
    from .cli.export_tabby import create_parser as tabby_parser
    from .cli.export_ssh_config import create_parser as ssh_parser
    
    # Add subcommands (using parent parsers to inherit arguments)
    subparsers.add_parser(
        'convert',
        parents=[convert_parser()],
        add_help=False,
        help='Convert PPK keys to OpenSSH format'
    )
    
    subparsers.add_parser(
        'bitwarden',
        parents=[bitwarden_parser()],
        add_help=False,
        help='Export to Bitwarden vault'
    )
    
    subparsers.add_parser(
        'tabby',
        parents=[tabby_parser()],
        add_help=False,
        help='Export to Tabby terminal'
    )
    
    subparsers.add_parser(
        'ssh-config',
        parents=[ssh_parser()],
        add_help=False,
        help='Generate SSH config file'
    )
    
    return parser


def launch_tui() -> int:
    """Launch the interactive TUI."""
    try:
        # Check if Textual is available
        try:
            from .ui.app import PuttyMigrationApp
            from .utils.bitwarden import prompt_bitwarden_import
        except ImportError as e:
            print("❌ TUI dependencies not installed")
            print(f"   Error: {e}")
            print()
            print("Install with: pip install textual")
            return 1
        
        # Check terminal size
        import shutil
        cols, rows = shutil.get_terminal_size((80, 24))
        
        if cols < 80 or rows < 24:
            print("⚠️  Terminal too small for TUI (minimum 80x24)")
            print(f"   Current size: {cols}x{rows}")
            print()
            print("Please resize your terminal or use CLI commands:")
            print("  putty-migrate --help")
            return 1
        
        # Launch TUI
        app = PuttyMigrationApp()
        app.run()
        
        # After TUI exits: Check for Bitwarden import
        if app.bitwarden_export_file:
            prompt_bitwarden_import(app.bitwarden_export_file)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  TUI cancelled by user")
        return 0
    except Exception as e:
        print(f"❌ TUI failed to start: {e}")
        print()
        print("Use CLI commands instead:")
        print("  putty-migrate --help")
        return 1


def main() -> int:
    """
    Main entry point - routes to TUI or CLI.
    
    Behavior:
        - No arguments → Launch TUI
        - With arguments → Parse and execute CLI command
        
    Returns:
        Exit code (0 = success, non-zero = error)
    """
    # Special case: No arguments → Launch TUI
    if len(sys.argv) == 1:
        return launch_tui()
    
    # Parse arguments for CLI mode
    parser = create_global_parser()
    args = parser.parse_args()
    
    # No command specified (just --help or --version) - already handled by argparse
    if not args.command:
        parser.print_help()
        return 0
    
    # Route to appropriate CLI command
    try:
        if args.command == 'convert':
            from .cli.convert_ppk import main as convert_main
            # Pass remaining args to the command
            return convert_main(sys.argv[2:])
        
        elif args.command == 'bitwarden':
            from .cli.export_bitwarden import main as bitwarden_main
            return bitwarden_main(sys.argv[2:])
        
        elif args.command == 'tabby':
            from .cli.export_tabby import main as tabby_main
            return tabby_main(sys.argv[2:])
        
        elif args.command == 'ssh-config':
            from .cli.export_ssh_config import main as ssh_main
            # ssh_main expects to parse sys.argv itself
            # Temporarily replace sys.argv
            original_argv = sys.argv
            sys.argv = ['putty-migrate ssh-config'] + sys.argv[2:]
            try:
                return ssh_main()
            finally:
                sys.argv = original_argv
        
        else:
            # Should never happen due to argparse validation
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Command cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Command failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
