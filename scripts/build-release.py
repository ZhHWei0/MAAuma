"""Build and verify a self-contained Windows x64 MaaUma distribution."""

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOCK = Path(__file__).with_name("release-dependencies.json")
SMOKE = Path(__file__).with_name("smoke-release.py")


def digest(path, algorithm="sha256"):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def download(cache, name, entry):
    url, check = entry
    algorithm, expected = check.split(":", 1)
    target = cache / name
    if target.is_file() and digest(target, algorithm) == expected:
        return target
    request = urllib.request.Request(url, headers={"User-Agent": "MaaUma-release-builder"})
    for attempt in range(3):
        try:
            with tempfile.NamedTemporaryFile(dir=cache, delete=False) as stream:
                part = Path(stream.name)
                try:
                    with urllib.request.urlopen(request, timeout=60) as source:
                        shutil.copyfileobj(source, stream)
                finally:
                    stream.close()
            if digest(part, algorithm) != expected:
                raise ValueError(f"Checksum mismatch: {name}")
            part.replace(target)
            print(f"Verified {name}", flush=True)
            return target
        except OSError:
            if attempt == 2:
                raise
        finally:
            if 'part' in locals():
                part.unlink(missing_ok=True)


def unpack(archive, destination):
    with zipfile.ZipFile(archive) as src:
        for member in src.infolist():
            path = PurePosixPath(member.filename)
            if (path.is_absolute() or ".." in path.parts or ":" in member.filename
                    or "\\" in member.filename or member.external_attr >> 28 == 0xA):
                raise ValueError(f"Unsafe archive path: {member.filename}")
            if archive.suffix == ".whl" and path.parts[0].endswith(".data"):
                raise ValueError(f"Unexpected wheel installation layout: {member.filename}")
        src.extractall(destination)


def write_zip(source, target, folder_name):
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for path in sorted(source.rglob("*")):
            name = (PurePosixPath(folder_name) / path.relative_to(source).as_posix()).as_posix()
            if path.is_file():
                archive.write(path, name)
            elif path.is_dir() and not any(path.iterdir()):
                archive.mkdir(name)


def assemble(package, dependencies, interface, version):
    unpack(dependencies["mfa-win.zip"], package)
    # MaaFramework's plugin loader checks this directory even when no plugins are used.
    (package / "runtimes" / "win-x64" / "native" / "plugins").mkdir(exist_ok=True)
    for pattern, destination in (
        ("dotnet-runtime.zip", package / "dotnet"),
        ("python-*-embed-amd64.zip", package / "python"),
        ("*.whl", package / "python" / "packages"),
    ):
        matches = sorted(path for path in dependencies.values() if path.match(pattern))
        if not matches:
            raise ValueError(f"No dependencies match {pattern}")
        for path in matches:
            unpack(path, destination)
    # ._pth gives embedded Python an isolated, relative import path (no installed Python or pip).
    (package / "python" / "python312._pth").write_text(
        "python312.zip\n.\npackages\n../agent\n", encoding="ascii"
    )
    shutil.copytree(
        ASSETS / "resource", package / "resource", dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("*.onnx", "keys.txt", "_runtime", "__pycache__"),
    )
    for name in ("det.onnx", "rec.onnx", "keys.txt"):
        shutil.copy2(dependencies[name], package / "resource" / "model" / "ocr" / name)
    shutil.copytree(
        ASSETS / "agent", package / "agent",
        ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc"),
    )
    interface["version"] = version.removeprefix("v")
    interface["agent"]["child_exec"] = "./python/python.exe"
    interface["agent"]["child_args"] = ["-B", "-u", "./agent/main.py"]
    (package / "interface.json").write_text(
        json.dumps(interface, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # The upstream MFA apphost is framework-dependent. Point only this process at our .NET.
    (package / "Start MaaUma.cmd").write_bytes(
        b'@echo off\r\nsetlocal\r\nset "DOTNET_ROOT_X64=%~dp0dotnet"\r\n'
        b'start "" /D "%~dp0." "%~dp0MFAAvalonia.exe"\r\n'
    )
    shutil.copy2(ROOT / "docs" / "quick-start.md", package / "使用说明.md")
    shutil.copy2(ROOT / "LICENSE", package / "LICENSE")
    shutil.copy2(ROOT / "docs" / "third-party.md", package / "THIRD-PARTY.md")
    notices = package / "licenses"
    notices.mkdir(exist_ok=True)
    for name in ("MFAAvalonia-LICENSE.txt", "MaaCommonAssets-LICENSE.txt"):
        shutil.copy2(dependencies[name], notices / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="e.g. v0.1.0 (defaults to interface.json version)")
    parser.add_argument("--cache", type=Path, default=ROOT / "build" / "release-cache")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Run on Windows x64 to validate the packaged Windows runtime")
    interface = json.loads((ASSETS / "interface.json").read_text(encoding="utf-8-sig"))
    version = args.version or ("v" + interface["version"].removeprefix("v"))
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?", version):
        parser.error("Version must look like v0.1.0 or v0.1.0-beta.1")
    cache, output = args.cache.resolve(), args.output.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(LOCK.read_text(encoding="utf-8"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {name: pool.submit(download, cache, name, entry) for name, entry in manifest.items()}
        dependencies = {name: future.result() for name, future in futures.items()}

    # Work in a fresh directory; never package the maintainer's MFA installation.
    label = f"MaaUma-{version}-win-x64"
    with tempfile.TemporaryDirectory(prefix="maauma-", dir=output) as workspace:
        work = Path(workspace)
        package = work / "stage" / label
        package.mkdir(parents=True)
        print("Assembling portable package...", flush=True)
        assemble(package, dependencies, interface, version)
        archive = work / (label + ".zip")
        print("Writing ZIP...", flush=True)
        write_zip(package, archive, label)
        # Verify an actual fresh extraction at a different, non-ASCII path.
        relocated = work / "解压 检查"
        print("Verifying fresh extraction...", flush=True)
        unpack(archive, relocated)
        app = relocated / label
        subprocess.run([str(app / "python" / "python.exe"), "-B", str(SMOKE), str(app)],
                       cwd=app, check=True, timeout=90)
        archive.replace(output / archive.name)

    artifact = output / (label + ".zip")
    (output / (artifact.name + ".sha256")).write_text(
        f"{digest(artifact)}  {artifact.name}\n", encoding="ascii"
    )
    print(f"Built {artifact} ({artifact.stat().st_size / 1024**2:.1f} MiB)")


if __name__ == "__main__":
    main()
