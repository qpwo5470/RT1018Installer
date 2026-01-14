# RT1018 Android Device Installer - GUI Application

A comprehensive GUI application for installing and managing RT1018 (EightPresso) Android devices over network.

## Features

### 1. Network Device Discovery
- Scan local network for Android devices
- Automatically detect devices on ports 5555 and 1206
- Display Android version and device model
- Multi-device selection with checkboxes

### 2. Installation
- Install APKs (RustDesk, Hangul Keyboard, EasyCard, EightPresso)
- Transfer application files and databases
- Grant necessary permissions
- Set Korean language and keyboard
- Set EightPresso as home launcher
- Android 12+ permission handling (automatic chown)
- Choose between default or backed-up installation sets

### 3. Backup
- Backup apps and files from devices
- Timestamped backup folders (human-friendly format)
- Save APKs, databases, preferences, and files
- Backup metadata in JSON format
- Use backed-up sets for future installations

### 4. Database Cleanup
- Scan MainDatabase.db for image references
- Find orphaned image files not referenced in database
- Move orphaned files to separate folder
- Clean up garbage files automatically

### 5. Device Monitoring
- Scrcpy integration (960×540 window)
- Real-time installation logs
- Progress bar showing installation status
- Per-device status tracking

## Prerequisites

### Required
1. **Python 3.7+** (uses only standard library, no pip packages needed)
   - Download: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Android Platform Tools (ADB)** - Windows version
   - Download: https://developer.android.com/studio/releases/platform-tools
   - Extract and add to PATH environment variable
   - Verify: Run `adb version` in terminal

### Optional
3. **Scrcpy** (for screen mirroring)
   - Download: https://github.com/Genymobile/scrcpy
   - Or install via: `winget install Genymobile.scrcpy`
   - Add to PATH

### NOT Required
- ❌ **WSL (Windows Subsystem for Linux)** - The original batch file used WSL, but this Python GUI doesn't need it!
- ❌ **Ubuntu or any Linux distribution**
- ❌ **Bash or shell scripting environment**

The Python GUI runs ADB commands directly on Windows, making installation much simpler.

## Installation

### Option 1: Using Pre-built Executable (Recommended)

**No Python installation required!**

1. Download or copy `RT1018_Installer.exe` from the `dist/` folder
2. Place it in the same directory as `setting-windows/` folder
3. Ensure ADB is installed and in PATH
4. Double-click `RT1018_Installer.exe` to run

### Option 2: Building the Executable Yourself

```cmd
# Build the executable
python build_exe.py

# The executable will be created at:
dist/RT1018_Installer.exe
```

See [BUILD.md](BUILD.md) for detailed build instructions.

### Option 3: Running from Python Source

If you have Python installed:

```cmd
python rt1018_installer_gui.py
```

No pip packages needed (uses only standard library)!

## Usage

### Initial Setup

1. **Enable Wireless Debugging on Android devices:**
   - Go to Settings > Developer Options
   - Enable "Wireless Debugging" or "ADB over Network"
   - Note the IP address and port

2. **Connect devices to same network as your PC**

### Scanning for Devices

1. The application **automatically detects** your network IP range on startup
   - Based on your PC's IP address (e.g., if your PC is `192.168.1.100`, it detects `192.168.1`)
   - Click "Auto" button to re-detect if your network changes
   - Manually edit the IP range if needed for different subnets
2. Click "Scan Network"
3. Wait for devices to be discovered (scans ports 5555 and 1206)
4. Devices will appear with checkboxes showing IP, model, and Android version

### Installing to Devices

1. Select devices using checkboxes
2. Choose installation source:
   - **Default Set**: Use files from `files_to_install` directory
   - **Backup Set**: Use previously backed-up configuration
3. Click "Install to Selected Devices"
4. Monitor progress in log window
5. Wait for completion (device will reboot automatically)

### Backing Up a Device

1. Select ONE device (backup works on single device)
2. Click "Backup from Device"
3. Backup will be saved with timestamp: `backup_192_168_1_100_20260109_143052`
4. Backed-up set can be used for future installations

