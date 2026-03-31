"""
SSH Import Dialog - Interactive configuration for ~/.ssh import on Linux.

Provides a 2-step dialog for:
1. Choosing import destination (~/.ssh vs ./openssh_keys)
2. Handling file conflicts (rename/overwrite/skip)
"""

from dataclasses import dataclass
from typing import Literal, List
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Static,
    RadioSet,
    RadioButton,
    Label,
)
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding


@dataclass
class SSHImportChoice:
    """User choices for SSH key import to ~/.ssh."""
    
    cancelled: bool = False
    """True if user cancelled the dialog"""
    
    import_to_ssh: bool = False
    """True if keys should be copied to ~/.ssh"""
    
    conflict_mode: Literal["rename", "overwrite", "skip"] = "rename"
    """How to handle existing files in ~/.ssh"""
    
    conflicts: List[str] = None
    """List of key names that already exist in ~/.ssh"""


class SSHImportDialog(ModalScreen[SSHImportChoice]):
    """
    Interactive dialog for Linux ~/.ssh import configuration.
    
    Flow:
    1. Ask if user wants to copy to ~/.ssh
    2. If yes + conflicts exist: Ask how to handle conflicts
    3. Return SSHImportChoice with user selections
    
    Example:
        choice = await self.app.push_screen_wait(SSHImportDialog(ppk_files))
        if not choice.cancelled and choice.import_to_ssh:
            # Copy to ~/.ssh with conflict_mode
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]
    
    CSS = """
    SSHImportDialog {
        align: center middle;
    }
    
    SSHImportDialog > Container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    
    SSHImportDialog .dialog-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    SSHImportDialog .dialog-subtitle {
        text-align: left;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    SSHImportDialog .conflict-list {
        background: $panel;
        padding: 1;
        margin-bottom: 1;
    }
    
    SSHImportDialog RadioSet {
        margin-bottom: 1;
    }
    
    SSHImportDialog Horizontal {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    
    SSHImportDialog Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, ppk_files: List[Path]):
        """
        Initialize the SSH import dialog.
        
        Args:
            ppk_files: List of PPK files that will be converted
        """
        super().__init__()
        self.ppk_files = ppk_files
        self.choice = SSHImportChoice()
        self.step = 1  # Current dialog step
        self.conflicts = []
    
    def compose(self) -> ComposeResult:
        """Create the initial dialog UI (Step 1: Destination)."""
        with Container():
            yield Static("🔑 SSH Keys Destination", classes="dialog-title")
            
            yield Static(
                "Where should the converted keys be saved?",
                classes="dialog-subtitle"
            )
            
            with RadioSet(id="destination"):
                yield RadioButton(
                    "✓ Copy to ~/.ssh (ready to use immediately)",
                    value=True,
                    id="opt-ssh"
                )
                yield RadioButton(
                    "Keep in ./openssh_keys (manual import later)",
                    id="opt-local"
                )
            
            yield Static(
                "💡 Tip: ~/.ssh keys are automatically detected by SSH clients",
                classes="dialog-subtitle"
            )
            
            with Horizontal():
                yield Button("Continue", variant="primary", id="continue")
                yield Button("Cancel", id="cancel")
    
    async def _check_conflicts(self) -> List[str]:
        """
        Scan ~/.ssh for existing keys that would conflict.
        
        Returns:
            List of key base names that already exist
        """
        ssh_dir = Path.home() / ".ssh"
        
        if not ssh_dir.exists():
            return []
        
        conflicts = []
        for ppk_file in self.ppk_files:
            key_name = ppk_file.stem  # Filename without .ppk extension
            
            # Check if private key exists
            if (ssh_dir / key_name).exists():
                conflicts.append(key_name)
        
        return conflicts
    
    async def _show_conflict_dialog(self):
        """Show Step 2: Conflict resolution options."""
        # Remove all existing widgets
        await self.query("*").remove()
        
        # Mount container FIRST (must be attached before mounting children)
        await self.mount(Container())
        container = self.query_one(Container)
        
        # Now mount children to the attached container
        await container.mount(
            Static("⚠️  File Conflicts Detected", classes="dialog-title")
        )
        
        await container.mount(
            Static(
                f"Found {len(self.conflicts)} existing key(s) in ~/.ssh:",
                classes="dialog-subtitle"
            )
        )
        
        # Show list of conflicts
        conflict_text = "\n".join(f"  • {name}" for name in self.conflicts[:5])
        if len(self.conflicts) > 5:
            conflict_text += f"\n  ... and {len(self.conflicts) - 5} more"
        
        await container.mount(
            Static(conflict_text, classes="conflict-list")
        )
        
        await container.mount(
            Static("How should conflicts be handled?", classes="dialog-subtitle")
        )
        
        # Conflict resolution options (Rename as default)
        # Mount RadioSet FIRST, then add children
        radio_set = RadioSet(id="conflict-mode")
        await container.mount(radio_set)
        
        # Now mount children to the attached RadioSet
        await radio_set.mount(
            RadioButton(
                "✓ Rename with number (recommended)",
                value=True,
                id="mode-rename"
            )
        )
        await radio_set.mount(
            Static("    Example: oracle → oracle.1 (keeps both keys)")
        )
        await radio_set.mount(
            RadioButton(
                "Overwrite existing files",
                id="mode-overwrite"
            )
        )
        await radio_set.mount(
            Static("    Creates backup as .bak (oracle → oracle.bak)")
        )
        await radio_set.mount(
            RadioButton(
                "Skip existing files",
                id="mode-skip"
            )
        )
        await radio_set.mount(
            Static("    Only copy keys that don't exist yet")
        )
        
        # Buttons - mount Horizontal FIRST, then buttons
        button_row = Horizontal()
        await container.mount(button_row)
        
        await button_row.mount(Button("Continue", variant="primary", id="finish"))
        await button_row.mount(Button("Cancel", id="cancel"))
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "cancel":
            self.choice.cancelled = True
            self.dismiss(self.choice)
        
        elif button_id == "continue":
            # Step 1: Check destination choice
            radio_set = self.query_one("#destination", RadioSet)
            selected_button = radio_set.pressed_button
            
            if selected_button and selected_button.id == "opt-ssh":
                # User wants to copy to ~/.ssh
                self.choice.import_to_ssh = True
                
                # Check for conflicts
                self.conflicts = await self._check_conflicts()
                
                if self.conflicts:
                    # Show conflict resolution dialog
                    await self._show_conflict_dialog()
                    self.step = 2
                else:
                    # No conflicts - finish
                    self.choice.conflict_mode = "rename"  # Default (won't matter)
                    self.dismiss(self.choice)
            else:
                # User wants local openssh_keys directory
                self.choice.import_to_ssh = False
                self.dismiss(self.choice)
        
        elif button_id == "finish":
            # Step 2: Get conflict mode
            radio_set = self.query_one("#conflict-mode", RadioSet)
            selected_button = radio_set.pressed_button
            
            if selected_button:
                if selected_button.id == "mode-rename":
                    self.choice.conflict_mode = "rename"
                elif selected_button.id == "mode-overwrite":
                    self.choice.conflict_mode = "overwrite"
                elif selected_button.id == "mode-skip":
                    self.choice.conflict_mode = "skip"
            
            self.choice.conflicts = self.conflicts
            self.dismiss(self.choice)
    
    def action_cancel(self) -> None:
        """Handle ESC key."""
        self.choice.cancelled = True
        self.dismiss(self.choice)
