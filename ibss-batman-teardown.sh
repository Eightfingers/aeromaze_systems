#!/bin/bash
set -e

IFACE="wlo1"

# 1. Stop BATMAN virtual interface
sudo ip link set bat0 down 2>/dev/null || true

# 2. Detach interface from BATMAN
sudo batctl if del "$IFACE" 2>/dev/null || true

# 3. Clear IPs from BATMAN and Wi-Fi interfaces
sudo ip addr flush dev bat0 2>/dev/null || true
sudo ip addr flush dev "$IFACE" 2>/dev/null || true

# 4. Return interface to normal Wi-Fi client mode
sudo ip link set "$IFACE" down
sudo iw dev "$IFACE" set type managed
sudo ip link set "$IFACE" up

# 5. Give control back to normal networking services
sudo systemctl start NetworkManager
sudo systemctl start wpa_supplicant
sudo nmcli dev set "$IFACE" managed yes
