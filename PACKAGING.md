# Packaging FlatCAM Plus

This document is for users who clone the repository and want to create their own local distributable build.

FlatCAM Plus is a Python/PyQt application. Build on the target operating system whenever possible:

- build macOS packages on macOS;
- build Linux packages on Linux;
- build Windows packages on Windows.

Cross-compiling GUI Python applications is fragile because PyQt, OpenGL/VisPy, GDAL, Rasterio, and native wheels are platform-specific.

## Shared Preparation

Start from a clean clone:

```bash
git clone https://github.com/thebestgoodguy/FlatCAM-Plus.git
cd FlatCAM-Plus
```

Create the runtime environment:

```bash
uv sync
```

Verify that the application starts before packaging:

```bash
python flatcam.py
```

Install PyInstaller in the same environment:

```bash
python -m pip install pyinstaller
```

Compile translation catalogs before building. The source repository keeps `.po` files, while runtime translation loading uses `.mo` files:

```bash
find locale -name "strings.po" -exec sh -c 'msgfmt "$1" -o "${1%.po}.mo"' sh {} \;
```

If `msgfmt` is not available, install GNU gettext first. On Ubuntu-like systems use `sudo apt install gettext`. On macOS, install it with Homebrew:

```bash
brew install gettext
export PATH="$(brew --prefix gettext)/bin:$PATH"
```

The platform-specific generator scripts below run the translation compilation step automatically when `msgfmt` is available.

## Windows

Install Inno Setup 6 first. With `winget`:

```powershell
winget install JRSoftware.InnoSetup
```

For both GitHub release installers, prepare a 64-bit Python environment and a 32-bit Python environment with the project dependencies installed. PyInstaller must run under the same architecture it is packaging.

If both Python launchers are registered, install PyInstaller in each environment:

```powershell
py -3.14-64 -m pip install pyinstaller
py -3.11-32 -m pip install pyinstaller   # 32-bit stays on 3.11: CPython publishes no 32-bit 3.14
```

Then build each installer from its own batch file:

```powershell
.\FlatCAMPlus_x64_installer_generator.bat
.\FlatCAMPlus_x32_installer_generator.bat
```

If a batch file fails, it keeps the window open and writes a timestamped log under:

```text
build\logs\
```

If the script cannot auto-detect one of the Python environments, pass the paths explicitly:

```powershell
.\FlatCAMPlus_x64_installer_generator.bat -PythonX64 "C:\Path\To\Python-64\python.exe"
.\FlatCAMPlus_x32_installer_generator.bat -PythonX86 "C:\Path\To\Python-32\python.exe"
```

The PyInstaller outputs are created at:

```text
dist\windows\x86\FlatCAMPlus\
dist\windows\x64\FlatCAMPlus\
```

The installer outputs are created at:

```text
dist\installer\FlatCAMPlus-Setup-<version>-x32.exe
dist\installer\FlatCAMPlus-Setup-<version>-x64.exe
```

The 32-bit build folder still uses the internal `x86` name, but the installer filename uses the user-facing `x32` label.

Upload both files to the GitHub release. A checkout launched from source can still ask that release for a newer version and read its body as the changelog; an installed build does not: PyInstaller sets `sys.frozen`, the application does not create its updater, and updating means running the newer installer.

The installer installs to:

```text
%ProgramFiles%\FlatCAMPlus
```

It also creates a Start Menu entry and a desktop shortcut for `FlatCAM Plus` by default. To build only one architecture:

```powershell
.\FlatCAMPlus_x64_installer_generator.bat
.\FlatCAMPlus_x32_installer_generator.bat
```

