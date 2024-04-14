#!/bin/bash

VERSION="0.0.2"

echo "Installing Torizon Emulator Manager ..."

sudo apt-get install libicu72 zlib1g unzip
wget https://github.com/microhobby/torizonEmulatorManager/releases/download/$VERSION/Torizon-Emulator-Manager-$VERSION.zip
sudo mkdir -p /opt/torizon-emulator-manager
sudo unzip Torizon-Emulator-Manager-$VERSION.zip -d /opt/torizon-emulator-manager
sudo ln -s /opt/torizon-emulator-manager/bin/Release/net8.0/linux-x64/publish/torizonEmulatorManager /usr/bin/torizon-emulator-manager

echo "Now run torizon-emulator-manager command to start the application."
