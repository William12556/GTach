# GTach Deployment and Release Guide

**Created**: 2025 08 13

## Step-by-Step Guide: Packaging, Distributing, and Installing GTach Application

### Prerequisites

Before you begin, ensure you have:
- Development machine (Mac, Linux, or Windows) with project files
- Raspberry Pi with network access
- SSH access to the Raspberry Pi
- Python 3.9+ installed on both systems
- All 143 project tests passing

---

### Part 1: Package Creation (on Development Machine)

#### Step 1: Open Terminal and Navigate to Project
```bash
cd /path/to/your/GTach
```

#### Step 2: Verify Project Status
```bash
# Run the test suite to ensure everything works
python -m pytest src/tests/ -v

# You should see: 143 tests passed
```

#### Step 3: Create the Deployment Package
```bash
# Navigate to the provisioning directory
cd src/provisioning

# Run the package creation script
python create_package.py
```

**What happens:** The system will:
- Collect all source files from `src/obdii`
- Process configuration templates for Raspberry Pi
- Generate installation scripts
- Create a compressed package file
- Save it to the `packages/` directory

#### Step 4: Verify Package Creation
```bash
# Check the packages directory
ls -la ../../packages/

# You should see a file like:
# gtach-pi-deployment-1.0.0-20250810_143022.tar.gz
```

---

### Part 2: Package Distribution

#### Step 5: Transfer Package to Raspberry Pi
```bash
# Copy the package to your Pi (replace with your Pi's IP address)
scp ../../packages/gtach-pi-deployment-*.tar.gz pi@192.168.1.100:/home/pi/
```

**Alternative method using USB drive:**
1. Copy the package file to a USB drive
2. Insert USB drive into Raspberry Pi
3. Copy file from USB to Pi's home directory

---

### Part 3: Installation (on Raspberry Pi)

#### Step 6: Connect to Raspberry Pi
```bash
# SSH into your Raspberry Pi
ssh pi@192.168.1.100
```

#### Step 7: Prepare Installation Directory
```bash
# Create application directory
sudo mkdir -p /opt/gtach

# Set ownership to pi user
sudo chown pi:pi /opt/gtach
```

#### Step 8: Extract and Install the Package
```bash
# Navigate to home directory where package was copied
cd /home/pi

# Extract the package
tar -xzf gtach-pi-deployment-*.tar.gz

# Navigate into extracted directory
cd gtach-pi-deployment-*

# Run the installation script
sudo chmod +x install.sh
sudo ./install.sh
```

**What the installer does:**
- Copies application files to `/opt/gtach/`
- Installs Python dependencies
- Sets up proper file permissions
- Creates systemd service (if configured)

#### Step 9: Verify Installation
```bash
# Check if files were installed
ls -la /opt/gtach/

# Try running the application
cd /opt/gtach
python3 main.py --help
```

---

### Part 4: Configuration and Service Setup

#### Step 10: Configure for Your Hardware
```bash
# Edit configuration for your specific setup
nano /opt/gtach/config/platform_config.json

# Make sure GPIO and display settings match your hardware
```

#### Step 11: Start the Application Service
```bash
# If systemd service was created during installation
sudo systemctl enable gtach
sudo systemctl start gtach

# Check service status
sudo systemctl status gtach
```

#### Step 12: Test Basic Functionality
```bash
# Check application logs
sudo journalctl -u gtach -f

# Or check log files directly
tail -f /opt/gtach/logs/session_*.log
```

---

### Part 5: Verification and Troubleshooting

#### Step 13: Verify Hardware Interfaces
```bash
# Test GPIO functionality (if your hardware supports it)
cd /opt/gtach
python3 -c "from src.obdii.utils.platform import get_platform_info; print(get_platform_info())"

# Should show Pi-specific capabilities
```

#### Step 14: Run Application Tests
```bash
# Run the test suite on the Pi to verify everything works
cd /opt/gtach
python3 -m pytest src/tests/ -v

# All tests should pass on the Pi as well
```

---

### Part 6: Updates (Future Deployments)

#### For Future Updates:

