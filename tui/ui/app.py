"""
Main Textual Application for PuTTY Migration Tools.

This is the entry point for the TUI interface.
"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, Vertical
from textual.widgets import Static, Button

from .screens.main_menu import MainMenuScreen
from ..core.file_operations import ensure_ppk_directory


class FirstTimeSetupDialog(ModalScreen):
    """Modal dialog shown when ppk_keys directory is created."""
    
    def __init__(self, path: Path, message: str):
        super().__init__()
        self.path = path
        self.message = message
    
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            with Vertical():
                yield Static(self.message, id="message")
                yield Button("Got it!", variant="primary", id="ok")
    
    def on_button_pressed(self) -> None:
        self.dismiss()


class PuttyMigrationApp(App):
    """
    Main TUI application for PuTTY Migration Tools.
    
    Features:
    - Cross-platform terminal UI
    - Dark theme
    - Keyboard navigation
    - Multiple screens with stack management
    - Auto-import to Bitwarden on exit (if export was created)
    """
    
    CSS_PATH = "styles.tcss"
    
    TITLE = "PuTTY Migration Tools"
    SUB_TITLE = "Convert PuTTY keys and sessions to modern formats"
    
    # Flag for Bitwarden auto-import
    bitwarden_export_file: str = None
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode", show=False),
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]
    
    def on_mount(self) -> None:
        """Called when app starts."""
        # Check if ppk_keys directory exists (create if not)
        check = ensure_ppk_directory()
        
        if check['created']:
            # Show dialog FIRST, then MainMenu via callback
            def show_main_menu(result):
                """Callback after dialog is dismissed."""
                self.push_screen(MainMenuScreen())
            
            self.push_screen(
                FirstTimeSetupDialog(
                    path=check['path'],
                    message=check['tui_message']
                ),
                callback=show_main_menu  # MainMenu shown after dialog
            )
        else:
            # No dialog needed - directly show MainMenu
            self.push_screen(MainMenuScreen())
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode (keeping dark only for this project)."""
        self.dark = not self.dark
    
    def action_pop_screen(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
