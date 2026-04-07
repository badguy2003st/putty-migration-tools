"""
Import Package Module - Import migration packages (Linux)

This module handles importing Windows-generated export packages:
- Extracts and validates ZIP structure
- Imports SSH keys to ~/.ssh with conflict handling
- Merges SSH config with backup
- Handles Bitwarden export (auto or manual)

v1.1.1: Complete export/import workflow
"""

import asyncio
import json
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Literal
from dataclasses import dataclass, field

from .converter import copy_key_to_ssh
from .file_operations import merge_ssh_config


@dataclass
class ImportOptions:
    """Import options selected by user."""
    
    ssh_keys: bool = False
    """Import SSH keys to ~/.ssh"""
    
    ssh_config: bool = False
    """Import SSH config to ~/.ssh/config"""
    
    bitwarden: bool = False
    """Handle Bitwarden export"""
    
    conflict_mode: Literal["rename", "overwrite", "skip"] = "rename"
    """Conflict handling mode for SSH keys"""
    
    bitwarden_auto_import: bool = False
    """Automatically run 'bw import' command"""


@dataclass
class PackageContents:
    """Contents of extracted package."""
    
    manifest: Dict[str, Any]
    """Parsed MANIFEST.json"""
    
    temp_dir: Path
    """Temporary directory with extracted files"""
    
    openssh_keys_dir: Optional[Path] = None
    """Path to openssh_keys/ directory"""
    
    ssh_config_file: Optional[Path] = None
    """Path to ssh-config file"""
    
    tabby_config_file: Optional[Path] = None
    """Path to tabby-config.json file"""
    
    bitwarden_export_file: Optional[Path] = None
    """Path to bitwarden-export.json file"""
    
    readme_file: Optional[Path] = None
    """Path to README.txt file"""


@dataclass
class ImportResult:
    """Result of import operation."""
    
    success: bool
    """Whether the import succeeded"""
    
    results: Dict[str, Any] = field(default_factory=dict)
    """Detailed results for each component"""
    
    manifest: Optional[Dict[str, Any]] = None
    """Manifest from package"""
    
    error: Optional[str] = None
    """Error message if failed"""


async def extract_and_validate_package(
    zip_file: Path,
    temp_dir: Path
) -> PackageContents:
    """
    Extract ZIP and validate structure.
    
    Args:
        zip_file: Path to ZIP file
        temp_dir: Temporary directory for extraction
        
    Returns:
        PackageContents with paths and manifest
        
    Raises:
        ValueError: If ZIP structure is invalid
        
    Example:
        with tempfile.TemporaryDirectory() as temp:
            contents = await extract_and_validate_package(
                Path("export.zip"),
                Path(temp)
            )
            print(f"Version: {contents.manifest['version']}")
    """
    zip_file = Path(zip_file).resolve()
    temp_dir = Path(temp_dir).resolve()
    
    if not zip_file.exists():
        raise ValueError(f"ZIP file not found: {zip_file}")
    
    # Extract ZIP
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: _extract_zip(zip_file, temp_dir)
    )
    
    # Validate MANIFEST.json exists
    manifest_file = temp_dir / "MANIFEST.json"
    if not manifest_file.exists():
        raise ValueError("Invalid ZIP: MANIFEST.json missing")
    
    # Parse manifest
    try:
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid MANIFEST.json: {e}")
    
    # Validate version
    if manifest.get('version') != '1.1.1':
        # Warning but not fatal
        pass
    
    # Find all components
    openssh_keys_dir = temp_dir / "openssh_keys"
    ssh_config_file = temp_dir / "ssh-config"
    tabby_config_file = temp_dir / "tabby-config.json"
    bitwarden_export_file = temp_dir / "bitwarden-export.json"
    readme_file = temp_dir / "README.txt"
    
    return PackageContents(
        manifest=manifest,
        temp_dir=temp_dir,
        openssh_keys_dir=openssh_keys_dir if openssh_keys_dir.exists() else None,
        ssh_config_file=ssh_config_file if ssh_config_file.exists() else None,
        tabby_config_file=tabby_config_file if tabby_config_file.exists() else None,
        bitwarden_export_file=bitwarden_export_file if bitwarden_export_file.exists() else None,
        readme_file=readme_file if readme_file.exists() else None
    )


def _extract_zip(zip_file: Path, temp_dir: Path) -> None:
    """Extract ZIP file to temp directory (synchronous)."""
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(temp_dir)


