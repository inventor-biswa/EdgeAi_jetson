# Jetson Orin Nano 8GB Bring-Up and NVMe Installation Journey

## Objective

Set up a new NVIDIA Jetson Orin Nano 8GB Developer Kit with:

* Latest firmware (QSPI update)
* JetPack 7 / L4T R39.2.0
* Ubuntu 24.04
* NVMe SSD as the primary boot device
* SSH access for remote development

---

## Initial Hardware Configuration

### Hardware

* NVIDIA Jetson Orin Nano 8GB Developer Kit
* 256 GB NVMe SSD
* 64 GB microSD Card
* HDMI Monitor
* USB Keyboard
* Ethernet/WiFi Network

### Software

Downloaded and flashed:

* Jetson Installer ISO (R39.2.0)
* Flashed using Balena Etcher

---

## Phase 1: First Boot Issues

After flashing the installer ISO to the microSD card and booting the Jetson:

### Observed Problems

* Boot entered UEFI Shell
* Installer repeatedly returned to Boot Manager
* System showed firmware mismatch

Firmware versions:

Current Firmware : 36.4.3
Required Firmware : 39.2.0

Messages observed:

* Firmware update required
* Capsule update prepared
* ISO boot loop detected
* Boot Manager looping continuously

The system was unable to complete installation while both the SD card and NVMe SSD were attached.

---

## Phase 2: Firmware Upgrade Investigation

We analyzed:

### Boot Manager

Detected:

* UEFI SD Device
* NVMe SSD
* Network Boot Entries

### Root Cause

The Jetson was still running an older QSPI firmware version (36.4.3) while the installer required R39.2.0.

This caused:

* Firmware update loops
* Installer loops
* Failed boot attempts

---

## Phase 3: Successful Firmware Upgrade

### Action Taken

Removed the NVMe SSD completely.

Rebooted using only:

* Jetson
* SD card containing installer ISO

### Result

Firmware update process finally executed successfully.

Upgrade path:

36.4.3
→
39.2.0

The QSPI firmware was updated on both firmware slots.

This was the critical breakthrough that resolved the installation loop.

---

## Phase 4: Reinstalling NVMe

After firmware upgrade:

### Actions

1. Powered down Jetson.
2. Reinserted NVMe SSD.
3. Booted again from installer SD card.

Installer menu became available:

* Install on NVMe
* Install on USB
* Install on eMMC
* Install on microSD

---

## Phase 5: NVMe Installation

Selected:

Install on NVMe

Installer then:

* Detected SSD correctly
* Partitioned SSD
* Created EFI partitions
* Created root filesystem
* Installed Ubuntu 24.04
* Installed NVIDIA drivers
* Installed JetPack components
* Configured bootloader

Installation completed successfully.

---

## Phase 6: First Successful Boot

System booted into:

Ubuntu 24.04 Desktop

Graphical environment loaded successfully.

Successfully reached:

* GNOME Desktop
* Firefox
* Terminal

The Jetson was now fully operational.

---

## Phase 7: Remote Access Validation

SSH access was configured and verified.

Successfully connected remotely and executed:

* htop
* System monitoring commands
* Storage verification commands

This confirmed remote administration capability.

---

## Final Verification Results

### JetPack Version

cat /etc/nv_tegra_release

Result:

R39.2.0

Meaning:

* JetPack 7 Developer Preview
* L4T R39.2.0
* Ubuntu 24.04

---

### Storage Verification

lsblk

Detected:

* microSD card (119 GB)
* NVMe SSD (238 GB)

---

### Root Filesystem Verification

df -h /

Result:

/dev/nvme0n1p1

This confirms:

The operating system is booting entirely from the NVMe SSD.

The microSD card is no longer serving as the operating system disk.

---

## Final System State

### Firmware

Version: 39.2.0

Status: Updated Successfully

---

### Operating System

Ubuntu 24.04

Status: Installed Successfully

---

### JetPack

JetPack 7 Developer Preview

Status: Installed Successfully

---

### Storage

Primary Boot Device:

256 GB NVMe SSD

Status: Operational

---

### Network

SSH Access:

Working

---

### Desktop Environment

GNOME Desktop:

Working

---

### Remote Development

Terminal Access:

Working

SSH Access:

Working

Ready for:

* Python Development
* Docker
* CUDA
* TensorRT
* OpenCV
* MQTT
* Edge AI Applications
* Computer Vision Workloads
* Full Stack IoT Development

---

## Key Lessons Learned

1. Firmware version mismatch can prevent Jetson installation.
2. QSPI firmware must be upgraded before installing newer JetPack releases.
3. Removing the NVMe SSD allowed the firmware upgrade process to complete successfully.
4. After firmware upgrade, the installer correctly detected and installed Ubuntu onto the SSD.
5. Always verify boot location using:

df -h /

and

lsblk

6. The final confirmation of success is seeing:

/dev/nvme0n1p1 mounted as /

which proves the Jetson is booting from NVMe.

---

## Final Achievement

Successfully transformed a Jetson Orin Nano 8GB Developer Kit from:

* Firmware 36.4.3
* Non-booting installer loops
* Failed installation attempts

into a fully operational system running:

* JetPack 7 (R39.2.0)
* Ubuntu 24.04
* NVMe SSD Boot
* SSH Access
* Graphical Desktop Environment

Ready for Edge AI, Computer Vision, LLMs, CUDA, TensorRT, Docker, and Full-Stack IoT development.
