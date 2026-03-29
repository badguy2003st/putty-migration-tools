"""
Tabby Export Module - Generate Tabby terminal configuration.

Converts PuTTY sessions to Tabby JSON format for import.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .registry import PuttySession
from .auth_detection import detect_auth_method


def session_to_tabby_connection(
    session: PuttySession,
    converted_keys: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Convert a PuTTY session to Tabby host format.
    
    Args:
        session: PuttySession object
        converted_keys: Optional mapping of PPK files to converted key paths
        
    Returns:
        Dictionary in Tabby host format
        
    Example:
        tabby_host = session_to_tabby_connection(putty_session)
    """
    import uuid
    
    # Detect authentication method
    auth_info = detect_auth_method(session.raw_data)
    
    # Base host object with required fields
    host = {
        "type": "ssh",
        "port": session.port,
        "groupId": None,
        "name": session.name,
        "host": session.hostname or "",
        "id": str(uuid.uuid4()),
        "hasCredentials": False,
    }
    
    # Add username if available (optional field)
    if session.username:
        host["username"] = session.username
    
    # Handle SSH key authentication
    if auth_info.method == "key" and auth_info.key_file:
        # Check if we have a converted OpenSSH key
        if converted_keys and auth_info.key_file in converted_keys:
            openssh_key_path = converted_keys[auth_info.key_file]
            
            # Extract filename without extension for notes field
            key_filename = Path(openssh_key_path).stem
            
            host["hasCredentials"] = True
            host["notes"] = key_filename
        else:
            # PPK file exists but not converted yet
            ppk_filename = Path(auth_info.key_file).stem
            
            host["hasCredentials"] = True
            host["notes"] = f"{ppk_filename} (not converted)"
    
    return host


def _infer_group(session_name: str, hostname: str) -> str:
    """
    Infer a group name from session name or hostname.
    
    Args:
        session_name: Session name
        hostname: Hostname
        
    Returns:
        Group name
    """
    # Common patterns to extract group names
    name_lower = session_name.lower()
    
    if any(x in name_lower for x in ['prod', 'production']):
        return "Production"
    elif any(x in name_lower for x in ['dev', 'development']):
        return "Development"
    elif any(x in name_lower for x in ['staging', 'stage', 'test']):
        return "Staging"
    elif any(x in name_lower for x in ['db', 'database', 'mysql', 'postgres']):
        return "Databases"
    elif any(x in name_lower for x in ['web', 'http', 'nginx', 'apache']):
        return "Web Servers"
    elif any(x in name_lower for x in ['vpn', 'gateway', 'router']):
        return "Network"
    
    # Default group
    return "Imported from PuTTY"


def generate_tabby_config(
    sessions: List[PuttySession],
    converted_keys: Optional[Dict[str, str]] = None,
    pretty: bool = True
) -> str:
    """
    Generate Tabby JSON configuration from PuTTY sessions.
    
    Args:
        sessions: List of PuTTY sessions
        converted_keys: Optional mapping of PPK → OpenSSH key paths
        pretty: Format JSON with indentation
        
    Returns:
        JSON string ready for Tabby import
        
    Example:
        sessions = read_putty_sessions()
        json_config = generate_tabby_config(sessions)
        
        # Write to file
        Path("tabby-config.json").write_text(json_config)
    """
    from datetime import datetime
    
    hosts = []
    
    for session in sessions:
        # Only export SSH sessions
        if session.is_ssh:
            host = session_to_tabby_connection(session, converted_keys)
            hosts.append(host)
    
    # Tabby expects this exact format
    config = {
        "version": 1,
        "exportedAt": datetime.utcnow().isoformat(timespec='milliseconds') + "Z",
        "groups": [],
        "hosts": hosts
    }
    
    if pretty:
        return json.dumps(config, indent=2, ensure_ascii=False)
    else:
        return json.dumps(config, ensure_ascii=False)


def generate_tabby_config_grouped(
    sessions: List[PuttySession],
    converted_keys: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate Tabby config (same as regular export - groups array is empty in Tabby).
    
    Args:
        sessions: List of PuTTY sessions
        converted_keys: Optional mapping of PPK → OpenSSH key paths
        
    Returns:
        JSON string ready for Tabby import
    """
    # Note: Tabby's groups array is empty, so this is now the same as regular export
    return generate_tabby_config(sessions, converted_keys, pretty=True)


def export_to_tabby_file(
    sessions: List[PuttySession],
    output_path: Path,
    converted_keys: Optional[Dict[str, str]] = None,
    grouped: bool = False
) -> tuple[bool, str]:
    """
    Export sessions to a Tabby JSON file.
    
    Args:
        sessions: List of PuTTY sessions
        output_path: Output file path
        converted_keys: Optional key mapping
        grouped: If True, organize by groups
        
    Returns:
        Tuple of (success, message)
        
    Example:
        success, msg = export_to_tabby_file(
            sessions,
            Path("./tabby-import.json"),
            grouped=True
        )
    """
    try:
        # Generate config
        if grouped:
            json_config = generate_tabby_config_grouped(sessions, converted_keys)
        else:
            json_config = generate_tabby_config(sessions, converted_keys)
        
        # Write to file (atomic write handled by file_operations)
        from .file_operations import write_file_atomic
        
        output_path = Path(output_path).expanduser()
        write_file_atomic(
            json_config,
            output_path,
            backup=True,
            permissions=0o644
        )
        
        return True, f"Exported {len(sessions)} session(s) to {output_path}"
        
    except Exception as e:
        return False, f"Export failed: {str(e)}"


def validate_tabby_config(json_str: str) -> tuple[bool, str]:
    """
    Validate a Tabby configuration JSON.
    
    Args:
        json_str: JSON configuration string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        config = json.loads(json_str)
        
        # Check required top-level fields
        if "hosts" not in config:
            return False, "Missing 'hosts' field"
        
        if not isinstance(config["hosts"], list):
            return False, "'hosts' must be a list"
        
        # Validate each host
        for i, host in enumerate(config["hosts"]):
            if not isinstance(host, dict):
                return False, f"Host {i} is not an object"
            
            required = ["type", "name", "host", "id"]
            for field in required:
                if field not in host:
                    return False, f"Host {i} missing required field: {field}"
        
        return True, "Valid Tabby configuration"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
