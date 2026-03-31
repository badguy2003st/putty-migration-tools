#!/usr/bin/env python3
"""
Build script for creating standalone executables using Nuitka.

Builds native single-file executables for Windows and Linux.

Usage:
    python build.py                    # Build for current platform
    python build.py --version 1.0.3    # Specify version
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


def ensure_nuitka_installed():
    """Ensure Nuitka is installed."""
    try:
        import nuitka
        print("[OK] Nuitka is installed")
        return True
    except ImportError:
        print("Nuitka not found. Installing...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'nuitka', 'ordered-set'],
                check=True
            )
            print("[OK] Nuitka installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("ERROR: Failed to install Nuitka")
            print("   Please install manually: pip install nuitka ordered-set")
            return False


def build_binary(version="1.0.0", debug=False):
    """
    Build binary for current platform using Nuitka.
    
    Args:
        version: Version string for binary name
        debug: Enable debug mode
    """
    platform_name, ext = get_platform_info()
    binary_name = f"putty-migrate-v{version}-{platform_name}{ext}"
    
    print("=" * 60)
    print(f"  Building PuTTY Migration Tools v{version}")
    print("=" * 60)
    print(f"Platform: {platform_name}")
    print(f"Binary: {binary_name}")
    print(f"Compiler: Nuitka")
    print(f"Mode: --onefile (single executable)")
    print(f"Debug: {debug}")
    print()
    
    # Ensure Nuitka is installed
    if not ensure_nuitka_installed():
        return False
    
    # Clean previous builds
    print("Cleaning previous builds...")
    for dir_name in ['build', 'dist']:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    
    print()
    
    # Build Nuitka command
    cmd = [
        sys.executable, '-m', 'nuitka',
        '--onefile',                                    # Single executable file
        '--assume-yes-for-downloads',                   # Auto-download compiler (MinGW on Windows)
        '--output-dir=dist',                            # Output directory
        f'--output-filename={binary_name}',             # Output filename
        '--enable-plugin=anti-bloat',                   # Reduce binary size
        '--nofollow-import-to=tkinter',                 # Exclude unused GUI
        '--nofollow-import-to=pytest',                  # Exclude test framework
        '--nofollow-import-to=setuptools',              # Exclude setuptools
        '--include-package=tui',                        # Include all tui modules
        '--include-package=textual',                    # Include textual
        '--include-package=cryptography',               # Include cryptography (key operations)
        '--include-package=rich',                       # Include rich (textual dependency)
        '--include-package-data=rich',                  # Include rich data files (unicode data)
        '--include-package-data=textual',               # Include textual data files
        '--follow-import-to=rich',                      # Follow all rich imports
        '--include-package=argon2pure',                 # PPK v3 support (v1.0.4+)
        '--follow-import-to=argon2pure',                # Follow argon2pure imports
        '--include-package=_argon2_cffi_bindings',      # Fast Argon2 via ctypes (v1.0.4+)
    ]
    
    # Add data files (TUI styles)
    styles_path = Path('tui/ui/styles.tcss')
    if styles_path.exists():
        if platform.system().lower() == 'windows':
            cmd.append(f'--include-data-files={styles_path}=tui/ui/styles.tcss')
        else:
            cmd.append(f'--include-data-files={styles_path}=tui/ui/styles.tcss')
    
    # Platform-specific options
    if platform.system().lower() == 'windows':
        cmd.append('--windows-console-mode=force')      # Always show console (for TUI/CLI tool)
        
        # Add icon if available
        icon_path = Path('icon.ico')
        if icon_path.exists():
            cmd.append(f'--windows-icon-from-ico={icon_path}')
    
    # Debug mode
    if debug:
        cmd.append('--debug')
    
    # Entry point
    cmd.append('putty_migrate.py')
    
    # Show command (for debugging)
    print("Nuitka command:")
    print("   " + " ".join(cmd))
    print()
    
    # Run Nuitka
    print("Running Nuitka compiler...")
    print("NOTE: First build will download MinGW64 compiler (~100 MB) and may take 5-10 minutes")
    print("      Subsequent builds will be faster (~3-5 minutes)")
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
                    print("   [OK] Binary works!")
                    print(f"   Output: {test_result.stdout.strip()}")
                else:
                    print("   [WARNING] Binary test failed!")
                    print(f"   Error: {test_result.stderr}")
                
                print()
                print("Binary ready for distribution!")
                print(f"   Location: {binary_path.absolute()}")
                print()
                print("Next steps:")
                print(f"   1. Test the binary: {binary_path}")
                print(f"   2. Try: {binary_path} --help")
                print(f"   3. Try: {binary_path}  (launch TUI)")
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
        description='Build PuTTY Migration Tools binary using Nuitka',
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
        help='Debug build (verbose output)'
    )
    
    args = parser.parse_args()
    
    # Build
    success = build_binary(version=args.version, debug=args.debug)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