To only build the PyInstaller folders without creating installers:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows_installer.ps1 -SkipInstaller
```

## macOS

Install Apple command line tools first:

```bash
xcode-select --install
```

Run the one-step DMG generator from the repository root:

```bash
chmod +x FlatCAMPlus_macos_dmg_generator.command packaging/macos/build_macos_dmg.sh
./FlatCAMPlus_macos_dmg_generator.command
```

The script builds the `.app` bundle, creates a local `.icns` icon from the bundled PNG assets, ad-hoc signs the app, and creates a DMG.

The automated outputs are created at:

```text
dist/macos/FlatCAM-Plus.app
dist/installer/FlatCAMPlus-<version>-macOS-<arch>.dmg
```

Useful options:

```bash
./FlatCAMPlus_macos_dmg_generator.command --no-dmg
./FlatCAMPlus_macos_dmg_generator.command --no-sign
./FlatCAMPlus_macos_dmg_generator.command --skip-app
PYTHON_BIN=/path/to/python3 ./FlatCAMPlus_macos_dmg_generator.command
```

For Developer ID signing, set `APPLE_DEVELOPER_ID` before running the generator:

```bash
APPLE_DEVELOPER_ID="Developer ID Application: YOUR NAME" ./FlatCAMPlus_macos_dmg_generator.command
```

Manual build of the `.app` bundle:

```bash
python -m PyInstaller flatcam.py \
  --name "FlatCAM-Plus" \
  --windowed \
  --clean \
  --noconfirm \
  --icon "assets/resources/app256.png" \
  --add-data "pyproject.toml:pyproject.toml" \
  --add-data "assets:assets" \
  --add-data "config:config" \
  --add-data "locale:locale" \
  --add-data "preprocessors:preprocessors" \
  --collect-submodules flatcam_plus \
  --collect-all PyQt6 \
  --collect-all vispy \
  --collect-all shapely \
  --collect-all rasterio
```

The app bundle is created at:

```text
dist/FlatCAM-Plus.app
```

For a local unsigned package, ad-hoc sign the bundle and create a DMG:

```bash
codesign --force --deep --sign - "dist/FlatCAM-Plus.app"
hdiutil create -volname "FlatCAM Plus" \
  -srcfolder "dist/FlatCAM-Plus.app" \
  -ov \
  -format UDZO \
  "FlatCAM-Plus-macOS.dmg"
```

For public macOS distribution, use an Apple Developer ID certificate and notarize the DMG with Apple:

```bash
codesign --force --deep --options runtime --sign "Developer ID Application: YOUR NAME" "dist/FlatCAM-Plus.app"
xcrun notarytool submit "FlatCAM-Plus-macOS.dmg" --apple-id "you@example.com" --team-id "TEAMID" --wait
xcrun stapler staple "FlatCAM-Plus-macOS.dmg"
```

## Linux

On Ubuntu-like systems, install common GUI/OpenGL runtime libraries:

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  libgl1 \
  libegl1 \
  libxkbcommon-x11-0 \
  libxcb-cursor0 \
  libxcb-xinerama0 \
  libspatialindex-dev \
  gdal-bin \
  libgdal-dev
```

Run the one-step portable package generator from the repository root:

```bash
chmod +x FlatCAMPlus_linux_portable_generator.sh packaging/linux/build_linux_portable.sh
./FlatCAMPlus_linux_portable_generator.sh
```

The script builds a PyInstaller folder distribution, writes a local `.desktop` launcher inside the portable folder, and creates a compressed archive.

The automated outputs are created at:

```text
dist/linux/FlatCAM-Plus/
dist/installer/FlatCAMPlus-<version>-linux-<arch>.tar.gz
```

Useful options:

```bash
./FlatCAMPlus_linux_portable_generator.sh --no-archive
./FlatCAMPlus_linux_portable_generator.sh --skip-build
PYTHON_BIN=/path/to/python3 ./FlatCAMPlus_linux_portable_generator.sh
```

Manual build of the Linux folder distribution:

```bash
python -m PyInstaller flatcam.py \
  --name "FlatCAM-Plus" \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "pyproject.toml:pyproject.toml" \
  --add-data "assets:assets" \
  --add-data "config:config" \
  --add-data "locale:locale" \
  --add-data "preprocessors:preprocessors" \
  --collect-submodules flatcam_plus \
  --collect-all PyQt6 \
  --collect-all vispy \
  --collect-all shapely \
  --collect-all rasterio
```

The Linux build is created at:

```text
dist/FlatCAM-Plus/
```

Create a compressed archive for sharing:

```bash
tar -C dist -czf FlatCAM-Plus-linux-x86_64.tar.gz FlatCAM-Plus
```

The repository also includes a basic Linux install helper in `Makefile` and desktop launcher files in `assets/linux/`. Those are useful for source-based Linux installs.

### Debian and RPM packages

Both formats come from one bundle and one metadata file. `nfpm` generates them, so there is no `debian/` tree and no `.spec` to keep in sync. PyInstaller is a `dev` dependency group in `pyproject.toml`, so `uv sync` provides the builder as well as the package metadata:

```bash
packaging/linux/build_linux_packages.sh            # bundle, glibc check, deb + rpm
packaging/linux/build_linux_packages.sh --skip-bundle   # reuse dist/linux/FlatCAM-Plus
```

The package installs the bundle under `/opt/flatcam-plus` and puts a launcher at `/usr/bin/flatcam-plus`, with the desktop entry, the icon and the AppStream metadata in the usual places. `packaging/linux/nfpm.yaml` is the only place the dependency lists live, spelled once per format because Debian and RPM name the same libraries differently.

**The bundle must be built against an old glibc.** glibc is forward-compatible only, so a bundle built on a recent distribution starts there and fails on older ones. `packaging/linux/check_glibc_floor.py` reads the bundle's own symbol requirements — the shared objects *and* the extensionless bootloader — and fails when they exceed the declared floor. The floor is **2.34**, and it is not a preference: `pyqt6-qt6` publishes only a `manylinux_2_34` x86_64 wheel, so that is the oldest glibc this application can run on, which happens to be exactly RHEL/Alma/Rocky 9. The release workflow therefore builds inside `quay.io/pypa/manylinux_2_34_x86_64`; building on a modern host would silently raise the floor above what the gate promises.

`.github/workflows/release.yml` runs this on a `v*` tag: it refuses a tag that disagrees with `pyproject.toml`, builds the bundle in the manylinux container, packages deb and rpm on the runner, builds the Windows installer, builds the Flatpak, and publishes the artifacts.

### Flatpak

The release also carries a `.flatpak` bundle built from `packaging/flatpak/`:

```bash
packaging/flatpak/build_flatpak.sh --skip-bundle   # bundles an existing dist/linux/FlatCAM-Plus
```

It wraps the same PyInstaller payload as the packages above, so there is one bundle to build and three formats to publish. The manifest asks for X11 through XWayland (`--socket=fallback-x11`, `QT_QPA_PLATFORM=xcb`) because the bundled Qt ships no Wayland plugin, and it points the same launcher at the sandbox path with `--env=FLATCAM_PLUS_HOME=/app/lib/flatcam-plus`.

This is **not** a Flathub submission. Flathub forbids shipping a prebuilt binary payload, so publishing there would mean building PyQt6 and the application against `org.kde.Sdk` as real modules; the self-hosted bundle is unsigned and installs with `flatpak install --user FlatCAMPlus-<version>-linux-x86_64.flatpak`. Application state lands in `~/.var/app/io.github.thebestgoodguy.FlatCAMPlus/`, which the sandbox owns, so the hardcoded `~/.FlatCAM` directory keeps working and persists.

### What runs in CI, and what it costs

Two workflows exist, and neither should be triggered casually:

| Workflow | Trigger | Guard |
| --- | --- | --- |
| `tests.yml` | push to `main`/`dev`, pull request, and the release job | prose-only commits (`**.md`, `odd/`, `.kiro/`, `design/`) run nothing; a second push to the same ref cancels the first; the job is capped at 20 minutes |
| `release.yml` | `v*` tag only | a run from anywhere else stops in the first job in seconds, before the build matrix; every job has its own timeout |

Rules that keep this cheap:

- Do not push to `dev` to "see if it works". Run the suite locally with `uv run --with pytest pytest tests -q`.
- Do not use `workflow_dispatch` on a branch to try the release: it now fails on purpose before spending minutes. To exercise the packaging without publishing, run the same scripts locally (`packaging/linux/build_linux_packages.sh`, `packaging/flatpak/build_flatpak.sh`).
- A failing packaging job is the cheap outcome; a hung one is the expensive one. That is why the timeouts exist and why the release jobs are bounded well under an hour.
- Standard runners are free for public repositories on GitHub's free plan; check the repository's billing setting before assuming otherwise, because this document cannot.

## Packaging Notes

- Always test import, project open/save, Gerber/Excellon rendering, CNCJob generation, and plugin startup from the packaged app.
- If a package starts but a plugin is missing, add the missing module with another `--collect-submodules` or `--hidden-import` entry and rebuild.
- If VisPy/OpenGL rendering fails on Linux, test on a machine with working OpenGL drivers and confirm the Qt/XCB libraries are installed.
- Do not include `doc/` or development caches in desktop runtime packages unless you intentionally want to ship them.
- Review third-party licenses before distributing commercial packages. PyQt6, Qt, GDAL/Rasterio, and other native dependencies may have license or redistribution requirements.
