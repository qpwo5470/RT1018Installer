# Changelog - RT1018 Installer GUI

All notable changes to this project will be documented in this file.

## [1.1] - 2026-01-10

### Added
- **Automatic IP range detection** on startup
  - Application now automatically detects your PC's network IP range
  - Example: If PC is on 192.168.1.100, it auto-fills "192.168.1"
  - Supports common private IP ranges (192.168.x, 10.x, 172.x)
  - "Auto" button to re-detect if network changes
  - Fallback to 192.168.1 if detection fails
  - Manual override still available

### Changed
- IP range field now populated automatically on first launch
- Added "Auto" button next to IP range entry field
- Improved logging to show detected IP and range

### Technical Details
- Uses socket.connect() to determine active network interface
- Falls back to hostname resolution if needed
- Extracts first three octets for /24 subnet
- Handles multiple network interfaces gracefully

---

## [1.0] - 2026-01-09

### Added - Initial Release
- Complete GUI replacement for batch file installer
- Network scanning for Android devices (ports 5555, 1206)
- Multi-device selection with checkboxes
- Android version and model detection
- Install button with sequential device processing
- Scrcpy screen integration (960×540)
- Real-time installation logs and progress bar
- Android 12+ automatic permission handling (chown)
- Backup functionality with timestamped folders
- Installation source selection (default/backup sets)
- Database image cleanup (orphan detection)
- PyInstaller build system for standalone .exe
- Comprehensive documentation (8+ documents)

### Features
1. LAN IP scanning on ports 5555 and 1206
2. Device list with Android versions and checkboxes
3. Install button iterating through selected devices
4. Scrcpy screen mirroring (960×540 window)
5. Installation result marking per device
6. Log screen and progress bar
7. Android 12+ chown handling (automatic detection)
8. Backup button with human-friendly timestamps
9. Installation source selection (default vs backed up)
10. Database image cleanup for MainDatabase.db
11. No WSL/Ubuntu required (pure Windows)

### Technical Stack
- Python 3.7+ with tkinter
- PyInstaller for executable build
- Uses only standard library (no pip packages for runtime)
- ADB commands via subprocess
- Threading for background operations
- Socket for network scanning

### Documentation
- GET_STARTED.md - Complete setup guide
- QUICK_START.md - Step-by-step user guide
- README.md - Full reference documentation
- BUILD.md - Build and customization guide
- SUMMARY.md - Project overview and metrics
- HOW_TO_BUILD.txt - Quick build reference
- INDEX.md - Complete file index
- PROJECT_STRUCTURE.txt - Visual structure guide

### Build System
- build_exe.py - Automated build script
- rt1018_installer.spec - PyInstaller configuration
- Creates standalone .exe (~15-20 MB)
- No Python needed for end users

---

## Planned Features (Future)

### v1.2 (Potential)
- [ ] Parallel device installation (install to multiple devices simultaneously)
- [ ] Custom installation profiles
- [ ] Network speed test before installation
- [ ] Log file export to disk
- [ ] APK version checker

### v1.3 (Potential)
- [ ] Device grouping by location/type
- [ ] Scheduled operations (auto-backup/install)
- [ ] Database/preferences editor in GUI
- [ ] Installation templates

---

## Version Numbering

Format: MAJOR.MINOR

- **MAJOR**: Incompatible changes (breaking changes)
- **MINOR**: New features (backward compatible)

Current: v1.1

---

## Notes

### v1.1 Notes
The automatic IP detection makes the app more user-friendly by eliminating the need to manually look up your network range. The algorithm tries multiple methods to find the correct IP:

1. UDP socket connection test (fastest, most accurate)
2. Hostname resolution (fallback)
3. All network interfaces scan (comprehensive fallback)
4. Default to 192.168.1 (last resort)

Users can still manually override if needed (for VPN, multiple networks, etc.)

### v1.0 Notes
Complete feature parity with original batch file installer, plus significant enhancements. The application successfully eliminates the WSL dependency while adding professional GUI features.

All 11 requested features implemented successfully.

---

## Upgrade Instructions

### From v1.0 to v1.1

No breaking changes. Simply rebuild:

```cmd
python build_exe.py
```

The new executable will include automatic IP detection.

Existing configurations, backups, and settings remain compatible.

---

## Bug Fixes

### v1.1
- Improved network interface detection on systems with multiple adapters
- Better error handling for network detection failures

### v1.0
- Initial stable release, no known bugs

---

## Contributors

- Initial development: Claude Code (Anthropic)
- Testing and requirements: RT1018 Project Team

---

## License

Internal use only.

---

## Support

For issues or questions:
1. Check documentation (README.md, QUICK_START.md)
2. Review logs in GUI window
3. Consult troubleshooting sections
