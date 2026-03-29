"""
Conversion Screen - PPK to OpenSSH/Bitwarden conversion UI.

Provides an interactive interface for converting .ppk keys to various formats.
"""

import glob
import os
from pathlib import Path
from typing import List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Button,
    Static,
    Header,
    Footer,
    ProgressBar,
    RadioSet,
    RadioButton,
    ListView,
    ListItem,
)
from textual.containers import Container, Vertical, Horizontal


class ConversionScreen(Screen):
    """PPK Key Conversion Screen.
    
    Features:
    - Scans ./ppk_keys/ directory for .ppk files
    - Allows selection of output format (OpenSSH/Bitwarden/SSH Config)
    - Shows progress with live updates
    - ESC to go back to main menu
    """
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        """Create the conversion screen UI."""
        yield Header()
        
        with Container(classes="content-container"):
            yield Static("🔑 PPK Key Conversion", classes="title")
            
            # File list section
            yield Static("📁 PPK Files Found:", classes="subtitle")
            yield ListView(id="file-list")
            
            # Format selection
            yield Static("📤 Output Format:", classes="subtitle")
            with RadioSet(id="format-selection"):
                yield RadioButton("📁 OpenSSH Files (individual .key files)", value=True)
                yield RadioButton("🔐 Bitwarden Import (vault items)")
                yield RadioButton("⚙️  SSH Config (~/.ssh/config entries)")
            
            # Progress section
            yield Static("Progress:", classes="subtitle")
            yield ProgressBar(id="progress", total=100, show_eta=False)
            yield Static("Ready to convert...", id="status-text", classes="status")
            
            # Log output (scrollable)
            yield Static("", id="log-output", classes="status")
            
            # Action buttons
            with Horizontal():
                yield Button("▶ Start Conversion", id="start", variant="success")
                yield Button("« Back to Menu", id="back")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        # Scan for PPK files and populate the list
        self._populate_file_list()
        
        # Focus the start button
        try:
            start_button = self.query_one("#start", Button)
            start_button.focus()
        except Exception:
            pass
    
    def _populate_file_list(self) -> None:
        """Scan for PPK files and populate the file list."""
        file_list = self.query_one("#file-list", ListView)
        
        # Get PPK files
        ppk_files = self._scan_ppk_files()
        
        if not ppk_files:
            file_list.append(ListItem(Static("⚠️  No .ppk files found in ./ppk_keys/")))
            file_list.append(ListItem(Static("    Place your .ppk files in the ppk_keys directory")))
            
            # Disable start button
            try:
                start_button = self.query_one("#start", Button)
                start_button.disabled = True
            except Exception:
                pass
        else:
            # Add each file to the list
            for ppk_file in ppk_files:
                file_name = os.path.basename(ppk_file)
                file_size = os.path.getsize(ppk_file)
                size_kb = file_size / 1024
                
                file_list.append(
                    ListItem(
                        Static(f"🔑 {file_name} ({size_kb:.1f} KB)")
                    )
                )
            
            # Update status
            status = self.query_one("#status-text", Static)
            status.update(f"Found {len(ppk_files)} .ppk file(s) ready to convert")
    
    def _scan_ppk_files(self) -> List[str]:
        """Scan the ppk_keys directory for .ppk files.
        
        Returns:
            List of absolute paths to .ppk files
        """
        ppk_dir = Path("./ppk_keys")
        
        if not ppk_dir.exists():
            ppk_dir.mkdir(exist_ok=True)
            return []
        
        # Find all .ppk files
        ppk_files = list(ppk_dir.glob("*.ppk"))
        return [str(f.absolute()) for f in ppk_files]
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "start":
            await self._start_conversion()
        elif button_id == "back":
            self.app.pop_screen()
    
    async def _start_conversion(self) -> None:
        """Start the conversion process with real backend integration."""
        from ...core.converter import (
            batch_convert_ppk_files,
            get_conversion_summary,
            check_puttykeys_available,
            copy_key_to_ssh
        )
        from ...utils.security import show_security_reminder
        from ...utils.platform import is_linux
        
        # Check if puttykeys is available
        if not await check_puttykeys_available():
            self.app.notify(
                "puttykeys library not found!\n\n"
                "Please install it using:\n"
                "pip install puttykeys",
                title="Missing Dependency",
                severity="error"
            )
            return
        
        # Get selected format
        radio_set = self.query_one("#format-selection", RadioSet)
        selected_index = radio_set.pressed_index
        
        formats = ["OpenSSH Files", "Bitwarden Import", "SSH Config"]
        selected_format = formats[selected_index] if selected_index < len(formats) else "OpenSSH Files"
        
        # Bitwarden SSH Key export
        if selected_format == "Bitwarden Import":
            await self._bitwarden_export()
            return
        
        # Get PPK files
        ppk_files = self._scan_ppk_files()
        
        if not ppk_files:
            self.app.notify(
                "No PPK files found!\nPlace .ppk files in the ppk_keys directory.",
                title="No Files",
                severity="warning"
            )
            return
        
        # NEW: Linux ~/.ssh import dialog (only for OpenSSH Files format)
        ssh_import_choice = None
        if selected_format == "OpenSSH Files" and is_linux():
            from .ssh_import_dialog import SSHImportDialog
            
            ssh_import_choice = await self.app.push_screen_wait(
                SSHImportDialog([Path(f) for f in ppk_files])
            )
            
            if ssh_import_choice.cancelled:
                return  # User cancelled the dialog
        
        # Update UI
        progress_bar = self.query_one("#progress", ProgressBar)
        status_text = self.query_one("#status-text", Static)
        log_output = self.query_one("#log-output", Static)
        start_button = self.query_one("#start", Button)
        
        # Disable start button during conversion
        start_button.disabled = True
        
        # Show initial status
        status_text.update(f"Converting {len(ppk_files)} file(s) to {selected_format}...")
        log_output.update("")
        
        try:
            # Determine output directory based on format
            if selected_format == "OpenSSH Files":
                output_dir = Path("./openssh_keys")
            elif selected_format == "SSH Config":
                output_dir = Path.home() / ".ssh"
            else:
                output_dir = Path("./openssh_keys")
            
            # Create output directory
            output_dir.mkdir(exist_ok=True)
            
            total = len(ppk_files)
            log_lines = []
            
            # Progress callback for batch conversion
            def progress_callback(current: int, total_files: int, filename: str):
                progress_bar.update(progress=(current / total_files) * 100)
                status_text.update(f"Processing {current}/{total_files}: {filename}...")
            
            # Convert all files
            results = await batch_convert_ppk_files(
                [Path(f) for f in ppk_files],
                output_dir,
                progress_callback=progress_callback
            )
            
            # NEW: Copy to ~/.ssh if requested (Linux only)
            copy_results = []
            if ssh_import_choice and ssh_import_choice.import_to_ssh:
                status_text.update("Copying keys to ~/.ssh...")
                
                # Copy both private and public keys
                for result in results:
                    if result.success and result.output_file:
                        # Copy private key
                        private_copy = await copy_key_to_ssh(
                            Path(result.output_file),
                            ssh_import_choice.conflict_mode
                        )
                        copy_results.append(private_copy)
                        
                        # Copy public key if exists
                        pub_file = Path(result.output_file).with_suffix('.pub')
                        if pub_file.exists():
                            public_copy = await copy_key_to_ssh(
                                pub_file,
                                ssh_import_choice.conflict_mode
                            )
                            copy_results.append(public_copy)
            
            # Build log output
            if copy_results:
                # Show ~/.ssh copy results
                log_lines.append("Keys created in ~/.ssh:")
                log_lines.append("━" * 60)
                
                # Group by key name (private + public)
                key_groups = {}
                for copy_result in copy_results:
                    dest_path = Path(copy_result['destination'])
                    key_name = dest_path.stem if dest_path.suffix != '.pub' else dest_path.stem
                    
                    if key_name not in key_groups:
                        key_groups[key_name] = {'private': None, 'public': None}
                    
                    if dest_path.suffix == '.pub':
                        key_groups[key_name]['public'] = copy_result
                    else:
                        key_groups[key_name]['private'] = copy_result
                
                # Display grouped results
                for key_name, group in sorted(key_groups.items()):
                    priv = group['private']
                    pub = group['public']
                    
                    if priv:
                        action_desc = {
                            'copied': 'no conflict',
                            'renamed': 'renamed - original kept',
                            'overwritten': 'overwritten - backed up as .bak',
                            'skipped': 'skipped - already exists'
                        }.get(priv['action'], priv['action'])
                        
                        # Show private key
                        priv_path = Path(priv['destination'])
                        log_lines.append(f"  🔑 {priv_path.name:<20} (600) [{action_desc}]")
                        
                        # Show public key
                        if pub:
                            pub_path = Path(pub['destination'])
                            log_lines.append(f"  🔓 {pub_path.name:<20} (644)")
                        
                        log_lines.append("")  # Empty line between keys
                
                # Show skipped keys if any
                skipped = [r for r in copy_results if r['action'] == 'skipped']
                if skipped:
                    log_lines.append("Keys skipped (already exist):")
                    for skip in skipped:
                        skip_name = Path(skip['destination']).name
                        log_lines.append(f"  ⏭  {skip_name}")
                    log_lines.append("")
                
                log_lines.append("💡 Tip: Test your keys with:")
                if copy_results:
                    first_key = Path(copy_results[0]['destination'])
                    log_lines.append(f"   ssh -i ~/.ssh/{first_key.name} user@host")
            else:
                # Original log output for non-Linux or openssh_keys directory
                for result in results:
                    file_name = os.path.basename(result.ppk_file)
                    if result.success:
                        log_lines.append(f"✅ {file_name} → {output_dir}")
                    else:
                        error_short = result.error[:50] if result.error else "Unknown error"
                        log_lines.append(f"❌ {file_name}: {error_short}")
            
            log_output.update("\n".join(log_lines))
            
            # Get summary
            summary = get_conversion_summary(results)
            
            # Update final status
            progress_bar.update(progress=100)
            if summary["successful"] == summary["total"]:
                status_text.update(
                    f"✅ All {summary['total']} file(s) converted successfully!"
                )
                status_text.set_classes("success")
            else:
                status_text.update(
                    f"⚠️  {summary['successful']}/{summary['total']} file(s) converted "
                    f"({summary['failed']} failed)"
                )
                status_text.set_classes("warning")
            
            # Show notification
            if summary["successful"] > 0:
                # Build notification message based on copy results
                if copy_results:
                    # ~/.ssh import notification
                    copied_count = sum(1 for r in copy_results if r['action'] in ['copied', 'renamed'])
                    skipped_count = sum(1 for r in copy_results if r['action'] == 'skipped')
                    overwritten_count = sum(1 for r in copy_results if r['action'] == 'overwritten')
                    
                    msg_lines = [
                        f"✅ Successfully converted {summary['successful']}/{summary['total']} PPK files!",
                        "",
                        f"📋 Copied to ~/.ssh/:"
                    ]
                    
                    if copied_count > 0:
                        msg_lines.append(f"  • {copied_count // 2} key pair(s) imported")
                    if skipped_count > 0:
                        msg_lines.append(f"  • {skipped_count // 2} key pair(s) skipped (already exist)")
                    if overwritten_count > 0:
                        msg_lines.append(f"  • {overwritten_count // 2} key pair(s) overwritten (backups created)")
                    
                    msg_lines.extend([
                        "",
                        "🔒 Keys have secure permissions (600/644)",
                        "",
                        "⚠️  Original .ppk files remain in ppk_keys/",
                        "Please backup and securely delete them when ready."
                    ])
                    
                    notification_msg = "\n".join(msg_lines)
                else:
                    # Standard openssh_keys directory notification
                    notification_msg = (
                        f"Successfully converted {summary['successful']}/{summary['total']} PPK files!\n\n"
                        f"Output directory: {output_dir}\n"
                        f"🔒 Keys have secure permissions (600)\n\n"
                        f"⚠️  Original .ppk files remain in ppk_keys/\n"
                        f"Please backup and securely delete them when ready."
                    )
                
                self.app.notify(
                    notification_msg,
                    title="Conversion Complete",
                    severity="information" if summary["failed"] == 0 else "warning",
                    timeout=10
                )
            else:
                self.app.notify(
                    "Conversion failed!\n\n"
                    "Check the log output for details.",
                    title="Conversion Failed",
                    severity="error"
                )
            
        except Exception as e:
            status_text.update(f"❌ Error: {str(e)}")
            status_text.set_classes("error")
            log_output.update(f"❌ Unexpected error: {str(e)}")
            self.app.notify(
                f"Conversion failed with error:\n{str(e)}",
                title="Error",
                severity="error"
            )
        finally:
            # Re-enable start button
            start_button.disabled = False
    
    async def _bitwarden_export(self) -> None:
        """Execute Bitwarden SSH Key export."""
        from ...core.registry import read_putty_sessions
        from ...core.bitwarden_export import generate_bitwarden_export, validate_bitwarden_export
        from ...core.auth_detection import detect_auth_method
        
        # Update UI
        progress_bar = self.query_one("#progress", ProgressBar)
        status_text = self.query_one("#status-text", Static)
        log_output = self.query_one("#log-output", Static)
        start_button = self.query_one("#start", Button)
        
        start_button.disabled = True
        status_text.update("Reading PuTTY sessions...")
        progress_bar.update(progress=10)
        
        try:
            # 1. Read PuTTY sessions
            sessions = read_putty_sessions()
            progress_bar.update(progress=20)
            
            # 2. Filter to sessions with SSH keys
            sessions_with_keys = [
                s for s in sessions 
                if detect_auth_method(s.raw_data).method == "key"
            ]
            
            if not sessions_with_keys:
                self.app.notify(
                    "No SSH key sessions found!\n\n"
                    "Only sessions with SSH key authentication can be exported to Bitwarden.\n\n"
                    "Make sure your PuTTY sessions are configured to use private key files.",
                    title="No Key-Based Sessions",
                    severity="warning",
                    timeout=10
                )
                status_text.update("No sessions with SSH key authentication found")
                log_output.update("⚠️  No sessions configured with SSH key authentication")
                return
            
            status_text.update(f"Found {len(sessions_with_keys)} session(s) with SSH keys...")
            progress_bar.update(progress=20)
            
            # 3. Auto-convert ALL PPK files to OpenSSH format
            ppk_keys_dir = Path("./ppk_keys")
            openssh_keys_dir = Path("./openssh_keys")
            openssh_keys_dir.mkdir(exist_ok=True)
            
            if ppk_keys_dir.exists():
                ppk_files = list(ppk_keys_dir.glob("*.ppk"))
                
                if ppk_files:
                    from ...core.converter import batch_convert_ppk_files
                    
                    status_text.update(f"Converting {len(ppk_files)} PPK file(s) to OpenSSH format...")
                    progress_bar.update(progress=30)
                    
                    # Progress callback for conversion (30% → 50%)
                    def conversion_progress(current: int, total: int, filename: str):
                        percent = 30 + (current / total * 20)  # 30% to 50%
                        progress_bar.update(progress=percent)
                        status_text.update(f"Converting {current}/{total}: {filename}...")
                    
                    # Convert all PPK files
                    results = await batch_convert_ppk_files(
                        ppk_files,
                        openssh_keys_dir,
                        progress_callback=conversion_progress
                    )
                    
                    # Build conversion log
                    conversion_log_lines = []
                    successful = sum(1 for r in results if r.success)
                    failed = len(results) - successful
                    
                    conversion_log_lines.append(f"PPK Conversion: {successful}/{len(results)} successful")
                    
                    if failed > 0:
                        conversion_log_lines.append(f"\n⚠️  {failed} conversions failed:")
                        for result in results:
                            if not result.success:
                                conversion_log_lines.append(f"  - {Path(result.ppk_file).name}: {result.error}")
                    
                    log_output.update("\n".join(conversion_log_lines))
                    
                    progress_bar.update(progress=50)
                    status_text.update(f"PPK conversion complete ({successful}/{len(results)}), generating export...")
            
            progress_bar.update(progress=60)
            status_text.update("Generating Bitwarden export...")
            
            # 4. Generate Bitwarden JSON (with PPK dir for public key extraction fallback)
            ppk_keys_dir = Path("./ppk_keys")
            json_export = generate_bitwarden_export(
                sessions_with_keys, 
                openssh_keys_dir,
                ppk_keys_dir if ppk_keys_dir.exists() else None
            )
            progress_bar.update(progress=80)
            
            # 5. Validate the export
            valid, msg = validate_bitwarden_export(json_export)
            if not valid:
                self.app.notify(
                    f"Export validation failed!\n\n{msg}",
                    title="Validation Error",
                    severity="error"
                )
                status_text.update(f"❌ Validation failed: {msg}")
                return
            
            progress_bar.update(progress=90)
            status_text.update("Writing export file...")
            
            # 6. Write export file
            output_path = Path("./bitwarden-export.json")
            output_path.write_text(json_export, encoding='utf-8')
            
            # Set flag for auto-import prompt on exit
            self.app.bitwarden_export_file = str(output_path.absolute())
            
            progress_bar.update(progress=100)
            
            # Count successful exports (parse JSON to get item count)
            import json
            export_data = json.loads(json_export)
            exported_count = len(export_data.get("items", []))
            
            # Update status
            status_text.update(f"✅ Exported {exported_count} SSH key(s) to Bitwarden format!")
            status_text.set_classes("success")
            
            # Build log output (append to existing conversion log)
            existing_log = log_output.renderable if hasattr(log_output, 'renderable') else ""
            log_lines = []
            
            # Keep conversion log if it exists
            if existing_log:
                log_lines.append(str(existing_log))
                log_lines.append("")
                log_lines.append("─" * 60)
                log_lines.append("")
            
            log_lines.append(f"✅ Generated Bitwarden export: {output_path.name}")
            log_lines.append(f"   {exported_count} SSH key(s) exported")
            log_lines.append("")
            log_lines.append("Import to Bitwarden:")
            log_lines.append("  1. bw login")
            log_lines.append("  2. bw unlock")
            log_lines.append(f"  3. bw import bitwardenjson {output_path.name}")
            log_output.update("\n".join(log_lines))
            
            # Show success notification
            self.app.notify(
                f"✅ Successfully exported {exported_count} SSH key(s)!\n\n"
                f"Output: {output_path.absolute()}\n\n"
                f"Import to Bitwarden:\n"
                f"  bw login\n"
                f"  bw unlock\n"
                f"  bw import bitwardenjson {output_path.name}\n\n"
                f"After import, your SSH keys will be available\n"
                f"in Bitwarden and usable with Bitwarden SSH Agent!",
                title="Bitwarden Export Complete",
                severity="information",
                timeout=15
            )
            
        except FileNotFoundError as e:
            status_text.update(f"❌ Error: {str(e)}")
            log_output.update(f"❌ {str(e)}")
            self.app.notify(
                str(e),
                title="Export Failed",
                severity="error",
                timeout=10
            )
        except Exception as e:
            status_text.update(f"❌ Error: {str(e)}")
            log_output.update(f"❌ Unexpected error: {str(e)}")
            self.app.notify(
                f"Bitwarden export failed:\n\n{str(e)}",
                title="Export Error",
                severity="error"
            )
        finally:
            start_button.disabled = False
