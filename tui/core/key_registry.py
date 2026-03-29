"""
Key Registry for PPK deduplication via SHA256 hashing.

This module implements two-phase key processing:
1. Process ./ppk_keys/ directory FIRST
2. Process Registry keys with deduplication

The KeyRegistry tracks all processed keys to avoid duplicate conversions.
"""

import hashlib
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class KeyInfo:
    """Information about a processed PPK key."""
    
    ppk_original: str
    """Original path to the PPK file"""
    
    openssh_path: str
    """Path to the converted OpenSSH private key"""
    
    public_key_path: Optional[str] = None
    """Path to the OpenSSH public key (if extracted)"""
    
    source: str = "unknown"
    """Source of the key: 'ppk_keys_dir' or 'putty_registry'"""
    
    sessions_using: List[str] = field(default_factory=list)
    """List of PuTTY session names that use this key"""
    
    hash_value: str = ""
    """SHA256 hash of the PPK file"""


class KeyRegistry:
    """
    Registry for tracking processed PPK keys with SHA256-based deduplication.
    
    Example:
        registry = KeyRegistry()
        
        # Process local PPK keys from ./ppk_keys/
        for ppk_file in glob.glob("./ppk_keys/*.ppk"):
            key_hash = registry.add_key(
                ppk_path=ppk_file,
                openssh_path="~/.ssh/my_key",
                source="ppk_keys_dir"
            )
        
        # Check for duplicate keys from Registry
        duplicate = registry.find_duplicate("C:\\Users\\...\\same_key.ppk")
        if duplicate:
            # Reuse existing key
            openssh_path = duplicate.openssh_path
        else:
            # Convert new key
            openssh_path = convert_new_key(...)
    """
    
    def __init__(self):
        """Initialize an empty key registry."""
        self.keys: Dict[str, KeyInfo] = {}  # hash → KeyInfo
    
    def calculate_hash(self, ppk_path: str) -> str:
        """
        Calculate SHA256 hash of a PPK file.
        
        Args:
            ppk_path: Path to the PPK file
            
        Returns:
            SHA256 hash as hexadecimal string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        ppk_path = os.path.expanduser(ppk_path)
        
        if not os.path.exists(ppk_path):
            raise FileNotFoundError(f"PPK file not found: {ppk_path}")
        
        sha256 = hashlib.sha256()
        
        try:
            with open(ppk_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
        except IOError as e:
            raise IOError(f"Cannot read PPK file {ppk_path}: {e}")
        
        return sha256.hexdigest()
    
    def add_key(
        self,
        ppk_path: str,
        openssh_path: str,
        source: str = "unknown",
        public_key_path: Optional[str] = None
    ) -> str:
        """
        Register a processed key in the registry.
        
        Args:
            ppk_path: Path to the original PPK file
            openssh_path: Path to the converted OpenSSH private key
            source: Source identifier ('ppk_keys_dir' or 'putty_registry')
            public_key_path: Optional path to the public key
            
        Returns:
            SHA256 hash of the PPK file
            
        Example:
            key_hash = registry.add_key(
                ppk_path="./ppk_keys/production.ppk",
                openssh_path="~/.ssh/production_key",
                source="ppk_keys_dir"
            )
        """
        key_hash = self.calculate_hash(ppk_path)
        
        self.keys[key_hash] = KeyInfo(
            ppk_original=ppk_path,
            openssh_path=openssh_path,
            public_key_path=public_key_path,
            source=source,
            sessions_using=[],
            hash_value=key_hash
        )
        
        return key_hash
    
    def find_duplicate(self, ppk_path: str) -> Optional[KeyInfo]:
        """
        Check if a key was already processed.
        
        Args:
            ppk_path: Path to the PPK file to check
            
        Returns:
            KeyInfo if duplicate found, None otherwise
            
        Example:
            duplicate = registry.find_duplicate("C:\\Keys\\my_key.ppk")
            if duplicate:
                print(f"Already processed: {duplicate.openssh_path}")
            else:
                print("New key - needs processing")
        """
        try:
            key_hash = self.calculate_hash(ppk_path)
            return self.keys.get(key_hash)
        except (FileNotFoundError, IOError):
            return None
    
    def link_session_to_key(self, key_hash: str, session_name: str) -> bool:
        """
        Link a PuTTY session to a key.
        
        This tracks which sessions use which keys for reporting purposes.
        
        Args:
            key_hash: SHA256 hash of the key
            session_name: Name of the PuTTY session
            
        Returns:
            True if linked successfully, False if key not found
            
        Example:
            registry.link_session_to_key(key_hash, "production-server")
        """
        if key_hash in self.keys:
            if session_name not in self.keys[key_hash].sessions_using:
                self.keys[key_hash].sessions_using.append(session_name)
            return True
        return False
    
    def get_all_keys(self) -> List[KeyInfo]:
        """
        Get all registered keys.
        
        Returns:
            List of KeyInfo objects
        """
        return list(self.keys.values())
    
    def get_keys_by_source(self, source: str) -> List[KeyInfo]:
        """
        Get all keys from a specific source.
        
        Args:
            source: Source identifier to filter by
            
        Returns:
            List of KeyInfo objects from that source
            
        Example:
            local_keys = registry.get_keys_by_source("ppk_keys_dir")
        """
        return [
            key_info for key_info in self.keys.values()
            if key_info.source == source
        ]
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about processed keys.
        
        Returns:
            Dictionary with counts by source
            
        Example:
            stats = registry.get_statistics()
            print(f"Local keys: {stats.get('ppk_keys_dir', 0)}")
            print(f"Registry keys: {stats.get('putty_registry', 0)}")
        """
        stats = {}
        for key_info in self.keys.values():
            source = key_info.source
            stats[source] = stats.get(source, 0) + 1
        return stats
    
    def __len__(self) -> int:
        """Return the number of registered keys."""
        return len(self.keys)
    
    def __contains__(self, key_hash: str) -> bool:
        """Check if a key hash is registered."""
        return key_hash in self.keys
