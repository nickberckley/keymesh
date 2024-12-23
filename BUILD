"""This is an utility script for quickly building Blender extension using Blender's command line arguments"""
"""Running `python build.py` in terminal will package contents of the /source/ and put it outside of the root folder"""
"""Command lines need to be executed in Blender executables location, which can be provided with --exe argument"""
"""--legacy argument can be used to build extension for Blender 4.1 and earlier (with root folder inside the .zip file)"""

DEFAULT_BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 4.3"


import os
import subprocess
import argparse
import sys
import glob
import zipfile

show_color = (
    False if os.environ.get("NO_COLOR") else
    sys.stdout.isatty()
)
YELLOW = "\033[93m"
RED = "\033[31m"
GREEN = "\033[32m"
ALERT = "\033[91m"
RESET = "\033[0m"


def main():
    # Argument for accepting Blender executable path.
    parser = argparse.ArgumentParser(description="Build Blender extension")
    parser.add_argument(
        "--exe",
        type=str,
        default=DEFAULT_BLENDER_PATH,
        help="Path to the Blender executable folder"
    )
    # Argument for packaging add-on for Blender 4.1 and previous versions.
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Puts add-on content in the root directory that is required by Blender 4.1 and earlier"
    )
    args = parser.parse_args()

    blender_exe = os.path.join(args.exe, "blender")
    if not os.path.isfile(blender_exe) and not os.path.isfile(blender_exe + ".exe"):
        print(f"Error: Blender executable not found at '{args.exe}'")
        return

    # Define paths.
    root_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(root_dir, "source")
    output_dir = os.path.abspath(os.path.join(root_dir, ".."))

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    # Execute the Blender command for building the add-on.
    command = (
        f"{blender_exe} --command extension build "
        f"--source-dir {source_dir} --output-dir {output_dir}"
    )
    try:
        print(f"{YELLOW if show_color else ''}Running: {command}{RED if show_color else ''} \n")
        subprocess.run(command, check=True)

        addon_id, addon_version = get_addon_id_version()
        expected_name = f"{addon_id}-{addon_version}.zip"
        new_name = f"{addon_id}_v{addon_version}.zip"

        # Find newly created .zip file.
        zip_files = glob.glob(os.path.join(output_dir, expected_name))
        if zip_files:
            zip_file = zip_files[0]

            # Rename the file.
            renamed_file = os.path.join(output_dir, new_name)
            if os.path.exists(renamed_file):
                os.remove(renamed_file)
            os.rename(zip_file, renamed_file)

            # Adjust package for legacy (4.1 and earlier) Blender versions.
            if args.legacy:
                create_root_folder_in_zip(renamed_file, addon_id)

        else:
            print(f"{ALERT}Error: Expected .zip file {expected_name} was not found.{RESET}")

        print(f"{GREEN if show_color else ''}\n Add-on successfully packaged.{RESET if show_color else ''}")

    except subprocess.CalledProcessError:
        print(f"{ALERT if show_color else ''}\n Error: Failed to package the add-on.{RESET if show_color else ''}")


def get_addon_id_version():
    addon_id = ""
    addon_version = ""
    toml_path = os.path.join("source", "blender_manifest.toml")

    with open(toml_path, "r") as toml_file:
        for line in toml_file:
            # Look for lines that start with 'id = ' and 'version = '
            if line.startswith("id = "):
                addon_id = line.split("=")[1].strip().replace('"', '')
            elif line.startswith("version = "):
                addon_version = line.split("=")[1].strip().replace('"', '')

    if not addon_id or not addon_version:
        raise ValueError("id or version not found in the .toml file.")
    
    return addon_id, addon_version


def create_root_folder_in_zip(filepath, addon_id):
    """Creates new .zip file with root folder named after extension ID"""

    temp_zip_path = filepath + ".temp"

    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip_ref:
            for file_name in zip_ref.namelist():
                # Add each file in the original zip inside the new zip with root folder.
                new_file_path = os.path.join(addon_id, file_name)
                new_zip_ref.writestr(new_file_path, zip_ref.read(file_name))

    os.remove(filepath)
    os.rename(temp_zip_path, filepath)


if __name__ == "__main__":
    main()
