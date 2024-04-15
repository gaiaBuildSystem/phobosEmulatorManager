# Torizon Emulator Manager

![](.doc/image.png)

The Torizon Emulator Manager is a graphical user interface that allows you to configure resources and run virtual machines that run Torizon OS. The Torizon Emulator Manager is based on the QEMU emulator and runs inside a Docker container with the necessary dependencies and leveraging the Docker bridge network to communicate with the external world.

## Installation

> ⚠️ **Warning**: The Torizon Emulator Manager depends on Docker. Make sure you have Docker installed on your host machine before running the Torizon Emulator Manager.

To install the Torizon Emulator Manager, you can run the following command:

```bash
wget -qO- https://github.com/commontorizon/torizonEmulatorManager/releases/download/0.0.4/install.sh | bash
```

The installation script will download the latest version of the Torizon Emulator Manager and add a symbolic link to your system `bin` directory. After the installation, you can run the Torizon Emulator Manager by typing `torizon-emulator-manager` in your terminal.

## Running Multiple Instances

To test fleet of devices, you can run multiple instances of the Torizon OS. Check the `Start Multiple Instances` checkbox and set the number of instances you want to run.

> ⚠️ **Warning**: Running multiple instances may require a lot of resources from your host machine. Make sure you have enough resources available. The manager will allocate the same amount of resources configured in the `Storage Size` and `RAM Size`fields for each instance.
