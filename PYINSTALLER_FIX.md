# PyInstaller Executable Path Fix

## Problem

When running the compiled executable, it showed error:
```
설치 파일을 찾을 수 없음
C:/Users/qpwo/5/AppData/Local/Temp/_MEI433362/install_files
```

The executable was looking for `install_files` in the temporary extraction directory instead of the actual directory where the `.exe` is located.

## Root Cause

PyInstaller extracts the executable to a temporary directory (like `_MEI433362`), and `__file__` points to that temp directory, not the actual `.exe` location.

## Solution

Updated `rt1018_installer_gui.py` (lines 52-58) to detect if running as compiled executable:

```python
# Handle both running as script and as PyInstaller executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable - use executable's directory
    self.base_dir = Path(sys.executable).parent
else:
    # Running as Python script - use script's directory
    self.base_dir = Path(__file__).parent
```

### How it works:

- **`sys.frozen`** is set to `True` by PyInstaller when running as executable
- **`sys.executable`** points to the actual `.exe` file location when frozen
- **`__file__`** points to the script location when running as Python

## Result

Now the executable correctly looks for:
- `install_files/` - in the same directory as `RT1018_Installer.exe`
- `backups/` - in the same directory as `RT1018_Installer.exe`

## Deployment Structure

```
YourFolder/
├── RT1018_Installer.exe      # The executable
├── install_files/             # Installation files (must exist)
│   ├── apk_files/
│   ├── data/
│   └── sdcard/
└── backups/                   # Created automatically
```

## Building

To rebuild the executable after changes:

```cmd
cd C:\Users\qpwo5\PycharmProjects\RT1018Installer
python -m PyInstaller --clean rt1018_installer.spec
```

Executable will be created at: `dist\RT1018_Installer.exe`

## Testing

1. Copy `dist\RT1018_Installer.exe` to a new folder
2. Copy `install_files\` folder to the same location
3. Run `RT1018_Installer.exe`
4. Should work without the path error!

## Date Fixed

2026-01-12
