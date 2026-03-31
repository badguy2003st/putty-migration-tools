"""
Conversion Screen - PPK to OpenSSH/Bitwarden conversion UI.

Provides an interactive interface for converting .ppk keys to various formats.

v1.1.0: Adds interactive password support for encrypted PPK files.
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
    RichLog,
)
from textual.containers import Container, Vertical, Horizontal


class CancelledByUser(Exception):
    """Raised when user cancels to edit passwords.txt."""
    pass


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
            
            # Encryption options (only visible for OpenSSH/SSH Config)
            yield Static("🔒 Encryption (for encrypted PPKs):", classes="subtitle", id="encryption-label")
            with RadioSet(id="encryption-mode"):
                yield RadioButton("🔒 Keep password encryption (recommended)", value=True)
                yield RadioButton("🔓 Remove password (unencrypted keys)")
            
            # Progress section
            yield Static("Progress:", classes="subtitle")
            yield ProgressBar(id="progress", total=100, show_eta=False)
            yield Static("Ready to convert...", id="status-text", classes="status")
            
            # Log output (scrollable with RichLog)
            yield Static("Conversion Log:", classes="subtitle")
            yield RichLog(id="log-output", highlight=True, markup=False, max_lines=500)
            
            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("▶ Start Conversion", id="start", variant="success")
                yield Button("💾 Export Log", id="export-log", variant="primary", disabled=True)
                yield Button("« Back to Menu", id="back")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        # Scan for PPK files and populate the list
        self._populate_file_list()
        
        # Set initial visibility of encryption options (visible by default for OpenSSH)
        self._update_encryption_visibility(0)  # OpenSSH is index 0
        
        # Focus the start button
        try:
            start_button = self.query_one("#start", Button)
            start_button.focus()
        except Exception:
            pass
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle format selection changes to show/hide encryption options."""
        if event.radio_set.id == "format-selection":
            selected_index = event.radio_set.pressed_index
            self._update_encryption_visibility(selected_index)
    
    def _update_encryption_visibility(self, format_index: int) -> None:
        """Update visibility of encryption options based on selected format.
        
        Args:
            format_index: Selected format (0=OpenSSH, 1=Bitwarden, 2=SSH Config)
        """
        try:
            encryption_label = self.query_one("#encryption-label", Static)
            encryption_radioset = self.query_one("#encryption-mode", RadioSet)
            
            # Show encryption options for OpenSSH (0) and SSH Config (2)
            # Hide for Bitwarden (1) - Bitwarden requires unencrypted keys
            if format_index in [0, 2]:  # OpenSSH or SSH Config
                encryption_label.display = True
                encryption_radioset.display = True
            else:  # Bitwarden
                encryption_label.display = False
                encryption_radioset.display = False
        except Exception:
            # Widget not found yet (initial setup)
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
        elif button_id == "export-log":
            await self._export_log()
        elif button_id == "back":
            self.app.pop_screen()
    
    async def _convert_with_password_retry(
        self,
        ppk_file: Path,
        output_dir: Path,
        passwords: List[str],
        current: int,
        total: int,
        keep_encryption: bool = True
    ):
        """
        Convert PPK file with interactive password retry dialog.
        
        v1.1.0: Implements interactive password retry with 3 options.
        BUG FIX: Pre-validates PPK encryption status to avoid false dialog triggers.
        
        Args:
            ppk_file: PPK file to convert
            output_dir: Output directory
            passwords: Passwords from passwords.txt
            current: Current file number (1-indexed)
            total: Total files being processed
            keep_encryption: Whether to keep password encryption (from UI RadioSet)
            
        Returns:
            ConversionResult
            
        Raises:
            CancelledByUser: If user cancels to edit passwords.txt
        """
        from ...core.converter import convert_ppk_to_openssh, ConversionResult, normalize_key_name
        from ...core.ppk_parser import detect_ppk_info
        from .password_dialog import PasswordDialog
        
        # v1.1.0 BUG FIX: Pre-validate PPK format and encryption status
        try:
            ppk_content = ppk_file.read_text(encoding='utf-8')
            ppk_info = detect_ppk_info(ppk_content)
        except Exception as e:
            # Invalid PPK format - return error immediately
            return ConversionResult(
                success=False,
                error=f"Invalid PPK format: {str(e)}",
                ppk_file=str(ppk_file)
            )
        
        # Try conversion with passwords from file
        # v1.1.0: keep_encryption based on user's UI choice
        normalized_name = normalize_key_name(ppk_file.stem)
        result = await convert_ppk_to_openssh(
            ppk_file,
            output_dir / normalized_name,
            passwords=passwords,
            keep_encryption=keep_encryption  # From UI RadioSet
        )
        
        if result.success:
            return result
        
        # v1.1.0 BUG FIX: Only show dialog if key is ACTUALLY encrypted
        # This prevents false positive triggers on unencrypted keys with other errors
        if not ppk_info.is_encrypted:
            # Unencrypted key with error → return error directly (no dialog)
            return result
        
        # Key is encrypted and passwords didn't work → show password dialog
        while True:
            dialog_result = await self.app.push_screen_wait(
                PasswordDialog(
                    ppk_file.name,
                    len(passwords),
                    current,
                    total
                )
            )
            
            if dialog_result.action == "skip":
                result.error = "Skipped by user (password required)"
                return result
            
            elif dialog_result.action == "cancel":
                raise CancelledByUser("User cancelled to edit passwords.txt")
            
            elif dialog_result.action == "try":
                # Retry with entered password
                # v1.1.0: Create DecryptionResult with password_used for re-encryption
                from ...core.ppk_parser import decrypt_ppk
                
                # Read PPK content for manual decryption
                ppk_content = ppk_file.read_text(encoding='utf-8')
                decrypt_result = decrypt_ppk(ppk_content, password=dialog_result.password)
                
                if decrypt_result.success:
                    # Manually convert with password stored
                    # v1.1.0: keep_encryption=True will re-encrypt with entered password
                    normalized_name = normalize_key_name(ppk_file.stem)
                    retry_result = await convert_ppk_to_openssh(
                        ppk_file,
                        output_dir / normalized_name,
                        password=dialog_result.password,
                        keep_encryption=True  # Re-encrypt with manual password!
                    )
                    return retry_result
                
                # Still failed - notify and loop (dialog shows again)
                self.app.notify(
                    f"Wrong password for {ppk_file.name}\n"
                    f"Try again, skip, or cancel",
                    severity="error",
                    timeout=3
                )
                continue
    
    async def _start_conversion(self) -> None:
        """Start the conversion process - launches worker for async operations."""
        from ...core.converter import check_puttykeys_available
        
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
        
        # Launch worker for conversion (required for push_screen_wait to work)
        self.run_worker(self._conversion_worker(selected_format), exclusive=True)
    
    async def _conversion_worker(self, selected_format: str) -> None:
        """Worker method for conversion - allows push_screen_wait() to work properly."""
        from ...core.converter import (
            get_conversion_summary,
            copy_key_to_ssh
        )
        from ...core.file_operations import ensure_ppk_directory, load_password_file
        from ...utils.platform import is_linux
        
        # Get encryption choice from UI RadioSet
        encryption_radioset = self.query_one("#encryption-mode", RadioSet)
        keep_encryption = (encryption_radioset.pressed_index == 0)  # True if "Keep password" is selected
        
        # v1.1.0: Ensure ppk directory exists (creates passwords.txt too)
        ppk_dir = Path("./ppk_keys")
        check = ensure_ppk_directory(ppk_dir)
        
        # Update UI elements
        progress_bar = self.query_one("#progress", ProgressBar)
        status_text = self.query_one("#status-text", Static)
        log_output = self.query_one("#log-output", RichLog)
        start_button = self.query_one("#start", Button)
        export_button = self.query_one("#export-log", Button)
        
        if check['created']:
            # Show first-time setup notification
            self.app.notify(
                check['tui_message'],
                title=check['tui_title'],
                severity="information",
                timeout=15
            )
            return  # Stop here, let user add files
        
        # v1.1.0: Load passwords from file
        passwords_from_file = load_password_file(check['passwords_file'])
        
        if passwords_from_file:
            status_text.update(
                f"Loaded {len(passwords_from_file)} password(s) from passwords.txt"
            )
        
        # Get PPK files
        ppk_files = self._scan_ppk_files()
        
        if not ppk_files:
            self.app.notify(
                "No PPK files found!\nPlace .ppk files in the ppk_keys directory.",
                title="No Files",
                severity="warning"
            )
            return
        
        # Disable start button during conversion
        start_button.disabled = True
        
        # Show initial status
        status_text.update(f"Converting {len(ppk_files)} file(s) to {selected_format}...")
        log_output.clear()
        
        try:
            # ALWAYS convert to ./openssh_keys staging directory FIRST
            # Then copy to ~/.ssh if user requests it (via ssh_import_choice)
            # This ensures conflict handling (rename/skip/overwrite) works correctly
            output_dir = Path("./openssh_keys")
            
            # ~/.ssh import dialog - show when user selects "SSH Config" format
            ssh_import_choice = None
            
            if selected_format == "SSH Config":
                from .ssh_import_dialog import SSHImportDialog
                
                ssh_import_choice = await self.app.push_screen_wait(
                    SSHImportDialog([Path(f) for f in ppk_files])
                )
                
                if ssh_import_choice.cancelled:
                    return  # User cancelled the dialog
            
            # Create output directory
            output_dir.mkdir(exist_ok=True)
            
            total = len(ppk_files)
            log_lines = []
            
            # Progress callback for conversion
            def progress_callback(current: int, total_files: int, filename: str):
                progress_bar.update(progress=(current / total_files) * 100)
                status_text.update(f"Processing {current}/{total_files}: {filename}...")
            
            # v1.1.0: Convert with password retry support
            # NOTE: Public keys are now extracted INSIDE convert_ppk_to_openssh()
            # before re-encryption, fixing the encrypted Ed25519 bug!
            results = []
            
            for i, ppk_file in enumerate(ppk_files, 1):
                try:
                    result = await self._convert_with_password_retry(
                        Path(ppk_file),
                        output_dir,
                        passwords_from_file,
                        i,
                        len(ppk_files),
                        keep_encryption=keep_encryption  # Pass user's encryption choice!
                    )
                    results.append(result)
                    
                    # Update progress
                    progress_callback(i, len(ppk_files), Path(ppk_file).name)
                    
                except CancelledByUser:
                    # User cancelled to edit passwords.txt
                    status_text.update("Cancelled by user")
                    self.app.notify(
                        f"Conversion cancelled.\n\n"
                        f"Edit {check['passwords_file']} to add passwords,\n"
                        f"then try again.",
                        title="Cancelled",
                        severity="information",
                        timeout=10
                    )
                    break  # Stop processing remaining files
            
            # Copy to ~/.ssh if requested
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
                        # BUG FIX: Use string concat instead of with_suffix() to handle dots in filename
                        pub_file = Path(str(result.output_file) + '.pub')
                        
                        if pub_file.exists():
                            public_copy = await copy_key_to_ssh(
                                pub_file,
                                ssh_import_choice.conflict_mode
                            )
                            copy_results.append(public_copy)
            
            # Build log output with improved error handling (v1.1.0)
            if copy_results:
                # Show ~/.ssh copy results
                log_lines.append("Keys created in ~/.ssh:")
                log_lines.append("━" * 60)
                
                # Group by key name (private + public)
                key_groups = {}
                for copy_result in copy_results:
                    dest_path = Path(copy_result['destination'])
                    
                    # BUG FIX: Handle .pub extension correctly for grouping
                    # "bggaming.de dagobert23.de.pub" → name="bggaming.de dagobert23.de.pub", stem="bggaming.de dagobert23.de"
                    if dest_path.name.endswith('.pub'):
                        # This is a public key - base name is everything except .pub
                        key_name = dest_path.name[:-4]  # Remove ".pub" suffix
                    else:
                        # This is a private key - use full name
                        key_name = dest_path.name
                    
                    if key_name not in key_groups:
                        key_groups[key_name] = {'private': None, 'public': None}
                    
                    if dest_path.name.endswith('.pub'):
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
                # Original log output with IMPROVED error handling (v1.1.0)
                for result in results:
                    file_name = os.path.basename(result.ppk_file)
                    if result.success:
                        log_lines.append(f"✅ {file_name} → {output_dir}")
                    else:
                        # v1.1.0: Smart error formatting based on error type
                        error = result.error if result.error else "Unknown error"
                        error_lower = error.lower()
                        
                        # Detect error types and format accordingly (order matters!)
                        # Check structural errors FIRST (Ed448, DSA, public keys, etc.)
                        
                        if "ed448" in error_lower and "not yet supported" in error_lower:
                            log_lines.append(f"⚠️  {file_name}: Ed448 not supported (library limitation)")
                            log_lines.append(f"   → Use Ed25519 instead (same 128-bit security)")
                        
                        elif "dsa" in error_lower and ("deprecated" in error_lower or "not supported" in error_lower):
                            log_lines.append(f"❌ {file_name}: DSA deprecated (insecure)")
                            log_lines.append(f"   → Generate new RSA or Ed25519 key")
                        
                        elif ("ssh2 public key" in error_lower or "public keys don't need" in error_lower):
                            log_lines.append(f"⏭  {file_name}: Public key (skip)")
                            log_lines.append(f"   → Remove .pub files from ppk_keys/")
                        
                        elif "already in openssh format" in error_lower:
                            log_lines.append(f"⏭  {file_name}: Already converted")
                        
                        elif "none of the" in error_lower and "passwords" in error_lower:
                            log_lines.append(f"🔒 {file_name}: Wrong password")
                            log_lines.append(f"   → Check/update passwords.txt")
                        
                        elif "password required" in error_lower or "encrypted" in error_lower and "password" in error_lower:
                            log_lines.append(f"🔒 {file_name}: Password required")
                            log_lines.append(f"   → Add password to passwords.txt")
                        
                        else:
                            # Generic error - show full message (multi-line if long)
                            if len(error) > 60:
                                log_lines.append(f"❌ {file_name}:")
                                # Split long errors into multiple lines
                                words = error.split()
                                line = "   "
                                for word in words:
                                    if len(line) + len(word) + 1 > 70:
                                        log_lines.append(line)
                                        line = "   " + word
                                    else:
                                        line += (" " if line != "   " else "") + word
                                if line.strip():
                                    log_lines.append(line)
                            else:
                                log_lines.append(f"❌ {file_name}: {error}")
            
            # Write to RichLog (one line at a time for proper scrolling)
            log_output.clear()
            for line in log_lines:
                log_output.write(line)
            
            # Enable export button now that we have log content
            export_button.disabled = False
            
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
            log_output.clear()
            log_output.write(f"❌ Unexpected error: {str(e)}")
            self.app.notify(
                f"Conversion failed with error:\n{str(e)}",
                title="Error",
                severity="error"
            )
        finally:
            # Re-enable start button
            start_button.disabled = False
    
    async def _export_log(self) -> None:
        """Export conversion log to a text file."""
        from datetime import datetime
        
        try:
            # Get log content from RichLog widget
            log_output = self.query_one("#log-output", RichLog)
            
            # RichLog stores lines internally - extract them
            log_lines = []
            for line in log_output.lines:
                # Convert Rich Text to plain string
                log_lines.append(line.text if hasattr(line, 'text') else str(line))
            
            if not log_lines:
                self.app.notify(
                    "No log content to export.\n"
                    "Run a conversion first.",
                    title="Empty Log",
                    severity="warning",
                    timeout=5
                )
                return
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = Path(f"conversion_log_{timestamp}.txt")
            
            # Add header to export
            export_content = [
                "=" * 70,
                "PPK Migration Tools - Conversion Log",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 70,
                "",
                *log_lines
            ]
            
            # Write to file
            log_file.write_text("\n".join(export_content), encoding='utf-8')
            
            # Show success notification
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
    
    async def _bitwarden_export(self) -> None:
        """Execute Bitwarden SSH Key export."""
        from ...core.registry import read_putty_sessions
        from ...core.bitwarden_export import generate_bitwarden_export, validate_bitwarden_export
        from ...core.auth_detection import detect_auth_method
        
        # Update UI
        progress_bar = self.query_one("#progress", ProgressBar)
        status_text = self.query_one("#status-text", Static)
        log_output = self.query_one("#log-output", RichLog)
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
                log_output.clear()
                log_output.write("⚠️  No sessions configured with SSH key authentication")
                return
            
            status_text.update(f"Found {len(sessions_with_keys)} session(s) with SSH keys...")
            progress_bar.update(progress=20)
            
            # 3. Auto-convert ALL PPK files to OpenSSH format (v1.1.0: with password support!)
            ppk_keys_dir = Path("./ppk_keys")
            openssh_keys_dir = Path("./openssh_keys")
            openssh_keys_dir.mkdir(exist_ok=True)
            
            # v1.1.0: Load passwords from passwords.txt
            from ...core.file_operations import load_password_file, ensure_ppk_directory
            check = ensure_ppk_directory(ppk_keys_dir)
            passwords_from_file = load_password_file(check['passwords_file'])
            
            if ppk_keys_dir.exists():
                ppk_files = list(ppk_keys_dir.glob("*.ppk"))
                
                if ppk_files:
                    status_text.update(f"Converting {len(ppk_files)} PPK file(s) to OpenSSH format...")
                    progress_bar.update(progress=30)
                    
                    # Progress callback for conversion (30% → 50%)
                    def conversion_progress(current: int, total: int, filename: str):
                        percent = 30 + (current / total * 20)  # 30% to 50%
                        progress_bar.update(progress=percent)
                        status_text.update(f"Converting {current}/{total}: {filename}...")
                    
                    # v1.1.0: Convert with password retry support (like OpenSSH conversion)
                    # NOTE: Bitwarden requires UNENCRYPTED keys (keep_encryption=False)!
                    results = []
                    for i, ppk_file in enumerate(ppk_files, 1):
                        try:
                            result = await self._convert_with_password_retry(
                                ppk_file,
                                openssh_keys_dir,
                                passwords_from_file,
                                i,
                                len(ppk_files),
                                keep_encryption=False  # Bitwarden requires unencrypted keys!
                            )
                            results.append(result)
                            conversion_progress(i, len(ppk_files), ppk_file.name)
                        except CancelledByUser:
                            # User cancelled - stop conversion
                            self.app.notify(
                                "Conversion cancelled by user.\n\n"
                                f"Edit {check['passwords_file']} to add passwords.",
                                title="Cancelled",
                                severity="information",
                                timeout=8
                            )
                            return  # Exit bitwarden export
                    
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
                    
                    log_output.clear()
                    for line in conversion_log_lines:
                        log_output.write(line)
                    
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
            exported_items = export_data.get("items", [])
            
            # Update status
            status_text.update(f"✅ Exported {exported_count} SSH key(s) to Bitwarden format!")
            status_text.set_classes("success")
            
            # Build detailed log output
            log_lines = []
            
            # Show PPK conversion summary if it happened
            if ppk_files:
                from ...core.converter import get_conversion_summary
                from ...core.converter import batch_convert_ppk_files
                # Get conversion results from earlier (stored in results variable)
                if 'results' in locals():
                    summary = get_conversion_summary(results)
                    log_lines.append(f"PPK Conversion: {summary['successful']}/{summary['total']} successful")
                    log_lines.append("─" * 60)
                    
                    for result in results:
                        file_name = Path(result.ppk_file).name
                        if result.success:
                            log_lines.append(f"✅ {file_name}")
                        else:
                            error = result.error[:50] if result.error else "Unknown error"
                            log_lines.append(f"❌ {file_name}: {error}")
                    
                    log_lines.append("")
                    log_lines.append("─" * 60)
                    log_lines.append("")
            
            # Bitwarden export details
            log_lines.append(f"Bitwarden Export: {exported_count} session(s)")
            log_lines.append("─" * 60)
            
            # List each exported item with details
            for item in exported_items:
                name = item.get("name", "Unknown")
                notes = item.get("notes", "")
                
                # Extract key type from notes (format: "SSH Key: RSA 2048")
                key_type = "Unknown"
                if "SSH Key:" in notes:
                    key_info = notes.split("SSH Key:")[1].split("\n")[0].strip()
                    key_type = key_info
                
                # Extract username from login
                username = ""
                if item.get("login"):
                    username = item["login"].get("username", "")
                
                user_info = f" ({username})" if username else ""
                log_lines.append(f"✅ {name}{user_info} - {key_type}")
            
            log_lines.append("")
            log_lines.append("─" * 60)
            log_lines.append(f"✅ Export file: {output_path.name}")
            log_lines.append("")
            log_lines.append("Import to Bitwarden:")
            log_lines.append("  1. bw login")
            log_lines.append("  2. bw unlock")
            log_lines.append(f"  3. bw import bitwardenjson {output_path.name}")
            
            # Write to log
            log_output.clear()
            for line in log_lines:
                log_output.write(line)
            
            # Enable export button so log can be exported
            export_button = self.query_one("#export-log", Button)
            export_button.disabled = False
            
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
            log_output.clear()
            log_output.write(f"❌ {str(e)}")
            self.app.notify(
                str(e),
                title="Export Failed",
                severity="error",
                timeout=10
            )
        except Exception as e:
            status_text.update(f"❌ Error: {str(e)}")
            log_output.clear()
            log_output.write(f"❌ Unexpected error: {str(e)}")
            self.app.notify(
                f"Bitwarden export failed:\n\n{str(e)}",
                title="Export Error",
                severity="error"
            )
        finally:
            start_button.disabled = False
