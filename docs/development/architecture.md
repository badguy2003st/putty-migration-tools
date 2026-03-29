# Code Architecture

Technical overview of the project structure and design.

---

## 📁 Project Structure

```
putty-migration-tools/
├── build.py                 # PyInstaller build script
├── ppk_keys/                # User's PPK files (input)
├── openssh_keys/            # Converted keys (output)
│
├── tui/                     # Main application package
│   ├── __init__.py
│   ├── __main__.py          # CLI/TUI entry point
│   ├── main.py              # Legacy entry
│   ├── requirements.txt     # Runtime dependencies
│   ├── requirements-dev.txt # Development dependencies
│   │
│   ├── cli/                 # CLI command implementations
│   │   ├── __init__.py
│   │   ├── convert_ppk.py   # PPK conversion command
│   │   ├── export_bitwarden.py  # Bitwarden export
│   │   ├── export_tabby.py      # Tabby export
│   │   └── export_ssh_config.py # SSH config generation
│   │
│   ├── core/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── converter.py         # PPK → OpenSSH conversion
│   │   ├── registry.py          # Windows Registry reading
│   │   ├── bitwarden_export.py  # Bitwarden JSON generation
│   │   ├── tabby_export.py      # Tabby JSON generation
│   │   ├── ssh_config.py        # SSH config generation
│   │   ├── auth_detection.py    # Auth method detection
│   │   ├── file_operations.py   # File I/O operations
│   │   ├── fuzzy_match.py       # Key fuzzy matching
│   │   └── key_registry.py      # Key deduplication
│   │
│   ├── ui/                  # TUI (Textual framework)
│   │   ├── __init__.py
│   │   ├── app.py           # Main Textual app
│   │   ├── styles.tcss      # TUI styling
│   │   └── screens/         # TUI screens
│   │       ├── __init__.py
│   │       ├── main_menu.py        # Main menu
│   │       ├── conversion.py       # PPK conversion screen
│   │       ├── export.py           # Export screen
│   │       ├── install.py          # Settings/install screen
│   │       └── ssh_import_dialog.py # Linux conflict dialog
│   │
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── platform.py      # Platform detection
│       ├── security.py      # File permissions, security
│       └── bitwarden.py     # Bitwarden CLI helpers
│
├── docs/                    # Documentation (this!)
└── dist/                    # Build output (binaries)
```

---

## 🏗️ Layer Architecture

### 1. Entry Layer (`__main__.py`)

**Responsibility:** Routes to CLI or TUI.

```python
def main() -> int:
    # No arguments → TUI
    if len(sys.argv) == 1:
        return launch_tui()
    
    # With arguments → CLI
    return route_to_cli_command()
```

### 2. CLI Layer (`cli/`)

**Responsibility:** Argument parsing, user interaction, calling core logic.

```python
# cli/convert_ppk.py
def create_parser():
    """Create argparse parser."""
    
async def run_convert(args):
    """Execute conversion with core logic."""
    ppk_files = find_ppk_files(args.input)
    results = await batch_convert_ppk_files(ppk_files)
```

### 3. Core Layer (`core/`)

**Responsibility:** Business logic, no UI dependencies.

```python
# core/converter.py
async def batch_convert_ppk_files(
    ppk_files: List[Path],
    output_dir: Path
) -> List[ConversionResult]:
    """Pure conversion logic, no CLI/TUI knowledge."""
```

### 4. UI Layer (`ui/`)

**Responsibility:** Textual-based TUI, calls core logic.

```python
# ui/screens/conversion.py
class ConversionScreen(Screen):
    async def _start_conversion(self):
        # Call core logic
        results = await batch_convert_ppk_files(...)
```

### 5. Utils Layer (`utils/`)

**Responsibility:** Cross-cutting concerns.

---

## 🔄 Data Flow

### PPK Conversion Flow

```
User Input (CLI/TUI)
    ↓
CLI Parser / TUI Screen
    ↓
core/converter.py
    ├→ core/file_operations.py (read PPK)
    ├→ puttykeys library (parse PPK)
    ├→ cryptography library (generate OpenSSH)
    └→ utils/security.py (set permissions)
    ↓
Output: OpenSSH keys
```

### Bitwarden Export Flow

```
User Input
    ↓
CLI/TUI
    ↓
core/bitwarden_export.py
    ├→ core/registry.py (read sessions)
    ├→ core/auth_detection.py (detect key auth)
    ├→ core/converter.py (convert PPKs if needed)
    └→ core/key_registry.py (deduplicate keys)
    ↓
Output: bitwarden-export.json
```

---

## 🎯 Design Patterns

### 1. Separation of Concerns

- **CLI/TUI**: User interface only
- **Core**: Business logic only
- **Utils**: Reusable utilities

### 2. Dependency Injection

```python
def batch_convert_ppk_files(
    ppk_files: List[Path],
    output_dir: Path,
    progress_callback: Optional[Callable] = None
):
    """Progress callback injected, not hardcoded."""
```

### 3. Result Objects

```python
@dataclass
class ConversionResult:
    """Standardized result object."""
    success: bool
    ppk_file: str
    output_file: Optional[Path]
    error: Optional[str]
```

### 4. Async/Await

```python
async def batch_convert_ppk_files(...):
    """Async for non-blocking operations."""
    for ppk_file in ppk_files:
        result = await convert_single(ppk_file)
```

---

## 🔑 Key Modules

### `core/converter.py`

**Purpose:** PPK to OpenSSH conversion.

**Key Functions:**
- `batch_convert_ppk_files()` - Batch conversion
- `convert_ppk_file()` - Single file
- `copy_key_to_ssh()` - Linux ~/.ssh copy

### `core/registry.py`

**Purpose:** Windows Registry reading.

**Key Functions:**
- `read_putty_sessions()` - Read all sessions
- `PuttySession` dataclass - Session representation

### `core/bitwarden_export.py`

**Purpose:** Generate Bitwarden JSON.

**Key Functions:**
- `generate_bitwarden_export()` - Create JSON
- `validate_bitwarden_export()` - Validate format

### `core/key_registry.py`

**Purpose:** Key deduplication and matching.

**Key Features:**
- Fuzzy matching for Pageant keys
- PPK → OpenSSH mapping
- Unique key registry

---

## 🚀 Extension Points

### Adding a New Export Format

1. Create `core/new_export.py`:
   ```python
   def generate_new_export(sessions, keys):
       # Generate export
   ```

2. Create `cli/export_new.py`:
   ```python
   def create_parser():
       # CLI args
   
   def run_export(args):
       # Call core logic
   ```

3. Add to `__main__.py`:
   ```python
   elif args.command == 'new':
       from .cli.export_new import main
       return main()
   ```

4. Add TUI screen (optional)

### Adding a New CLI Flag

Modify respective `cli/*.py` file:
```python
parser.add_argument(
    '--my-flag',
    action='store_true',
    help='My new flag'
)
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test core logic independently
- Mock file I/O
- Test edge cases

### Integration Tests
- Test CLI commands end-to-end
- Test with real PPK files (fixtures)
- Validate output formats

### Manual Testing
- TUI navigation
- Cross-platform testing
- Real-world scenarios

---

## 🚀 Next Steps

- **[Contributing Guide](contributing.md)** - Development workflow
- **[Building Guide](building.md)** - Create binaries
