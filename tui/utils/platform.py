"""
Platform detection utilities.

Provides cross-platform compatibility helpers.
"""

import platform
import sys
from typing import Literal

PlatformType = Literal["windows", "linux", "unknown"]


def get_platform() -> PlatformType:
    """
    Detect the current operating system.
    
    Returns:
        "windows", "linux", or "unknown"
    """
    system = platform.system().lower()
    
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == "windows"


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == "linux"


def check_python_version(minimum: tuple = (3, 8)) -> bool:
    """
    Check if Python version meets minimum requirement.
    
    Args:
        minimum: Minimum version tuple (major, minor)
        
    Returns:
        True if version is sufficient
    """
    return sys.version_info >= minimum


def get_python_version() -> str:
    """Get Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_linux_distro() -> str:
    """
    Detect Linux distribution.
    
    Returns:
        Distribution name: "ubuntu", "debian", "fedora", "arch", or "unknown"
    """
    if not is_linux():
        return "unknown"
    
    try:
        # Check /etc/os-release (standard method)
        with open("/etc/os-release") as f:
            content = f.read().lower()
            
            # Check for specific distributions
            if "ubuntu" in content:
                return "ubuntu"
            elif "debian" in content:
                return "debian"
            elif "fedora" in content:
                return "fedora"
            elif "arch" in content:
                return "arch"
            elif "centos" in content:
                return "centos"
            elif "rhel" in content or "red hat" in content:
                return "rhel"
    except (FileNotFoundError, IOError):
        pass
    
    return "unknown"
