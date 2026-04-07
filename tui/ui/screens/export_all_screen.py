"""
Export All Screen - Windows TUI for complete package export

Creates a portable ZIP package containing:
- Converted OpenSSH keys
- SSH configuration
- Tabby terminal config
- Bitwarden vault export

v1.1.1: Complete export/import workflow
"""

from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer, ProgressBar, RichLog
from textual.containers import Container, Vertical, Horizontal
from textual import work

from ...core.export_package import create_export_package, generate_default_zip_filename, ExportPackageResult
from ...core.file_operations import load_password_file


class ExportAllScreen(Screen):
    """
    Windows TUI screen for exporting all PuTTY data to ZIP.
    
    Features:
    - Shows progress during export
    - Displays status log
    - Shows export summary on success
    - Handles errors gracefully
    """
    
    CSS = """
    ExportAllScreen {
        align: center middle;
    }
    
    #export-container {
        width: 80;
        height: auto;
        border: solid $accent;
        padding: 1 2;
    }
    
    #export-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    #export-progress {
        width: 100%;
        margin: 1 0;
    }
    
    #export-log {
        width: 100%;
        height: 15;
        border: solid $primary;
        margin: 1 0;
    }
    
    #button-container {
        align: center middle;
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    
    .export-button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.export_result: Optional[ExportPackageResult] = None
        self.is_exporting = False
    
    def compose(self) -> ComposeResult:
        """Create the export UI."""
        yield Header()
        
        with Container(id="export-container"):
            yield Static("📦 Export All to ZIP", id="export-title")
            yield Static("Creates a complete migration package for Linux", id="export-subtitle")
            
            yield ProgressBar(total=100, show_eta=False, id="export-progress")
            yield RichLog(id="export-log", wrap=True, highlight=True, markup=True)
            
            with Horizontal(id="button-container", classes="action-buttons"):
                yield Button("🚀 Start Export", id="start-export", variant="success")
                yield Button("⬅️  Back", id="back", variant="default")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        log = self.query_one("#export-log", RichLog)
        log.write("[bold cyan]Ready to export[/bold cyan]")
        log.write("")
        log.write("This will create a ZIP package containing:")
        log.write("  • Converted OpenSSH keys")
        log.write("  • SSH configuration")
        log.write("  • Tabby terminal config")
        log.write("  • Bitwarden vault export")
        log.write("")
        log.write("[yellow]Click 'Start Export' to begin[/yellow]")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        
        if button_id == "start-export":
            if not self.is_exporting:
                self.start_export()
        elif button_id == "back":
            self.action_go_back()
    
    @work(exclusive=True)
    async def start_export(self) -> None:
        """Start the export process."""
        self.is_exporting = True
        
        # Disable start button
        start_btn = self.query_one("#start-export", Button)
        start_btn.disabled = True
        
        log = self.query_one("#export-log", RichLog)
        progress = self.query_one("#export-progress", ProgressBar)
        
        log.clear()
        log.write("[bold cyan]🚀 Starting export...[/bold cyan]")
        log.write("")
        
        try:
            # Load passwords
            ppk_dir = Path("./ppk_keys").resolve()
            passwords_file = ppk_dir / "passwords.txt"
            
            passwords = []
            if passwords_file.exists():
                passwords = load_password_file(passwords_file)
                log.write(f"[green]✓[/green] Loaded {len(passwords)} password(s)")
            else:
                log.write("[yellow]⚠[/yellow] No passwords.txt found (unencrypted keys only)")
            
            log.write("")
            
            # Generate output filename
            output_zip = Path.cwd() / generate_default_zip_filename()
            
            # Progress callback
            def on_progress(current: int, total: int, message: str):
                percent = int((current / total) * 100)
                progress.update(progress=percent)
                log.write(f"[cyan]{message}[/cyan]")
            
            # Start export
            log.write(f"[bold]Output:[/bold] {output_zip.name}")
            log.write("")
            
            result = await create_export_package(
                output_zip,
                ppk_dir,
                passwords=passwords,
                progress_callback=on_progress
            )
            
            self.export_result = result
            
            if result.success:
                # Success!
                log.write("")
                log.write("[bold green]✅ Export Complete![/bold green]")
                log.write("")
                log.write(f"[bold]ZIP File:[/bold] {result.zip_file}")
                log.write(f"[bold]Size:[/bold] {self._format_size(result.size_bytes)}")
                log.write("")
                
                if result.manifest:
                    counts = result.manifest.get('counts', {})
                    log.write("[bold]Contents:[/bold]")
                    log.write(f"  • {counts.get('ssh_keys_exported', 0)} SSH keys")
                    log.write(f"  • {counts.get('sessions_ssh', 0)} session configurations")
                    log.write(f"  • Tabby terminal config")
                    log.write(f"  • Bitwarden vault export")
                    log.write("")
                    
                    enc_status = result.manifest.get('encryption_status', {})
                    if enc_status.get('encrypted_keys', 0) > 0:
                        log.write(f"[yellow]ℹ[/yellow] {enc_status['encrypted_keys']} encrypted keys preserved")
                    
                    errors = result.manifest.get('errors', [])
                    if errors:
                        log.write("")
                        log.write(f"[yellow]⚠ {len(errors)} keys could not be converted:[/yellow]")
                        for error in errors[:5]:  # Show first 5
                            log.write(f"  • {error['file']}: {error['error']}")
                
                log.write("")
                log.write("[bold cyan]📋 Next Steps:[/bold cyan]")
                log.write("1. Copy ZIP to your Linux machine")
                log.write("2. Run: putty-migrate import-all --zip <file>")
                log.write("3. Select import options interactively")
                
                progress.update(progress=100)
                
                # Change button to "Done"
                start_btn.label = "✓ Done"
                start_btn.variant = "primary"
                start_btn.disabled = False
                self.is_exporting = False  # Reset flag so Back button works
                
            else:
                # Failed
                log.write("")
                log.write(f"[bold red]❌ Export Failed[/bold red]")
                log.write(f"[red]{result.error}[/red]")
                
                start_btn.label = "🔄 Retry"
                start_btn.disabled = False
                self.is_exporting = False
        
        except Exception as e:
            log.write("")
            log.write(f"[bold red]❌ Unexpected Error[/bold red]")
            log.write(f"[red]{str(e)}[/red]")
            
            start_btn.label = "🔄 Retry"
            start_btn.disabled = False
            self.is_exporting = False
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def action_go_back(self) -> None:
        """Go back to main menu."""
        if not self.is_exporting:
            self.app.pop_screen()