### Cleaning Database Images

1. Click "Clean Database Images"
2. Select the MainDatabase.db file
3. Select the image files directory (containing hash-named files)
4. Review orphaned files list
5. Confirm to move orphaned files to `deleted_orphans` folder

### Using Scrcpy

1. Select a device
2. Click "Start Scrcpy"
3. A 960×540 window will open showing device screen
4. Click "Stop Scrcpy" to close

## Directory Structure

```
RT1018Installer/
├── rt1018_installer_gui.py          # Main application
├── requirements.txt                  # Dependencies info
├── README.md                         # This file
├── setting-windows/
│   └── setting-windows/
│       ├── files_to_install/         # Default installation files
│       │   ├── apk_files/           # APK files
│       │   └── suwon/               # Configuration files
│       │       ├── files/           # App files
│       │       └── Backup/          # Database and preferences
│       └── scripts/                 # Original batch scripts (reference)
└── backups/                         # Backed-up device configurations
    └── backup_192_168_1_100_20260109_143052/
        ├── backup_info.json         # Backup metadata
        ├── apk_files/              # Backed-up APKs
        └── suwon/                  # Backed-up files
```

## Installation Process Details

The installer performs these steps for each device:

1. **Request root access** - Enable root via `adb root`
2. **Install APKs** - Install all APK files
3. **Grant permissions** - Grant required app permissions
4. **Initialize app** - Launch app to create directory structure
5. **Transfer files** - Push files to device storage
6. **Fix ownership** - Apply chown for Android 12+ (automatic detection)
7. **Stop app** - Force stop before configuration
8. **Set language/keyboard** - Configure Korean language and keyboard
9. **Reboot device** - Apply settings
10. **Set home app** - Configure EightPresso as launcher

## Backup Format

Backups are saved in timestamped folders with this structure:

```
backup_192_168_1_100_20260109_143052/
├── backup_info.json                 # Metadata
├── apk_files/
│   └── EightPresso.apk
└── suwon/
    ├── files/                       # Files from /sdcard
    └── Backup/
        ├── files/                   # Files from /data/data
        ├── MainDatabase.db
        └── com.releasetech.eightpresso.basic_preferences.xml
```

## Troubleshooting

### ADB Connection Issues
- Ensure device is on same network
- Check firewall settings (allow ports 5555, 1206, 5037)
- Verify wireless debugging is enabled
- Try manual connection: `adb connect 192.168.1.100:5555`

### Installation Fails
- Check if device has root access
- Ensure sufficient storage space
- Verify all required files exist in `files_to_install`
- Check logs for specific error messages

### Scrcpy Not Working
- Install scrcpy from official repository
- Ensure scrcpy is in PATH
- Check device is connected: `adb devices`

### Android 12+ Permission Issues
- The app automatically detects Android 12+ and applies chown
- If issues persist, manually check ownership:
  ```cmd
  adb shell stat -c '%U' /data/data/com.releasetech.eightpresso.basic
  ```

## Comparison with Original Batch File

| Feature | Batch File | GUI Application |
|---------|-----------|-----------------|
| **Prerequisites** | **WSL + Ubuntu + ADB** | **Just Python + ADB** |
| IP range detection | Manual entry | **Auto-detected** + manual override |
| Network scanning | Manual IP entry | Automatic LAN scan (ports 5555, 1206) |
| Multi-device | Single device | Multiple devices |
| Progress tracking | Text output | Progress bar + logs |
| Backup | Not supported | Full backup with restore |
| Database cleanup | Not supported | Automatic orphan detection |
| Screen mirroring | Not supported | Scrcpy integration |
| Installation source | Fixed | Default or backed-up sets |
| Android 12 handling | Manual | Automatic detection |
| User interface | Command line | Full GUI |
| Setup time | ~10 min (WSL install) | ~2 min |

## License

This tool is provided as-is for internal use.

## Support

For issues or questions, check the logs in the application or consult the original batch scripts in `setting-windows/setting-windows/scripts/`.
