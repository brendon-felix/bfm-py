# BFM-PY - BIOS Flash Manager (Python)

Python equivalent of the nushell `bfm.nu` script for building, saving, and flashing BIOS bootleg binaries.

## Features

- Build BIOS binaries for different platforms (U60, U61, U65, X60)
- Manage version numbers in BiosId.env files
- Save bootlegs to local and network locations
- Flash binaries using DediProg
- Cross-platform colored terminal output

## Usage

```bash
python bfm.py [platform] [options]
```

### Platforms
- `U60` - Glacier
- `U61` - Winters  
- `U65` - Avalanche
- `X60` - Springs (default)

### Options

- `-b, --build` - Build the binary
- `-r, --release` - Build a release binary (default is debug)
- `-l, --bootleg` - Use the latest bootleg binary
- `-s, --save` - Save the build to the bootlegs folder
- `-n, --network` - Save the bootleg to the network drive
- `-f, --flash` - Flash the binary using DediProg
- `-t, --tree TREE` - Specify a specific tree to use
- `-p, --path PATH` - Manually specify a filepath for a binary to flash
- `-a, --append STRING` - Append a string to the bootleg basename
- `-d, --no-decrement` - Don't decrement the feature number
- `-v, --set-version VERSION` - Set the feature version number directly

### Examples

```bash
# Build and flash X60 (Springs) binary
python bfm.py X60 --build --flash

# Build release binary for U60 and save to bootlegs
python bfm.py U60 --build --release --save

# Flash existing bootleg for U61
python bfm.py U61 --bootleg --flash

# Build with custom tree and save to network
python bfm.py --build --tree MyCustomTree --network

# Set specific version and build
python bfm.py --build --set-version 42 --save
```

## Configuration

The script uses these default paths:
- Development location: `C:\Users\felixb\BIOS`
- Network location: `\\wks-file.ftc.rd.hpicorp.net\MAIN_LAB\SHARES\LAB\Brendon Felix\Bootlegs`

## Requirements

- Python 3.6+
- Windows environment with PowerShell
- DediProg tools (for flashing)
- Access to the BIOS development trees

## File Structure

Each platform has its own configuration:
- Repository location based on tree selection
- Platform package location (`HpPlatformPkg`)
- Build output location (`BLD/FV`)
- Bootleg storage location
- BiosId.env file location for version management