async def import_package(
    zip_file: Path,
    options: ImportOptions,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> ImportResult:
    """
    Import selected components from export package.
    
    Steps:
    1. Extract ZIP to temp directory
    2. Validate MANIFEST.json
    3. If ssh_keys: Import keys with conflict handling
    4. If ssh_config: Merge SSH config
    5. If bitwarden: Show instructions or run bw import
    6. Cleanup temp directory
    
    Args:
        zip_file: Path to ZIP file
        options: ImportOptions with user selections
        progress_callback: Optional callback(current, total, message)
        
    Returns:
        ImportResult with success status and details
        
    Example:
        options = ImportOptions(
            ssh_keys=True,
            ssh_config=True,
            conflict_mode="rename"
        )
        
        result = await import_package(
            Path("export.zip"),
            options,
            progress_callback=lambda cur, tot, msg: print(f"{cur}/{tot}: {msg}")
        )
        
        if result.success:
            print(f"Imported {len(result.results)} components")
    """
    zip_file = Path(zip_file).resolve()
    
    results = {
        'ssh_keys': None,
        'ssh_config': None,
        'bitwarden': None
    }
    
    # Determine total steps
    total_steps = 2  # Extract + validate
    if options.ssh_keys:
        total_steps += 1
    if options.ssh_config:
        total_steps += 1
    if options.bitwarden:
        total_steps += 1
    
    try:
        # Step 1: Extract and validate
        if progress_callback:
            progress_callback(1, total_steps, "Extracting ZIP...")
        
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            
            try:
                contents = await extract_and_validate_package(zip_file, temp_dir)
            except ValueError as e:
                return ImportResult(
                    success=False,
                    error=str(e)
                )
            
            if progress_callback:
                progress_callback(2, total_steps, "Validated package")
            
            current_step = 2
            
            # Step 2: Import SSH Keys (if selected)
            if options.ssh_keys and contents.openssh_keys_dir:
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps, "Importing SSH keys...")
                
                key_results = []
                
                # Import all files (private and public keys)
                for key_file in contents.openssh_keys_dir.iterdir():
                    if key_file.is_file():
                        try:
                            result = await copy_key_to_ssh(
                                key_file,
                                mode=options.conflict_mode
                            )
                            key_results.append(result)
                        except Exception as e:
                            key_results.append({
                                'success': False,
                                'source': str(key_file),
                                'error': str(e)
                            })
                
                results['ssh_keys'] = {
                    'success': True,
                    'count': len(key_results),
                    'details': key_results
                }
            
            # Step 3: Import SSH Config (if selected)
            if options.ssh_config and contents.ssh_config_file:
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps, "Importing SSH config...")
                
                ssh_config_content = contents.ssh_config_file.read_text(encoding='utf-8')
                ssh_config_path = Path.home() / ".ssh" / "config"
                
                success, message = merge_ssh_config(
                    ssh_config_content,
                    ssh_config_path,
                    interactive=False  # Use automatic merge
                )
                
                results['ssh_config'] = {
                    'success': success,
                    'message': message
                }
            
            # Step 4: Handle Bitwarden (if selected)
            if options.bitwarden and contents.bitwarden_export_file:
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps, "Handling Bitwarden export...")
                
                if options.bitwarden_auto_import:
                    # Check for BW_SESSION env variable
                    import os
                    bw_session = os.environ.get('BW_SESSION')
                    
                    if not bw_session:
                        results['bitwarden'] = {
                            'success': False,
                            'auto_imported': False,
                            'error': (
                                "BW_SESSION not set. Please unlock Bitwarden first:\n"
                                "  1. bw login (if not logged in)\n"
                                "  2. export BW_SESSION=$(bw unlock --raw)\n"
                                "  3. Try import again"
                            )
                        }
                    else:
                        # Try to run bw import automatically
                        try:
                            result = subprocess.run(
                                ['bw', 'import', 'bitwardenjson', str(contents.bitwarden_export_file)],
                                capture_output=True,
                                text=True,
                                timeout=30,
                                env=os.environ.copy()  # Pass environment with BW_SESSION
                            )
                            
                            if result.returncode == 0:
                                # Import successful - now sync
                                try:
                                    sync_result = subprocess.run(
                                        ['bw', 'sync'],
                                        capture_output=True,
                                        text=True,
                                        timeout=30,
                                        env=os.environ.copy()
                                    )
                                    
                                    synced = (sync_result.returncode == 0)
                                    
                                    results['bitwarden'] = {
                                        'success': True,
                                        'auto_imported': True,
                                        'synced': synced,
                                        'output': result.stdout,
                                        'sync_output': sync_result.stdout if synced else sync_result.stderr
                                    }
                                except Exception as sync_error:
                                    results['bitwarden'] = {
                                        'success': True,
                                        'auto_imported': True,
                                        'synced': False,
                                        'output': result.stdout,
                                        'sync_error': str(sync_error)
                                    }
                            else:
                                results['bitwarden'] = {
                                    'success': False,
                                    'auto_imported': False,
                                    'error': result.stderr
                                }
                        except FileNotFoundError:
                            results['bitwarden'] = {
                                'success': False,
                                'auto_imported': False,
                                'error': "bw CLI not found. Install: https://bitwarden.com/help/cli/"
                            }
                        except subprocess.TimeoutExpired:
                            results['bitwarden'] = {
                                'success': False,
                                'auto_imported': False,
                                'error': "bw import timed out"
                            }
                else:
                    # Copy export file to current directory
                    dest = Path.cwd() / "bitwarden-export.json"
                    shutil.copy(contents.bitwarden_export_file, dest)
                    results['bitwarden'] = {
                        'success': True,
                        'auto_imported': False,
                        'file': str(dest)
                    }
            
            if progress_callback:
                progress_callback(total_steps, total_steps, "Import complete!")
        
        return ImportResult(
            success=True,
            results=results,
            manifest=contents.manifest
        )
        
    except Exception as e:
        return ImportResult(
            success=False,
            error=f"Import failed: {str(e)}"
        )