##### Step 15: Create New Package (on Development Machine)
```bash
# Update version number in your code first
# Then create new package
cd /path/to/your/GTach/src/provisioning
python create_package.py
```

##### Step 16: Deploy Update (on Pi)
```bash
# The system automatically creates backups before updates
# Copy new package to Pi and extract
tar -xzf gtach-pi-deployment-NEW_VERSION.tar.gz
cd gtach-pi-deployment-NEW_VERSION

# Run update installation
sudo ./install.sh
```

---

### Quick Command Summary

**On Development Machine (Packaging):**
```bash
cd /path/to/your/GTach
python -m pytest src/tests/ -v                    # Verify tests pass
cd src/provisioning && python create_package.py    # Create package
scp ../../packages/gtach-*.tar.gz pi@PI_IP:/home/pi/  # Transfer to Pi
```

**On Pi (Installation):**
```bash
tar -xzf gtach-*.tar.gz                          # Extract package
cd gtach-* && sudo ./install.sh                  # Install
sudo systemctl start gtach                       # Start service
sudo systemctl status gtach                      # Check status
```

---

### Common Issues and Solutions

**Problem:** Permission denied during installation  
**Solution:** Make sure you're using `sudo` for installation commands

**Problem:** Package not found error  
**Solution:** Verify the package was transferred correctly and filename matches

**Problem:** GPIO not working  
**Solution:** Check that SPI/I2C interfaces are enabled in `raspi-config`

**Problem:** Service won't start  
**Solution:** Check logs with `sudo journalctl -u gtach -f` for error messages

**Problem:** Tests fail on Pi  
**Solution:** Ensure all Python dependencies installed correctly with `pip3 list`

---

## Step-by-Step Guide: Creating a GitHub Release for GTach Application

### Prerequisites

Before creating a release, ensure you have:
- All changes committed and pushed to the main branch
- All 143 tests passing
- Documentation updated (README, changelogs, etc.)
- Version numbers updated in code
- Package created and tested per the installation guide

---

### Part 1: Prepare for Release

#### Step 1: Verify Project Status
```bash
# Navigate to project directory
cd /path/to/your/GTach

# Ensure all changes are committed
git status

# Should show: "nothing to commit, working tree clean"
```

#### Step 2: Run Final Tests
```bash
# Run complete test suite
python -m pytest src/tests/ -v

# Verify all 143 tests pass
# Fix any failing tests before proceeding
```

#### Step 3: Update Version Information
```bash
# Update version in key files (if not already done)
# src/provisioning/__init__.py
# src/obdii/__init__.py (if exists)
# pyproject.toml or setup.py

# Example version: "1.0.0" for first release
```

#### Step 4: Create Release Package
```bash
# Create deployment package for the release
cd src/provisioning
python create_package.py

# Verify package creation
ls -la ../../packages/
```

---

### Part 2: Commit Final Changes

#### Step 5: Commit Version Updates
```bash
# Add all updated files
git add .

# Commit with descriptive message
git commit -m "Release v1.0.0: Initial GTach application release

- Complete provisioning system with 143 passing tests
- Cross-platform development support (Mac/Pi)
- Hyperpixel Round display integration
- Protocol-compliant documentation
- Deployment package system with rollback capability"

# Push to GitHub
git push origin main
```

---

### Part 3: Create GitHub Release

#### Step 6: Navigate to GitHub Repository
1. Open web browser
2. Go to: `https://github.com/yourusername/GTach`
3. Log in if not already authenticated

#### Step 7: Start Release Creation
1. Click on **"Releases"** in the right sidebar
   - Or go directly to: `https://github.com/yourusername/GTach/releases`
2. Click **"Create a new release"** button

#### Step 8: Configure Release Details

##### Tag Version
1. In **"Choose a tag"** field, type: `v1.0.0`
2. Select **"Create new tag: v1.0.0 on publish"**

##### Release Title
```
GTach v1.0.0 - Initial Release
```

