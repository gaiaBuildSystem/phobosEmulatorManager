#!/bin/bash

VERSION="0.0.15"

echo "📦 Installing Torizon Emulator Manager ..."

echo "🔑 we need sudo permissions"
sudo echo "🔓 sudo permissions granted"

wget -O /tmp/torizon-emulator-manager \
    https://github.com/commontorizon/torizonEmulatorManager/releases/download/$VERSION/torizon-emulator-manager
wget -O /tmp/docker-compose.yml \
    https://github.com/commontorizon/torizonEmulatorManager/releases/download/$VERSION/docker-compose.yml

echo "📦 Moving Assets ..."

sudo mkdir -p /opt/torizon-emulator-manager
sudo mv -f /tmp/torizon-emulator-manager /opt/torizon-emulator-manager
sudo mv -f /tmp/docker-compose.yml /opt/torizon-emulator-manager
sudo chmod +x /opt/torizon-emulator-manager/torizon-emulator-manager
sudo ln -sf /opt/torizon-emulator-manager/torizon-emulator-manager /usr/bin/torizon-emulator-manager

echo "🛜  Pre-downloading the image ..."
docker compose -f /opt/torizon-emulator-manager/docker-compose.yml pull

echo "🎉 Torizon Emulator Manager installed successfully!"
echo "Now run torizon-emulator-manager command to start the application."
