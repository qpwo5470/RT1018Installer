"""
Build script for RT1018 Installer executable
Installs PyInstaller if needed and builds the executable
"""

import subprocess
import sys
import os
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed, install if not"""
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install PyInstaller")
            print("\nPlease install manually:")
            print("  pip install pyinstaller")
            return False

def clean_build_folders():
    """Clean previous build artifacts"""
    import shutil

    folders_to_clean = ['build', 'dist', '__pycache__']
    for folder in folders_to_clean:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder_path)

    # Remove spec file bytecode
    for file in Path('.').glob('*.spec'):
        pyc_file = file.with_suffix('.pyc')
        if pyc_file.exists():
            pyc_file.unlink()

def build_executable():
    """Build the executable using PyInstaller"""
    print("\n" + "="*60)
    print("Building RT1018 Installer Executable")
    print("="*60 + "\n")

    # Check/install PyInstaller
    if not check_pyinstaller():
        return False

    # Clean old builds
    print("\nCleaning previous builds...")
    clean_build_folders()

    # Build using spec file
    print("\nBuilding executable (this may take 1-2 minutes)...")
    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "rt1018_installer.spec"
        ])
        # Copy README to dist folder
        import shutil
        dist_readme = Path('DIST_README.txt')
        if dist_readme.exists():
            shutil.copy(dist_readme, Path('dist/README.txt'))
            print("✓ Copied README to dist folder")

        print("\n" + "="*60)
        print("✓ BUILD SUCCESSFUL!")
        print("="*60)
        print(f"\nExecutable created at: {Path('dist/RT1018_Installer.exe').absolute()}")
        print(f"README created at: {Path('dist/README.txt').absolute()}")
        print("\nYou can now:")
        print("  1. Run dist/RT1018_Installer.exe directly")
        print("  2. Copy dist/RT1018_Installer.exe to any location")
        print("  3. Share it with others (no Python needed!)")
        print("\nNote: Users still need ADB and Scrcpy installed separately")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "="*60)
        print("✗ BUILD FAILED")
        print("="*60)
        print(f"\nError: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