##### Release Description
```markdown
# GTach v1.0.0 - Initial Release

## Overview
First stable release of GTach - Hyperpixel Round Display Application for Raspberry Pi with cross-platform development support.

## Features
- ✅ Complete provisioning system for deployment automation
- ✅ Cross-platform development (Multi-platform → Raspberry Pi)
- ✅ Hyperpixel 2.1" Round display integration (480x480)
- ✅ Protocol-driven development with AI coordination
- ✅ 143 comprehensive tests with 100% success rate
- ✅ Safe update mechanism with automatic rollback
- ✅ Thread-safe operations with comprehensive logging

## Hardware Support
- **Target Platform**: Raspberry Pi (any compatible model)
- **Display**: Pimoroni Hyperpixel 2.1" Round (480x480 pixels)
- **Development**: Any modern development machine with display simulation
- **Touch Support**: Capacitive multi-touch with Python library

## Installation

### Quick Install (Recommended)
Follow the complete step-by-step guide in the README.md

### Manual Package Installation
1. Download `gtach-pi-deployment-v1.0.0.tar.gz` from release assets
2. Transfer to Raspberry Pi: `scp gtach-*.tar.gz pi@PI_IP:/home/pi/`
3. Extract and install: `tar -xzf gtach-*.tar.gz && cd gtach-* && sudo ./install.sh`

## What's Included
- Complete source code with provisioning system
- Installation scripts for Raspberry Pi deployment
- Configuration templates for cross-platform operation
- Comprehensive test suite (143 tests)
- Protocol documentation and hardware guides
- Development tools and AI coordination materials

## System Requirements

### Development Environment
- Modern development machine (Mac, Linux, or Windows)
- Python 3.9+
- Git and development dependencies

### Deployment Environment  
- Raspberry Pi with Raspberry Pi OS
- Pimoroni Hyperpixel 2.1" Round display
- Python 3.9+
- 1GB+ available storage

## Testing Status
- **Unit Tests**: 143/143 passing ✅
- **Cross-Platform**: Multi-platform compatibility verified ✅
- **Hardware Integration**: Hyperpixel display validated ✅
- **Deployment**: Package installation tested ✅

## Documentation
- Complete installation guide in README.md
- Hardware setup documentation in `doc/hardware/`
- Protocol documentation in `doc/protocol/`
- API documentation in source code

## Known Issues
- None reported for v1.0.0

## Breaking Changes
- Initial release - no previous versions

## Contributors
- Project Lead - Lead Developer
- Claude AI - Development assistance and coordination

## Support
For issues, questions, or contributions:
- Create an issue on GitHub
- Follow the development protocols in `doc/protocol/`
- Refer to troubleshooting guide in README.md

---

**Full Changelog**: Initial release
```

#### Step 9: Upload Release Assets

1. Click **"Attach binaries by dropping them here or selecting them"**
2. Upload the deployment package from `packages/` directory:
   - `gtach-pi-deployment-v1.0.0-YYYYMMDD_HHMMSS.tar.gz`
3. Optionally upload additional files:
   - `README.md` (standalone copy)
   - `CHANGELOG.md` (if you have one)
   - Hardware documentation PDFs

#### Step 10: Configure Release Options

##### Release Type
- ✅ **Set as the latest release** (checked)
- ⬜ **Set as a pre-release** (unchecked for stable release)

##### Discussion
- ✅ **Create a discussion for this release** (optional but recommended)

---

### Part 4: Publish and Verify

#### Step 11: Publish Release
1. Review all information for accuracy
2. Click **"Publish release"** button
3. Wait for GitHub to process the release

#### Step 12: Verify Release
1. Check that release appears at: `https://github.com/yourusername/GTach/releases`
2. Verify download links work for attached assets
3. Confirm tag was created: `https://github.com/yourusername/GTach/tags`

#### Step 13: Test Release Download
```bash
# Test downloading the release
curl -L -o gtach-v1.0.0.tar.gz \
  https://github.com/yourusername/GTach/releases/download/v1.0.0/gtach-pi-deployment-v1.0.0-*.tar.gz

# Verify file integrity
tar -tzf gtach-v1.0.0.tar.gz | head -10
```

---

### Part 5: Post-Release Activities

