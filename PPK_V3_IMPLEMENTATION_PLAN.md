# PPK v3 Support Implementation Plan - v1.0.4

## 1. Problem Statement

### Current Situation (v1.0.3)
- **Library**: `puttykeys` v1.0.3
- **Supported**: PPK v2 format only (PuTTY <0.75)
- **Not Supported**: PPK v3 format (PuTTY 0.75+, since February 2021)

### Impact
- **PuTTY 0.75+** (released Feb 2021) uses PPK v3 by default
- **~90% of users** likely have PPK v3 keys
- **Error message**: "Unsupported key type" (misleading - actually format issue)
- **Current workaround**: Manual conversion to PPK v2 in PuTTYgen

### PPK v3 vs v2 Differences

**PPK v2:**
```
PuTTY-User-Key-File-2: ssh-rsa
Encryption: aes256-cbc
[Standard AES encryption]
```

**PPK v3:**
```
PuTTY-User-Key-File-3: ssh-rsa
Encryption: aes256-cbc
Key-Derivation: Argon2id
Argon2-Memory: 8192
Argon2-Passes: 21
Argon2-Parallelism: 1
Argon2-Salt: [hex]
```

**Key Change**: Argon2id key derivation instead of simple password hashing

---

## 2. Current Test Files

Located in: `test/ppk_keys/`

| File | Version | Type | Encrypted | Password | Status v1.0.3 |
|------|---------|------|-----------|----------|---------------|
| unraid21.ppk | v2 | ssh-rsa | No | - | ✅ Works |
| test2.ppk | v2 | ssh-rsa | No | - | ✅ Works |
| test2-pass.ppk | v2 | ssh-rsa | Yes | test | ✅ Works |
| test.ppk | v3 | ssh-rsa | No | - | ❌ Fails |
| test-pass.ppk | v3 | ssh-rsa | Yes | test | ❌ Fails |

**Password file**: `test/test-file-password.txt` (contains: `test`)

---

## 3. Research: PPK v3 Support Options

### Option A: Upgrade puttykeys Library

**Check PyPI:**
```bash
pip index versions puttykeys
```

**Evaluation:**
- ✅ Easiest if v3 support exists
- ✅ Minimal code changes
- ❌ May not support v3 (need to verify)
- ❌ Library may be abandoned

**Action**: Research latest version and changelog

### Option B: Alternative Python Libraries

**Candidates:**
1. **paramiko** (SSH library)
   - May have PPK support
   - Heavier dependency
   - Check if supports PPK v3

2. **ppk3-parser** (if exists)
   - Specialized for PPK v3
   - Check PyPI

3. **cryptography** (already used)
   - Low-level crypto operations
   - Would need custom PPK parser

**Action**: Test each library with test files

### Option C: Custom PPK v3 Parser

**Implementation Requirements:**
1. **Parse PPK v3 format** (text-based)
2. **Argon2id key derivation**:
   ```python
   from argon2 import low_level
   
   key = low_level.hash_secret_raw(
       secret=password.encode(),
       salt=salt_bytes,
       time_cost=passes,
       memory_cost=memory,
       parallelism=parallelism,
       hash_len=32,  # AES-256
       type=low_level.Type.ID
   )
   ```

3. **AES-256-CBC decryption** (already in cryptography)
4. **OpenSSH format generation**

**Pros:**
- ✅ Full control
- ✅ No external library dependency
- ✅ Can optimize for our use case

**Cons:**
- ❌ Complex implementation
- ❌ More code to maintain
- ❌ Security-critical code (crypto)

**Dependencies:**
- `argon2-cffi` (for Argon2id)
- `cryptography` (already used)

**Action**: Prototype if Options A/B fail

### Option D: Subprocess puttygen.exe (NOT RECOMMENDED)

**Why not:**
- ❌ Requires PuTTY installed
- ❌ Not portable
- ❌ Windows-only
- ❌ Unreliable

---

## 4. Additional Features for v1.0.4

### 4.1 TUI Password Prompt

**Problem**: TUI shows "unsupported key type" instead of prompting for password

