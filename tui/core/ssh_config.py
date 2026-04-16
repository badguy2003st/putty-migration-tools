"""
SSH Config Generator

Converts PuTTY sessions to OpenSSH config format with two-phase key processing:
1. Process ./ppk_keys/ directory FIRST
2. Process Registry keys with deduplication
"""

import os
import glob
from typing import List, Dict, Optional, TextIO
from dataclasses import dataclass

from .registry import PuttySession, read_putty_sessions, split_user_at_host
from .auth_detection import detect_auth_method, AuthInfo, format_auth_info
from .key_registry import KeyRegistry, KeyInfo
from .fuzzy_match import fuzzy_match_key, get_best_match, interactive_match_selection


@dataclass
class SSHConfigEntry:
    """Represents an SSH config entry."""
    
    host_alias: str
    """Host alias (for SSH config 'Host' line)"""
    
    hostname: str
    """Actual hostname or IP"""
    
    port: int = 22
    """SSH port"""
    
    user: Optional[str] = None
    """SSH username"""
    
    identity_file: Optional[str] = None
    """Path to private key"""
    
    comments: List[str] = None
    """Additional comments"""
    
    session_name: Optional[str] = None
    """Original PuTTY session name (displayed as comment above Host block)"""
    
    def __post_init__(self):
        if self.comments is None:
            self.comments = []
    
    def to_ssh_config(self) -> str:
        """
        Convert to SSH config format.
        
        Returns:
            SSH config formatted string
        """
        lines = []
        
        # Session name as comment ABOVE the Host block
        if self.session_name:
            lines.append(f"# Name der alten PuTTY Session: {self.session_name}")
        
        # Host line
        lines.append(f"Host {self.host_alias}")
        
        # Hostname
        lines.append(f"    HostName {self.hostname}")
        
        # User (if specified)
        if self.user:
            lines.append(f"    User {self.user}")
        
        # Port (if not default)
        if self.port != 22:
            lines.append(f"    Port {self.port}")
        
        # Identity file (if specified) - WITHOUT quotes
        if self.identity_file:
            lines.append(f"    IdentityFile {self.identity_file}")
        
        # Add comments (only for TODO/warnings)
        for comment in self.comments:
            lines.append(f"    # {comment}")
        
        # Keep-alive
        lines.append("    ServerAliveInterval 60")
        
        return "\n".join(lines)