#### Step 14: Update Project Documentation
```bash
# Update any references to "development version" in docs
# Update installation instructions to reference the release
# Commit documentation updates

git add .
git commit -m "docs: Update documentation for v1.0.0 release"
git push origin main
```

#### Step 15: Announce Release (Optional)
- Update project README with release badge
- Notify users/stakeholders
- Create social media posts if applicable
- Update any external documentation

#### Step 16: Prepare for Next Development Cycle
```bash
# Bump version for next development cycle
# Update version to "1.1.0-dev" or similar in code
# Create development branch if needed

git checkout -b develop
# Make version updates for next cycle
git commit -m "chore: Bump version for v1.1.0 development"
git push origin develop
```

---

### Quick Command Summary

**Pre-Release:**
```bash
cd /path/to/your/GTach
python -m pytest src/tests/ -v                    # Verify tests pass
cd src/provisioning && python create_package.py    # Create package
git add . && git commit -m "Release v1.0.0: ..."  # Commit
git push origin main                               # Push to GitHub
```

**GitHub Web Interface:**
1. Go to GitHub → Releases → Create a new release
2. Tag: `v1.0.0`, Title: `GTach v1.0.0 - Initial Release`
3. Add release description with features and installation info
4. Upload deployment package from `packages/` directory
5. Publish release

**Post-Release:**
```bash
curl -L -o test-download.tar.gz RELEASE_URL        # Test download
git commit -m "docs: Update for v1.0.0 release"   # Update docs
git push origin main                               # Push updates
```

---

### Release Versioning Guidelines

**Version Format:** `vMAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

#### Stable Release Versions
- **MAJOR** (1.x.x): Breaking changes, major feature additions
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, small improvements

#### Pre-Stable Release Development Versions

**Development Phases:**
- **alpha** - Early development, major features incomplete, unstable
- **beta** - Feature complete, testing phase, may have bugs
- **rc** (release candidate) - Stable, final testing before release

**Pre-Release Format Examples:**
- `v0.1.0-alpha.1` - First alpha of initial development
- `v0.2.0-alpha.3` - Third alpha with new features
- `v0.3.0-beta.1` - First beta, feature complete
- `v0.3.0-beta.2` - Second beta with bug fixes
- `v0.3.0-rc.1` - First release candidate
- `v0.3.0-rc.2` - Second release candidate
- `v1.0.0` - First stable release

**Development Branch Versions:**
- `v0.1.0-dev` - Active development on main branch
- `v0.2.0-dev+build.123` - Development with build metadata

#### Version Progression Examples

**Pre-1.0 Development Cycle:**
```
v0.1.0-alpha.1    # Initial prototype
v0.1.0-alpha.2    # Core features added
v0.2.0-alpha.1    # Major feature milestone
v0.3.0-beta.1     # Feature freeze, testing begins
v0.3.0-beta.2     # Bug fixes
v0.3.0-rc.1       # Release candidate
v0.3.0-rc.2       # Final fixes
v1.0.0            # First stable release
```

**Post-1.0 Development:**
```
v1.0.0            # Stable release
v1.1.0-alpha.1    # Next feature development
v1.1.0-beta.1     # Feature testing
v1.1.0-rc.1       # Release candidate
v1.1.0            # Next stable release
v1.1.1            # Bug fix release
v2.0.0-alpha.1    # Breaking changes development
```

#### Pre-Release GitHub Release Guidelines

**Alpha Releases:**
- Mark as **pre-release** ✅
- Include warning about instability
- Limited distribution for developers only
- Tag format: `v0.x.x-alpha.x`

**Beta Releases:**
- Mark as **pre-release** ✅
- Include testing instructions
- Broader testing community access
- Tag format: `v0.x.x-beta.x`

**Release Candidates:**
- Mark as **pre-release** ✅
- Production-like testing
- Final validation before stable
- Tag format: `v0.x.x-rc.x`

**Development Builds:**
- Mark as **pre-release** ✅
- Automated or frequent releases
- Internal use only
- Tag format: `v0.x.x-dev` or `v0.x.x-dev+build.x`

---

This comprehensive guide provides complete deployment and release procedures for the GTach application, ensuring reliable installation and professional release management.

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