**Solution**:
```python
# tui/ui/screens/conversion.py or password_prompt.py

from textual.screen import Screen
from textual.widgets import Input, Button, Label

class PasswordPromptScreen(Screen):
    def compose(self):
        yield Label("Enter password for encrypted key:")
        yield Input(password=True, id="password_input")
        yield Button("OK", id="ok_button")
        yield Button("Skip", id="skip_button")
    
    def on_button_pressed(self, event):
        if event.button.id == "ok_button":
            password = self.query_one("#password_input").value
            self.dismiss(password)
        else:
            self.dismiss(None)
```

**Integration**:
- Detect encrypted PPK during conversion
- Show prompt per-key basis
- Allow retry on wrong password
- Allow skip to continue batch

### 4.2 Multi-Password File Support

**Use Case**: User has multiple keys with different passwords

**CLI Flag:**
```bash
putty-migrate convert --password-file passwords.txt
```

**File Format (passwords.txt):**
```
password1
password2
password3
```

**Logic:**
```python
def load_passwords(password_file: Path) -> List[str]:
    """Load passwords from file, one per line."""
    return [
        line.strip() 
        for line in password_file.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]

async def convert_with_password_list(
    ppk_file: Path,
    passwords: List[str]
) -> ConversionResult:
    """Try each password until one works."""
    
    for i, password in enumerate(passwords, 1):
        try:
            result = await convert_ppk_to_openssh(ppk_file, password)
            if result.success:
                result.password_used = i  # Track which password worked
                return result
        except EncryptionError:
            continue  # Try next password
    
    # All passwords failed
    return ConversionResult(
        success=False,
        error="None of the provided passwords worked"
    )
```

**Output:**
```
✅ test2-pass.ppk (password #1 worked)
✅ client-key.ppk (password #3 worked)
❌ oracle-key.ppk (no matching password)
```

### 4.3 Re-encryption Support

**Use Case**: Keys for ~/.ssh should remain encrypted

**CLI Flag:**
```bash
putty-migrate convert --password test --keep-encryption
```

**Behavior:**
1. Decrypt PPK with provided password
2. Convert to OpenSSH format
3. **Re-encrypt** OpenSSH key with same password
4. Use standard OpenSSH encryption (PEM + AES-256)

**Implementation:**
```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

async def convert_with_reencryption(
    ppk_file: Path,
    output_file: Path,
    password: str,
    keep_encryption: bool = False
) -> ConversionResult:
    
    # 1. Decrypt PPK
    openssh_key_text = puttykeys.ppkraw_to_openssh(ppk_content, password)
    
    # 2. Load as private key object
    private_key = serialization.load_ssh_private_key(
        openssh_key_text.encode(),
        password=None,  # Already decrypted
        backend=default_backend()
    )
    
    # 3. Determine encryption
    if keep_encryption and password:
        encryption_algo = serialization.BestAvailableEncryption(
            password.encode()
        )
    else:
        encryption_algo = serialization.NoEncryption()
    
    # 4. Serialize to OpenSSH format
    openssh_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=encryption_algo
    )
    
    # 5. Write to file
    output_file.write_bytes(openssh_bytes)
```

**Security Note**: Re-encrypted keys use OpenSSH's bcrypt-based encryption, which is more modern than PPK v2's AES-CBC but less secure than PPK v3's Argon2id.

### 4.4 Smart Password Error Handling

**Problem**: Unencrypted keys fail when `--password` is provided

**Current Behavior:**
```bash
putty-migrate convert --password test
# unraid21.ppk (unencrypted) → ERROR: "block length..."
```

**Desired Behavior:**
```bash
putty-migrate convert --password test
# unraid21.ppk (unencrypted) → SUCCESS (password ignored, info message)
```

**Implementation:**
```python
async def convert_with_smart_password(
    ppk_content: str,
    password: Optional[str]
) -> Tuple[str, bool]:
    """
    Try conversion with password, fallback to no password.
    Returns: (openssh_key, was_encrypted)
    """
    
    if password:
        try:
            # Try with password first
            openssh_key = puttykeys.ppkraw_to_openssh(ppk_content, password)
            return (openssh_key, True)
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # "block length" error = password on unencrypted key
            if "block length" in error_msg or "multiple" in error_msg:
                # Try without password
                try:
                    openssh_key = puttykeys.ppkraw_to_openssh(ppk_content, '')
                    return (openssh_key, False)  # Was NOT encrypted
                except:
                    raise e  # Re-raise original error
            else:
                raise  # Different error, propagate
    else:
        # No password provided
        openssh_key = puttykeys.ppkraw_to_openssh(ppk_content, '')
        return (openssh_key, False)
```

