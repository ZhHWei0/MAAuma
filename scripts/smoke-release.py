"""Verify the extracted package with its own runtime, without a game or emulator."""

import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys


def main(root):
    app = root / "MFAAvalonia.exe"
    python = root / "python" / "python.exe"
    dotnet = root / "dotnet"
    native = root / "runtimes" / "win-x64" / "native"
    data = json.loads((root / "interface.json").read_text(encoding="utf-8"))
    agent = data["agent"]
    assert app.is_file() and (root / "Start MaaUma.cmd").is_file()
    assert Path(sys.executable).resolve() == python.resolve()
    assert (root / agent["child_exec"]).resolve() == python.resolve()
    assert not (root / "agent" / ".venv").exists()
    runtimes = subprocess.check_output([str(dotnet / "dotnet.exe"), "--list-runtimes"], encoding="utf-8")
    assert "Microsoft.NETCore.App 10.0." in runtimes
    assert str(dotnet) in runtimes
    print("Bundled .NET and embedded Python found.", flush=True)

    # Use the exact client DLLs supplied with the bundled frontend.
    os.environ["MAAFW_BINARY_PATH"] = str(native)
    with os.add_dll_directory(str(native)):
        from maa.agent_client import AgentClient
        from maa.library import Library
        from maa.resource import Resource

        version_api = Library.framework().MaaVersion
        version_api.restype = ctypes.c_char_p
        version = version_api().decode()
        print(f"MFA native framework: {version}", flush=True)

        resource = Resource()
        for relative in data["resource"][0]["path"]:
            bundle = root / relative
            assert resource.post_bundle(bundle).wait().succeeded, f"Could not load {bundle}"
        print("MaaUma resource and OCR model loaded.", flush=True)

        # Use a loopback-only ephemeral port so the smoke does not write a socket
        # in MaaFramework's fixed C:\Temp directory on the build machine.
        client = AgentClient.create_tcp()
        assert client.identifier and client.set_timeout(15000)
        child_env = dict(os.environ)
        child_env.pop("MAAFW_BINARY_PATH")
        command = [str(python), *agent["child_args"], client.identifier]
        with subprocess.Popen(command, cwd=root, env=child_env, creationflags=subprocess.CREATE_NO_WINDOW) as child:
            try:
                assert client.bind(resource)
                assert client.connect(), f"MaaUma Agent did not connect (exit={child.poll()})"
                assert {
                    "DailyRaceSelectStableNumber",
                    "DailyLegendSelectCard",
                    "DailyLegendConfigureRaceFilter",
                    "RewardDerbySpin",
                }.issubset(client.custom_action_list)
            finally:
                if client.connected:
                    client.disconnect()
                if child.poll() is None:
                    child.terminate()
                child.wait(timeout=10)
        print("Packaged Agent connected and registered the custom actions.", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
