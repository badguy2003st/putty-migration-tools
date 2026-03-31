"""
Install Screen - Dependency checker and installer UI.

Provides an interactive interface for checking and installing dependencies.
"""

import shutil
from typing import Dict

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Button,
    Static,
    Header,
    Footer,
    ListView,
    ListItem,
)
from textual.containers import Container, Vertical, Horizontal


class InstallScreen(Screen):
    """Dependency Install Screen.
    
    Features:
    - Checks for required Python dependencies (pip packages)
    - Shows installation status for Python and pip
    - Provides install instructions
    - Platform-specific guidance
    - ESC to go back to main menu
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        """Create the install screen UI."""
        yield Header()
        
        with Container(classes="content-container"):
            yield Static("📦 Dependency Installer", classes="title")
            
            # Platform info
            yield Static(id="platform-info", classes="subtitle")
            
            # Dependency list
            yield Static("🔍 Dependency Status:", classes="subtitle")
            yield ListView(id="dependency-list")
            
            # Instructions
            yield Static("", id="install-instructions", classes="status")
            
            # Action buttons
            with Vertical():
                yield Button("🔄 Refresh Status", id="refresh", variant="primary")
                yield Button("📋 Show Install Guide", id="guide")
                yield Button("« Back to Menu", id="back")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        # Show platform info
        self._show_platform_info()
        
        # Check dependencies
        self._check_dependencies()
        
        # Focus refresh button
        try:
            refresh_button = self.query_one("#refresh", Button)
            refresh_button.focus()
        except Exception:
            pass
    
    def _show_platform_info(self) -> None:
        """Display platform information."""
        from ...utils.platform import is_windows, is_linux, get_linux_distro
        
        platform_text = "🖥️  Platform: "
        
        if is_windows():
            platform_text += "Windows"
        elif is_linux():
            distro = get_linux_distro()
            platform_text += f"Linux ({distro})"
        else:
            platform_text += "Unknown (Windows/Linux only)"
        
        platform_info = self.query_one("#platform-info", Static)
        platform_info.update(platform_text)
    
    def _check_python_package(self, package_name: str) -> bool:
        """Check if a Python package is installed."""
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    def _check_dependencies(self) -> None:
        """Check which dependencies are installed."""
        dep_list = self.query_one("#dependency-list", ListView)
        
        # Clear existing items
        dep_list.clear()
        
        # System tools
        system_tools = {
            "python3": {"desc": "Python 3.8+", "required": True},
            "pip": {"desc": "Package manager", "required": True},
            "bw": {"desc": "Bitwarden CLI", "required": False},
        }
        
        # Python packages (v1.1.0: custom PPK parser)
        python_packages = {
            "textual": {"desc": "TUI framework", "required": True},
            "rich": {"desc": "Console output", "required": True},
            "cryptography": {"desc": "Key parsing", "required": True},
            "argon2pure": {"desc": "PPK v3 KDF", "required": True},
            "_argon2_cffi_bindings": {"desc": "Performance boost", "required": False},
        }
        
        # Track results
        results = {"system": {}, "packages": {}}
        
        # Check system tools
        dep_list.append(ListItem(Static("System Tools:", classes="subtitle")))
        for cmd, info in system_tools.items():
            is_installed = shutil.which(cmd) is not None
            results["system"][cmd] = {"installed": is_installed, "required": info["required"]}
            
            # Icon based on status
            if is_installed:
                status_icon = "✅"
                status_class = "success"
            elif info["required"]:
                status_icon = "❌"
                status_class = "error"
            else:
                status_icon = "⚠️ "
                status_class = "warning"
            
            req_label = " (optional)" if not info["required"] else ""
            item_text = f"{status_icon} {cmd:12} - {info['desc']}{req_label}"
            dep_list.append(ListItem(Static(item_text, classes=status_class)))
        
        # Check Python packages
        dep_list.append(ListItem(Static("\nPython Packages:", classes="subtitle")))
        for pkg, info in python_packages.items():
            is_installed = self._check_python_package(pkg)
            results["packages"][pkg] = {"installed": is_installed, "required": info["required"]}
            
            # Icon based on status
            if is_installed:
                status_icon = "✅"
                status_class = "success"
            elif info["required"]:
                status_icon = "❌"
                status_class = "error"
            else:
                status_icon = "⚠️ "
                status_class = "warning"
            
            req_label = " (optional)" if not info["required"] else ""
            item_text = f"{status_icon} {pkg:21} - {info['desc']}{req_label}"
            dep_list.append(ListItem(Static(item_text, classes=status_class)))
        
        # Update instructions based on missing dependencies
        self._update_instructions(results, python_packages)
    
    def _update_instructions(self, results: Dict, python_packages: Dict) -> None:
        """Update installation instructions based on missing dependencies."""
        instructions = self.query_one("#install-instructions", Static)
        
        # Check for missing REQUIRED dependencies
        missing_system = [
            cmd for cmd, data in results["system"].items() 
            if not data["installed"] and data["required"]
        ]
        missing_packages = [
            pkg for pkg, data in results["packages"].items()
            if not data["installed"] and data["required"]
        ]
        
        # All required deps installed
        if not missing_system and not missing_packages:
            # Check optional deps
            optional_missing = []
            if not results["system"].get("bw", {}).get("installed"):
                optional_missing.append("bw (Bitwarden CLI)")
            if not results["packages"].get("_argon2_cffi_bindings", {}).get("installed"):
                optional_missing.append("argon2-cffi-bindings")
            
            msg = "✅ All required dependencies installed!\n\n"
            
            if optional_missing:
                msg += f"⚠️  Optional (recommended):\n"
                for opt in optional_missing:
                    msg += f"   • {opt}\n"
                msg += "\n"
            
            msg += "📦 To install/update packages:\n"
            msg += "   pip install -r tui/requirements.txt\n\n"
            msg += "v1.1.0: textual, rich, cryptography, argon2"
            
            instructions.update(msg)
            instructions.set_classes("success status")
            return
        
        # Show what's missing
        install_text = "❌ Missing required dependencies:\n\n"
        
        if "python3" in missing_system:
            install_text += "• python3: Download from https://www.python.org/downloads/\n"
        if "pip" in missing_system:
            install_text += "• pip: Included with Python 3.4+, check your installation\n"
        
        if missing_packages:
            install_text += f"\n• Python packages ({len(missing_packages)}): Run pip install -r tui/requirements.txt\n"
        
        install_text += "\nClick 'Show Install Guide' for detailed instructions."
        
        instructions.update(install_text)
        instructions.set_classes("error status")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "refresh":
            self._check_dependencies()
            self.app.notify("Dependency status refreshed", severity="information")
        elif button_id == "guide":
            self._show_install_guide()
        elif button_id == "back":
            self.app.pop_screen()
    
    def _show_install_guide(self) -> None:
        """Show detailed installation guide."""
        guide_text = (
            "📖 Installation Guide\n\n"
            "PuTTY Migration Tools v1.1.0\n"
            "Requires Python 3.8 or higher\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. Install Python:\n"
            "   • Windows: https://www.python.org/downloads/\n"
            "   • Linux: Usually pre-installed\n\n"
            "2. Install Python packages:\n"
            "   pip install -r tui/requirements.txt\n\n"
            "   Required packages:\n"
            "   • textual (TUI framework)\n"
            "   • rich (console output)\n"
            "   • cryptography (key parsing)\n"
            "   • argon2pure (PPK v3 KDF)\n\n"
            "   Optional (recommended):\n"
            "   • argon2-cffi-bindings (speed boost)\n\n"
            "3. Optional - Bitwarden Export:\n"
            "   Download Bitwarden CLI from:\n"
            "   https://bitwarden.com/help/cli/\n\n"
            "4. Run the tool:\n"
            "   python -m tui\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ v1.1.0: Custom PPK parser (no puttykeys!)\n"
            "   Supports PPK v2 + v3, all key types"
        )
        
        self.app.notify(
            guide_text,
            title="Installation Guide",
            severity="information",
            timeout=20
        )
