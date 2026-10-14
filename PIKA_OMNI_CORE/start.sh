#!/bin/bash

# 🎨 Colors for Cyberpunk UI
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear

echo -e "${CYAN}========================================================${NC}"
echo -e "${PURPLE}          PIKA AGI - NEURAL BOOT SEQUENCE               ${NC}"
echo -e "${CYAN}========================================================${NC}"

# 1. Checking Permissions
echo -e "${GREEN}[1/3]${NC} Verifying Hardware Permissions..."
termux-setup-storage

# 2. Cleaning Logs
echo -e "${GREEN}[2/3]${NC} Cleaning old neural logs..."
rm -f /sdcard/pika_ear.m4a
rm -f /sdcard/window_dump.xml

# 3. Igniting Engine
echo -e "${GREEN}[3/3]${NC} Awakening Pika's Consciousness..."
echo -e "${PURPLE}--------------------------------------------------------${NC}"

# Running the server with quiet env mode to keep UI clean
node server.js
