#!/bin/bash

echo "🔍 Checking for required dependencies ..."

_WGET_OK=1
_DOCKER_OK=1
_DOCKER_COMPOSE_OK=0
_DEP_MISSING=0

# check for wget
if ! command -v wget &> /dev/null; then
    _WGET_OK=0
    _DEP_MISSING=1
fi

# check for docker
if ! command -v docker &> /dev/null; then
    _DOCKER_OK=0
    _DEP_MISSING=1
fi

# check for docker compose plugin
if docker compose version &>/dev/null; then
    _DOCKER_COMPOSE_OK=1
else
    _DEP_MISSING=1
fi

# now list for user if some dependencies are missing
echo "wget is $([[ $_WGET_OK -eq 1 ]] && echo "ok" || echo "not ok")"
echo "docker is $([[ $_DOCKER_OK -eq 1 ]] && echo "ok" || echo "not ok")"
echo "docker compose is $([[ $_DOCKER_COMPOSE_OK -eq 1 ]] && echo "ok" || echo "not ok")"

if [ $_DEP_MISSING -eq 1 ]; then
    echo "❌ Some dependencies are missing. Please install them before running this script."
    exit 69
fi

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

if [ ! -f /opt/phobos-emulator-manager/phobos.img ]; then
    # there was never a phobos.img
    # so, make a placeholder file
    touch /opt/phobos-emulator-manager/phobos.img
fi

echo "🎉 PhobOS Emulator Manager installed successfully!"
echo "Now run phobos-emulator-manager command to start the application."
