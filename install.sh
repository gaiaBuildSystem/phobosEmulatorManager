#!/bin/bash

echo "📦 Installing PhobOS Emulator Manager ..."

echo "🔑 we need sudo permissions"
sudo echo "🔓 sudo permissions granted"

# check if PHOBOS_EMULATOR_TEST is set, so we nee to download from source
if [ -z "$PHOBOS_EMULATOR_TEST" ]; then
    wget -O /tmp/phobos-emulator-manager \
        https://github.com/gaiaBuildSystem/phobosEmulatorManager/releases/latest/download/phobos-emulator-manager
    wget -O /tmp/docker-compose.yml \
        https://github.com/gaiaBuildSystem/phobosEmulatorManager/releases/latest/download/docker-compose.yml
else
    echo "🧪 Downloading from the repo source to test ..."
    wget -O /tmp/phobos-emulator-manager \
        https://github.com/gaiaBuildSystem/phobosEmulatorManager/raw/refs/heads/main/phobos-emulator-manager
    wget -O /tmp/docker-compose.yml \
        https://github.com/gaiaBuildSystem/phobosEmulatorManager/raw/refs/heads/main/docker-compose.yml
fi

echo "📦 Moving Assets ..."

sudo mkdir -p /opt/phobos-emulator-manager
sudo mv -f /tmp/phobos-emulator-manager /opt/phobos-emulator-manager
sudo mv -f /tmp/docker-compose.yml /opt/phobos-emulator-manager
sudo chmod +x /opt/phobos-emulator-manager/phobos-emulator-manager
sudo ln -sf /opt/phobos-emulator-manager/phobos-emulator-manager /usr/bin/phobos-emulator-manager

echo "🛜  Pre-downloading the image ..."

# get the arch and set the tag accordingly
ARCH=$(uname -m)

if [ "$ARCH" == "x86_64" ]; then
    export TAG="latest"
elif [ "$ARCH" == "aarch64" ]; then
    export TAG="latest"
else
    echo "❌ Unsupported architecture: $ARCH"
    echo "Please run this script on an x86_64 or aarch64 machine."
    exit 1
fi

docker compose -f /opt/phobos-emulator-manager/docker-compose.yml pull

echo "🎉 PhobOS Emulator Manager installed successfully!"
echo "Now run phobos-emulator-manager command to start the application."
