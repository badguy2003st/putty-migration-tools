"""
Export Package Module - Create complete migration packages (Windows)

This module orchestrates the export of all PuTTY data into a portable
ZIP package for Linux migration:
- Converts PPK keys to OpenSSH format
- Generates SSH config
- Generates Tabby terminal config
- Generates Bitwarden vault export
- Packages everything with metadata

v1.1.1: Complete export/import workflow
"""

import asyncio
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field

from .converter import batch_convert_ppk_files, ConversionResult
from .registry import read_putty_sessions, PuttySession
from .ssh_config import generate_ssh_config_content
from .tabby_export import generate_tabby_config
from .bitwarden_export import generate_bitwarden_export
from .file_operations import load_password_file
from ..utils.platform import get_platform


@dataclass
class ExportPackageResult:
    """Result of export package creation."""
    
    success: bool
    """Whether the export succeeded"""
    
    zip_file: Optional[Path] = None
    """Path to created ZIP file"""
    
    manifest: Optional[Dict[str, Any]] = None
    """Export manifest (metadata)"""
    
    error: Optional[str] = None
    """Error message if failed"""
    
    size_bytes: int = 0
    """Size of ZIP file in bytes"""
    
    counts: Dict[str, int] = field(default_factory=dict)
    """Item counts (keys, sessions, etc.)"""