**Output Message:**
```
✅ test2-pass.ppk (converted with password)
✅ unraid21.ppk (key was not encrypted, password ignored)
```

---

## 5. Implementation Steps

### Phase 1: Research (Week 1)

- [ ] Check `puttykeys` latest version on PyPI
- [ ] Test `paramiko` PPK v3 support
- [ ] Search for `ppk3-parser` or similar
- [ ] Evaluate Argon2id libraries (`argon2-cffi`)
- [ ] **Decision**: Select best approach (A, B, or C)

### Phase 2: Core PPK v3 Support (Week 1-2)

**If Option A (puttykeys upgrade):**
- [ ] Update `requirements.txt`
- [ ] Test with all test files
- [ ] Update build.py if needed

**If Option B (alternative library):**
- [ ] Add new library to requirements.txt
- [ ] Create adapter in converter.py
- [ ] Test compatibility
- [ ] Update build.py

**If Option C (custom parser):**
- [ ] Add `argon2-cffi` to requirements.txt
- [ ] Create `ppk_v3_parser.py` module
- [ ] Implement Argon2id key derivation
- [ ] Implement PPK v3 format parser
- [ ] Implement AES-256-CBC decryption
- [ ] Test with test-pass.ppk
- [ ] Update build.py (include argon2 package)

### Phase 3: Enhanced Password Handling (Week 2)

**3.1 Multi-Password File Support:**
- [ ] Add `--password-file` argument to `cli/convert_ppk.py`
- [ ] Create `load_passwords()` function in `core/converter.py`
- [ ] Implement password iteration logic
- [ ] Track which password succeeded
- [ ] Update help text and examples

**3.2 Smart Password Fallback:**
- [ ] Create `convert_with_smart_password()` wrapper
- [ ] Detect "block length" errors
- [ ] Retry without password automatically
- [ ] Add info message to result
- [ ] Update batch converter

**3.3 Re-encryption Support:**
- [ ] Add `--keep-encryption` flag
- [ ] Implement re-encryption logic
- [ ] Test encryption strength
- [ ] Document security implications

### Phase 4: TUI Password Prompt (Week 2)

- [ ] Create `tui/ui/screens/password_prompt.py`
- [ ] Add password Input widget (masked)
- [ ] Add OK/Skip/Retry buttons
- [ ] Integrate into conversion screen
- [ ] Test with encrypted keys
- [ ] Handle wrong password gracefully

### Phase 5: Testing (Week 3)

**Unit Tests:**
- [ ] Test all 5 PPK files (v2 and v3)
- [ ] Test password file loading
- [ ] Test smart password fallback
- [ ] Test re-encryption
- [ ] Test TUI password prompt

**Integration Tests:**
```bash
# Test v2 (should still work)
putty-migrate convert
# Should convert: test2.ppk, unraid21.ppk

# Test v2 with password
putty-migrate convert --password test
# Should convert: test2-pass.ppk (and others with INFO)

# Test v3 (NEW)
putty-migrate convert
# Should convert: test.ppk (NEW!)

# Test v3 with password (NEW)
putty-migrate convert --password test
# Should convert: test-pass.ppk (NEW!)

# Test password file
putty-migrate convert --password-file test/test-file-password.txt
# Should try all passwords

# Test re-encryption
putty-migrate convert --password test --keep-encryption
# Should create encrypted OpenSSH keys
```

### Phase 6: Nuitka Build (Week 3)

**Dependencies Check:**
- [ ] If using argon2-cffi: Add to build.py
  ```python
  cmd.append('--include-package=argon2')
  cmd.append('--include-package-data=argon2')
  ```

- [ ] Test local Nuitka build
- [ ] Verify binary size (may increase with argon2)
- [ ] Test binary on clean Windows VM
- [ ] Test binary on Linux

**Expected Binary Sizes:**
- Windows: 68-75 MB (may increase ~5-10 MB if argon2)
- Linux: 28-35 MB (may increase ~3-5 MB)

