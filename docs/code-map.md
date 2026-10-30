# Code map

Status: **present** = exists in the tree today, **planned** = does not exist yet. Every module below is present; planned work appears as issues in `docs/issue-drafts/` and moves a module's status here in the same PR.

Target hardware: Quest 2 (Snapdragon XR2 Gen 1, Adreno 650). Build host: x86_64 Linux. See `SPEC.md` for the Musts each module serves.

## quest-app-java
- **Path:** `packages/quest-runtime/app/src/main/java/net/stearlight/quest/`
- **What:** the Android activity, rootfs extraction, and the bridges to Android services.
- **Files:** `QuestActivity.java` (activity, Linux session start/stop, worker pool), `RootfsArchive.java` (tar extraction with path checks), `BluetoothBridge.java`, `NetworkBridge.java`, `UsbNetworkBridge.java`, `AudioBridge.java`, `NativeAudioServer.java`, `PcmQueue.java`, `DesktopAppBridge.java`, `BootAnimation.java`, `BatterySnapshot.java`, `ClockBridge.java`.
- **Status:** present. **Serves:** M1, M5, M7, M8, M9.

## quest-app-native
- **Path:** `packages/quest-runtime/app/src/main/cpp/`
- **What:** the OpenXR frame loop, tracking and hand input, GPU frame hand-off, and the video bridge.
- **Files:** `quest_main.cpp` (frame loop), `gpu_bridge.cpp`, `gpu_frames.h`, `video_bridge.cpp`, `socket_registry.cpp`, `play_space.h`, `hand_*.h`, `controller_input.h`, `gamepad_state.h`, `presentation_shader.h`, `passthrough.h`.
- **Status:** present. **Serves:** M4, M6.

## quest-linux-bridges
- **Path:** `packages/quest-runtime/linux/` (`*.cpp`, `*.c`, `*.h`, `*-bridge.js`)
- **What:** the Linux side of every bridge: Vulkan WSI for the eyes, the video decoder bridge, Bluetooth, network and power over D-Bus, the SDL gamepad, shared Mesa timelines, socket reporting.
- **Files:** `quest_wsi.cpp`, `quest_driver.cpp`, `video-bridge.cpp`, `bluetooth-bridge.cpp`, `network-bridge.h`, `power-bridge.h`, `sdl-gamepad.cpp`, `sdl3-gamepad.cpp`, `mesa-shared-timeline.h`, `socket-report.c`, `steam-update-ui.cpp`, `runtime-monitor.cpp`.
- **Status:** present. **Serves:** M4, M5, M6, M7.

## quest-linux-session
- **Path:** `packages/quest-runtime/linux/` (`*.sh`, `*.py`)
- **What:** session start, the desktop manager (SSH/RDP in developer mode), Proton and FEX game launchers, Flatpak, prepare-* setup steps.
- **Files:** `start-session.sh`, `prepare-desktop.sh`, `desktop-manager.py`, `proton-game-launcher.py`, `fex-game-launcher.py`, `flatpak-launcher.py`, `frame_menus.py`, `prepare-*.py`, `prepare-*.sh`.
- **Status:** present. **Serves:** M1, M3, M4.

## steam-update
- **Path:** `packages/quest-runtime/linux/steam-os-update.py`, `steam_channels.py`
- **What:** the signed Steam OS update path and channel switching.
- **Status:** present. **Serves:** M8.

## stearlight-runtime
- **Path:** `packages/stearlight-runtime/`
- **What:** the Vulkan WSI shim (`vulkan_wsi_shim.c`), the timeline semaphore bridge (`vulkan_timeline_bridge.inc`), and the fake tracking provider (`fake_tracking.cpp`) that feeds SteamVR.
- **Status:** present. **Serves:** M4.

## system-files
- **Path:** `system_files/`
- **What:** files copied into the rootfs: the session scripts, `etc/local.d/arm64-vm.start`, the gamescope session, the polkit helper shims.
- **Status:** present. **Serves:** M1, M3.

## build-and-ci
- **Path:** `build_files/`, `post_process/`, `.github/workflows/`, `Containerfile`, `Justfile`
- **What:** rootfs and APK build, payload staging, release publishing, CI. `build_files/quest/check.sh` is the one place tests are run.
- **Status:** present. **Serves:** M1, M8.

## tests
- **Path:** `tests/`, `packages/quest-runtime/tests/`
- **What:** host-runnable tests (Python unittest, shell, JS, small C/C++). Only the files listed in `build_files/quest/check.sh` run in CI.
- **Status:** present (many files exist but are not wired in; see stage 4 of the roadmap).

## windows-runtime
- **Path:** `packages/windows-runtime/`, `post_process/*.ps1`, `build_files/*arm64*`
- **What:** the unmaintained Windows and QEMU VM runtime and its patches.
- **Status:** present, out of scope for 1.0 (Won't W1). Issues are `after-1.0`.
