#!/bin/bash
set -e

IFACE="wlo1"
SSID="aeromazeibss"
FREQ="2437"
IPADDR="192.168.65.146/24"

echo "[*] Stopping NetworkManager and wpa_supplicant..."
sudo systemctl stop NetworkManager || true
sudo systemctl stop wpa_supplicant || true

echo "[*] Bringing interface down..."
sudo ip link set "$IFACE" down

echo "[*] Switching interface to IBSS (ad-hoc) mode..."
sudo iw "$IFACE" set type ibss

echo "[*] Bringing interface up..."
sudo ip link set "$IFACE" up

echo "[*] Joining IBSS network \"$SSID\" on $FREQ MHz..."
sudo iw "$IFACE" ibss join "$SSID" "$FREQ"

echo "[*] Assigning IP address $IPADDR..."
sudo ip addr add "$IPADDR" dev "$IFACE" || true

echo "[+] IBSS network configured!"
	
