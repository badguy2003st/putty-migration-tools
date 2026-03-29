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
    
    def _check_dependencies(self) -> None:
        """Check which dependencies are installed."""
        dep_list = self.query_one("#dependency-list", ListView)
        
        # Clear existing items
        dep_list.clear()
        
        # Define dependencies to check (Python packages only)
        dependencies = {
            "python3": "Python 3.8+",
            "pip": "Python package manager",
        }
        
        # Check each dependency
        results = {}
        for cmd, description in dependencies.items():
            is_installed = shutil.which(cmd) is not None
            results[cmd] = is_installed
            
            # Create status line
            if is_installed:
                status_icon = "✅"
                status_class = "success"
            else:
                status_icon = "❌"
                status_class = "error"
            
            # Add to list
            item_text = f"{status_icon} {cmd:12} - {description}"
            dep_list.append(ListItem(Static(item_text, classes=status_class)))
        
        # Update instructions based on missing dependencies
        self._update_instructions(results)
    
    def _update_instructions(self, results: Dict[str, bool]) -> None:
        """Update installation instructions based on missing dependencies."""
        instructions = self.query_one("#install-instructions", Static)
        
        missing = [cmd for cmd, installed in results.items() if not installed]
        
        if not missing:
            instructions.update(
                "✅ All core dependencies installed!\n\n"
                "📦 Install Python packages:\n"
                "   pip install -r tui/requirements.txt\n\n"
                "This will install: textual, rich, puttykeys"
            )
            instructions.set_classes("success status")
            return
        
        # Show what's missing
        install_text = "❌ Missing required dependencies:\n\n"
        
        if "python3" in missing:
            install_text += "• python3: Download from https://www.python.org/downloads/\n"
        if "pip" in missing:
            install_text += "• pip: Included with Python 3.4+, check your installation\n"
        
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
            "PuTTY Migration Tools requires Python 3.8 or higher.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1. Install Python:\n"
            "   • Windows: https://www.python.org/downloads/\n"
            "   • Linux: Usually pre-installed\n\n"
            "2. Install Python packages:\n"
            "   pip install -r tui/requirements.txt\n\n"
            "   This installs:\n"
            "   • textual (TUI framework)\n"
            "   • rich (console output)\n"
            "   • puttykeys (PPK conversion)\n\n"
            "3. Run the tool:\n"
            "   python -m tui\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ No external tools needed!\n"
            "All functionality is pure Python."
        )
        
        self.app.notify(
            guide_text,
            title="Installation Guide",
            severity="information",
            timeout=20
        )
