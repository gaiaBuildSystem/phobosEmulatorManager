using Slint;
using AppWindow;
using Torizon.Shell;

var win = new Window();

var startEmulatorFunc = (int ram, int storage, int instances) => {
    var bin_path = AppContext.BaseDirectory;

    win.RunOnUiThread(() => {
        win.runningMessage = "Downloading emulator image ...";
    });

    Exec.Bash(
        $"cd {bin_path}/assets && " +
        $"RAM={ram} " +
        $"STORAGE={storage} " +
        $"INSTANCES={instances} " +
        $"docker compose pull emulator"
    );

    win.RunOnUiThread(() => {
        win.runningMessage = "Running ...";
    });

    Exec.Bash(
        $"cd {bin_path}/assets && " +
        $"RAM={ram} " +
        $"STORAGE={storage} " +
        $"INSTANCES={instances} " +
        $"docker compose run --rm --service-ports emulator"
    );

    win.RunOnUiThread(() => {
        win.runningMessage = "Cleaning up emulator resources ...";
    });

    Exec.Bash($"cd {bin_path}/assets && docker compose down");

    win.RunOnUiThread(() => {
        win.running = false;
    });
};

win.StartEmulator = () => {
    Console.WriteLine("Starting Emulator");

    var rs = (int)win.ramSize;
    var ss = (int)win.storageSize;
    var iss = (int)win.instances;

    new Thread(() => {
        startEmulatorFunc(
            rs,
            ss,
            iss
        );
    }).Start();
};

// for some reason, the window size is not being set correctly
// so we set it after a delay
Slint.Timer.Start(TimerMode.SingleShot, 1000, () => {
    win.RunOnUiThread(() => {
        win.Width = 600;
        win.Height = 680;
    });
});

win.Run();