### Phase 7: Documentation (Week 3)

**Update Files:**
- [ ] `docs/troubleshooting.md` - Remove v3 limitation, add new features
- [ ] `README.md` - Remove Known Limitations section
- [ ] `CHANGELOG.md` - Add v1.0.4 release notes
- [ ] `docs/guides/convert-ppk.md` - Add new flag examples
- [ ] `docs/guides/binary/cli.md` - Document --password-file, --keep-encryption
- [ ] `docs/guides/python/cli.md` - Same as above

**New Sections:**
- Password file format example
- Re-encryption security notes
- TUI password prompt usage

### Phase 8: Release (Week 4)

- [ ] Update version in code
- [ ] Final testing (all platforms)
- [ ] Create release notes
- [ ] Tag v1.0.4
- [ ] Push tag (triggers GitHub Actions)
- [ ] Monitor build (~25-30 min)
- [ ] Download and test release binaries
- [ ] Publish release

---

## 6. Nuitka Compatibility Checklist

### Current Dependencies (v1.0.3)
```
textual>=0.47.0
rich>=13.7.0
puttykeys>=1.0.3
cryptography>=41.0.0
```

### Potential New Dependencies

**If Option C (custom parser):**
```
argon2-cffi>=23.1.0  # For Argon2id key derivation
```

### Build.py Updates

**If adding argon2:**
```python
# In build.py, add to package includes:
cmd.extend([
    '--include-package=argon2',
    '--include-package=_argon2_cffi_bindings',  # C bindings
    '--follow-import-to=argon2',
])

# Might need data files:
cmd.append('--include-package-data=argon2')
```

### Testing Strategy

1. **Build locally first:**
   ```bash
   python build.py --version 1.0.4-test
   ```

2. **Test binary:**
   ```bash
   # Test all PPK files
   dist/putty-migrate-v1.0.4-test-windows.exe convert -i test/ppk_keys
   
   # Should convert all 5 files successfully
   ```

3. **Check dependencies:**
   ```bash
   # Binary should NOT require external DLLs
   # Everything must be embedded
   ```

4. **GitHub Actions build:**
   - Monitor build logs for errors
   - Check artifact sizes
   - Download and test both platforms

---

## 7. Security Considerations

### Argon2id Parameters (PPK v3)

**PuTTY defaults:**
- Memory: 8192 KB (8 MB)
- Passes: 21
- Parallelism: 1

**Security level**: 
Resistant to GPU attacks, as intended by PPK v3 design.

### Re-encryption (OpenSSH)

**OpenSSH encryption uses:**
- bcrypt KDF (100 rounds by default)
- AES-256-CBC or AES-256-CTR

**Security comparison:**
- PPK v3 (Argon2id): ★★★★★ (strongest)
- OpenSSH (bcrypt): ★★★★☆ (strong)
- PPK v2 (simpleAES): ★★☆☆☆ (weak)

**Recommendation**: Document that re-encrypted keys are secure but slightly less resistant to brute-force than PPK v3.

### Password File Security

**Risk**: passwords.txt in plaintext

**Mitigation:**
- Document to delete after use
- Warn about file permissions
- Consider adding `--password-file-delete-after` flag

---

## 8. Error Messages Improvement

### Current (Misleading)
```
❌ test-pass.ppk: Unsupported key type. Only RSA and Ed25519 keys are supported.
```

### Improved
```python
def detect_ppk_version(ppk_content: str) -> int:
    """Detect PPK format version."""
    if ppk_content.startswith('PuTTY-User-Key-File-3'):
        return 3
    elif ppk_content.startswith('PuTTY-User-Key-File-2'):
        return 2
    return 0

def interpret_conversion_error(error: Exception, ppk_content: str) -> str:
    """Convert error to user-friendly message."""
    
    # Check PPK version first
    version = detect_ppk_version(ppk_content)
    if version == 3 and "unsupported" in str(error).lower():
        return "PPK v3 format detected but not supported in this version. Please upgrade to v1.0.4+ or convert to PPK v2 in PuTTYgen."
    
    # ... existing error handling
```

