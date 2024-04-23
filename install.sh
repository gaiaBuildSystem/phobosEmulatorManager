#!/bin/bash

VERSION="0.0.8"

echo "📦 Installing Torizon Emulator Manager ..."

wget https://github.com/commontorizon/torizonEmulatorManager/releases/download/$VERSION/torizon-emulator-manager
wget https://github.com/commontorizon/torizonEmulatorManager/releases/download/$VERSION/docker-compose.yml
wget wget https://github.com/commontorizon/torizonEmulatorManager/releases/download/$VERSION/docker-compose.wsl.yml

sudo mkdir -p /opt/torizon-emulator-manager
sudo mv torizon-emulator-manager /opt/torizon-emulator-manager
sudo mv docker-compose.yml /opt/torizon-emulator-manager
sudo chmod +x /opt/torizon-emulator-manager/torizon-emulator-manager
sudo ln -sf /opt/torizon-emulator-manager/torizon-emulator-manager /usr/bin/torizon-emulator-manager

echo "🛜 Downloading the image ..."
docker compose -f /opt/torizon-emulator-manager/docker-compose.yml pull

echo "🎉 Torizon Emulator Manager installed successfully!"
echo "Now run torizon-emulator-manager command to start the application."