class SSHConfigGenerator:
    """
    Main class for generating SSH config from PuTTY sessions.
    
    Implements two-phase key processing with deduplication.
    """
    
    def __init__(
        self,
        ppk_keys_dir: str = "./ppk_keys",
        ssh_dir: str = "~/.ssh",
        interactive: bool = True
    ):
        """
        Initialize the SSH config generator.
        
        Args:
            ppk_keys_dir: Directory containing PPK files
            ssh_dir: SSH directory for converted keys
            interactive: Whether to prompt user for Pageant matches
        """
        self.ppk_keys_dir = os.path.expanduser(ppk_keys_dir)
        self.ssh_dir = os.path.expanduser(ssh_dir)
        self.interactive = interactive
        self.registry = KeyRegistry()
        self.ssh_entries: List[SSHConfigEntry] = []
    
    def generate(self) -> List[SSHConfigEntry]:
        """
        Generate SSH config entries from PuTTY sessions.
        
        This implements the full two-phase processing workflow.
        
        Returns:
            List of SSHConfigEntry objects
            
        Raises:
            RuntimeError: If not on Windows or cannot read Registry
        """
        print("\n" + "=" * 60)
        print("  PuTTY → SSH Config Converter")
        print("=" * 60)
        print()
        
        # Phase 1: Process local PPK files
        self._phase1_process_local_keys()
        
        # Phase 2: Process PuTTY Registry sessions
        self._phase2_process_registry_sessions()
        
        return self.ssh_entries
    
    def _phase1_process_local_keys(self):
        """Phase 1: Process ./ppk_keys/ directory."""
        print("🔍 PHASE 1: Processing local PPK keys...")
        print()
        
        if not os.path.exists(self.ppk_keys_dir):
            print(f"   ⚠️  Directory not found: {self.ppk_keys_dir}")
            print("   Skipping Phase 1")
            print()
            return
        
        # Find all PPK files
        ppk_pattern = os.path.join(self.ppk_keys_dir, "*.ppk")
        ppk_files = glob.glob(ppk_pattern)
        
        if not ppk_files:
            print(f"   ℹ️  No .ppk files found in {self.ppk_keys_dir}")
            print()
            return
        
        print(f"   Found {len(ppk_files)} PPK file(s)")
        print()
        
        for ppk_file in ppk_files:
            key_name = os.path.splitext(os.path.basename(ppk_file))[0]
            print(f"   🔄 Processing: {os.path.basename(ppk_file)}")
            
            # For now, just register the key (conversion happens separately)
            # In full implementation, this would call converter.convert_ppk()
            openssh_path = os.path.join(self.ssh_dir, key_name)
            public_key_path = openssh_path + ".pub"
            
            try:
                key_hash = self.registry.add_key(
                    ppk_path=ppk_file,
                    openssh_path=openssh_path,
                    public_key_path=public_key_path,
                    source="ppk_keys_dir"
                )
                print(f"      ✅ Registered: {key_name}")
            except Exception as e:
                print(f"      ❌ Failed: {e}")
        
        stats = self.registry.get_statistics()
        local_count = stats.get("ppk_keys_dir", 0)
        print()
        print(f"✅ Phase 1 complete: {local_count} keys registered")
        print()
    
    def _phase2_process_registry_sessions(self):
        """Phase 2: Process PuTTY Registry sessions."""
        print("🔍 PHASE 2: Processing PuTTY Registry sessions...")
        print()
        
        try:
            sessions = read_putty_sessions()
        except RuntimeError as e:
            print(f"   ❌ Cannot read PuTTY sessions: {e}")
            return
        
        if not sessions:
            print("   ℹ️  No PuTTY sessions found")
            print()
            return
        
        print(f"   Found {len(sessions)} session(s)")
        print()
        
        ssh_sessions = [s for s in sessions if s.is_ssh]
        
        if not ssh_sessions:
            print("   ⚠️  No SSH sessions found (only non-SSH protocols)")
            print()
            return
        
        for session in ssh_sessions:
            print(f"   🔄 Session: {session.name}")
            self._process_session(session)
        
        print()
        print(f"✅ Phase 2 complete: {len(self.ssh_entries)} sessions processed")
        print()
    
    def _process_session(self, session: PuttySession):
        """Process a single PuTTY session."""
        # Detect authentication method
        auth = detect_auth_method(session.raw_data)
        print(f"      📋 {format_auth_info(auth)}")
        
        # Handle user@host notation
        hostname, username = split_user_at_host(session.hostname, session.username)
        
        # Determine identity file based on auth method
        identity_file = None
        comments = []
        
        if auth.method == "key" and auth.key_file:
            # Check for duplicate
            duplicate = self.registry.find_duplicate(auth.key_file)
            
            if duplicate:
                print(f"      ♻️  Duplicate: Reusing {os.path.basename(duplicate.openssh_path)}")
                identity_file = duplicate.openssh_path
                
                # Link session to key
                key_hash = duplicate.hash_value
                self.registry.link_session_to_key(key_hash, session.name)
            else:
                print(f"      🆕 New key: {os.path.basename(auth.key_file)}")
                # Register new key (conversion happens separately)
                key_name = os.path.splitext(os.path.basename(auth.key_file))[0]
                openssh_path = os.path.join(self.ssh_dir, key_name)
                
                try:
                    key_hash = self.registry.add_key(
                        ppk_path=auth.key_file,
                        openssh_path=openssh_path,
                        source="putty_registry"
                    )
                    identity_file = openssh_path
                    self.registry.link_session_to_key(key_hash, session.name)
                    comments.append(f'Converted from: "{auth.key_file}"')
                except Exception as e:
                    print(f"      ⚠️  Cannot register key: {e}")
                    comments.append(f"TODO: Convert key manually: {auth.key_file}")
        
        elif auth.method == "pageant":
            # Try fuzzy matching
            available_keys = [k.ppk_original for k in self.registry.get_all_keys()]
            
            if available_keys:
                best_match = get_best_match(session.name, available_keys, threshold=0.90)
                
                if best_match:
                    # Auto-match with high confidence
                    print(f"      🎯 Auto-matched: {best_match.key_name} ({best_match.confidence:.0%})")
                    key_hash = self.registry.calculate_hash(best_match.ppk_path)
                    key_info = self.registry.keys.get(key_hash)
                    if key_info:
                        identity_file = key_info.openssh_path
                        self.registry.link_session_to_key(key_hash, session.name)
                        comments.append(f"Originally used Pageant")
                        comments.append(f"Auto-matched: {best_match.key_name} ({best_match.confidence:.0%})")
                else:
                    # Multiple or uncertain matches
                    matches = fuzzy_match_key(session.name, available_keys)
                    
                    if matches and self.interactive:
                        selected = interactive_match_selection(session.name, matches)
                        if selected:
                            key_hash = self.registry.calculate_hash(selected.ppk_path)
                            key_info = self.registry.keys.get(key_hash)
                            if key_info:
                                identity_file = key_info.openssh_path
                                self.registry.link_session_to_key(key_hash, session.name)
                                comments.append(f"Originally used Pageant")
                                comments.append(f"Manually matched: {selected.key_name}")
                    
                    if not identity_file:
                        print(f"      ⚠️  No match selected")
                        comments.append("Originally used Pageant (no matching key found)")
                        comments.append("TODO: Add your key with: IdentityFile ~/.ssh/your_key")
            else:
                print(f"      ⚠️  No keys available for matching")
                comments.append("Originally used Pageant (no keys to match)")
                comments.append("TODO: Add your key with: IdentityFile ~/.ssh/your_key")
        
        else:  # password
            comments.append("Authentication: Password")
        
        # Create SSH config entry
        entry = SSHConfigEntry(
            host_alias=session.name,
            hostname=hostname,
            port=session.port,
            user=username if username else None,
            identity_file=identity_file,
            comments=comments
        )
        
        self.ssh_entries.append(entry)
        print(f"      ✅ Added to SSH config")


