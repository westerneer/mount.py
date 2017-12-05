#!/usr/bin/env python

# Original author: Christian Vallentin <mail@vallentinsource.com>
# Updated by: Akos Rajtmar <akos@rajtmar.hu>
# Website: https://rajtmar.hu
# Repository: https://github.com/westerneer/mount.py
#
# Date Created: March 25, 2016
# Last Modified: December 06, 2017
#
# Developed and tested using Python 3.5.1

import os
import subprocess
import re

def list_media_devices():
	# If the major number is 8, that indicates it to be a disk device.
	#
	# The minor number is the partitions on the same device:
	# - 0 means the entire disk
	# - 1 is the primary
	# - 2 is extended
	# - 5 is logical partitions
	# The maximum number of partitions is 15.
	#
	# Use `$ sudo fdisk -l` and `$ sudo sfdisk -l /dev/sda` for more information.
	with open("/proc/partitions", "r") as f:
		devices = []
		
		for line in f.readlines()[2:]: # skip header lines
			words = [ word.strip() for word in line.split() ]
			minor_number = int(words[1])
			device_name = words[3]
			
			if (minor_number % 16) == 0:
				path = "/sys/class/block/" + device_name
				
				if os.path.islink(path):
					if os.path.realpath(path).find("/usb") > 0:
						devices.append("/dev/" + device_name)
		
		return devices


def get_device_name(device):
	return os.path.basename(device)

def get_device_block_path(device):
	return "/sys/block/%s" % get_device_name(device)

def get_media_path(device):
	return "/media/" + get_device_name(device)

def get_mountpoint(partition):
	if not is_mounted(partition):
		return False
	return subprocess.check_output("df %s" % partition, shell=True).decode().splitlines()[1].split()[5]

def get_partitions(device):
	partitions = []
	for p in subprocess.check_output("fdisk -l %s" % device, shell=True).decode().splitlines():
		result = re.search('/dev/[a-z]+[0-9]+',p)
		if result:
			partitions.append(result.group(0))
	return partitions


def is_mounted(partition):
	for line in subprocess.check_output("df %s" % partition, shell=True).decode().splitlines():
		if re.search(partition, line):
			 return True
	return False


def mount_partition(partition, name=None):
	if not name:
		path = get_media_path(partition)
	else:
		path = get_media_path(name)
	if not is_mounted(partition):
		os.system("mkdir -p %s" % path)
		os.system("mount %s %s" % (partition, path))

def unmount_partition(partition):
	if is_mounted(partition):
		folder = get_mountpoint(partition)
		os.system("umount %s" % partition)
		os.system("rmdir %s" % folder)


def mount_all(device):
	partitions = get_partitions(device)
	for partition in partitions:
		name = get_device_name(partition)
		mount_partition(partition, name)

def unmount_all(device):
	partitions = get_partitions(device)
	for partition in partitions:
		unmount_partition(partition)


def is_removable(device):
	path = get_device_block_path(device) + "/removable"
	
	if os.path.exists(path):
		with open(path, "r") as f:
			return f.read().strip() == "1"
	
	return None


def get_size(device):
	path = get_device_block_path(device) + "/size"
	
	if os.path.exists(path):
		with open(path, "r") as f:
			# Multiply by 512, as Linux sectors are always considered to be 512 bytes long
			# Resource: https://git.kernel.org/cgit/linux/kernel/git/torvalds/linux.git/tree/include/linux/types.h?id=v4.4-rc6#n121
			return int(f.read().strip()) * 512
	
	return -1

def get_label(device):
	return subprocess.check_output("lsblk --output LABEL %s" % device, shell=True).decode().splitlines()[2]

def get_model(device):
	path = get_device_block_path(device) + "/device/model"
	
	if os.path.exists(path):
		with open(path, "r") as f:
			return f.read().strip()
	return None

def get_vendor(device):
	path = get_device_block_path(device) + "/device/vendor"
	
	if os.path.exists(path):
		with open(path, "r") as f:
			return f.read().strip()
	return None


if __name__ == "__main__":
	devices = list_media_devices()
	
	for device in devices:
		mount_all(device)
		
		print("Drive:", get_device_name(device))
		print("Mounted:", "Yes" if is_mounted(device) else "No")
		print("Removable:", "Yes" if is_removable(device) else "No")
		print("Size:", get_size(device), "bytes")
		print("Size:", "%.2f" % (get_size(device) / 1024 ** 3), "GB")
		print("Model:", get_model(device))
		print("Vendor:", get_vendor(device))
		print(" ")
		
		unmount_all(device)
