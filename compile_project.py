#!/usr/bin/env python3
"""
Compile project script - Packages aoe2_overlay.py into executables for Mac and Windows.
Requires PyInstaller to be installed: pip install pyinstaller
"""

import os
import sys
import platform
import subprocess
import shutil
import tempfile


def main():
    # Project file to compile
    target_script = "aoe2_overlay.py"
    game_folder = "aoe2"

    # Check if the target script exists
    if not os.path.exists(target_script):
        print(f"Error: {target_script} not found in the current directory.")
        return 1

    # Create output directory
    output_dir = "dist"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Determine current OS
    current_os = platform.system()

    # Clean any previous build artifacts first
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("aoe2_overlay.spec"):
        os.remove("aoe2_overlay.spec")

    # Base PyInstaller command with all data directories included
    base_cmd = [
        "pyinstaller",
        "--clean",
        "--windowed",  # Better for GUI applications
        # Don't use --onefile for more reliability
        "--name", "aoe2_overlay",
        # "--collect-all", "PyQt6",  # Ensure all Qt components are included

        # Include all necessary data directories
        "--add-data", f"common{os.pathsep}common",
        "--add-data", f"{game_folder}{os.pathsep}{game_folder}",
        "--add-data", f"pictures/common{os.pathsep}pictures/common",
        "--add-data", f"pictures/{game_folder}{os.pathsep}pictures/{game_folder}",
        "--add-data", f"build_orders/{game_folder}{os.pathsep}build_orders/{game_folder}",
        "--add-data", f"audio{os.pathsep}audio",
        "--hidden-import", "PIL._tkinter_finder",  # Common hidden dependency
    ]

    # On macOS, we need special handling for PyQt6
    # if current_os == "Darwin":
    #     # Exclude problematic PyQt6 modules that cause symlink errors
    #     base_cmd.extend([
    #         "--exclude-module", "PyQt6.QtBluetooth",
    #         "--exclude-module", "PyQt6.QtWebEngineCore"
    #     ])

    # Add the target script
    base_cmd.append(target_script)

    # Add icon if it exists
    icon_file = "pictures/common/icon/salamander_sword_shield.ico"
    if os.path.exists(icon_file):
        base_cmd.extend(["--icon", icon_file])
    elif os.path.exists("icon.ico" if current_os == "Windows" else "icon.icns"):
        base_cmd.extend(["--icon", "icon.ico" if current_os == "Windows" else "icon.icns"])

    # Compile for the current OS
    print(f"Building executable for {current_os}...")
    try:
        # Run PyInstaller directly without creating a spec file first
        subprocess.check_call(base_cmd)

        # Package the output in a platform-specific way
        if current_os == "Darwin":  # macOS
            app_path = os.path.join("dist", "aoe2_overlay.app")
            output_zip = os.path.join(output_dir, "aoe2_overlay_mac.zip")

            if os.path.exists(app_path):
                print(f"Creating ZIP archive for macOS: {output_zip}")
                # Create a temporary directory for ZIP creation to avoid nested directories
                with tempfile.TemporaryDirectory() as temp_dir:
                    shutil.copytree(app_path, os.path.join(temp_dir, "aoe2_overlay.app"))
                    shutil.make_archive(os.path.splitext(output_zip)[0], 'zip', temp_dir)
                print(f"Successfully created: {output_zip}")
        elif current_os == "Windows":
            src_dir = os.path.join("dist", "aoe2_overlay")
            dst_zip = os.path.join(output_dir, "aoe2_overlay_windows.zip")

            if os.path.exists(src_dir):
                print(f"Creating ZIP archive for Windows: {dst_zip}")
                with tempfile.TemporaryDirectory() as temp_dir:
                    shutil.copytree(src_dir, os.path.join(temp_dir, "aoe2_overlay"))
                    shutil.make_archive(os.path.splitext(dst_zip)[0], 'zip', temp_dir)
                print(f"Successfully created: {dst_zip}")

        # Copy additional files to a separate folder for documentation
        docs_dir = os.path.join(output_dir, "documentation")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)

        for file in ['Readme.md', 'Changelog.md', 'LICENSE', 'version.json']:
            if os.path.exists(file):
                shutil.copy(file, docs_dir)
                print(f"Copied {file} to documentation directory")

        # Copy source file for reference
        if os.path.exists(f"{game_folder}_overlay.py"):
            shutil.copy(f"{game_folder}_overlay.py", docs_dir)
            print(f"Copied {game_folder}_overlay.py to documentation directory")

    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return 1

    print("\nNOTE: This script has built the executable for your current platform.")
    print("To build for both Windows and macOS, you need to run this script on each platform.")

    return 0


if __name__ == "__main__":
    sys.exit(main())