### New Messages (v1.0.4+)
```
✅ test-pass.ppk (PPK v3, decrypted with password)
✅ test.ppk (PPK v3, unencrypted)
✅ test2-pass.ppk (PPK v2, decrypted with password #1)
✅ unraid21.ppk (PPK v2, key was not encrypted - password ignored)
❌ client.ppk (wrong password or corrupted key)
```

---

## 9. Migration Path (v1.0.3 → v1.0.4)

### Breaking Changes
**None!** v1.0.4 is fully backward compatible.

### New Features (Optional)
- PPK v3 support (automatic)
- `--password-file` flag (opt-in)
- `--keep-encryption` flag (opt-in)
- TUI password prompt (automatic for encrypted keys)
- Smart password handling (automatic)

### User Action Required
**None.** Just upgrade and existing workflows continue working, plus PPK v3 now works.

---

## 10. Known Issues / Limitations

### After v1.0.4

**Still not supported:**
- DSA keys (deprecated, insecure)
- ECDSA keys except Ed25519 (puttykeys limitation)
- PPK v1 (ancient, unlikely to encounter)

**Platform-specific:**
- `--to-ssh` flag: Linux only
- TUI: Works on all platforms
- Re-encryption: All platforms

---

## 11. Session Prompt for Implementation

**For next session (at token limit ~160k):**

```
# PuTTY Migration Tools v1.0.4 - PPK v3 & Advanced Password Features

## Current State
- v1.0.3: Released successfully with Nuitka
- PPK v2 support works perfectly
- PPK v3 not supported (critical issue)
- Documentation updated with limitations

## Implementation Task
Read: PPK_V3_IMPLEMENTATION_PLAN.md (this file)

## Quick Start
1. Research Phase:
   - Check `pip index versions puttykeys`
   - Test if newer version supports PPK v3
   - If not: Evaluate option B or C

2. Test Files Ready:
   - test/ppk_keys/*.ppk (5 files, mix of v2/v3)
   - test/test-file-password.txt (password: test)

3. Features to Implement:
   - PPK v3 decryption (Argon2id)
   - --password-file support
   - --keep-encryption flag
   - TUI password prompt
   - Smart password fallback

4. Build Requirements:
   - Must work with Nuitka compiler
   - Test all new dependencies before final build
   - Watch binary size (acceptable up to ~80MB Win, ~35MB Linux)

5. Testing:
   - All 5 test/*.ppk files must convert successfully
   - Test password file with multiple passwords
   - Test re-encryption
   - Test TUI prompt

6. Files to Modify:
   - tui/core/converter.py (main logic)
   - tui/cli/convert_ppk.py (new flags)
   - tui/ui/screens/ (password prompt)
   - tui/requirements.txt (new deps if needed)
   - build.py (package includes)
   - docs/*.md (update all guides)

## Success Criteria
```bash
putty-migrate convert -i test/ppk_keys
# Should convert ALL 5 files successfully (including v3!)
```

Start with research phase, then implement chosen solution!
```

---

## 12. Timeline Estimate

| Phase | Duration | Tasks |
|-------|----------|-------|
| Research | 1-2 days | Evaluate options A/B/C |
| PPK v3 Core | 2-3 days | Implement chosen solution |
| Password Features | 2-3 days | Multi-pass, re-encrypt, smart fallback |
| TUI Prompt | 1-2 days | Password input screen |
| Testing | 2-3 days | All features, all platforms |
| Nuitka Build | 1 day | Build & test binaries |
| Documentation | 1-2 days | Update all docs |
| Release | 1 day | Tag, build, publish |
| **Total** | **2-3 weeks** | Full implementation |

---

## 13. Success Metrics

### Must Pass
- ✅ All 5 test PPK files convert successfully
- ✅ Nuitka build succeeds (both platforms)
- ✅ Binary size acceptable (<80MB Windows, <40MB Linux)
- ✅ No external DLL dependencies
- ✅ All test cases pass

### Nice to Have
- 🎯 Binary size stays close to v1.0.3 (~70MB Win, ~30MB Linux)
- 🎯 Build time under 30 minutes
- 🎯 Zero breaking changes
- 🎯 Comprehensive error messages

---

**Plan Version**: 1.0  
**Created**: 2026-03-29  
**For Release**: v1.0.4 (estimated mid-April 2026)
