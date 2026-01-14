# RT1018 Installer - Structure Migration Summary

## What Changed

### 1. Folder Structure Reorganization

**Before:**
```
setting-windows/
└── setting-windows/          # Redundant nesting
    └── files_to_install/
        ├── apk_files/
        └── suwon/            # Meaningless name
            ├── Backup/       # Confusing - these are DEFAULT install files
            │   ├── files/
            │   ├── MainDatabase.db
            │   └── *.xml
            └── files/        # Unclear purpose
                └── 광고_*, 팝업_*, 화면_*
```

**After:**
```
install_files/                # Clear, direct name
├── apk_files/               # APK files
├── data/                    # Data files → /data/data/
│   ├── files/               # App internal files
│   ├── MainDatabase.db
│   └── *.xml
└── sdcard/                  # SD card files → /sdcard/
    └── files/
        └── 광고_*, 팝업_*, 화면_*
```

### 2. Backup Structure Improved

**Before:**
```
backups/backup_*/
├── apk_files/
└── suwon/                   # Meaningless
    └── Backup/              # Nested for no reason
```

**After:**
```
backups/backup_*/
├── apk_files/               # APKs
├── data/                    # Data files
│   ├── files/
│   ├── MainDatabase.db
│   └── *.xml
└── sdcard/                  # SD card files
    └── files/
```

**Benefits:**
- Backup structure now **matches** install structure
- Can use backups as installation source seamlessly
- Easy to compare backup vs default

### 3. Code Changes

**Updated paths in `rt1018_installer_gui.py`:**

1. **Base path:**
   - Old: `self.files_dir = self.base_dir / "setting-windows" / "setting-windows" / "files_to_install"`
   - New: `self.files_dir = self.base_dir / "install_files"`

2. **Installation (install_to_device):**
   - Old: `suwon_dir = source / "suwon"`
   - Old: `files_src = suwon_dir / "files"`  (SD card)
   - Old: `backup_src = suwon_dir / "Backup"`  (app data)
   - New: `sdcard_src = source / "sdcard"`
   - New: `data_src = source / "data"`

3. **Backup (start_backup):**
   - Old: Creates `suwon/Backup/` structure
   - New: Creates `data/` and `sdcard/` directories
   - Now mirrors installation structure

## Files Affected

### Modified:
- `rt1018_installer_gui.py` - All path references updated

### Created:
- `install_files/` - New installation source directory
- `STRUCTURE.md` - Documentation of new structure
- `MIGRATION_SUMMARY.md` - This file

### Can be Deleted (after verification):
- `setting-windows/` - Old structure (keep temporarily as backup)

## Testing Checklist

- [ ] Run application - `python rt1018_installer_gui.py`
- [ ] Scan network for devices
- [ ] Install to device from default set
- [ ] Verify installation succeeds
- [ ] Backup from device
- [ ] Verify backup structure matches new format
- [ ] Install from backup to another device
- [ ] Verify backup installation works

## Rollback Plan

If issues occur:
1. The old `setting-windows/` folder is still present
2. Revert the path changes in `rt1018_installer_gui.py`
3. Change line 53 back to:
   ```python
   self.files_dir = self.base_dir / "setting-windows" / "setting-windows" / "files_to_install"
   ```

## Next Steps

1. **Test thoroughly** with the checklist above
2. **If successful**: Delete `setting-windows/` folder
3. **If issues**: Report errors and rollback

## Benefits Summary

✅ **Clarity** - No more confusing "suwon" or nested "Backup" folders
✅ **Consistency** - Backups match installation structure
✅ **Simplicity** - Removed redundant `setting-windows/setting-windows/` nesting
✅ **Maintainability** - Anyone can understand the structure
✅ **Flexibility** - Easy to switch between default and backup installations
