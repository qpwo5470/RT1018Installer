========================================
RT1018 INSTALLER - STANDALONE EXECUTABLE
========================================

This folder contains the standalone executable for RT1018 Installer.

FILE:
-----
RT1018_Installer.exe  (~15-20 MB)


WHAT THIS IS:
-------------
A complete Android device installer with GUI that:
- Scans network for devices
- Installs apps and files
- Backs up device configurations
- Cleans database images
- Integrates screen mirroring


NO PYTHON NEEDED!
-----------------
This executable runs on any Windows PC without requiring Python installation.


REQUIREMENTS:
-------------
1. ADB (Android Platform Tools) - REQUIRED
   Download: https://developer.android.com/studio/releases/platform-tools
   Must be added to PATH

2. Scrcpy (optional, for screen mirroring)
   Download: https://github.com/Genymobile/scrcpy
   Or: winget install Genymobile.scrcpy


INSTALLATION FILES:
-------------------
The executable must be in the same directory as the "setting-windows" folder.

Correct structure:
    YourFolder/
    ├── RT1018_Installer.exe      <-- This file
    └── setting-windows/           <-- Must exist!
        └── setting-windows/
            └── files_to_install/
                ├── apk_files/
                └── suwon/


HOW TO USE:
-----------
1. Copy RT1018_Installer.exe to desired location
2. Make sure setting-windows/ folder is in same directory
3. Make sure ADB is installed
4. Double-click RT1018_Installer.exe
5. Follow the GUI instructions


DISTRIBUTION:
-------------
You can copy RT1018_Installer.exe to any computer.

Just make sure to also copy:
- setting-windows/ folder (installation files)
- Documentation (README.md, QUICK_START.md)

And ensure the user has ADB installed.


DOCUMENTATION:
--------------
Full documentation is available in:
- README.md - Complete reference
- QUICK_START.md - Step-by-step guide
- BUILD.md - Build instructions


TROUBLESHOOTING:
----------------
If the executable won't start:
1. Check if setting-windows/ folder exists
2. Verify ADB is installed: adb version
3. Check antivirus (may block the .exe)
4. Run from command prompt to see errors:
   RT1018_Installer.exe


SUPPORT:
--------
For issues, check the full documentation in README.md


========================================
Version: 1.0
Built with: PyInstaller
========================================
