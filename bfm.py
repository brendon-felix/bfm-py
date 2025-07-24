#!/usr/bin/env python3
"""
BFM (Build and Flash Manager) - Python equivalent of bfm.nu
Build, save, and flash BIOS binaries
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Any
import glob

DEV_LOC = r'C:\Users\felixb\BIOS' # Local trees in here
LOCAL_BOOTLEGS = r'C:\Users\felixb\BIOS\Bootlegs'
NET_LOC = r'\\wks-file.ftc.rd.hpicorp.net\MAIN_LAB\SHARES\LAB\Brendon Felix\Bootlegs'

class Colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    RED_BOLD = '\033[1;31m'
    GREEN_BOLD = '\033[1;32m'


def print_colored(text: str, color: str = "") -> None:
    print(f"{color}{text}{Colors.RESET}")


def check_dpcmd_available() -> None:
    if shutil.which("dpcmd") is None:
        print_colored("Error: 'dpcmd' command not found in system PATH", Colors.RED_BOLD)
        print_colored("Ensure DediProg SF Software is installed and added to PATH", Colors.RED)
        display = "https://www.dediprog.com/download"
        url = "https://www.dediprog.com/download?productCategory=3&productName=2561&fileType="
        print_colored(f"Download from: \033]8;;{url}\033\\{display}\033]8;;\033\\ (Ctrl+Click)", Colors.YELLOW)
        sys.exit(1)


def get_repo_loc(tree: Optional[str], default: str) -> str:
    if tree is not None:
        return os.path.join(DEV_LOC, tree)
    else:
        return os.path.join(DEV_LOC, default)


def create_config(name: str, tree: Optional[str], default_tree: str, biosid_loc: str) -> Dict[str, str]:
    repo_loc = get_repo_loc(tree, default_tree)
    
    # Validate that the repository tree exists
    if not os.path.exists(repo_loc):
        tree_name = tree if tree is not None else default_tree
        raise FileNotFoundError(f"Repository tree not found: {repo_loc}")
    
    pltpkg_loc = os.path.join(repo_loc, 'HpPlatformPkg')
    
    return {
        'name': name,
        'repo_loc': repo_loc,
        'pltpkg_loc': pltpkg_loc,
        'bld_path': os.path.join(pltpkg_loc, 'BLD', 'FV'),
        'bootleg_loc': os.path.join(DEV_LOC, 'Bootlegs', name),
        'network_loc': os.path.join(NET_LOC, name),
        'biosid_loc': os.path.join(pltpkg_loc, biosid_loc)
    }


def get_config(platform: Optional[str], tree: Optional[str]) -> Dict[str, str]:
    if platform == 'U60':
        return create_config('Glacier', tree, 'HpWintersWks', 'MultiProject/U60Glacier/BLD/BiosId.env')
    elif platform == 'U61':
        return create_config('Winters', tree, 'HpWintersWks', 'MultiProject/U61Blizzard/BLD/BiosId.env')
    elif platform == 'U65':
        return create_config('Avalanche', tree, 'HpAvalancheWks', 'BLD/RSPS/BiosId.env')
    elif platform == 'X60' or platform is None:
        return create_config('Springs', tree, 'HpSpringsWks', 'MultiProject/X60Steamboat/BLD/BiosId.env')
    else:
        raise ValueError(f"Unknown platform: {platform}")


def format_hex(value: int, reverse: bool = False) -> str:
    hex_str = f"{value:02X}"
    if reverse:
        return hex_str
    return hex_str


def decode_hex(hex_str: str) -> int:
    return int(hex_str, 16)


def set_version(file_path: str, version: Optional[int] = None):
    """Set version in BiosId.env file"""

    if not os.path.exists(file_path):
        print_colored(f"BiosId.env file not found at {os.path.basename(file_path)}", Colors.RED)
        raise FileNotFoundError("BiosId.env file not found")
    
    # Read file and find current version
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    curr_version_str = None
    for line in lines:
        if 'VERSION_FEATURE' in line and '=' in line:
            match = re.search(r'VERSION_FEATURE.*?=(.+)', line)
            if match:
                curr_version_str = match.group(1).strip()
                break
    
    if curr_version_str is None:
        raise ValueError("VERSION_FEATURE not found in BiosId.env")
    
    curr_version = decode_hex(curr_version_str)
    
    if version is None:
        new_version = (curr_version - 1) % 100
    else:
        new_version = version % 100
    
    print_colored(f"Setting feature version {curr_version} → {new_version}", Colors.YELLOW)
    
    # Update file contents
    new_lines = []
    for line in lines:
        if 'VERSION_FEATURE' in line:
            new_lines.append(line.replace(curr_version_str, format_hex(new_version, reverse=True)))
        else:
            new_lines.append(line)
    
    with open(file_path, 'w') as f:
        f.writelines(new_lines)


def build(config: Dict[str, str], release: bool = False) -> None:
    """Build the binary"""
    os.chdir(config['pltpkg_loc'])
    
    command_map = {
        'Glacier': 'HpBldGlacier.bat',
        'Winters': 'HpBldBlizzard.bat',
        'Avalanche': 'HpBiosBuild.bat',
        'Springs': 'HpBldSprings.bat'
    }
    
    command = command_map.get(config['name'], 'HpBldSprings.bat')
    
    try:
        if release:
            print_colored("Building RELEASE binary...", Colors.PURPLE)
            subprocess.run([command, 'r'], check=True, shell=True)
        else:
            print_colored("Building DEBUG binary...", Colors.PURPLE)
            subprocess.run([command], check=True, shell=True)
    except subprocess.CalledProcessError:
        print_colored("Build failed", Colors.RED)
        raise RuntimeError("Build failed")


def check_and_create_directories(config: Dict[str, str], args) -> None:
    """Check if directories exist and prompt for creation if needed"""
    directories_to_check = []
    
    if args.save:
        directories_to_check.append(('local bootlegs', config['bootleg_loc']))
    
    if args.network:
        directories_to_check.append(('network bootlegs', config['network_loc']))
    
    if args.output:
        directories_to_check.append(('custom output', args.output))
    
    for dir_type, dir_path in directories_to_check:
        if not os.path.exists(dir_path):
            print_colored(f"{dir_type.capitalize()} directory does not exist: {dir_path}", Colors.YELLOW)
            response = input(f"Create {dir_type} directory? (y/N): ").strip().lower()
            if response not in ('y', 'yes'):
                print_colored(f"Save to {dir_type} folder will be skipped", Colors.RED)
                # Remove the corresponding flag so save operation is skipped
                if dir_type == 'local bootlegs':
                    args.save = False
                elif dir_type == 'network bootlegs':
                    args.network = False
                elif dir_type == 'custom output':
                    args.output = None
            else:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print_colored(f"Created {dir_type} directory: {dir_path}", Colors.GREEN)
                except OSError as e:
                    print_colored(f"Failed to create {dir_type} directory: {e}", Colors.RED)
                    raise RuntimeError(f"Could not create {dir_type} directory: {dir_path}")


def save_bootleg(bootleg_loc: str, binary_path: str, append: Optional[str] = None) -> None:
    """Save bootleg to specified location"""
    # Directory should already exist or have been created earlier
    if not os.path.exists(bootleg_loc):
        os.makedirs(bootleg_loc, exist_ok=True)
    
    if append is None:
        bootleg_basename = os.path.basename(binary_path)
    else:
        path_obj = Path(binary_path)
        bootleg_basename = f"{path_obj.stem}_{append}{path_obj.suffix}"
    
    bootleg_path = os.path.join(bootleg_loc, bootleg_basename)
    shutil.copy2(binary_path, bootleg_path)
    print(f"Saved bootleg {Colors.BLUE}{bootleg_basename}{Colors.RESET} to ", end="")


def get_binary(path: str) -> Optional[Dict[str, Any]]:
    """Get binary file information"""
    try:
        if os.path.isdir(path):
            # Look for .bin files that match pattern
            pattern = os.path.join(path, "*.bin")
            files = glob.glob(pattern)
            # Filter out pvt files and look for 32/64 bit files
            valid_files = []
            for f in files:
                basename = os.path.basename(f).lower()
                if 'pvt' not in basename and ('32' in basename or '64' in basename):
                    valid_files.append(f)
            
            if valid_files:
                # Sort by modification time and get the latest
                latest_file = max(valid_files, key=os.path.getmtime)
                stat = os.stat(latest_file)
                return {
                    'name': latest_file,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                }
        elif os.path.isfile(path):
            stat = os.stat(path)
            return {
                'name': path,
                'size': stat.st_size,
                'modified': stat.st_mtime
            }
    except (OSError, IOError):
        pass
    
    return None


def format_filesize(size_bytes: int) -> str:
    """Format file size in MiB"""
    mib = size_bytes / (1024 * 1024)
    return f"{mib:.2f} MiB"


def print_info(binary: Dict[str, Any]) -> None:
    """Print binary information"""
    print_colored(os.path.basename(binary['name']), Colors.BLUE)
    print(f"Size: {format_filesize(binary['size'])}")


def find_build(bld_path: str) -> Optional[Dict[str, Any]]:
    """Find binary in build folder"""
    binary = get_binary(bld_path)
    if binary is not None:
        print("Found binary in build folder: ", end="")
        print_info(binary)
    return binary


def find_bootleg(bootleg_loc: str) -> Optional[Dict[str, Any]]:
    """Find binary in bootlegs folder"""
    binary = get_binary(bootleg_loc)
    if binary is not None:
        print("Found binary in bootlegs folder: ", end="")
        print_info(binary)
    return binary


def find_path(path: str) -> Optional[Dict[str, Any]]:
    """Find binary at specified path"""
    binary = get_binary(path)
    if binary is not None:
        print("Found specified binary: ", end="")
        print_info(binary)
    return binary


def flash(binary: Dict[str, Any]) -> None:
    """Flash binary using DediProg"""
    print_colored("Flashing binary...", Colors.PURPLE)
    try:
        subprocess.run(['dpcmd', '--batch', binary['name'], '--verify'], check=True)
        print_colored("\nFlash successful", Colors.GREEN_BOLD)
    except subprocess.CalledProcessError as err:
        print(f"Flash command failed: {err}")
        raise RuntimeError("Flash failed")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Build, save, and flash a bootleg binary",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('platform', nargs='?', 
                       help='Platform (U60, U61, U65, X60)')
    parser.add_argument('-b', '--build', action='store_true',
                       help='Build the binary')
    parser.add_argument('-r', '--release', action='store_true',
                       help='Build a release binary')
    parser.add_argument('-l', '--bootleg', action='store_true',
                       help='Use the latest bootleg binary')
    parser.add_argument('-s', '--save', action='store_true',
                       help='Save the build to the bootlegs folder')
    parser.add_argument('-n', '--network', action='store_true',
                       help='Save the bootleg to the network drive')
    parser.add_argument('-f', '--flash', action='store_true',
                       help='Flash the binary using DediProg')
    parser.add_argument('-t', '--tree', type=str,
                       help='Specify a specific tree to use')
    parser.add_argument('-p', '--path', type=str,
                       help='Manually specify a filepath for a binary to flash')
    parser.add_argument('-a', '--append', type=str,
                       help='Append a string to the bootleg filename when saving')
    parser.add_argument('-o', '--output', type=str,
                       help='Specify a custom directory to save the bootleg')
    parser.add_argument('-d', '--decrement', action='store_true',
                       help="Decrement the feature number")
    parser.add_argument('-v', '--set-version', type=int,
                       help='Set the feature version number directly')
    
    args = parser.parse_args()
    
    # Check if dpcmd is available (required for flashing)
    # check_dpcmd_available()
    
    try:
        config = get_config(args.platform, args.tree)
        print(f"Using config for {Colors.BLUE}{config['name']}{Colors.RESET} with tree {os.path.basename(config['repo_loc'])}")
        
        # Check and create directories early if save operations are requested
        check_and_create_directories(config, args)
        
        binary = None
        
        if args.build:
            if args.set_version is not None:
                set_version(config['biosid_loc'], args.set_version)
            elif args.decrement:
                set_version(config['biosid_loc'])
            
            build(config, args.release)
            binary = find_build(config['bld_path'])
        elif args.bootleg:
            binary = find_bootleg(config['bootleg_loc'])
        elif args.path is not None:
            binary = find_path(args.path)
        else:
            print_colored("Warning: No binary provided → Checking build folder...", Colors.YELLOW)
            binary = find_build(config['bld_path'])
        
        if binary is None:
            raise RuntimeError("No binary found")
        
        if args.save:
            save_bootleg(config['bootleg_loc'], binary['name'], args.append)
            print("local bootlegs folder")
        
        if args.network:
            save_bootleg(config['network_loc'], binary['name'], args.append)
            print("network bootlegs folder")
        
        if args.output:
            save_bootleg(args.output, binary['name'], args.append)
            print(f"custom output folder: {args.output}")
        
        if args.flash:
            flash(binary)
        else:
            print_colored("Skipped flash", Colors.YELLOW)
            
    except Exception as e:
        print_colored(f"Error: {e}", Colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