def generate_ssh_config_content(sessions: List[PuttySession]) -> str:
    """
    Generate SSH config content from PuTTY sessions (simplified for TUI).
    
    This is a simplified version that generates basic SSH config entries
    without the full two-phase key processing workflow.
    
    Args:
        sessions: List of PuTTY sessions
        
    Returns:
        SSH config formatted string
        
    Example:
        sessions = read_putty_sessions()
        config_content = generate_ssh_config_content(sessions)
    """
    from .converter import normalize_key_name
    
    entries = []
    
    for session in sessions:
        if not session.is_ssh:
            continue
        
        # Detect auth method
        auth = detect_auth_method(session.raw_data)
        
        # Handle user@host notation
        hostname, username = split_user_at_host(session.hostname, session.username)
        
        # Determine identity file
        identity_file = None
        comments = []
        
        if auth.method == "key" and auth.key_file:
            # Normalize key name (spaces → hyphens)
            key_name = os.path.splitext(os.path.basename(auth.key_file))[0]
            key_name = normalize_key_name(key_name)
            identity_file = f"~/.ssh/{key_name}"
            # Don't add conversion comment - assume keys are already converted
        elif auth.method == "pageant":
            comments.append("Originally used Pageant")
            comments.append("TODO: Specify IdentityFile path")
        else:
            comments.append("Authentication: Password")
        
        # Create entry
        entry = SSHConfigEntry(
            session_name=session.name,  # Original session name for comment
            host_alias=hostname,         # Use IP/hostname as Host
            hostname=hostname,
            port=session.port,
            user=username if username else None,
            identity_file=identity_file,
            comments=comments
        )
        
        entries.append(entry)
    
    # Build config content
    if not entries:
        return ""
    
    lines = [
        "# ==========================================",
        "# PuTTY Sessions (exported by TUI)",
        "# ==========================================",
        ""
    ]
    
    for entry in entries:
        lines.append(entry.to_ssh_config())
        lines.append("")
    
    # Join with \n first, then convert to platform-appropriate line endings
    content = "\n".join(lines)
    
    # Normalize line endings to platform-appropriate format
    platform_type = get_platform()
    if platform_type == "windows":
        line_ending = "\r\n"
    else:
        line_ending = "\n"
    
    # Normalize existing line endings to \n, then convert to platform format
    normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
    if line_ending != '\n':
        normalized_content = normalized_content.replace('\n', line_ending)
    
    return normalized_content


def write_ssh_config(
    entries: List[SSHConfigEntry],
    output_file: str = "~/.ssh/config",
    backup: bool = True
) -> None:
    """
    Write SSH config entries to file.
    
    Args:
        entries: List of SSHConfigEntry objects
        output_file: Path to SSH config file
        backup: Whether to backup existing config
    """
    output_file = os.path.expanduser(output_file)
    
    # Backup existing config if requested
    if backup and os.path.exists(output_file):
        backup_file = output_file + ".backup"
        print(f"📋 Backing up existing config to: {backup_file}")
        
        with open(output_file, 'r') as src:
            with open(backup_file, 'w') as dst:
                dst.write(src.read())
    
    # Write new config
    print(f"📝 Writing SSH config to: {output_file}")
    
    # Get platform-appropriate line ending
    platform_type = get_platform()
    if platform_type == "windows":
        line_ending = "\r\n"
    else:
        line_ending = "\n"
    
    with open(output_file, 'a') as f:
        f.write(line_ending + "# ==========================================" + line_ending)
        f.write("# PuTTY Sessions (converted)" + line_ending)
        f.write("# ==========================================" + line_ending + line_ending)
        
        for entry in entries:
            f.write(entry.to_ssh_config())
            f.write(line_ending + line_ending)
    
    print(f"✅ SSH config written successfully")
