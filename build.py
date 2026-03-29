#!/usr/bin/env python3
"""
Build script for creating standalone executables.

Builds single-file executables for Windows and Linux.

Usage:
    python build.py                    # Build for current platform
    python build.py --version 1.0.1    # Specify version
    python build.py --debug            # Debug build
"""

import sys
import os
import platform
import subprocess
import shutil
from pathlib import Path
import argparse


def get_platform_info():
    """Get current platform information."""
    system = platform.system().lower()
    
    if system == "windows":
        return "windows", ".exe"
    elif system == "linux":
        return "linux", ""
    else:
        raise RuntimeError(f"Unsupported platform: {system}. Only Windows and Linux are supported.")


def build_binary(version="1.0.0", debug=False):
    """
    Build binary for current platform using PyInstaller.
    
    Args:
        version: Version string for binary name
        debug: Enable debug mode (console visible, no UPX compression)
    """
    platform_name, ext = get_platform_info()
    binary_name = f"putty-migrate-v{version}-{platform_name}{ext}"
    
    print("=" * 60)
    print(f"  Building PuTTY Migration Tools v{version}")
    print("=" * 60)
    print(f"Platform: {platform_name}")
    print(f"Binary: {binary_name}")
    print(f"Debug: {debug}")
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller not found!")
        print("   Install with: pip install pyinstaller")
        return False
    
    # Clean previous builds
    print("Cleaning previous builds...")
    for dir_name in ['build', 'dist']:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    print()
    
    # Build PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',                                    # Single file
        '--name', binary_name,                          # Output name
        '--console',                                    # Console app
    ]
    
    # Add data files (TUI styles)
    styles_path = Path('tui/ui/styles.tcss')
    if styles_path.exists():
        if platform.system().lower() == 'windows':
            cmd.extend(['--add-data', f'{styles_path};tui/ui'])
        else:
            cmd.extend(['--add-data', f'{styles_path}:tui/ui'])
    
    # Hidden imports (modules that PyInstaller might miss)
    hidden_imports = [
        'textual',
        'textual.app',
        'textual.screen',
        'textual.widgets',
        'textual.containers',
        'puttykeys',
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.backends',
        'tui.cli.convert_ppk',
        'tui.cli.export_bitwarden',
        'tui.cli.export_tabby',
        'tui.cli.export_ssh_config',
    ]
    
    for module in hidden_imports:
        cmd.extend(['--hidden-import', module])
    
    # Platform-specific options
    if platform.system().lower() == 'windows':
        # Add icon if available
        icon_path = Path('icon.ico')
        if icon_path.exists():
            cmd.extend(['--icon', str(icon_path)])
        
        # Windows-specific imports
        cmd.extend(['--hidden-import', 'winreg'])
    
    # Debug or production build
    if debug:
        cmd.append('--debug=all')
    else:
        cmd.append('--strip')          # Strip symbols (Linux)
    
    # CRITICAL FIXES for binary reliability
    cmd.append('--noupx')                        # Prevent Windows DLL load errors
    cmd.extend(['--collect-all', 'tui'])         # Include all tui modules (prevents import errors)
    cmd.extend(['--copy-metadata', 'textual'])   # Preserve package metadata
    cmd.extend(['--copy-metadata', 'puttykeys']) # Preserve package metadata
    
    # Windows-specific fixes
    if platform.system().lower() == 'windows':
        cmd.extend(['--runtime-tmpdir', '.'])    # Use current directory instead of TEMP
    
    # Entry point
    cmd.append('tui/__main__.py')
    
    # Show command (for debugging)
    print("PyInstaller command:")
    print("   " + " ".join(cmd))
    print()
    
    # Run PyInstaller
    print("Running PyInstaller...")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print()
            print("=" * 60)
            print("  BUILD SUCCESSFUL")
            print("=" * 60)
            
            # Get binary info
            binary_path = Path('dist') / binary_name
            
            if binary_path.exists():
                size_mb = binary_path.stat().st_size / (1024 * 1024)
                
                print(f"Binary: {binary_path}")
                print(f"Size: {size_mb:.1f} MB")
                print("=" * 60)
                print()
                
                # Test binary
                print("Testing binary...")
                test_cmd = [str(binary_path), '--version']
                test_result = subprocess.run(test_cmd, capture_output=True, text=True)
                
                if test_result.returncode == 0:
                    print("   OK: Binary works!")
                    print(f"   Output: {test_result.stdout.strip()}")
                else:
                    print("   WARNING: Binary test failed!")
                    print(f"   Error: {test_result.stderr}")
                
                print()
                print("Binary ready for distribution!")
                print(f"   Location: {binary_path.absolute()}")
                print()
                
                return True
            else:
                print("ERROR: Binary not found after build!")
                return False
        
    except subprocess.CalledProcessError as e:
        print()
        print("ERROR: Build failed!")
        print(f"   Error code: {e.returncode}")
        return False
    except Exception as e:
        print()
        print(f"ERROR: Unexpected error: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Build PuTTY Migration Tools binary',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version',
        default='1.0.0',
        help='Version string (default: 1.0.0)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug build (no compression, verbose output)'
    )
    
    args = parser.parse_args()
    
    # Build
    success = build_binary(version=args.version, debug=args.debug)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
