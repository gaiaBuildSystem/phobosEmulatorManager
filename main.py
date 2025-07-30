import os
import json
import subprocess
import concurrent.futures
import slint # type: ignore
from slint import Timer, TimerMode, ListModel # type: ignore
from datetime import timedelta

# get the script path
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

# load the components using load_file to set the style
app_components = slint.load_file("./ui/AppWindow.slint", style="fluent-dark")
class App(app_components.AppWindow): # type: ignore


    def exec_bash(self, command):
        future = self.__executor.submit(self.__run_command, command)
        return future


    def __run_command(self, command):
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            executable="/bin/bash",
            env=os.environ
        )

        return result


    def ___init(self):
        # we are good to go
        self.__init()

        # for some reason the ListModel does not work
        # if early initialized
        # so we need to do it here
        self.emulatorList = ListModel([])

        # let's already populate the emulator list
        if os.path.exists(os.path.join(os.path.expanduser("~"), ".pem", "emulators.json")):
            with open(os.path.join(os.path.expanduser("~"), ".pem", "emulators.json"), "r") as f:
                data = json.load(f)
                for key in data.keys():
                    self.emulatorList.append(key)

        self.timer.start(
            TimerMode.SingleShot,
            timedelta(milliseconds=100),
            self.__check_auto_test
        )


    def __auto_close(self):
        self.hide()


    def __check_auto_test(self):
        if "PHOBOS_EMULATOR_TEST" in os.environ and os.environ["PHOBOS_EMULATOR_TEST"] == "1":
            self.timer.start(
                TimerMode.SingleShot,
                timedelta(milliseconds=10000),
                self.__auto_close
            )


    def __on_load(self):
        self.Width = 600
        self.Height = 800

        self.timer.start(
            TimerMode.SingleShot,
            timedelta(milliseconds=100),
            self.___init
        )


    def __init__(self):
        super().__init__()

        self.canCreateInstances = False
        self.Width = 599
        self.Height = 779
        self.storageSize = 8
        self.ramSize = 4
        self.instances = 1
        self.running = False
        self.settled = False
        self.runningMessage = "Running ..."
        self.messageFooterText = "Emulator is not running"
        self.messageFooterLevel = "warn"
        self.backDeg = 40
        # Slint public function
        self.__init = getattr(self, "__init")

        # for futures
        self.__future = None
        self.__executor = concurrent.futures.ThreadPoolExecutor()
        # status flags
        self.__pulling = False
        self.__starting = False
        self.__cleaning = False
        self.__debugging = False

        # when setting the emulator name
        self.__emulatorName = None

        # timer
        self.timer = Timer()
        self.timer.start(
            TimerMode.SingleShot,
            timedelta(milliseconds=100),
            self.__on_load
        )


    def __status_handle(self):
        if self.__pulling:
            if self.__future.done():
                self.__pulling = False
                self.__starting = True
                self.runningMessage = "RUNNING ..."
                self.settled = True

                self.__future = self.exec_bash(
                    f"""
                    cd {SCRIPT_PATH}/assets && \
                    RAM={self.ramSize} \
                    STORAGE={self.storageSize} \
                    INSTANCES={self.instances} \
                    USER_VM_NAME={self.__emulatorName} \
                    docker compose run --rm --service-ports -it emulator
                    """
                )

        if self.__starting:
            if self.__future.done():
                self.__starting = False
                self.__cleaning = True
                self.settled = False
                self.runningMessage = "Cleaning up emulator resources ..."

                self.__future = self.exec_bash(
                    f"""
                    cd {SCRIPT_PATH}/assets && \
                    docker compose down
                    """
                )

        if self.__cleaning:
            if self.__future.done():
                self.__cleaning = False
                self.running = False
                self.__executor.shutdown()
                self.__executor = concurrent.futures.ThreadPoolExecutor()
                self.timer.stop()

        if self.__debugging:
            self.__debugging = False
            self.__pulling = False
            self.__starting = True
            self.runningMessage = "RUNNING ..."
            self.settled = True

            self.__future = self.exec_bash(
                    f"""
                    cd {SCRIPT_PATH}/assets && \
                    RAM={self.ramSize} \
                    STORAGE={self.storageSize} \
                    INSTANCES={self.instances} \
                    PHOBOS_LOCAL_IMG_PATH={os.environ['PHOBOS_LOCAL_IMG_PATH']} \
                    docker compose run --rm --service-ports -it emulator-debug
                    """
                )


    @slint.callback
    def startEmulator(self):
        if 'PHOBOS_LOCAL_IMG_PATH' not in os.environ or os.environ['PHOBOS_LOCAL_IMG_PATH'] == "/dev/null":
            self.__pulling = True
            self.runningMessage = "Downloading emulator image ..."

            self.__future = self.exec_bash(
                f"""
                cd {SCRIPT_PATH}/assets && \
                RAM={self.ramSize} \
                STORAGE={self.storageSize} \
                INSTANCES={self.instances} \
                USER_VM_NAME={self.__emulatorName} \
                docker compose pull emulator
                """
            )
        else:
            # if the PHOBOS_LOCAL_IMG_PATH is set, we are in debug mode
            # and we need to run the emulator-debug image
            self.__debugging = True

        self.timer.start(
            TimerMode.Repeated,
            timedelta(milliseconds=500),
            self.__status_handle
        )


    @slint.callback
    def runStoredEmulator(self, name: str):
        print(f"Running stored emulator with name [{name}] ...")
        self.__emulatorName = name

        self.__pulling = True
        self.runningMessage = "Downloading emulator image ..."

        self.__future = self.exec_bash(
            f"""
            cd {SCRIPT_PATH}/assets && \
            RAM={self.ramSize} \
            STORAGE={self.storageSize} \
            INSTANCES={self.instances} \
            USER_VM_NAME={self.__emulatorName} \
            docker compose pull emulator
            """
        )

        self.timer.start(
            TimerMode.Repeated,
            timedelta(milliseconds=500),
            self.__status_handle
        )

        return True


    @slint.callback
    def storeEmulator(self, name: str) -> bool:
        print(f"Storing emulator image [{name}] ...")

        # multiple instances cannot be stored
        if self.instances > 1:
            print("Multiple instances cannot be stored.")
            self.messageFooterLevel = "error"
            self.messageFooterText = "Multiple instances cannot be stored."
            return False

        # if the HOME/.pem/ does not exists create it
        if not os.path.exists(os.path.join(os.path.expanduser("~"), ".pem")):
            os.makedirs(os.path.join(os.path.expanduser("~"), ".pem"))

        # check if the HOME/.pem/emulators.json file exists
        if not os.path.exists(os.path.join(os.path.expanduser("~"), ".pem", "emulators.json")):
            # create the file
            with open(os.path.join(os.path.expanduser("~"), ".pem", "emulators.json"), "w") as f:
                f.write("{}\n")

        # read the file
        with open(os.path.join(os.path.expanduser("~"), ".pem", "emulators.json"), "r+") as f:
            data = json.load(f)
            # check if the name already exists
            for key in data.keys():
                if key == name:
                    print(f"Emulator image [{name}] already exists.")
                    self.messageFooterLevel = "error"
                    self.messageFooterText = f"Emulator image with name [{name}] already exists."
                    return False

            # ok seems like we are good to go
            # store it as a new entry
            data[name] = {
                "storage": self.storageSize,
                "ram": self.ramSize
            }

            # write the file
            f.seek(0)
            f.write(json.dumps(data, indent=4))
            f.truncate()
            print(f"Emulator image [{name}] stored.")
            self.emulatorList.append(name)

        return True


    @slint.callback
    def rmStoredEmulator(self, name: str) -> bool:
        print(f"Removing stored emulator with name [{name}]")

        for i, item in enumerate(self.emulatorList):
            if item == name:
                # remove it from the json
                with open(os.path.join(os.path.expanduser("~"), ".pem", "emulators.json"), "r+") as f:
                    data = json.load(f)
                    del data[name]
                    # write it back
                    f.seek(0)
                    f.write(json.dumps(data, indent=4))
                    f.truncate()
                    print(f"Emulator image [{name}] removed.")
                    del self.emulatorList[i]

                # also remove the ~/.pem/phobos-name.img file
                if os.path.exists(os.path.join(os.path.expanduser("~"), ".pem", f"phobos-{name}.img")):
                    os.remove(os.path.join(os.path.expanduser("~"), ".pem", f"phobos-{name}.img"))
                    print(f"Emulator image file [{name}] removed.")

                return True

        return False


# instantiate the app and start the event loop
app = App()
app.run()
