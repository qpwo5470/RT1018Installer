# RT1018 Installer - Directory Structure

## Overview
Clean, logical directory structure for the RT1018 Android Device Installer.

## Main Structure

```
RT1018Installer/
├── rt1018_installer_gui.py      # Main application
├── install_files/               # Files to install on devices
│   ├── apk_files/              # APK files
│   │   ├── rustdesk-1.1.9.apk
│   │   ├── hangulkeyboard.apk
│   │   ├── EasyCard-A_v1.0.3.0_mod.apk
│   │   └── EightPresso.apk
│   ├── data/                   # App data files (installed to /data/data/)
│   │   ├── files/              # App internal files
│   │   ├── MainDatabase.db     # Database file
│   │   └── com.releasetech.eightpresso.basic_preferences.xml
│   └── sdcard/                 # SD card files (installed to /sdcard/)
│       └── files/              # Files directory
└── backups/                    # Device backups
    └── backup_DEVICE_TIMESTAMP/  # Format: backup_192_168_0_57_20260110_033911
        ├── apk_files/          # Backed up APKs
        │   └── EightPresso.apk
        ├── data/               # App data from /data/data/
        │   ├── files/
        │   ├── MainDatabase.db
        │   └── com.releasetech.eightpresso.basic_preferences.xml
        ├── sdcard/             # Files from /sdcard/
        │   └── files/
        └── backup_info.json    # Backup metadata
```

## Installation Source Folders

### `install_files/apk_files/`
Contains all APK files to install:
- rustdesk-1.1.9.apk
- hangulkeyboard.apk
- EasyCard-A_v1.0.3.0_mod.apk
- EightPresso.apk

### `install_files/data/`
Contains app data files that go to `/data/data/com.releasetech.eightpresso.basic/`:
- `files/` - App internal files (images, cache, etc.)
- `MainDatabase.db` - Main database
- `com.releasetech.eightpresso.basic_preferences.xml` - App preferences

### `install_files/sdcard/`
Contains files that go to `/sdcard/Android/data/com.releasetech.eightpresso.basic/`:
- `files/` - SD card files directory

## Backup Structure

When you backup a device, it creates:
```
backups/backup_192_168_0_57_20260110_033911/
├── apk_files/              # APKs from device
├── data/                   # Data from /data/data/
│   ├── files/
│   ├── MainDatabase.db
│   └── *.xml
├── sdcard/                 # Files from /sdcard/
│   └── files/
└── backup_info.json        # Device info, timestamp, etc.
```

This structure **matches the install_files structure**, making it easy to:
1. Backup from one device
2. Use that backup to install on other devices
3. Compare backups to the default installation set

## Changes from Old Structure

**Old structure** (confusing):
```
setting-windows/setting-windows/files_to_install/
├── apk_files/
└── suwon/                  # Meaningless name
    ├── Backup/             # Actually app data files
    └── files/              # Actually sdcard files
```

**New structure** (clear):
```
install_files/
├── apk_files/              # APK files
├── data/                   # App data files
└── sdcard/                 # SD card files
```

## Benefits

1. **Clear naming** - No more "suwon" (meaningless), "Backup" (confusing)
2. **Logical organization** - Mirrors Android file system structure
3. **Consistent backups** - Same structure as installation files
4. **Easy to understand** - Anyone can see what goes where
5. **No redundant nesting** - Removed `setting-windows/setting-windows/`

## Usage

### Installing Default Set
1. Put your files in `install_files/`
2. Select "기본 설정" (Default Set)
3. Click "선택한 디바이스에 설치"

### Installing from Backup
1. Backup a device (creates `backups/backup_*/`)
2. Select "백업 설정" (Backup Set)
3. Choose the backup from dropdown
4. Click "선택한 디바이스에 설치"

### Creating Backups
1. Select exactly one device
2. Click "디바이스에서 백업"
3. Backup saved to `backups/backup_DEVICE_TIMESTAMP/`
