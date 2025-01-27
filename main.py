import os
import subprocess
import concurrent.futures
import slint # type: ignore
from slint import Timer, TimerMode
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

        self.timer.start(
            TimerMode.SingleShot,
            timedelta(milliseconds=100),
            self.__check_auto_test
        )


    def __auto_close(self):
        self.hide()


    def __check_auto_test(self):
        if "TORIZON_EMULATOR_TEST" in os.environ:
            self.timer.start(
                TimerMode.SingleShot,
                timedelta(milliseconds=10000),
                self.__auto_close
            )


    def __on_load(self):
        self.Width = 600
        self.Height = 700

        self.timer.start(
            TimerMode.SingleShot,
            timedelta(milliseconds=500),
            self.___init
        )


    def __init__(self):
        super().__init__()

        self.canCreateInstances = False
        self.Width = 599
        self.Height = 679
        self.storageSize = 8
        self.ramSize = 4
        self.instances = 1
        self.running = False
        self.settled = False
        self.runningMessage = "Running ..."
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

        # timer
        self.timer = Timer()
        self.timer.start(
            TimerMode.SingleShot,
            timedelta(milliseconds=1000),
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
                    docker compose run --rm --service-ports emulator
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


    @slint.callback
    def startEmulator(self):
        self.__pulling = True
        self.runningMessage = "Downloading emulator image ..."

        self.__future = self.exec_bash(
            f"""
            cd {SCRIPT_PATH}/assets && \
            RAM={self.ramSize} \
            STORAGE={self.storageSize} \
            INSTANCES={self.instances} \
            docker compose pull emulator
            """
        )

        self.timer.start(
            TimerMode.Repeated,
            timedelta(milliseconds=500),
            self.__status_handle
        )


# instantiate the app and start the event loop
app = App()
app.run()