def get_import_summary(result: ImportResult) -> str:
    """
    Generate human-readable import summary.
    
    Args:
        result: ImportResult object
        
    Returns:
        Formatted summary string
    """
    if not result.success:
        return f"❌ Import failed: {result.error}"
    
    lines = ["✅ Import Complete!", ""]
    
    # SSH Keys summary
    if result.results.get('ssh_keys'):
        ssh_data = result.results['ssh_keys']
        lines.append("SSH Keys:")
        
        if ssh_data.get('details'):
            copied = sum(1 for d in ssh_data['details'] if d.get('action') == 'copied')
            renamed = sum(1 for d in ssh_data['details'] if d.get('action') == 'renamed')
            skipped = sum(1 for d in ssh_data['details'] if d.get('action') == 'skipped')
            
            lines.append(f"  • {ssh_data['count']} files processed")
            if copied:
                lines.append(f"  • {copied} keys copied")
            if renamed:
                lines.append(f"  • {renamed} renamed (conflicts)")
            if skipped:
                lines.append(f"  • {skipped} skipped")
        
        lines.append("")
    
    # SSH Config summary
    if result.results.get('ssh_config'):
        ssh_config_data = result.results['ssh_config']
        lines.append("SSH Config:")
        lines.append(f"  • {ssh_config_data['message']}")
        lines.append("")
    
    # Bitwarden summary
    if result.results.get('bitwarden'):
        bw_data = result.results['bitwarden']
        lines.append("Bitwarden:")
        
        if bw_data.get('auto_imported'):
            if bw_data['success']:
                lines.append("  • ✅ Automatically imported to vault")
                # Show sync status
                if bw_data.get('synced'):
                    lines.append("  • ✅ Synced with server")
                elif bw_data.get('synced') is False:
                    lines.append("  • ⚠️  Sync failed (run 'bw sync' manually)")
            else:
                error_msg = bw_data.get('error', 'Unknown error')
                # Format multi-line errors
                if '\n' in error_msg:
                    lines.append(f"  • ❌ Auto-import failed:")
                    for error_line in error_msg.split('\n'):
                        if error_line.strip():
                            lines.append(f"    {error_line}")
                else:
                    lines.append(f"  • ❌ Auto-import failed: {error_msg}")
        else:
            if bw_data.get('file'):
                lines.append(f"  • File ready: {bw_data['file']}")
                lines.append("  • Run: bw import bitwardenjson bitwarden-export.json")
                lines.append("         bw sync")
        
        lines.append("")
    
    return "\n".join(lines)


def validate_zip_structure(zip_file: Path) -> tuple[bool, str]:
    """
    Quick validation of ZIP structure without extraction.
    
    Args:
        zip_file: Path to ZIP file
        
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        valid, msg = validate_zip_structure(Path("export.zip"))
        if not valid:
            print(f"Invalid: {msg}")
    """
    if not zip_file.exists():
        return False, f"File not found: {zip_file}"
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            # Check for MANIFEST.json
            if 'MANIFEST.json' not in zf.namelist():
                return False, "Missing MANIFEST.json"
            
            # Check for README.txt
            if 'README.txt' not in zf.namelist():
                return False, "Missing README.txt"
            
            # Check for openssh_keys/ directory
            has_keys = any(name.startswith('openssh_keys/') for name in zf.namelist())
            if not has_keys:
                return False, "Missing openssh_keys/ directory"
            
            return True, "Valid export package"
            
    except zipfile.BadZipFile:
        return False, "Corrupted or invalid ZIP file"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
