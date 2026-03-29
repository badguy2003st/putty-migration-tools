"""
Fuzzy matching for Pageant sessions.

When a PuTTY session uses Pageant (no direct key file), we try to match
it with available PPK keys based on session name similarity.
"""

import os
from typing import List, Dict
from difflib import SequenceMatcher
from dataclasses import dataclass


@dataclass
class KeyMatch:
    """Represents a potential key match for a session."""
    
    ppk_path: str
    """Path to the PPK file"""
    
    key_name: str
    """Base name of the key file"""
    
    confidence: float
    """Match confidence (0.0 to 1.0)"""
    
    reason: str
    """Reason for the match (exact, contains, fuzzy)"""


def fuzzy_match_key(session_name: str, available_keys: List[str]) -> List[KeyMatch]:
    """
    Try to match a session name with available PPK keys.
    
    Uses multiple strategies:
    1. Exact match (case-insensitive, normalized)
    2. Contains match (substring matching)
    3. Fuzzy match (Levenshtein distance via SequenceMatcher)
    
    Args:
        session_name: Name of the PuTTY session
        available_keys: List of paths to available PPK files
        
    Returns:
        List of KeyMatch objects, sorted by confidence (highest first)
        
    Example:
        >>> keys = ["./ppk_keys/production.ppk", "./ppk_keys/staging.ppk"]
        >>> matches = fuzzy_match_key("production-server", keys)
        >>> if matches and matches[0].confidence > 0.85:
        ...     print(f"Auto-match: {matches[0].key_name}")
    """
    matches = []
    
    # Normalize session name for comparison
    session_normalized = _normalize_name(session_name)
    
    for key_path in available_keys:
        key_name = os.path.basename(key_path)
        key_base = os.path.splitext(key_name)[0]  # Remove .ppk extension
        key_normalized = _normalize_name(key_base)
        
        # Strategy 1: Exact match (case-insensitive, normalized)
        if session_normalized == key_normalized:
            matches.append(KeyMatch(
                ppk_path=key_path,
                key_name=key_name,
                confidence=1.0,
                reason="exact"
            ))
            continue
        
        # Strategy 2: Contains match
        if key_normalized in session_normalized or session_normalized in key_normalized:
            # Calculate confidence based on length ratio
            shorter = min(len(session_normalized), len(key_normalized))
            longer = max(len(session_normalized), len(key_normalized))
            confidence = shorter / longer
            
            matches.append(KeyMatch(
                ppk_path=key_path,
                key_name=key_name,
                confidence=max(0.8, confidence),  # Minimum 0.8 for contains
                reason="contains"
            ))
            continue
        
        # Strategy 3: Fuzzy match (Levenshtein-like via SequenceMatcher)
        ratio = SequenceMatcher(None, session_normalized, key_normalized).ratio()
        if ratio > 0.6:  # Threshold for fuzzy matches
            matches.append(KeyMatch(
                ppk_path=key_path,
                key_name=key_name,
                confidence=ratio,
                reason="fuzzy"
            ))
    
    # Sort by confidence (highest first)
    matches.sort(key=lambda x: x.confidence, reverse=True)
    
    return matches


def _normalize_name(name: str) -> str:
    """
    Normalize a name for comparison.
    
    Removes common separators and converts to lowercase.
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name
        
    Example:
        >>> _normalize_name("Production-Server_Key")
        'productionserverkey'
    """
    # Convert to lowercase
    name = name.lower()
    
    # Remove common separators
    for char in ['-', '_', ' ', '.']:
        name = name.replace(char, '')
    
    return name


def get_best_match(
    session_name: str,
    available_keys: List[str],
    threshold: float = 0.85
) -> KeyMatch | None:
    """
    Get the best matching key for a session, if confidence meets threshold.
    
    Args:
        session_name: Name of the PuTTY session
        available_keys: List of paths to available PPK files
        threshold: Minimum confidence required (0.0 to 1.0)
        
    Returns:
        Best KeyMatch if confidence >= threshold, None otherwise
        
    Example:
        >>> best = get_best_match("prod-server", keys, threshold=0.85)
        >>> if best:
        ...     print(f"Using key: {best.key_name} ({best.confidence:.0%})")
    """
    matches = fuzzy_match_key(session_name, available_keys)
    
    if matches and matches[0].confidence >= threshold:
        return matches[0]
    
    return None


def interactive_match_selection(
    session_name: str,
    matches: List[KeyMatch],
    max_options: int = 5
) -> KeyMatch | None:
    """
    Interactively ask user to select the correct key match.
    
    Args:
        session_name: Name of the session
        matches: List of potential matches
        max_options: Maximum number of options to show
        
    Returns:
        Selected KeyMatch or None if user chooses manual
        
    Example:
        >>> matches = fuzzy_match_key("server", keys)
        >>> selected = interactive_match_selection("server", matches)
    """
    print(f"\n⚠️  Session '{session_name}' used Pageant - select matching key:")
    
    # Show top N matches
    display_matches = matches[:max_options]
    
    for i, match in enumerate(display_matches, 1):
        print(f"   {i}) {match.key_name} (confidence: {match.confidence:.0%}, reason: {match.reason})")
    
    print(f"   {len(display_matches) + 1}) None / Skip (will add manual comment)")
    
    while True:
        try:
            choice = input("   Choose: ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(display_matches):
                return display_matches[choice_num - 1]
            elif choice_num == len(display_matches) + 1:
                return None
            else:
                print("   Invalid choice. Try again.")
        except (ValueError, EOFError):
            print("   Invalid input. Try again.")
