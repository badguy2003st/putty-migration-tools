"""
Export Screen - PuTTY Sessions export to Tabby/SSH Config.

Provides an interactive interface for exporting PuTTY registry sessions.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Button,
    Static,
    Header,
    Footer,
    DataTable,
    RadioSet,
    RadioButton,
    Input,
)
from textual.containers import Container, Vertical, Horizontal


class ExportScreen(Screen):
    """Session Export Screen.
    
    Features:
    - Displays PuTTY sessions from Windows Registry
    - Allows export to Tabby JSON or SSH Config
    - Shows session preview in a table
    - ESC to go back to main menu
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        """Create the export screen UI."""
        yield Header()
        
        with Container(classes="content-container"):
            yield Static("📤 Export PuTTY Sessions", classes="title")
            
            # Platform check
            yield Static(id="platform-warning", classes="warning")
            
            # Session preview table
            yield Static("📋 PuTTY Sessions:", classes="subtitle")
            yield DataTable(id="sessions-table")
            
            # Export format selection
            yield Static("📤 Export Format:", classes="subtitle")
            with RadioSet(id="export-format"):
                yield RadioButton("📁 SSH Config (OpenSSH format)", value=True)
                yield RadioButton("🖥️  Tabby JSON (terminal client)")
            
            # Output path
            yield Static("💾 Output Path:", classes="subtitle")
            yield Input(
                placeholder="Leave empty for default location",
                id="output-path"
            )
            
            # Status
            yield Static("Ready to export...", id="status-text", classes="status")
            
            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("▶ Export Sessions", id="export", variant="success")
                yield Button("🔄 Refresh", id="refresh")
                yield Button("« Back to Menu", id="back")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        # Check if on Windows
        from ...utils.platform import is_windows
        
        if not is_windows():
            warning = self.query_one("#platform-warning", Static)
            warning.update(
                "⚠️  Not running on Windows - PuTTY Registry export not available\n"
                "    This feature requires Windows and PuTTY installation"
            )
            
            # Disable export button
            try:
                export_button = self.query_one("#export", Button)
                export_button.disabled = True
            except Exception:
                pass
        else:
            # Load sessions
            self._load_sessions()
        
        # Set default output path
        from ...utils.platform import is_windows
        if is_windows():
            default_ssh_config = "$HOME\\.ssh\\config"
        else:
            default_ssh_config = "~/.ssh/config"
        
        input_field = self.query_one("#output-path", Input)
        input_field.placeholder = f"Default: {default_ssh_config}"
        
        # Focus export button
        try:
            export_button = self.query_one("#export", Button)
            export_button.focus()
        except Exception:
            pass
    
    def _load_sessions(self) -> None:
        """Load PuTTY sessions from Windows Registry."""
        table = self.query_one("#sessions-table", DataTable)
        status = self.query_one("#status-text", Static)
        
        # Add columns
        table.add_columns("Session Name", "Hostname", "Username", "Port", "Auth")
        
        try:
            # Import registry reader and auth detection
            from ...core.registry import read_putty_sessions
            from ...core.auth_detection import detect_auth_method
            
            # Read sessions
            sessions = read_putty_sessions()
            
            if not sessions:
                table.add_row("No sessions found", "-", "-", "-", "-")
                status.update("⚠️  No PuTTY sessions found in Registry")
                
                # Disable export
                export_button = self.query_one("#export", Button)
                export_button.disabled = True
            else:
                # Add each session to table
                for session in sessions:
                    # Detect authentication method from raw registry data
                    auth_info = detect_auth_method(session.raw_data)
                    
                    # Determine auth method display
                    if auth_info.method == "password":
                        auth_display = "🔒 Password"
                    elif auth_info.method == "key":
                        auth_display = "🔑 Key"
                    elif auth_info.method == "pageant":
                        auth_display = "🔐 Pageant"
                    else:
                        auth_display = "❓ Unknown"
                    
                    table.add_row(
                        session.name,
                        session.hostname or "-",
                        session.username or "-",
                        str(session.port),
                        auth_display
                    )
                
                status.update(f"✅ Found {len(sessions)} session(s) ready to export")
        
        except ImportError:
            table.add_row("Error", "Registry module not available", "-", "-", "-")
            status.update("❌ Error: Could not load registry reader")
        except Exception as e:
            table.add_row("Error", str(e), "-", "-", "-")
            status.update(f"❌ Error reading sessions: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "export":
            await self._start_export()
        elif button_id == "refresh":
            self._refresh_sessions()
        elif button_id == "back":
            self.app.pop_screen()
    
    def _refresh_sessions(self) -> None:
        """Refresh the session list."""
        # Clear table
        table = self.query_one("#sessions-table", DataTable)
        table.clear(columns=True)
        
        # Reload
        self._load_sessions()
        
        self.app.notify("Sessions refreshed", severity="information")
    
    async def _start_export(self) -> None:
        """Start the export process with real backend integration."""
        from ...core.registry import read_putty_sessions
        from ...core.tabby_export import export_to_tabby_file
        from ...core.ssh_config import generate_ssh_config_content
        from ...core.file_operations import write_file_atomic, merge_ssh_config
        from ...utils.platform import is_windows
        from pathlib import Path
        
        # Check we're on Windows
        if not is_windows():
            self.app.notify(
                "PuTTY Registry export is only available on Windows!",
                title="Platform Not Supported",
                severity="error"
            )
            return
        
        # Get selected format
        radio_set = self.query_one("#export-format", RadioSet)
        selected_index = radio_set.pressed_index
        
        formats = ["SSH Config", "Tabby JSON"]
        selected_format = formats[selected_index] if selected_index < len(formats) else "SSH Config"
        
        # Get output path
        output_path_str = self.query_one("#output-path", Input).value.strip()
        if not output_path_str:
            # Use defaults
            if selected_format == "SSH Config":
                output_path_str = "~/.ssh/config" if not is_windows() else str(Path.home() / ".ssh" / "config")
            else:
                output_path_str = "./tabby-config.json"
        
        output_path = Path(output_path_str).expanduser()
        
        # Update status
        status = self.query_one("#status-text", Static)
        status.update(f"Exporting to {selected_format}...")
        
        try:
            # Read PuTTY sessions
            sessions = read_putty_sessions()
            
            if not sessions:
                self.app.notify(
                    "No PuTTY sessions found in Registry!",
                    title="No Sessions",
                    severity="warning"
                )
                status.update("⚠️  No sessions to export")
                status.set_classes("warning")
                return
            
            # Filter to SSH sessions only
            ssh_sessions = [s for s in sessions if s.is_ssh]
            
            if not ssh_sessions:
                self.app.notify(
                    "No SSH sessions found (only SSH sessions are exported)!",
                    title="No SSH Sessions",
                    severity="warning"
                )
                status.update("⚠️  No SSH sessions to export")
                status.set_classes("warning")
                return
            
            # Simulate a small delay for UI feedback
            import asyncio
            await asyncio.sleep(0.2)
            
            # Export based on format
            if selected_format == "Tabby JSON":
                # Export to Tabby
                success, message = export_to_tabby_file(
                    ssh_sessions,
                    output_path,
                    grouped=True
                )
                
                if success:
                    status.update(f"✅ Exported {len(ssh_sessions)} session(s) to Tabby JSON")
                    status.set_classes("success")
                    self.app.notify(
                        f"Successfully exported {len(ssh_sessions)} SSH session(s)!\n\n"
                        f"Output file: {output_path}\n\n"
                        f"Import to Tabby:\n"
                        f"  Settings → Profiles & Connections → Import",
                        title="Export Complete",
                        severity="information",
                        timeout=10
                    )
                else:
                    status.update(f"❌ Export failed: {message}")
                    status.set_classes("error")
                    self.app.notify(
                        f"Export failed!\n\n{message}",
                        title="Export Error",
                        severity="error"
                    )
            
            else:  # SSH Config
                # Generate SSH config content
                config_content = generate_ssh_config_content(ssh_sessions)
                
                if not config_content:
                    status.update("⚠️  No valid SSH config entries generated")
                    status.set_classes("warning")
                    self.app.notify(
                        "Could not generate SSH config entries!",
                        title="Export Warning",
                        severity="warning"
                    )
                    return
                
                # Check if file exists (merge vs create new)
                if output_path.exists():
                    # Merge with existing
                    success, message = merge_ssh_config(
                        config_content,
                        output_path,
                        interactive=False  # Auto-merge for now
                    )
                else:
                    # Create new file
                    write_file_atomic(
                        config_content,
                        output_path,
                        backup=False,
                        permissions=0o644
                    )
                    success = True
                    message = f"Created SSH config at {output_path}"
                
                if success:
                    status.update(f"✅ Exported {len(ssh_sessions)} session(s) to SSH Config")
                    status.set_classes("success")
                    self.app.notify(
                        f"Successfully exported {len(ssh_sessions)} SSH session(s)!\n\n"
                        f"Output file: {output_path}\n\n"
                        f"Usage:\n"
                        f"  ssh <session-name>",
                        title="Export Complete",
                        severity="information",
                        timeout=10
                    )
                else:
                    status.update(f"❌ Export failed: {message}")
                    status.set_classes("error")
                    self.app.notify(
                        f"Export failed!\n\n{message}",
                        title="Export Error",
                        severity="error"
                    )
        
        except Exception as e:
            status.update(f"❌ Error: {str(e)}")
            status.set_classes("error")
            self.app.notify(
                f"Export failed with error:\n\n{str(e)}",
                title="Error",
                severity="error"
            )
