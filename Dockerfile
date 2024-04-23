# ARGUMENTS --------------------------------------------------------------------
##
# Board architecture
##
ARG IMAGE_ARCH=

##
# Base container version
##
ARG SDK_BASE_VERSION=4-8.0-rc
ARG BASE_VERSION=next

##
# Directory of the application inside container
##
ARG APP_ROOT=

##
# Board GPU vendor prefix
##
ARG GPU=

# ARGUMENTS --------------------------------------------------------------------



# BUILD ------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS Build

ARG IMAGE_ARCH
ARG APP_ROOT

ENV RUST_BACKTRACE=1

# this is needed for the build to work witht he libslint

# FIXME: for now we need to use the xvfb-run to avoid the backend to crash
#        this is a workaround and should be fixed in the future,
#        I think that for interpret the .slint should not be needed to have
#        a display server running. But we work with what we have.
RUN apt-get -q -y update && \
    apt-get -q -y install \
    libfontconfig1 \
    mesa-utils \
    x11-xserver-utils \
    libxkbcommon-x11-0 \
    libfontconfig1 \
	libfreetype6 \
	libgbm1 \
	libinput10 \
	libxkbcommon0 \
    xkb-data \
    xvfb

COPY . /build
WORKDIR /build

RUN dotnet restore && \
    xvfb-run dotnet publish -c Release -r linux-${IMAGE_ARCH} && \
    # we need to move the output to the correct folder
    if [ "${IMAGE_ARCH}" = "amd64" ]; then \
        mv /build/bin/Release/net8.0/linux-x64 /build/bin/Release/net8.0/linux-amd64 ; \
    fi

# BUILD ------------------------------------------------------------------------



# DEPLOY ------------------------------------------------------------------------
FROM --platform=linux/${IMAGE_ARCH} \
    torizon/wayland-base${GPU}:${BASE_VERSION} AS Deploy

ARG IMAGE_ARCH
ARG GPU
ARG APP_ROOT

# for vivante GPU we need some "special" sauce
RUN apt-get -q -y update && \
        if [ "${GPU}" = "-vivante" ] || [ "${GPU}" = "-imx8" ]; then \
            apt-get -q -y install \
            imx-gpu-viv-wayland-dev \
        ; else \
            apt-get -q -y install \
            libgl1 \
        ; fi \
    && \
    apt-get clean && apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

# Install Slint dependencies
# Install Slint and .net dependencies
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install \
    libicu72 zlib1g unzip \
    libfontconfig1 \
    mesa-utils \
    x11-xserver-utils \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libfreetype6 \
    libgbm1 \
    libinput10 \
    libxkbcommon0 \
    xkb-data \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get -y update && apt-get install -y --no-install-recommends \
# DO NOT REMOVE THIS LABEL: this is used for VS Code automation
    # __torizon_packages_prod_start__
    # __torizon_packages_prod_end__
# DO NOT REMOVE THIS LABEL: this is used for VS Code automation
	&& apt-get clean && apt-get autoremove && rm -rf /var/lib/apt/lists/*

# use docker tools
COPY --from=docker:dind /usr/local/bin/docker /usr/local/bin/
COPY --from=docker:dind /usr/local/libexec/docker/cli-plugins /usr/local/lib/docker/cli-plugins

# Default to the Skia backend for best performance
ENV SLINT_BACKEND=winit-skia
# Default style to fluent
ENV SLINT_STYLE=fluent

# Copy the application compiled in the build step to the $APP_ROOT directory
# path inside the container, where $APP_ROOT is the torizon_app_root
# configuration defined in settings.json
COPY --from=Build /build/bin/Release/net8.0/linux-${IMAGE_ARCH}/publish ${APP_ROOT}

# "cd" (enter) into the APP_ROOT directory
WORKDIR ${APP_ROOT}

USER root

# Command executed in runtime when the container starts
CMD ["./torizonEmulatorManager"]

# DEPLOY ------------------------------------------------------------------------
