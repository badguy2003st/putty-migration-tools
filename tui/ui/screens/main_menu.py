"""
Main Menu Screen - Entry point for the TUI.

Displays the main navigation options for all tools.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer
from textual.containers import Container, Vertical


class MainMenuScreen(Screen):
    """Main menu screen with navigation to all features.
    
    Navigation:
    - Tab/Shift+Tab: Navigate between buttons
    - Enter/Space: Select/activate button (automatic)
    - Q: Quit application
    - ESC: Go back
    """
    
    BINDINGS = [
        Binding("tab", "focus_next", "Next", show=True),
        Binding("shift+tab", "focus_previous", "Previous", show=True),
    ]
    
    def on_mount(self) -> None:
        """Set initial focus when screen is mounted."""
        # Focus the first button (Convert) for keyboard navigation
        try:
            first_button = self.query_one("#convert", Button)
            first_button.focus()
        except Exception:
            # Fallback: focus any button
            buttons = self.query(Button)
            if buttons:
                buttons.first().focus()
    
    def compose(self) -> ComposeResult:
        """Create the main menu UI."""
        yield Header()
        
        with Container(classes="menu-container"):
            yield Static("🔧 PuTTY Migration Tools", id="menu-title")
            yield Static(self._get_status_text(), id="menu-status")
            
            with Vertical():
                yield Button("🔑 Convert PPK Keys", id="convert", variant="primary")
                yield Button("📤 Export Sessions", id="export", variant="primary")
                
                # v1.1.1: Platform-specific export/import buttons
                from ...utils.platform import is_windows
                if is_windows():
                    yield Button("📦 Export All to ZIP", id="export-all", variant="primary")
                else:
                    yield Button("📥 Import All from ZIP", id="import-all", variant="primary")
                
                yield Button("⚙️  Settings", id="settings")
                yield Button("ℹ️  About", id="about")
                yield Button("❌ Exit", id="exit", variant="error")
        
        yield Footer()
    
    def _get_status_text(self) -> str:
        """Get status information about dependencies."""
        # Check for dependencies
        status_lines = []
        
        try:
            import textual
            status_lines.append("✅ Textual UI available")
        except ImportError:
            status_lines.append("❌ Textual not installed")
        
        # Check if on Windows (for Registry access)
        from ...utils.platform import is_windows
        if is_windows():
            status_lines.append("✅ Windows - Registry access available")
        else:
            status_lines.append("⚠️  Non-Windows - Limited features")
        
        # Check for PuTTY sessions (Windows only)
        if is_windows():
            try:
                from ...core.registry import count_putty_sessions
                session_count = count_putty_sessions()
                if session_count > 0:
                    status_lines.append(f"✅ Found {session_count} PuTTY session(s)")
                else:
                    status_lines.append("⚠️  No PuTTY sessions found")
            except Exception:
                status_lines.append("⚠️  Could not read PuTTY sessions")
        
        return "\n".join(status_lines)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "exit":
            self.app.exit()
        elif button_id == "convert":
            # Navigate to Conversion Screen
            from .conversion import ConversionScreen
            self.app.push_screen(ConversionScreen())
        elif button_id == "export":
            # Navigate to Export Screen
            from .export import ExportScreen
            self.app.push_screen(ExportScreen())
        elif button_id == "export-all":
            # v1.1.1: Navigate to Export All screen (Windows)
            from .export_all_screen import ExportAllScreen
            self.app.push_screen(ExportAllScreen())
        elif button_id == "import-all":
            # v1.1.1: Navigate to Import All screen (Linux)
            from .import_all_screen import ImportAllScreen
            self.app.push_screen(ImportAllScreen())
        elif button_id == "settings":
            # Navigate to Install/Settings screen
            from .install import InstallScreen
            self.app.push_screen(InstallScreen())
        elif button_id == "about":
            self._show_about()
    
    def _show_not_implemented(self, feature: str) -> None:
        """Show a message that a feature is not yet implemented."""
        self.app.notify(
            f"{feature} - Not yet implemented in TUI\n"
            f"Use the CLI: python -m tui.cli.export_ssh_config",
            title="Feature Info",
            severity="information",
            timeout=5
        )
    
    def _launch_ssh_config_export(self) -> None:
        """Launch SSH config export (currently via CLI notification)."""
        self.app.notify(
            "SSH Config Export\n\n"
            "Run from command line:\n"
            "  python -m tui --dry-run\n\n"
            "Or use full CLI:\n"
            "  python -m tui.cli.export_ssh_config --help",
            title="SSH Config Export",
            severity="information",
            timeout=10
        )
    
    def _show_about(self) -> None:
        """Show about information."""
        try:
            from tui import __version__
        except ImportError:
            __version__ = "0.9.0"
        
        self.app.notify(
            f"PuTTY Migration Tools v{__version__}\n\n"
            "Pure Python implementation\n"
            "Cross-platform • Security-first • Open Source\n\n"
            "Features:\n"
            "• Convert PPK keys to OpenSSH\n"
            "• Export sessions to SSH config\n"
            "• Export sessions to Tabby\n"
            "• Two-phase key deduplication\n"
            "• Fuzzy matching for Pageant\n\n"
            "License: MIT\n"
            "GitHub: github.com/yourusername/putty-migration-tools",
            title="About",
            severity="information",
            timeout=15
        )
