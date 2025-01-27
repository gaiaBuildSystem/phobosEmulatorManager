#!/bin/bash

echo "📦 Installing Torizon Emulator Manager ..."

echo "🔑 we need sudo permissions"
sudo echo "🔓 sudo permissions granted"

# check if TORIZON_EMULATOR_TEST is set, so we nee to download from source
if [ -z "$TORIZON_EMULATOR_TEST" ]; then
    wget -O /tmp/torizon-emulator-manager \
        https://github.com/commontorizon/torizonEmulatorManager/releases/latest/download/torizon-emulator-manager
    wget -O /tmp/docker-compose.yml \
        https://github.com/commontorizon/torizonEmulatorManager/releases/latest/download/docker-compose.yml
else
    echo "🧪 Downloading from the repo source to test ..."
    wget -O /tmp/torizon-emulator-manager \
        https://github.com/commontorizon/torizonEmulatorManager/raw/refs/heads/main/torizon-emulator-manager
    wget -O /tmp/docker-compose.yml \
        https://github.com/commontorizon/torizonEmulatorManager/raw/refs/heads/main/docker-compose.yml
fi

echo "📦 Moving Assets ..."

sudo mkdir -p /opt/torizon-emulator-manager
sudo mv -f /tmp/torizon-emulator-manager /opt/torizon-emulator-manager
sudo mv -f /tmp/docker-compose.yml /opt/torizon-emulator-manager
sudo chmod +x /opt/torizon-emulator-manager/torizon-emulator-manager
sudo ln -sf /opt/torizon-emulator-manager/torizon-emulator-manager /usr/bin/torizon-emulator-manager

echo "🛜  Pre-downloading the image ..."

# get the arch and set the tag accordingly
ARCH=$(uname -m)

if [ "$ARCH" == "x86_64" ]; then
    export TAG="amd64-v2"
elif [ "$ARCH" == "aarch64" ]; then
    export TAG="arm64-v2"
else
    echo "❌ Unsupported architecture: $ARCH"
    echo "Please run this script on an x86_64 or aarch64 machine."
    exit 1
fi

docker compose -f /opt/torizon-emulator-manager/docker-compose.yml pull

echo "🎉 Torizon Emulator Manager installed successfully!"
echo "Now run torizon-emulator-manager command to start the application."