async def create_export_package(
    output_zip: Path,
    ppk_dir: Path,
    passwords: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> ExportPackageResult:
    """
    Create complete export package for Linux migration.
    
    This function orchestrates all export operations:
    1. Convert PPK → OpenSSH (with password handling)
    2. Generate SSH Config
    3. Generate Tabby JSON
    4. Generate Bitwarden JSON
    5. Create MANIFEST.json
    6. Create README.txt
    7. Package everything in ZIP
    
    Args:
        output_zip: Path for output ZIP file
        ppk_dir: Directory containing PPK files
        passwords: List of passwords for encrypted PPK files
        progress_callback: Optional callback(current, total, message)
        
    Returns:
        ExportPackageResult with success status and metadata
        
    Example:
        result = await create_export_package(
            Path("./export.zip"),
            Path("./ppk_keys"),
            passwords=["password1", "password2"],
            progress_callback=lambda cur, tot, msg: print(f"{cur}/{tot}: {msg}")
        )
        
        if result.success:
            print(f"Created: {result.zip_file}")
            print(f"Size: {result.size_bytes} bytes")
    """
    output_zip = Path(output_zip).resolve()
    ppk_dir = Path(ppk_dir).resolve()
    
    # Create temp directory for intermediate files
    temp_dir = output_zip.parent / ".export_temp"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Total steps: 7 (convert, ssh-config, tabby, bitwarden, manifest, readme, zip)
        total_steps = 7
        
        if progress_callback:
            progress_callback(0, total_steps, "Starting export...")
        
        # Step 1: Convert PPK files (most time-consuming)
        if progress_callback:
            progress_callback(1, total_steps, "Converting PPK keys...")
        
        ppk_files = list(ppk_dir.glob("*.ppk"))
        if not ppk_files:
            return ExportPackageResult(
                success=False,
                error=f"No PPK files found in {ppk_dir}"
            )
        
        openssh_dir = temp_dir / "openssh_keys"
        openssh_dir.mkdir(exist_ok=True)
        
        conversion_results = await batch_convert_ppk_files(
            ppk_files,
            openssh_dir,
            passwords=passwords,
            keep_encryption=True  # Preserve encryption
        )
        
        successful_conversions = [r for r in conversion_results if r.success]
        failed_conversions = [r for r in conversion_results if not r.success]
        
        if not successful_conversions:
            return ExportPackageResult(
                success=False,
                error="No PPK files could be converted"
            )
        
        # Step 2: Read PuTTY sessions
        if progress_callback:
            progress_callback(2, total_steps, "Reading PuTTY sessions...")
        
        try:
            sessions = read_putty_sessions()
            ssh_sessions = [s for s in sessions if s.is_ssh]
        except Exception as e:
            # Non-fatal: Can still export keys
            sessions = []
            ssh_sessions = []
        
        # Step 3: Generate SSH Config
        if progress_callback:
            progress_callback(3, total_steps, "Generating SSH config...")
        
        ssh_config_content = ""
        if ssh_sessions:
            ssh_config_content = generate_ssh_config_content(ssh_sessions)
        
        # Step 4: Generate Tabby JSON
        if progress_callback:
            progress_callback(4, total_steps, "Generating Tabby config...")
        
        tabby_json = ""
        if ssh_sessions:
            tabby_json = generate_tabby_config(ssh_sessions)
        
        # Step 5: Generate Bitwarden JSON
        if progress_callback:
            progress_callback(5, total_steps, "Generating Bitwarden export...")
        
        bitwarden_json = ""
        if ssh_sessions:
            bitwarden_json = generate_bitwarden_export(
                ssh_sessions,
                openssh_dir,
                ppk_keys_dir=ppk_dir
            )
        
        # Step 6: Create manifest
        if progress_callback:
            progress_callback(6, total_steps, "Creating metadata...")
        
        manifest = generate_manifest(
            ppk_count=len(ppk_files),
            conversion_results=conversion_results,
            sessions=sessions
        )
        
        # Step 7: Create README
        readme_txt = generate_readme_txt(manifest)
        
        # Step 8: Package as ZIP
        if progress_callback:
            progress_callback(7, total_steps, "Creating ZIP archive...")
        
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add README and MANIFEST
            zf.writestr('README.txt', readme_txt)
            zf.writestr('MANIFEST.json', json.dumps(manifest, indent=2))
            
            # Add openssh_keys/
            for key_file in openssh_dir.iterdir():
                if key_file.is_file():
                    arcname = f"openssh_keys/{key_file.name}"
                    zf.write(key_file, arcname)
            
            # Add configs (only if content exists)
            if ssh_config_content:
                zf.writestr('ssh-config', ssh_config_content)
            if tabby_json:
                zf.writestr('tabby-config.json', tabby_json)
            if bitwarden_json:
                zf.writestr('bitwarden-export.json', bitwarden_json)
        
        # Get ZIP size
        zip_size = output_zip.stat().st_size
        
        return ExportPackageResult(
            success=True,
            zip_file=output_zip,
            manifest=manifest,
            size_bytes=zip_size,
            counts=manifest.get('counts', {})
        )
        
    except Exception as e:
        return ExportPackageResult(
            success=False,
            error=f"Export failed: {str(e)}"
        )
    
    finally:
        # Cleanup temp directory
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def generate_manifest(
    ppk_count: int,
    conversion_results: List[ConversionResult],
    sessions: List[PuttySession]
) -> Dict[str, Any]:
    """
    Generate MANIFEST.json content.
    
    Args:
        ppk_count: Total number of PPK files found
        conversion_results: List of conversion results
        sessions: List of PuTTY sessions
        
    Returns:
        Manifest dictionary
    """
    import platform
    
    successful = [r for r in conversion_results if r.success]
    failed = [r for r in conversion_results if not r.success]
    ssh_sessions = [s for s in sessions if s.is_ssh]
    
    # Count encrypted keys (those with password_index > 0)
    encrypted_count = sum(1 for r in successful if r.password_index and r.password_index > 0)
    unencrypted_count = len(successful) - encrypted_count
    
    # Count key types (would need key type detection, for now estimate)
    # This is a simplified version - could be enhanced
    key_types = {
        "rsa": len([r for r in successful if "rsa" in r.ppk_file.lower()]),
        "ed25519": len([r for r in successful if "ed25519" in r.ppk_file.lower()]),
        "ecdsa": len([r for r in successful if "ecdsa" in r.ppk_file.lower()])
    }
    
    # Adjust counts (if no matches, assume remaining are RSA)
    identified = sum(key_types.values())
    if identified < len(successful):
        key_types["rsa"] += (len(successful) - identified)
    
    # Build errors list
    errors = []
    for result in failed:
        errors.append({
            "file": Path(result.ppk_file).name,
            "error": result.error or "Unknown error"
        })
    
    # Build warnings
    warnings = []
    if encrypted_count > 0:
        warnings.append(f"{encrypted_count} encrypted keys - passwords required on import")
    if failed:
        warnings.append(f"{len(failed)} keys could not be converted")
    
    # Detect current platform dynamically
    current_platform = get_platform()
    platform_display = {
        "windows": "Windows",
        "linux": "Linux",
        "unknown": "Unknown"
    }.get(current_platform, "Unknown")
    
    manifest = {
        "version": "1.1.1",
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform_display,
        "computer_name": platform.node(),
        "user": platform.node(),  # Safe fallback
        
        "counts": {
            "ppk_files_found": ppk_count,
            "ppk_files_converted": len(successful),
            "ppk_files_failed": len(failed),
            "ssh_keys_exported": len(successful),
            "sessions_total": len(sessions),
            "sessions_ssh": len(ssh_sessions),
            "sessions_other": len(sessions) - len(ssh_sessions),
            "bitwarden_items": len(ssh_sessions),
            "tabby_hosts": len(ssh_sessions),
            "ssh_config_entries": len(ssh_sessions)
        },
        
        "encryption_status": {
            "encrypted_keys": encrypted_count,
            "unencrypted_keys": unencrypted_count,
            "encryption_preserved": True
        },
        
        "key_types": key_types,
        
        "errors": errors,
        "warnings": warnings,
        
        "compatibility": {
            "openssh_version": "any",
            "bitwarden_version": "any",
            "tabby_version": "1.0+",
            "requires_passwords": encrypted_count > 0
        }
    }
    
    return manifest


def generate_readme_txt(manifest: Dict[str, Any]) -> str:
    """
    Generate README.txt content.
    
    Args:
        manifest: Manifest dictionary
        
    Returns:
        README.txt content as string
    """
    counts = manifest.get('counts', {})
    exported_at = manifest.get('exported_at', 'Unknown')
    
    # Format date (remove timezone info for readability)
    try:
        dt = datetime.fromisoformat(exported_at.replace('Z', '+00:00'))
        date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        date_str = exported_at
    
    readme = f"""PuTTY Migration Tools - Export Package
 =======================================

 Created: {date_str}
 Platform: {platform_display}
 Version: 1.1.1

Contents
--------
- openssh_keys/         : {counts.get('ssh_keys_exported', 0)} SSH private keys (OpenSSH format)
- ssh-config            : OpenSSH configuration for {counts.get('sessions_ssh', 0)} sessions
- tabby-config.json     : Tabby terminal config for {counts.get('tabby_hosts', 0)} sessions
- bitwarden-export.json : Bitwarden SSH Keys (Type 5) for {counts.get('bitwarden_items', 0)} sessions

Import on Linux
---------------
1. Copy this ZIP file to your Linux machine

2. Run the import tool:
   putty-migrate import-all --zip {Path('putty-migration-export.zip').name}

3. Select what to import (interactive):
   [ ] SSH Keys to ~/.ssh
   [ ] SSH Config to ~/.ssh/config
   [ ] Bitwarden vault (via bw CLI)

Manual Import
-------------
If you prefer manual import:

1. Extract the ZIP file:
   unzip {Path('putty-migration-export.zip').name} -d putty-export

2. Copy SSH keys:
   cp putty-export/openssh_keys/* ~/.ssh/
   chmod 600 ~/.ssh/key*
   chmod 644 ~/.ssh/*.pub

3. Add SSH config:
   cat putty-export/ssh-config >> ~/.ssh/config

4. Import to Bitwarden:
   bw import bitwardenjson putty-export/bitwarden-export.json

5. Import to Tabby:
   a. Install tabby-home plugin first:
      - Open Tabby → Settings (⚙️) → Plugins
      - Search for "home"
      - Install "tabby-home" plugin
      - Restart Tabby

   b. Import connections:
      - Open "Tabby Home" tab
      - Click "Import Connection" button (top-right)
      - Select tabby-config.json file
      - Confirm import

Documentation
-------------
https://github.com/badguy2003st/putty-migration-tools

Support
-------
Issues: https://github.com/badguy2003st/putty-migration-tools/issues

Security Warning
----------------
⚠️  This ZIP contains your SSH private keys!
   • Transfer via encrypted channel (SFTP, SCP)
   • Delete after successful import
   • Don't store in cloud storage unencrypted
   • Set restrictive permissions: chmod 600 export.zip
"""
    
    return readme


def generate_default_zip_filename() -> str:
    """
    Generate default ZIP filename with timestamp.
    
    Returns:
        Filename string (e.g., "putty-migration-export-20260403-203045.zip")
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"putty-migration-export-{timestamp}.zip"
