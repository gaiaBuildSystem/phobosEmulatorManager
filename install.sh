#!/bin/bash

echo "📦 Installing Torizon Emulator Manager ..."

echo "🔑 we need sudo permissions"
sudo echo "🔓 sudo permissions granted"

wget -O /tmp/torizon-emulator-manager \
    https://gitlab.com/commontorizon/torizonEmulatorManager/-/jobs/artifacts/main/raw/torizon-emulator-manager?job=build-docker-image
wget -O /tmp/docker-compose.yml \
    https://gitlab.com/commontorizon/torizonEmulatorManager/-/jobs/artifacts/main/raw/docker-compose.yml?job=build-docker-image

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
