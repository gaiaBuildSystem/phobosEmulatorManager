# ARGUMENTS --------------------------------------------------------------------
##
# Board architecture
##
ARG IMAGE_ARCH=

##
# Base container version
##
ARG BASE_VERSION=4

##
# Board GPU vendor prefix
##
ARG GPU=

# ARGUMENTS --------------------------------------------------------------------


# DEPLOY ------------------------------------------------------------------------
FROM --platform=linux/${IMAGE_ARCH} \
    torizon/wayland-base${GPU}:${BASE_VERSION} AS Deploy

ARG IMAGE_ARCH
ARG GPU

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
    libicu72 \
    zlib1g \
    unzip \
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
    python3 \
    python3-pip \
    pipenv \
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
ENV SLINT_STYLE=fluent-dark

# Copy the application compiled in the build step to the $APP_ROOT directory
# path inside the container, where $APP_ROOT is the torizon_app_root
# configuration defined in settings.json
COPY ./ui /home/torizon/ui
COPY ./assets /home/torizon/assets
COPY ./main.py /home/torizon
COPY ./Pipfile /home/torizon
COPY ./Pipfile.lock /home/torizon

# "cd" (enter) into the APP_ROOT directory
WORKDIR /home/torizon

# "install"
RUN pipenv sync

USER root

# Command executed in runtime when the container starts
CMD ["pipenv", "run", "python", "main.py"]

# DEPLOY ------------------------------------------------------------------------
