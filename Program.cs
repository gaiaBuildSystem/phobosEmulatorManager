using Slint;
using AppWindow;
using Torizon.Shell;

var win = new Window();

Console.WriteLine("Hello Torizon!");

var startEmulatorFunc = (int ram, int storage, int instances) => {
    Exec.Bash(
        $"cd ./assets && " +
        $"RAM={ram} " +
        $"STORAGE={storage} " +
        $"INSTANCES={instances} " +
        $"docker compose run --rm --service-ports emulator &&" +
        $"docker compose down"
    );
};

win.StartEmulator = () => {
    Console.WriteLine("Starting Emulator");

    startEmulatorFunc(
        int.Parse(win.ramSize.Replace("\"", "")),
        int.Parse(win.storageSize.Replace("\"", "")),
        int.Parse(win.instances.Replace("\"", ""))
    );

    Environment.Exit(0);
};

win.Run();
