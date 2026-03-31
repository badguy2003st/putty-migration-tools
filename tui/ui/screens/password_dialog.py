"""
Password Dialog Screen - Interactive password input for encrypted PPK files.

v1.1.0: Provides 3 options when password is required:
- Try: Enter password manually
- Skip: Skip this file and continue
- Cancel: Stop conversion to edit passwords.txt
"""

from dataclasses import dataclass
from pathlib import Path

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static, Input, Button
from textual.containers import Container, Horizontal
from textual.binding import Binding


@dataclass
class PasswordDialogResult:
    """Result from password dialog interaction."""
    
    action: str
    """Action chosen: 'try', 'skip', or 'cancel'"""
    
    password: str = ""
    """Password entered (only for 'try' action)"""
    
    ppk_filename: str = ""
    """PPK filename being processed"""


class PasswordDialog(Screen[PasswordDialogResult]):
    """
    Password input dialog for encrypted PPK files.
    
    Shows when:
    - PPK file is encrypted
    - Passwords from passwords.txt didn't work
    
    User options:
    - Try: Enter password and retry
    - Skip: Skip this file, continue with next
    - Cancel: Stop batch, edit passwords.txt
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]
    
    def __init__(
        self, 
        ppk_filename: str, 
        passwords_tried: int, 
        current: int, 
        total: int
    ):
        """
        Initialize password dialog.
        
        Args:
            ppk_filename: Name of PPK file needing password
            passwords_tried: Number of passwords tried from file
            current: Current file number
            total: Total files to process
        """
        super().__init__()
        self.ppk_filename = ppk_filename
        self.passwords_tried = passwords_tried
        self.current = current
        self.total = total
    
    def compose(self) -> ComposeResult:
        """Create dialog UI."""
        yield Header()
        
        with Container(classes="dialog-container"):
            yield Static(
                f"🔒 Password Required [{self.current}/{self.total}]", 
                classes="title"
            )
            yield Static(f"\nFile: {self.ppk_filename}", classes="subtitle")
            
            if self.passwords_tried > 0:
                yield Static(
                    f"⚠️  Tried {self.passwords_tried} password(s) from passwords.txt\n"
                    f"   None of them worked for this file",
                    classes="warning"
                )
            else:
                yield Static(
                    "ℹ️  No passwords found in passwords.txt",
                    classes="info"
                )
            
            yield Static("\nEnter password or choose an option:", classes="label")
            yield Input(
                placeholder="Type password here...", 
                password=True, 
                id="password-input"
            )
            
            with Horizontal(classes="button-row"):
                yield Button("✓ Try Password", id="try", variant="primary")
                yield Button("⏭ Skip This File", id="skip")
                yield Button("✕ Cancel & Edit passwords.txt", id="cancel", variant="error")
            
            yield Static(
                "\n💡 Tip: Edit ppk_keys/passwords.txt to add your passwords",
                classes="hint"
            )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Focus password input when dialog opens."""
        self.query_one("#password-input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in password input."""
        if event.input.id == "password-input":
            # Trigger Try button
            self._try_password()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        
        if button_id == "try":
            self._try_password()
        
        elif button_id == "skip":
            self.dismiss(PasswordDialogResult(
                action="skip",
                ppk_filename=self.ppk_filename
            ))
        
        elif button_id == "cancel":
            self.dismiss(PasswordDialogResult(
                action="cancel",
                ppk_filename=self.ppk_filename
            ))
    
    def _try_password(self) -> None:
        """Process Try Password action."""
        password_input = self.query_one("#password-input", Input)
        password = password_input.value
        
        if not password:
            self.app.notify(
                "Please enter a password",
                severity="warning",
                timeout=3
            )
            return
        
        self.dismiss(PasswordDialogResult(
            action="try",
            password=password,
            ppk_filename=self.ppk_filename
        ))
    
    def action_cancel(self) -> None:
        """Handle ESC key."""
        self.dismiss(PasswordDialogResult(
            action="cancel",
            ppk_filename=self.ppk_filename
        ))
