"""
Import All Screen - Linux TUI for importing migration packages

Imports Windows-generated export packages with selective options:
- SSH keys to ~/.ssh
- SSH configuration
- Bitwarden vault export

v1.1.1: Complete export/import workflow
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Static, Header, Footer, RichLog, Input, Checkbox, RadioSet, RadioButton, Label
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual import work

from ...core.import_package import import_package, ImportOptions, ImportResult, validate_zip_structure, get_import_summary


class ImportAllScreen(Screen):
    """
    Linux TUI screen for importing ZIP packages from Windows.
    
    Features:
    - File selection for ZIP
    - Checkbox selection for components
    - Conflict mode selection
    - Bitwarden import options
    - Results summary
    """
    
    CSS = """
    ImportAllScreen {
        align: center middle;
    }
    
    #import-container {
        width: 85;
        height: auto;
        max-height: 95%;
        border: solid $accent;
        padding: 1 2;
    }
    
    #import-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 0;
    }
    
    #import-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #file-input-container {
        height: auto;
        margin: 0 0 1 0;
        border: solid $primary-darken-2;
        padding: 0 1;
    }
    
    #options-container {
        height: auto;
        margin: 0 0 1 0;
        border: solid $primary-darken-2;
        padding: 0 1;
    }
    
    #ssh-options-row {
        height: auto;
        margin: 0 0 1 0;
    }
    
    #ssh-options-row Checkbox {
        margin: 0 2 0 0;
    }
    
    #import-log {
        width: 100%;
        height: 10;
        border: solid $primary;
        margin: 0 0 1 0;
    }
    
    #button-container {
        align: center middle;
        width: 100%;
        height: auto;
        margin-top: 0;
    }
    
    .section-label {
        text-style: bold;
        color: $accent;
        margin: 0 0;
    }
    
    .option-checkbox {
        margin: 0 0 1 0;
    }
    
    .radio-group {
        layout: horizontal;
        height: auto;
        width: 100%;
        border: none;
        background: transparent;
        padding: 0;
        margin: 0 0 1 2;
    }
    
    .radio-group RadioButton {
        margin: 0 2 0 0;
    }
    """
    
    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.import_result: Optional[ImportResult] = None
        self.is_importing = False
        self.zip_validated = False
    
    def compose(self) -> ComposeResult:
        """Create the import UI."""
        yield Header()
        
        with ScrollableContainer(id="import-container"):
            yield Static("📥 Import All from ZIP", id="import-title")
            yield Static("Import Windows migration package", id="import-subtitle")
            
            # File selection
            with Vertical(id="file-input-container"):
                yield Label("ZIP File Path:", classes="section-label")
                yield Input(
                    placeholder="Path to putty-migration-export-*.zip",
                    id="zip-file-input"
                )
                yield Static("", id="validation-status")
            
            # Import options
            with Vertical(id="options-container"):
                yield Label("Import Options:", classes="section-label")
                
                # SSH options grouped horizontally
                with Horizontal(id="ssh-options-row"):
                    yield Checkbox("🔑 SSH Keys to ~/.ssh", id="opt-ssh-keys", value=True)
                    yield Checkbox("⚙️  SSH Config to ~/.ssh/config", id="opt-ssh-config", value=True)
                
                # Conflict mode (conditional, under SSH Keys)
                yield Label("   Conflict Mode:", classes="section-label", id="conflict-label")
                with RadioSet(id="conflict-mode", classes="radio-group"):
                    yield RadioButton("Rename", value=True)
                    yield RadioButton("Overwrite")
                    yield RadioButton("Skip")
                
                # Bitwarden separate
                yield Checkbox("🔐 Bitwarden Vault", id="opt-bitwarden", value=False, classes="option-checkbox")
                
                # Bitwarden mode (conditional)
                yield Label("   Bitwarden Mode:", classes="section-label", id="bw-label")
                with RadioSet(id="bw-mode", classes="radio-group"):
                    yield RadioButton("Show instructions", value=True)
                    yield RadioButton("Auto-import")
            
            # Log only (no progress bar - tool is fast!)
            yield RichLog(id="import-log", wrap=True, highlight=True, markup=True)
            
            # Buttons
            with Horizontal(id="button-container", classes="action-buttons"):
                yield Button("🚀 Start Import", id="start-import", variant="success")
                yield Button("💾 Export Log", id="export-log", variant="primary", disabled=True)
                yield Button("⬅️  Back", id="back", variant="default")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        # Set focus on input field
        zip_input = self.query_one("#zip-file-input", Input)
        zip_input.focus()
        
        # Set initial visibility of conditional options
        self._update_conditional_visibility()
        
        log = self.query_one("#import-log", RichLog)
        log.write("[bold cyan]Ready to import[/bold cyan]")
        log.write("")
        
        # Auto-detect ZIP file
        detected_zip = self._auto_detect_zip()
        
        if detected_zip:
            zip_input.value = str(detected_zip)
            self._validate_zip_file(detected_zip)
            
            log.write(f"[green]✓ Auto-detected: {detected_zip.name}[/green]")
            log.write(f"  [dim]Location: {detected_zip.parent}[/dim]")
            log.write("")
            log.write("[cyan]You can edit the path if needed[/cyan]")
        else:
            log.write("[yellow]⚠ No ZIP file found in common locations[/yellow]")
            log.write("Enter path to putty-migration-export-*.zip manually")
        
        log.write("")
        log.write("Steps:")
        log.write("1. Verify/edit ZIP file path")
        log.write("2. Select what to import")
        log.write("3. Click 'Start Import'")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Validate ZIP file when path changes."""
        if event.input.id == "zip-file-input":
            zip_path = event.value.strip()
            if zip_path:
                self._validate_zip_file(Path(zip_path))
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes to show/hide conditional options."""
        self._update_conditional_visibility()
    
    def _update_conditional_visibility(self) -> None:
        """Show/hide conditional options based on checkbox state."""
        try:
            # Get checkbox states
            ssh_keys_checked = self.query_one("#opt-ssh-keys", Checkbox).value
            bitwarden_checked = self.query_one("#opt-bitwarden", Checkbox).value
            
            # Show/hide conflict mode (only if SSH keys checked)
            conflict_label = self.query_one("#conflict-label", Label)
            conflict_mode = self.query_one("#conflict-mode", RadioSet)
            
            conflict_label.display = ssh_keys_checked
            conflict_mode.display = ssh_keys_checked
            
            # Show/hide bitwarden mode (only if Bitwarden checked)
            bw_label = self.query_one("#bw-label", Label)
            bw_mode = self.query_one("#bw-mode", RadioSet)
            
            bw_label.display = bitwarden_checked
            bw_mode.display = bitwarden_checked
            
        except Exception:
            # Widgets not ready yet
            pass
    
    def _auto_detect_zip(self) -> Optional[Path]:
        """Auto-detect ZIP file in common locations."""
        import re
        from typing import List, Tuple
        
        search_locations = [
            Path.cwd(),
            Path.home(),
            Path.home() / "Downloads",
        ]
        
        def extract_filename_timestamp(path: Path) -> Optional[str]:
            match = re.search(r'(\d{8}-\d{6})', path.name)
            return match.group(1) if match else None
        
        def get_newest_zip(zip_files: List[Path]) -> Path:
            if not zip_files:
                return None
            if len(zip_files) == 1:
                return zip_files[0]
            
            files_with_ts: List[Tuple[str, Path]] = []
            for f in zip_files:
                ts = extract_filename_timestamp(f)
                if ts:
                    files_with_ts.append((ts, f))
            
            if len(files_with_ts) == len(zip_files):
                files_with_ts.sort(reverse=True, key=lambda x: x[0])
                return files_with_ts[0][1]
            
            return max(zip_files, key=lambda p: p.stat().st_mtime)
        
        for location in search_locations:
            if not location.exists():
                continue
            
            zip_files = list(location.glob("putty-migration-export-*.zip"))
            if zip_files:
                return get_newest_zip(zip_files)
        
        return None
    
    def _validate_zip_file(self, zip_path: Path) -> None:
        """Validate the ZIP file."""
        status = self.query_one("#validation-status", Static)
        
        valid, message = validate_zip_structure(zip_path)
        
        if valid:
            status.update(f"[green]✓ {message}[/green]")
            self.zip_validated = True
        else:
            status.update(f"[red]✗ {message}[/red]")
            self.zip_validated = False
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        button_id = event.button.id
        
        if button_id == "start-import":
            if not self.is_importing and self.zip_validated:
                self.start_import()
        elif button_id == "export-log":
            self._export_log()
        elif button_id == "back":
            self.action_go_back()
    
    def _export_log(self) -> None:
        """Export import log to a text file."""
        try:
            log_output = self.query_one("#import-log", RichLog)
            
            log_lines = []
            for line in log_output.lines:
                log_lines.append(line.text if hasattr(line, 'text') else str(line))
            
            if not log_lines:
                self.app.notify(
                    "No log content to export.\nRun an import first.",
                    title="Empty Log",
                    severity="warning",
                    timeout=5
                )
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = Path(f"import_log_{timestamp}.txt")
            
            export_content = [
                "=" * 70,
                "PuTTY Migration Tools - Import Log",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 70,
                "",
                *log_lines
            ]
            
            log_file.write_text("\n".join(export_content), encoding='utf-8')
            
            self.app.notify(
                f"Log exported successfully!\n\n"
                f"File: {log_file.absolute()}\n"
                f"Lines: {len(log_lines)}",
                title="Export Complete",
                severity="information",
                timeout=8
            )
            
        except Exception as e:
            self.app.notify(
                f"Failed to export log:\n{str(e)}",
                title="Export Error",
                severity="error",
                timeout=5
            )
    
    @work(exclusive=True)
    async def start_import(self) -> None:
        """Start the import process."""
        self.is_importing = True
        
        start_btn = self.query_one("#start-import", Button)
        start_btn.disabled = True
        
        log = self.query_one("#import-log", RichLog)
        
        log.clear()
        log.write("[bold cyan]🚀 Starting import...[/bold cyan]")
        log.write("")
        
        try:
            zip_input = self.query_one("#zip-file-input", Input)
            zip_path = Path(zip_input.value.strip())
            
            if not zip_path.exists():
                log.write(f"[red]✗ File not found: {zip_path}[/red]")
                start_btn.disabled = False
                self.is_importing = False
                return
            
            # Get import options
            opt_ssh_keys = self.query_one("#opt-ssh-keys", Checkbox).value
            opt_ssh_config = self.query_one("#opt-ssh-config", Checkbox).value
            opt_bitwarden = self.query_one("#opt-bitwarden", Checkbox).value
            
            conflict_radio = self.query_one("#conflict-mode", RadioSet)
            conflict_modes = ["rename", "overwrite", "skip"]
            conflict_mode = conflict_modes[conflict_radio.pressed_index] if conflict_radio.pressed_index is not None else "rename"
            
            bw_radio = self.query_one("#bw-mode", RadioSet)
            bw_auto = (bw_radio.pressed_index == 1) if bw_radio.pressed_index is not None else False
            
            options = ImportOptions(
                ssh_keys=opt_ssh_keys,
                ssh_config=opt_ssh_config,
                bitwarden=opt_bitwarden,
                conflict_mode=conflict_mode,
                bitwarden_auto_import=bw_auto
            )
            
            log.write(f"[bold]Source:[/bold] {zip_path.name}")
            
            import_list = []
            if opt_ssh_keys:
                import_list.append(f"SSH Keys ({conflict_mode})")
            if opt_ssh_config:
                import_list.append("SSH Config")
            if opt_bitwarden:
                import_list.append(f"Bitwarden ({'auto' if bw_auto else 'manual'})")
            
            import_text = ", ".join(import_list) if import_list else "Nothing selected"
            log.write(f"[bold]Import:[/bold] {import_text}")
            log.write("")
            
            if not import_list:
                log.write("[yellow]⚠ No import options selected[/yellow]")
                start_btn.disabled = False
                self.is_importing = False
                return
            
            # Progress callback
            def on_progress(current: int, total: int, message: str):
                log.write(f"[cyan]{message}[/cyan]")
            
            # Start import
            result = await import_package(
                zip_path,
                options,
                progress_callback=on_progress
            )
            
            self.import_result = result
            
            if result.success:
                log.write("")
                summary = get_import_summary(result)
                
                for line in summary.split('\n'):
                    if line.startswith('✅'):
                        log.write(f"[bold green]{line}[/bold green]")
                    elif line.startswith('❌'):
                        log.write(f"[bold red]{line}[/bold red]")
                    elif '✓' in line or '•' in line:
                        log.write(f"[green]{line}[/green]")
                    elif 'Run:' in line:
                        log.write(f"[yellow]{line}[/yellow]")
                    else:
                        log.write(line)
                
                # Enable export log button
                export_btn = self.query_one("#export-log", Button)
                export_btn.disabled = False
                
                start_btn.label = "✓ Done"
                start_btn.variant = "primary"
                start_btn.disabled = False
                self.is_importing = False
                
            else:
                log.write("")
                log.write(f"[bold red]❌ Import Failed[/bold red]")
                log.write(f"[red]{result.error}[/red]")
                
                start_btn.label = "🔄 Retry"
                start_btn.disabled = False
                self.is_importing = False
        
        except Exception as e:
            log.write("")
            log.write(f"[bold red]❌ Unexpected Error[/bold red]")
            log.write(f"[red]{str(e)}[/red]")
            
            start_btn.label = "🔄 Retry"
            start_btn.disabled = False
            self.is_importing = False
    
    def action_go_back(self) -> None:
        """Go back to main menu."""
        if not self.is_importing:
            self.app.pop_screen()
