# Code map

Status: **present** means it exists in the tree today; **planned** means it does not exist yet. Every module below is present. Planned work is an issue (see `ROADMAP.md`); the pull request that does it moves the module's status here. Line numbers were checked against the tree when this was written and will drift; the symbol names are the stable anchor.

Target hardware: Quest 2 (Snapdragon XR2 Gen 1, Adreno 650). Build host: x86_64 Linux. The Musts (M1 to M9) are in `SPEC.md`.

## How the parts connect

```
  Android app (Java + OpenXR C++)           Linux session inside the app (PRoot, ARM64 rootfs)
  quest-app-java   quest-app-native         quest-linux-session  ->  Steam client, SteamVR, desktop
        |                |                          |                       |
        | files under the app state dir             | launchers             | Vulkan calls
        v                v                          v                       v
   Android services   eye swapchains <--- quest-linux-bridges <---- stearlight-runtime (WSI shim)
   (audio, Bluetooth,  (two OpenXR        (WSI driver, video,        + fake tracking provider
    network, battery)   eye images)        D-Bus and input bridges)
```

The Android side owns the headset: the activity, OpenXR frame loop, rootfs extraction and the Android services. The Linux side runs Valve's Steam software under PRoot and talks back through files, sockets and shared GPU buffers. Details of each connection are under each module's **Interfaces**.

## Modules

| Module | Path | Serves | Status |
|---|---|---|---|
| [quest-app-java](#quest-app-java) | `packages/quest-runtime/app/src/main/java` | M1, M2, M3, M4, M5, M7, M8, M9 | present |
| [quest-app-native](#quest-app-native) | `packages/quest-runtime/app/src/main/cpp` | M1, M4, M6 | present |
| [quest-linux-bridges](#quest-linux-bridges) | `packages/quest-runtime/linux (*.c *.cpp *.h *.js)` | M1, M2, M4, M5, M6, M7, M8 | present |
| [quest-linux-session](#quest-linux-session) | `packages/quest-runtime/linux (*.sh *.py)` | M1, M3, M4, M5, M6 | present |
| [steam-update](#steam-update) | `packages/quest-runtime/linux (steam-os-update.py, steam_channels.py)` | M1, M8 | present |
| [stearlight-runtime](#stearlight-runtime) | `packages/stearlight-runtime` | M1, M2, M3, M4, M6 | present |
| [system-files](#system-files) | `system_files` | M1, M2, M4, M7, M8 | present |
| [build-and-ci](#build-and-ci) | `build_files, post_process, .github, Containerfile` | M1, M8; its host checks gate every Must | present |
| [tests](#tests) | `tests, packages/quest-runtime/tests` | M2 to M8 (no test of M9) | present |
| [windows-runtime](#windows-runtime) | `packages/windows-runtime` | none (out of scope, W1) | present |

## Interlinks

Which module uses which, from each module's own **Depends on** list.

| Module | Depends on |
|---|---|
| quest-app-java | build-and-ci, quest-app-native, quest-linux-session |
| quest-app-native | quest-app-java |
| quest-linux-bridges | quest-app-native, quest-linux-session |
| quest-linux-session | quest-app-java, quest-linux-bridges, steam-update |
| steam-update | quest-linux-bridges, quest-linux-session |
| stearlight-runtime | none |
| system-files | quest-linux-session, steam-update, stearlight-runtime |
| build-and-ci | stearlight-runtime |
| tests | none |
| windows-runtime | none |

## quest-app-java
**Path:** `packages/quest-runtime/app/src/main/java/net/stearlight/quest/`, `packages/quest-runtime/app/src/main/AndroidManifest.xml`, `packages/quest-runtime/app/build.gradle`   **Status:** present   **Serves:** M1, M2, M3, M4, M5, M7, M8, M9   **Platforms:** Quest 2 runtime (Android app), linux build host (Gradle build)
**Purpose:** This is the Android side of the app. It is a `NativeActivity` that installs and starts the bundled Linux runtime under PRoot, then publishes Android state (battery, network, Bluetooth, USB network, audio) as small files that the Linux side reads. It also bridges audio PCM, Bluetooth pairing and advertising, and desktop-app launches between Android and that runtime.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `QuestActivity.java` | Activity, lifecycle, runtime install and launch, device-state publisher | `QuestActivity` (:24), `onCreate` (:50), `requestLinux` (:71), `startLinux` (:101), `stopLinux` (:111), `killLinux` (:117), `runLinux` (:133), `writeDeviceState` (:82), `onDestroy` (:199) |
| `NativeAudioServer.java` | Runs the bundled musl PulseAudio server with its own deadlines | `start` (:13), `close` (:41) |
| `NetworkBridge.java` | Publishes Wi-Fi state, scan results and interface addresses; holds the low-latency Wi-Fi lock | `resumed` (:25), `publishInterfaces` (:40), `poll` (:61) |
| `BatterySnapshot.java` | Immutable battery sample; keeps the last good percentage for 30 s | `update` (:11), `capacity` (:16), `charging` (:20) |
| `AudioBridge.java` | Audio focus, and the speaker and microphone PCM sockets | `setResumed` (:37), `updateStreams` (:46), `Session.run` (:80), `readSpeakers` (:167) |
| `PcmQueue.java` | Bounded frame-aligned PCM queue between the socket reader and AudioTrack | `put` (:23), `take` (:36), `close` (:57) |
| `ClockBridge.java` | Writes the guest's timezone rules from Android's tzdata | `sync` (:18), `readZone` (:45) |
| `BootAnimation.java` | Decodes the boot movie frames for the status swapchain | `bootComplete` (:34), `frame` (:38) |
| `BluetoothBridge.java` | Bluetooth command queue, device snapshot, advertising, pairing and profile connect | `poll` (:150), `publish` (:86), `discover` (:109), `deviceOperation` (:116), `reply` (:143), `close` (:186) |
| `RootfsArchive.java` | Extracts the gzip tar rootfs and overlay, with path checks | `extract` (:33), `extract` (:36), `safeName` (:19), `destination` (:25) |
| `DesktopAppBridge.java` | Launches optional desktop apps as separate PRoot sessions from request files | `start` (:48), `poll` (:83), `close` (:106) |
| `UsbNetworkBridge.java` | Requests the USB transport network and publishes its state | `request` (:40), `publish` (:66), `release` (:85), `close` (:89) |
| `AndroidManifest.xml` | Permissions, features, exported VR launcher activity | `activity` (:27), `application` (:23), `uses-feature` (:3) |
| `build.gradle` | Module build: SDK levels, ABI, payload paths, signing, OpenXR dependency | `minSdk` (:10), `targetSdk` (:11), `payload` (:2), `signingConfigs` (:20-31) |

### Interfaces
- **Inputs / outputs:**
  - Intent extra `developerRuntime` (boolean) skips the PRoot launch and waits for an ADB runtime: `QuestActivity.java:165`.
  - `onNewIntent` replaces the intent and re-requests the Linux session: `QuestActivity.java:70`.
  - Broadcast `ACTION_BATTERY_CHANGED`: `QuestActivity.java:56`, handled at `:40`.
  - Broadcast `android.hardware.usb.action.USB_STATE`, extra `connected`: `UsbNetworkBridge.java:30`, `:23-24`.
  - Runtime permission request, codes 7 (Bluetooth, microphone) and 8 (fine location): `QuestActivity.java:58-59`, `NetworkBridge.java:94`.
  - Settings intents: Wi-Fi at `NetworkBridge.java:97`; Bluetooth at `BluetoothBridge.java:106` and `:135`; Wi-Fi, Bluetooth or general settings from a desktop request at `DesktopAppBridge.java:90`.
  - Wi-Fi scan start `wifi.startScan()`: `NetworkBridge.java:93`. Low-latency Wi-Fi lock tag `Stearlight:VR`: `NetworkBridge.java:29`.
  - Audio focus `AUDIOFOCUS_GAIN` with `USAGE_GAME` and `CONTENT_TYPE_MUSIC`: `AudioBridge.java:30-36`.
  - Timezone read from `TimeZone.getDefault().getID()`: `QuestActivity.java:99`.
  - Packaged assets read: `rootfs.list` and `rootfs/part-NNN.bin` (`QuestActivity.java:196`), `rootfs.sha256` (`:144`), `quest-overlay.bin` (`:157`), `boot/clips.json` and `boot/<name>-NNNN.png` (`BootAnimation.java:27`, `:48`).
  - Rootfs files read: `opt/quest/audio.pa` (`NativeAudioServer.java:18`); `.stearlight-ready` marker (`QuestActivity.java:137`, `ClockBridge.java:19`); `home/stearlight/.cache/stearlight/os-update/installed.json` and `activated.json` (`QuestActivity.java:155-156`); timezone databases `/apex/com.android.tzdata/etc/tz/tzdata`, `/data/misc/zoneinfo/current/tzdata`, `/system/usr/share/zoneinfo/tzdata` (`ClockBridge.java:14-16`).
  - Files under the app files directory, `getFilesDir()`:
    - `linux-session.lock` (`QuestActivity.java:104`);
    - `linux.pid` (`:122`, `:175`);
    - `rootfs/` and `rootfs-install/` staging (`:55`, `:139`);
    - `quest-overlay-version` (`:151`);
    - `tmp/` and `shm/` (`:161-162`);
    - `logs/linux.log` (`:164`, `:179`) and `logs/audio-server.log` (`NativeAudioServer.java:31`);
    - `rootfs/etc/resolv.conf` rewritten from the active link DNS (`QuestActivity.java:96`);
    - `rootfs/etc/localtime` symlink, `rootfs/etc/timezone`, `rootfs/usr/share/zoneinfo/<zone>` (`ClockBridge.java:20-37`).
  - State directory `getStateDirectory()` = `files/state` (`QuestActivity.java:72`). It is bound into the guest at `/run/stearlight/quest` (`:172`). Written files:
    - `device.json` via `device.json.tmp` (`:95`);
    - `linux-status` (`:100`);
    - `external-runtime.ready` created at `:165` and deleted at `:136`; `external-runtime` deleted at `:166`;
    - `network.tsv` via `network.tsv.next` (`NetworkBridge.java:88`);
    - `network-interfaces.tsv` via `.next` (`:56-58`);
    - `bluetooth-devices.tsv` via `bluetooth-devices.tmp` (`BluetoothBridge.java:97`);
    - `bluetooth-reply.json` via `bluetooth-reply.tmp` (`:146-147`);
    - `usb-network.json` and `usb-network-scope` (`UsbNetworkBridge.java:76-77`);
    - `desktop-app-requests/<id>.result` (`DesktopAppBridge.java:43-45`) and `desktop-app-logs/desktop-app-<id>.log` (`:80`);
    - `native-audio.pa` (`NativeAudioServer.java:17`), `native-audio.pid` (`:24`), `pulse-state/` (`:16`).
  - State files read or consumed:
    - `desktop-mode.active` (`DesktopAppBridge.java:84`);
    - `desktop-device-settings.request` (`:85`);
    - `desktop-app-requests/<32 hex>.request` (`:97`);
    - `network-scan.request` and `network-settings.request` (`NetworkBridge.java:91`, `:96`);
    - `bluetooth-command.json` (`BluetoothBridge.java:154`).
  - State files removed at startup: `dashboard.ready`, `gpu-capture.request`, `xr-eye-capture.request` (`QuestActivity.java:51-53`); `network-settings.request` and `network-scan.request` (`NetworkBridge.java:22`); `bluetooth-command.json` and `bluetooth-reply.json` (`BluetoothBridge.java:62`); `desktop-device-settings.request` (`DesktopAppBridge.java:27`).
  - Audio sockets (`LocalSocket`, filesystem namespace): `state/audio-output.sock` and `state/audio-input.sock` (`AudioBridge.java:76`). The PulseAudio native socket is `tmp/stearlight-runtime/pulse/native` (`NativeAudioServer.java:15`, `:33`).
  - Child processes:
    - `/system/bin/sh` wrapper that writes its pid and execs PRoot (`QuestActivity.java:177`);
    - `libproot_exec.so` with `--kill-on-exit --sysvipc --link2symlink -r <root>` and binds `/dev /proc /sys /tmp /dev/shm /run/stearlight/quest /proc/net` (`:172-174`), command `/bin/bash /opt/quest/start-session.sh` (`:172`);
    - `libproot_loader.so` via `PROOT_LOADER` (`:178`);
    - `/system/bin/sh` wrapper for PulseAudio, with `LD_PRELOAD=libquest_audio_identity.so`, `libquest_audio_loader.so`, and `usr/bin/pulseaudio --daemonize=no --exit-idle-time=-1 --use-pid-file=no --disable-shm=yes -n --file=<native-audio.pa>` (`NativeAudioServer.java:25-27`);
    - desktop apps as `libproot_exec.so` with a per-request `-r <root>`, bindings, `-w <cwd>`, and `/usr/bin/env -i` (`DesktopAppBridge.java:54-76`).
  - Environment set for the Linux session: `LD_LIBRARY_PATH`, `PROOT_LOADER`, `PROOT_TMP_DIR`, `PROOT_QUEST_ROBUST=1`, `TMPDIR=/tmp`, `HOME`, `USER`, `LOGNAME`, `PATH`, `GLIBC_TUNABLES=glibc.pthread.rseq=0`, `QUEST_NATIVE_PULSE=1` (`QuestActivity.java:178-180`). PulseAudio: `PULSE_RUNTIME_PATH`, `PULSE_STATE_PATH`, `PULSE_DLPATH` (`NativeAudioServer.java:29-30`). Desktop apps accept only the allowlisted environment keys (`DesktopAppBridge.java:17-23`, `:72`).
  - Exit status 75 restarts the session. Status 78 means "Linux IPC verification failed" (`QuestActivity.java:189`).
  - JNI, Java to native: `startSocketRegistry(String)` (`QuestActivity.java:78`), `stopSocketRegistry()` (`:79`), `setUsbNetwork(long)` (`:38`), `networkInterfaceIndex(String)` (`:39`). Implemented at `packages/quest-runtime/app/src/main/cpp/socket_registry.cpp:106`, `:122`, `:120`, `:121`. The library is `stearlight_quest` (`QuestActivity.java:25`; `AndroidManifest.xml:28`).
  - JNI, native to Java: `onXrAudioFocus(boolean)` (`QuestActivity.java:75`, called from `cpp/quest_main.cpp:204`); `getBootBitmap()` (`:80`, called from `cpp/quest_main.cpp:238`); `bootComplete()` (`:81`, called from `cpp/quest_main.cpp:239`).
- **Wire formats:**
  - `device.json` is a JSON object with: `battery_percent`, `charging`, `battery_status`, `battery_plugged`, `battery_voltage_mv`, `battery_temperature_tenths_c`, `battery_charge_time_ms`, `connected`, `validated`, `wifi`, `dns[]`, `addresses[]`, `bluetooth_available`, `bluetooth_permission`, `bluetooth_enabled`, `bluetooth_le_advertising`, and `input_device_batteries[{name, sources, battery_present, battery_capacity}]` (`QuestActivity.java:87-94`).
  - `network.tsv` lines, tab-separated: `enabled\t0|1`, `connected\t0|1`, `validated\t0|1`, `current\t<base64 SSID>\t<base64 BSSID>`, and `ap\t<base64 SSID>\t<base64 BSSID>\t<signal 0-100>\t<frequency MHz>\t<security>` (`NetworkBridge.java:73-86`). Security values are 392 for PSK, 648 for EAP, 0 otherwise (`:39`).
  - `network-interfaces.tsv` lines, space-separated: `<ifname> <index> <4|6> <prefix> <address>`. Loopback rows are added as `lo` at 127.0.0.1/8 and ::1/128 (`NetworkBridge.java:46-55`).
  - `bluetooth-devices.tsv`: first line `adapter\t0|1`; then per device `address\tname\tbondState\tlinked\tdeviceClass\trssi\tuuids` with comma-joined UUIDs. Tabs and newlines in names are replaced with spaces (`BluetoothBridge.java:85`, `:91-95`).
  - `bluetooth-command.json` in, with `id`, `operation` and `properties` (`BluetoothBridge.java:157-161`). `bluetooth-reply.json` out, with `id`, `success`, `error` (`:145`).
  - `usb-network.json`: `status`, `available`, `interface`, `scope_id`, `bandwidth_kbps`, `addresses[]` (`UsbNetworkBridge.java:72-73`). `usb-network-scope`: `<index> <ipv4|-> <prefix> <network handle, unsigned decimal>` (`:77`).
  - Desktop app request: file `<32 lowercase hex>.request`, at most 65536 bytes (`DesktopAppBridge.java:97`, `:100`). JSON fields: `root` (under the private `home/stearlight/.local/share/stearlight/` tree), optional `cwd`, optional `bindings[]` of `{source, target}` (at most 32), `environment` (allowlisted keys, values at most 8192 bytes), `command[]` (1 to 128 strings) (`:50-76`). Result file `<id>.result`: `{state, code, error}` (`:40-45`).
  - Desktop settings request: a file with text `wifi`, `bluetooth` or `headset`, at most 32 bytes (`:86-90`).
  - PCM, speakers: stereo signed 16-bit little-endian, 48000 Hz, 4-byte frames, 240-frame (5 ms) chunks (`AudioBridge.java:17-18`, `:121`). PCM, microphone: mono signed 16-bit little-endian, 48000 Hz, 960-byte reads (`:91-97`).
  - Boot animation: 450 by 450 ARGB bitmap (`BootAnimation.java:19`). `clips.json` has `startup.duration_ms`, `loop.duration_ms` and `starts_ms[]` per clip (`:35`, `:42-47`).
  - Android tzdata record: 24-byte header, then 52-byte index entries (40-byte ID, data-relative offset, length, unused raw UTC offset). The record must start with `TZif` (`ClockBridge.java:46-61`).
  - Rootfs payload: gzip tar with ustar and PAX headers. Header checksum is checked (`RootfsArchive.java:39-42`). The gzip trailer is read to completion before the install is accepted (`:63`).

### Depends on / used by
- **Depends on:**
  - `quest-app-native`: the JNI symbols listed above (`socket_registry.cpp`, and the `QuestActivity` callbacks used by `quest_main.cpp`).
  - `quest-linux-session`: the rootfs entry script `/opt/quest/start-session.sh` (`QuestActivity.java:172`) and the guest's `/run/stearlight/quest` mount (`:172`).
  - `build-and-ci`: the Gradle properties `questPayload` (`build.gradle:2`), `questBuildDir` (`:3`) and `questSigningStore` (`:20`). The payload supplies `assets/` and `jniLibs/` (`:17`), and the CMake `QUEST_PAYLOAD` argument (`:15`).
  - Native libraries from the payload: `libproot_exec.so`, `libproot_loader.so`, `libquest_audio_loader.so` (`QuestActivity.java:172`, `:178`; `NativeAudioServer.java:25-27`); `libquest_audio_identity.so` under `opt/quest/` in the rootfs (`NativeAudioServer.java:26`).
- **Used by:**
  - `quest-app-native`: calls `onXrAudioFocus`, `getBootBitmap` and `bootComplete` on the activity (`cpp/quest_main.cpp:204`, `:238`, `:239`).
  - The Linux-side bridges read the state files this module publishes. Those readers are in `quest-linux-bridges` and `quest-linux-session`, which I did not read for this section. The module boundary is the file names listed under Interfaces.

### Open issues
- #1 Bound the Linux session stop so a missing pid cannot hold the session lock (`QuestActivity.java:111-132`)
- #2 Clear the advertise callback when a start request fails (`BluetoothBridge.java:176-185`)
- #3 Wait for and kill desktop app processes when the desktop bridge closes (`DesktopAppBridge.java:106-110`)
- #5 Keep onDestroy from polling for the Linux pid on the UI thread (`QuestActivity.java:117-132`, `:199`)
- #26 Decode boot animation frames off the render thread (`BootAnimation.java:38-61`)
- #27 Stop publishing the Bluetooth device list on every discovery result (`BluetoothBridge.java:43-60`, `:150-153`)
- #28 Run the Linux session outside the poller thread pool (`QuestActivity.java:26`, `:71`, `:184-185`)
- #64 Test the hardlink fallback in rootfs extraction (`RootfsArchive.java:54`, `:65`)
- #65 Test that rootfs extraction rejects escaping archive paths (`RootfsArchive.java:21-22`)
- #77 Honor the developer-runtime extra only in debuggable builds (`QuestActivity.java:136`, `:165`; `AndroidManifest.xml:27`)
- #78 Read the signing passwords from build inputs, not from source (`build.gradle:20-31`)
- #114 Acceptance: a Bluetooth keyboard or gamepad pairs from the headset (`BluetoothBridge.java:182`)
- #116 Acceptance: uninstalling the app removes its data and leaves no processes (`QuestActivity.java:114-131`; `DesktopAppBridge.java:107`)

### Notes
- **Thread pool.** `workers` has two threads (`QuestActivity.java:26`). `startLinux` takes one for the whole session: it is submitted at `:71` and blocks in `linux.waitFor()` at `:184`. That leaves one thread for the four periodic pollers scheduled at `:60`, `:63`, `:65` and `:67`.
- **Session lock.** `runLinux` holds an exclusive `FileLock` on `linux-session.lock` (`:104-108`). The lock is released in the `finally` at `:108`, after `stopLinux()`, `audioServer.close()` and `stopSocketRegistry()`. `stopLinux` loops on `process.isAlive()` with no bound (`:114`).
- **Killing PRoot.** `killLinux` sends SIGKILL with `android.os.Process.killProcess`, not `destroy()`, because `destroy()` sends TERM and PRoot can inherit blocked signals (`:119-120`, `:129`). The pid is read from `linux.pid` and rejected if it is 1 or this process's own pid (`:128`).
- **Advertising callback.** `callback` is assigned at `BluetoothBridge.java:178` before `startAdvertising` at `:182`. `onStartFailure` clears it (`:180`), but an exception thrown by `startAdvertising` goes to the `catch` at `:183` and leaves it set.
- **Rootfs trust.** The rootfs archive digest must equal `rootfs.sha256` before the install is kept (`QuestActivity.java:141-145`). Extraction rejects absolute paths and `..` components (`RootfsArchive.java:19-24`). Existing rootfs directories without the `.stearlight-ready` marker are preserved for recovery, not overwritten (`QuestActivity.java:146`).
- **Overlay refresh.** The overlay is re-extracted when `lastUpdateTime` changes (`QuestActivity.java:150-158`). The `opt/steamvr` tree is skipped when the update-state markers exist (`:155-156`; `RootfsArchive.java:49`).
- **Manifest.** `allowBackup` is `false` (`AndroidManifest.xml:23`). The activity is exported, `singleTask`, and has VR launcher category (`:27`, `:29`).
- **Build signing.** `build.gradle:25` and `:27` set the store and key passwords to the literal `'android'`. The block is active only when `questSigningStore` is set (`:20`).

## quest-app-native
**Path:** `packages/quest-runtime/app/src/main/cpp/`   **Status:** present   **Serves:** M1, M4, M6   **Platforms:** Quest 2 runtime (Android NDK build); Quest 3 and Quest 3S paths in `device_profile.h`
**Purpose:** This is the native half of the Quest app. It runs the OpenXR session and frame loop, publishes headset and controller tracking into files the Linux side reads, and bridges GPU frames, video decode and physical gamepads between Android and Linux. It also runs a small socket registry that exposes loopback TCP state to the Linux side.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `CMakeLists.txt` | Builds the `stearlight_quest` shared library and links OpenXR, EGL, GLES3, jnigraphics and mediandk. | `add_library` (`CMakeLists.txt:6`), `-uANativeActivity_onCreate` (`:11`) |
| `quest_main.cpp` | Activity entry point and the OpenXR frame loop. | `android_main` (`quest_main.cpp:400`), `Runtime::initialize` (`:93`), `Runtime::frame` (`:255`), `Runtime::events` (`:205`), `Runtime::shutdown` (`:398`) |
| `gpu_bridge.cpp` | Receives Linux frames as three shared DMA-BUF images and presents them. | `GpuBridge::initialize` (`gpu_bridge.cpp:22`), `receiveFrames` (`:60`), `poll` (`:108`), `draw` (`:128`), `capture` (`:119`), `shutdown` (`:163`) |
| `gpu_bridge.h` | GPU socket wire structs and the `GpuBridge` class. | `QuestGpuHello` (`gpu_bridge.h:6`), `QuestGpuPresent` (`:9`), `QuestGpuRelease` (`:13`), `class GpuBridge` (`:26`) |
| `gpu_frames.h` | Lease bookkeeping for the three GPU slots. `FramePool` has no caller in this module. | `quest::FrameLeases` (`gpu_frames.h:7`), `publish` (`:13`), `adopt` (`:18`), `reconnect` (`:12`), `quest::FramePool` (`:28`) |
| `socket_registry.cpp` | Worker thread that takes socket fds over SCM_RIGHTS, writes `proc-net/tcp`, and binds the USB network socket. | `serve` (`socket_registry.cpp:52`), `stillOwned` (`:47`), `bindUsbSocket` (`:24`), JNI `startSocketRegistry` (`:106`), `setUsbNetwork` (`:120`), `networkInterfaceIndex` (`:121`), `stopSocketRegistry` (`:122`) |
| `video_bridge.cpp` | Hardware H.264 and HEVC decode through MediaCodec for the Linux client. | `VideoBridge::initialize` (`video_bridge.cpp:107`), `serve` (`:113`), `serveClient` (`:122`), `Decoder::submit` (`:49`), `Decoder::output` (`:72`), `shutdown` (`:154`) |
| `video_bridge.h` | `VideoBridge` class declaration. | `class VideoBridge` (`video_bridge.h:9`) |
| `video_protocol.h` | Video socket request and response layout. | `QuestVideoRequest` (`video_protocol.h:8`), `QuestVideoResponse` (`:13`), operations (`:4-5`) |
| `quest_bridge.h` | Tracking shared-memory layout and its seqlock publisher. | `QuestTracking` (`quest_bridge.h:21`), `QuestHaptic` (`:16`), `questPublishTracking` (`:37`) |
| `quest_motion.h` | Head velocity side file (56 bytes). | `QuestMotion` (`quest_motion.h:11`), `questPublishMotion` (`:18`), `questReadMotion` (`:25`), `questMotionVelocity` (`:36`) |
| `hand_tracking.h` | Creates OpenXR hand trackers, locates joints each frame, and publishes the `hands` file. | `HandTracking::initialize` (`hand_tracking.h:31`), `update` (`:49`), `publish` (`:67`), `shutdown` (`:80`) |
| `hand_input.h` | Maps an aim pose and pinch to a trigger, and forwards the menu gesture. | `HandInput::apply` (`hand_input.h:19`), armed state (`:33-35`) |
| `hand_protocol.h` | `hands` file layout (26 joints per hand). | `QuestHands` (`hand_protocol.h:7`), `questPublishHands` (`:13`), `questReadHands` (`:19`) |
| `hand_render.h` | Skins and draws the OpenXR hand mesh into each eye. | `HandRender::initialize` (`hand_render.h:43`), `update` (`:67`), `draw` (`:74`) |
| `hand_math.h` | Matrix helpers for eye view-projection and hand skinning. | `viewProjection` (`hand_math.h:17`), `handSkinMatrix` (`:23`) |
| `passthrough.h` | Controls the passthrough compositor layer from request files and a style file. | `Passthrough::initialize` (`passthrough.h:66`), `update` (`:92`), `updateStyle` (`:38`), `suspend` (`:103`) |
| `play_space.h` | Builds the seated-origin `chaperone_info` JSON. | `questPlaySpace` (`play_space.h:10`) |
| `controller_input.h` | Reads one controller's buttons and axes from tracking, and merges hand buttons. | `controllerInput` (`controller_input.h:12`), `frameButtons` (`:24`) |
| `gamepad_state.h` | Internal gamepad state (48 bytes) and its seqlock helpers. | `QuestGamepadState` (`gamepad_state.h:7`), `gamepadState` (`:14`), `publishGamepad` (`:31`), `readGamepad` (`:37`) |
| `external_gamepad.h` | Shared file for a physical gamepad (152 bytes). | `QuestExternalGamepad` (`external_gamepad.h:6`), `publishExternalGamepad` (`:14`), `readExternalGamepad` (`:20`), `gamepadAxis` (`:33`) |
| `android_gamepad.h` | Finds a physical pad through `InputDevice` JNI and writes it to the external file. | `AndroidGamepad::initialize` (`android_gamepad.h:56`), `handle` (`:71`), `tick` (`:101`) |
| `device_profile.h` | Headset enum, name parsing, and per-headset eye sizes. | `headsetFromName` (`device_profile.h:9`), `eyeSize` (`:26`), `touchPlus` (`:23`) |
| `loading_boost.h` | CPU boost budget for loading and short interactions. | `LoadingBoost::update` (`loading_boost.h:13`) |
| `presentation_shader.h` | GLSL source strings for the presentation pass. | `presentationVertex` (`presentation_shader.h:3`), `presentationFragment` (`:4`) |

### Interfaces
- **Inputs / outputs, app files dir** (`directory`, from the `getStateDirectory` callback at `quest_main.cpp:95-96`):
  - `tracking`: created, sized and mapped read-write as `QuestTracking` (`quest_main.cpp:100-101`).
  - `tracking-motion`: mapped read-write as `QuestMotion` (`quest_main.cpp:105-111`).
  - `hands`: mapped read-write as `QuestHands` (`hand_tracking.h:32-34`).
  - `external-gamepad`: mapped read-write as `QuestExternalGamepad` (`android_gamepad.h:64-68`).
  - `headset-profile`: written as `1 <headset-id>` through `headset-profile.next` and rename (`quest_main.cpp:132-133`).
  - `bootstrapper.ready`: removed at start (`quest_main.cpp:97`), checked per frame (`:300`).
  - `dashboard.ready`: removed at start (`quest_main.cpp:102`), checked per frame (`:299`).
  - `play-space.vrchap`: removed at start (`quest_main.cpp:103`), published through `.next` and rename (`:248-252`).
  - `performance-profile`: read as text `Performance` or `Powersave` (`quest_main.cpp:304-305`).
  - `performance-boost.request`, `interaction-boost.request`: mtime checked and a deadline double read (`quest_main.cpp:312-318`).
  - `passthrough.enabled` (existence, `passthrough.h:94`), `passthrough.composition-ready` (existence, `quest_main.cpp:336`), `passthrough-style.tsv` (read, `passthrough.h:40`).
  - `passthrough.status` (written, `passthrough.h:35`), `passthrough.supported` (created and removed, `passthrough.h:67`, `:89`, `:110`).
  - `gpu-capture.request` and `xr-eye-capture.request` (checked and removed, `gpu_bridge.cpp:121`, `:133-134`, `:150-151`), `gpu-capture.rgba` (`gpu_bridge.cpp:125`) and `xr-eye-capture.rgba` (`:155`).
  - `model-left.glb` and `model-right.glb`, or `model-<n>.glb` when the name has neither word (`quest_main.cpp:201`).
- **Sockets, app files dir:**
  - `gpu.sock`: SOCK_SEQPACKET, listening, non-blocking (`gpu_bridge.cpp:52`).
  - `video.sock`: SOCK_STREAM, listening with backlog 2, mode 0600 (`video_bridge.cpp:108-110`).
  - `haptics.sock`: SOCK_DGRAM, bound, mode 0600 (`quest_main.cpp:142-147`).
  - `socket-registry.sock`: SOCK_DGRAM with SO_PASSCRED, mode 0600 (`socket_registry.cpp:109-112`).
  - `usb-network.sock`: SOCK_SEQPACKET, listening, mode 0600 (`socket_registry.cpp:114-117`).
  - `proc-net/`: directory created with mode 0700 (`socket_registry.cpp:108`); `proc-net/tcp` and `proc-net/tcp.tmp` are rewritten and renamed (`:55-61`).
- **JNI exports called from the Java activity:** `startSocketRegistry(String)` (`socket_registry.cpp:106`), `stopSocketRegistry()` (`:122`), `setUsbNetwork(long)` (`:120`), `networkInterfaceIndex(String) -> int` (`:121`).
- **JNI calls into Java:** `getStateDirectory()` (`quest_main.cpp:95-96`), `getBootBitmap()` (`:238`), `bootComplete()` (`:239`), `onXrAudioFocus(boolean)` (`:204`), and `android/view/InputDevice` static and instance methods (`android_gamepad.h:57-62`).
- **Android entry:** `android_main` via `ANativeActivity` (`quest_main.cpp:400`); `ro.product.model` read through `__system_property_get` (`quest_main.cpp:130`); input events through `app->onInputEvent` (`quest_main.cpp:99`).
- **Other Android APIs:** AHardwareBuffer allocate, describe and socket transfer (`gpu_bridge.cpp:21`, `:27-28`); MediaCodec decoder (`video_bridge.cpp:38-47`); DMA-BUF `mmap` of a fd sent by the client (`video_bridge.cpp:29-33`).

### Wire formats
- **Video request** `QuestVideoRequest`, 32 bytes: `magic, operation, bytes, width, height, codec` (uint32) and `timestamp` (uint64). `video_protocol.h:8`, size assert `:14`. Operations: CONFIGURE=1, PACKET=2, POLL=3, SHARED_OUTPUT=4 (`video_protocol.h:4-5`). Codec 4 is AVC and 5 is HEVC (`video_bridge.cpp:37-38`).
- **Video response** `QuestVideoResponse`, 32 bytes: `magic`, `status` (int32), `bytes, width, height, color` (uint32), `timestamp` (uint64). `video_protocol.h:13`, size assert `:14`. Status 0 is a frame, 1 is accepted, 2 is format changed, negative is failure (`video_protocol.h:9-12`).
- **Video packet:** Annex-B access unit up to 8 MiB (`video_protocol.h:2`, `:5`). Decoded frames are NV12, `width*height*3/2` bytes. Color 19 (planar) is interleaved into NV12 (`video_bridge.cpp:91-103`).
- **GPU hello** `QuestGpuHello`, 88 bytes: `magic` 0x53475131, `version` 4, `count` 3, `available_mask`, three `QuestGpuBuffer {width, height, stride, format, allocation_size}` (`gpu_bridge.h:3-6`, size assert `gpu_bridge.h:14`). Sent with the three DMA-BUF fds in SCM_RIGHTS (`gpu_bridge.cpp:76-79`).
- **GPU present** `QuestGpuPresent`, 120 bytes: `magic, slot, frame_id, vk_format, pose_sequence`, `predicted_monotonic_ns`, and two `QuestGpuView {position[3], orientation[4], fov[4]}` (`gpu_bridge.h:8-12`).
- **GPU release** `QuestGpuRelease`, 16 bytes: `magic, slot, frame_id` (`gpu_bridge.h:13`). Magic 0x53475131 is a release and 0x53475132 is an accept (`gpu_bridge.h:4`, `gpu_bridge.cpp:91-100`).
- **Tracking** `QuestTracking`, version 2, magic 0x53515231: `quest_bridge.h:9`, layout `:21-33`. Field `sequence` is the seqlock counter (`quest_bridge.h:38-41`).
- **Haptic datagram** `QuestHaptic`, 20 bytes: `magic, hand, duration_seconds, frequency, amplitude` (`quest_bridge.h:16-20`).
- **Motion** `QuestMotion`, 56 bytes, magic 0x53514d31, version 1 (`quest_motion.h:9`, `:11-17`).
- **Hands** `QuestHands`, magic 0x53514831, version 1, 26 joints per hand (`hand_protocol.h:6-12`).
- **External gamepad** `QuestExternalGamepad`, 152 bytes, magic 0x53514550, version 1 (`external_gamepad.h:6-12`). It embeds `QuestGamepadState`, 48 bytes, magic 0x53514750 (`gamepad_state.h:7-12`).
- **Socket registry request:** a datagram carrying one int32 original fd number with a stream-socket fd in SCM_RIGHTS and SCM_CREDENTIALS (`socket_registry.cpp:67-82`). **USB bind:** the client sends an int32 flag, 0 or 1, with one fd; the server replies with an int32 result (`socket_registry.cpp:25-45`).
- **proc-net/tcp:** Linux-style header and rows with `%08X:%04X` addresses (`socket_registry.cpp:57-60`).
- **Passthrough style:** text `version mode hue r g b a strength`; version must be 1 (`passthrough.h:43`).
- **Headset profile:** text `1 <headset-id>` (`quest_main.cpp:133`).

### Depends on / used by
- **Depends on:**
  - quest-app-java: the `QuestActivity` JNI exports and callbacks listed under Interfaces (`socket_registry.cpp:106-122`, `quest_main.cpp:95-96`, `:204`, `:238-239`).
  - OpenXR loader, EGL, GLES3, AHardwareBuffer, MediaCodec and mediandk, linked in `CMakeLists.txt:12`.
- **Used by:**
  - quest-app-java: starts and stops the socket registry and sets the USB network handle (`socket_registry.cpp:106`, `:120`, `:122`).
  - quest-linux-bridges: the Linux side is the client of `gpu.sock`, `video.sock` and `haptics.sock`, and reads `tracking`. One client check is named in `docs/issue-drafts/S1.04.md:7` at `packages/quest-runtime/linux/video-bridge.cpp:69`. The Linux code itself was not read here.
  - quest-linux-session: the request and profile files (`performance-profile`, `passthrough.enabled`, `*.request`) are written on the Linux side. Not read in this module.
  - build-and-ci: builds `CMakeLists.txt`. Not read here.

### Open issues
- #4 Send no frame payload after a failed video response (`video_bridge.cpp:145-148`).
- #25 Publish the socket registry table only when it changes (`socket_registry.cpp:47-50`, `:63-98`).
- #26 Decode boot animation frames off the render thread (the Where line names `BootAnimation.java:38-61`; the caller at `quest_main.cpp:238` is in this module).

### Notes
- **Seqlock publication.** Writers bump `sequence` to odd, copy, then bump it to even. Readers retry on an odd or changed value (`quest_bridge.h:37-44`, `quest_motion.h:18-24`, `gamepad_state.h:31-44`, `external_gamepad.h:14-32`). The tracking sample must be taken before the busy mark (`quest_bridge.h:35`), and `quest_main.cpp:260-295` does that. Readers also reject external gamepad samples older than 2 seconds (`external_gamepad.h:28-29`).
- **GPU slot lifetime.** A slot is released to Linux only after both eye reads and the next adoption. The main thread's `finish` and `poll` set this up (`quest_main.cpp:367-370`, `gpu_bridge.cpp:112`, `:162`). `gpu_frames.h:5-6` documents the rule. The receive thread and the main thread share `historyLock` (`gpu_bridge.cpp:64`, `:109`).
- **Video threading.** One accept loop spawns one `std::async` session per connection, capped at four clients (`video_bridge.cpp:113-118`). Each session owns its `Decoder` and MediaCodec (`video_bridge.cpp:123`). Shutdown calls `shutdown(SHUT_RDWR)` on each client (`video_bridge.cpp:155`).
- **Socket permissions differ.** `video.sock` and `haptics.sock` are chmod 0600 (`video_bridge.cpp:110`, `quest_main.cpp:147`). `gpu.sock` is bound at `gpu_bridge.cpp:52` with no chmod in this module. The socket registry checks that the peer uid equals `getuid()` (`socket_registry.cpp:27`, `:77`).
- **Error paths differ.** The `XR()` macro throws (`quest_main.cpp:39-40`). Any throw after initialization reaches the catch in `android_main` (`quest_main.cpp:400`). Video errors do not throw; they set status -1 (`video_bridge.cpp:136-147`). Codec PTS is a monotonic clock, and the guest frame tag is restored from a map capped at 256 entries (`video_bridge.cpp:67-70`, `:85`).

## quest-linux-bridges
**Path:** `packages/quest-runtime/linux/`   **Status:** present   **Serves:** M1, M2, M4, M5, M6, M7, M8   **Platforms:** Quest 2 runtime (aarch64 Linux guest)
**Purpose:** These are the guest-side adapters that let Steam, SteamVR, games and the desktop run on the Quest 2 with its Android services underneath. C and C++ shims are preloaded or built as their own binaries; they interpose libc, Vulkan, SDL, X11, libdrm and D-Bus calls and bridge them to files and sockets under `/run/stearlight/quest`. The `.js` files run inside Valve's Steam UI and forward state to a local HTTP service on port 27771.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `angle-probe.c` | Diagnostic: checks that ANGLE/EGL reaches Adreno Vulkan and reads back a red pixel | `main` (`angle-probe.c:6`) |
| `audio-identity.c` | Preload shim: accepts only no-op `setresuid`/`setresgid`, because Android's seccomp traps real calls | `setresuid` (`audio-identity.c:8`), `setresgid` (`audio-identity.c:15`) |
| `bluetooth-bridge.cpp` | Owns the `org.bluez`, NetworkManager and UPower D-Bus names; runs the bus loop that hosts the other two bridges | `quest_services_run` (`bluetooth-bridge.cpp:521`), `command` (`:139`), `synchronize` (`:287`), `handle` (`:343`) |
| `capture-matrix.h` | NEON fast paths for Steam's RGB-to-YUV row functions, enabled only when byte fingerprints match | `quest_matrix_y` (`capture-matrix.h:15`), `quest_matrix_uv` (`:29`), `ARGBToYRowMatrix_C` (`:80`), `ARGBToUVRowMatrix_C` (`:97`) |
| `compositor-launcher.c` | Execs the real `vrcompositor.bin` with the Quest ICD and the final-pass flag | `main` (`compositor-launcher.c:4`) |
| `controller_pose.h` | Converts OpenXR grip poses to SteamVR controller model poses (Quest 2 and Touch Plus) | `controllerComponentPose` (`controller_pose.h:9`), `controllerModelPose` (`:30`, `:35`) |
| `desktop-access-runtime.c` | Preload: reports a failed `audit_open` as `EPROTONOSUPPORT` for the developer-access service only | `audit_open` (`desktop-access-runtime.c:10`) |
| `desktop-pam.c` | PAM module for the desktop account: checks the local shadow hash, then reserves the desktop on 127.0.0.1:27771 | `pam_sm_authenticate` (`desktop-pam.c:56`), `reserve_desktop` (`:16`) |
| `desktop-ui-bridge.js` | Injected into Steam's UI: desktop password, start and session calls; interaction boost; channel and developer settings | `call` (`desktop-ui-bridge.js:7`), `synchronizeUpdates` (`:45`), `install` (`:114`), `chunks.push` (`:165`) |
| `desktop-windows.js` | KWin script: prints the window list as `STEARLIGHT_WINDOWS` JSON when it changes | `publish` (`desktop-windows.js:4`), `watch` (`:10`) |
| `display-pulse.h` | Paces Linux presentation to the OpenXR display tick through a futex on the tracking sequence | `QuestDisplayPulse::wait` (`display-pulse.h:14`) |
| `external-gamepad-reader.h` | Maps the physical-gamepad state file read-only; retries the open once per second | `ExternalGamepadReader::read` (`external-gamepad-reader.h:13`) |
| `eye_projection.h` | Validates OpenXR field of view and converts it to OpenVR tangent edges (top and bottom swapped) | `validEyeFov` (`eye_projection.h:6`), `eyeProjection` (`:10`) |
| `frame-menu-bridge.js` | Feeds Valve's Frame menus (performance, display, desktop windows, launchers) from the Frame service | `call` (`frame-menu-bridge.js:8`), `emit` (`:17`), `perf.UpdateSettings` (`:86`), `installVR` (`:120`), `chunks.push` (`:149`) |
| `game-launch-wrapper.c` | Execs `<self>.quest-real`, dropping the `--oom-score-adjust 900` argument; requests a loading boost first | `main` (`game-launch-wrapper.c:11`) |
| `gamescopereaper.c` | Runs one game as a subreaper; on primary exit it signals the game's process group and children | `main` (`gamescopereaper.c:23`), `children` (`:14`), `stop` (`:13`) |
| `glx-probe.c` | Diagnostic: imports a Vulkan DMA-BUF into GL through EGL or GLX and reads back a pixel | `main` (`glx-probe.c:16`) |
| `gpu-probe.c` | Diagnostic: Vulkan device, timeline-semaphore export and import, and swapchain present checks | `main` (`gpu-probe.c:10`) |
| `hand_skeleton.h` | Converts 26 OpenXR hand joints into 31 SteamVR bone transforms | `handSkeleton` (`hand_skeleton.h:24`), `handPoseValid` (`:17`), `HandBoneParents` (`:23`) |
| `headset_profile.h` | Reads the headset model file (defaults to Quest 2) and builds the device serial | `readHeadsetProfile` (`headset_profile.h:5`), `headsetSerial` (`:10`) |
| `ipc-probe.c` | Diagnostic: SysV shared memory, robust mutex and owner-death checks | `main` (`ipc-probe.c:29`), `killed_owner` (`:17`) |
| `local-vr-audio.h` | Starts PipeWire and WirePlumber for local VR, and stops them while streaming or the desktop owns audio | `LocalVRAudio::poll` (`local-vr-audio.h:45`), `start` (`:19`) |
| `lsof-launcher.c` | Answers Steam's CEF socket-owner query from `/proc`; any other query execs `/opt/quest/lsof` | `main` (`lsof-launcher.c:56`), `table` (`:22`), `output` (`:35`) |
| `mango-sensors.c` | Preload for MangoHud: an inaccessible thermal or drm sysfs directory reads as empty | `opendir` (`mango-sensors.c:11`) |
| `mesa-shared-timeline.h` | Mesa Turnip timeline semaphore whose payload is a 4 KiB memfd shared between processes | `quest_kgsl_queue_submit` (`mesa-shared-timeline.h:152`), `quest_timeline_wait` (`:77`), `quest_timeline_import` (`:102`) |
| `mirror-readback.h` | GPU blit of a swapchain image into a host-visible buffer for the spectator mirror | `MirrorReadback::record` (`mirror-readback.h:57`), `create` (`:33`), `read` (`:83`) |
| `network-bridge.h` | Presents Android's Wi-Fi state as NetworkManager D-Bus objects | `questNetwork::model` (`network-bridge.h:60`), `synchronize` (`:107`), `handle` (`:127`) |
| `network-interfaces.h` | Preloaded `getifaddrs`, `if_nametoindex` and `if_indextoname`, served from Android's interface table | `getifaddrs` (`network-interfaces.h:16`), `freeifaddrs` (`:52`), `if_nametoindex` (`:60`), `if_indextoname` (`:67`) |
| `pcvr_color_shader.h` | Rewrites one exact SPIR-V shader (Frame's SE2 final pass) to convert scene RGB to linear | `pcvrColorShader` (`pcvr_color_shader.h:10`) |
| `performance-boost.h` | Writes a 15-second monotonic boost deadline using write-then-rename | `quest_request_loading_boost` (`performance-boost.h:9`) |
| `power-bridge.h` | Presents battery and AC state as UPower objects with PropertiesChanged signals | `questPower::model` (`power-bridge.h:42`), `synchronize` (`:66`), `handle` (`:89`) |
| `quest_driver.cpp` | OpenVR server driver: HMD, two controllers, haptics, gamepad state and battery, all from the tracking files | `Provider::Init` (`quest_driver.cpp:204`), `RunFrame` (`:207`), `HmdDriverFactory` (`:257`), `readTracking` (`:44`) |
| `quest_wsi.cpp` | Vulkan ICD wrapper: compositor DMA-BUF swapchain to Android, room view, spectator mirror, and a capture swapchain for Steam | `vkCreateSwapchainKHR` (`quest_wsi.cpp:296`), `vkAcquireNextImageKHR` (`:305`), `vkQueuePresentKHR` (`:327`), `Swapchain::initialize` (`:262`), `vkRegisterDisplayEventEXT` (`:402`) |
| `roomview-bridge.js` | Mirrors Valve's room-view and gamepad-mode flags into the `stearlight_quest` VR settings section | `RegisterForSystemBehaviorFlags` wrapper (`roomview-bridge.js:9`), `RegisterForRoomViewChangedEvents` wrapper (`:27`) |
| `roomview_shaders.h` | Recognizes the room-view star, background and distort shaders and rewrites the compositor's copies | `roomViewShader` (`roomview_shaders.h:25`), `roomViewStarShader` (`:10`), `roomViewStarDraw` (`:18`), `roomViewBackgroundShader` (`:60`) |
| `runtime-monitor.cpp` | Process entry point for the VR monitor: starts services, SteamVR, the Steam client and the desktop handover | `main` (`runtime-monitor.cpp:188`), `Session::poll` (`:152`), `Session::startVR` (`:115`), `Session::startClient` (`:133`), `QuestShareStatus::poll` (`:36`) |
| `sdl3-gamepad.cpp` | Preload for SDL3: attaches the physical pad as an SDL3 virtual joystick; removes its own preload from `LD_PRELOAD` | `scopePreload` (`sdl3-gamepad.cpp:14`), `feed` (`:77`), `quest_SDL_Init` (`:116`), `dlsym` (`:124`) |
| `sdl-gamepad.cpp` | Preload for SDL2: feeds Quest gamepad state into SDL2 virtual joysticks; optional frame pacing for Ren'Py | `feed` (`sdl-gamepad.cpp:75`), `map` (`:65`), `SDL_Init` (`:145`), `SDL_GL_SwapWindow` (`:128`), `SDL_DYNAPI_entry` (`:154`), `dlsym` (`:181`) |
| `shader-replay-launcher.c` | Runs the real shader-replay tool with one thread and the Turnip ICD | `main` (`shader-replay-launcher.c:9`) |
| `share-mirror.h` | Layout and mapping of the bounded 1280x720 spectator mirror file | `QuestShareMirror` (`share-mirror.h:17`), `quest_share_map` (`:25`) |
| `socket-report.c` | Preload for socket calls: reports loopback sockets to Android, routes USB-subnet sockets over NCM, batches stream datagrams | `usb_socket` (`socket-report.c:50`), `report` (`:115`), `recv` (`:162`), `bind` (`:172`), `connect` (`:177`), `sendmmsg` (`:200`) |
| `steam-capture.h` | Preload for X11 capture: Steam's screen capture reads the compositor mirror instead of GLX | `glXGetProcAddress` (`steam-capture.h:14`), `quest_capture_image` (`:18`), `XShmGetImage` (`:45`), `XGetImage` (`:51`) |
| `steam-update-bridge.js` | Hides the BIOS update type from Steam's updater; keeps client and OS update results | `attach` (`steam-update-bridge.js:8`) |
| `steam-update-ui.cpp` | Preload for `exec*`: runs Valve's updater UI child on a private Gamescope compositor | `execute` (`steam-update-ui.cpp:57`), `execve` (`:138`), `getenv` (`:147`), `scopePreload` (`:38`) |
| `store-browser-bridge.js` | Starts Valve's VR Store browser on its real store origin | `views.Create` override (`store-browser-bridge.js:8`) |
| `store-browser-watch.c` | inotify watcher: reruns the Steam and CEF adapter scripts when Steam's files change | `quest_watch_step` (`store-browser-watch.c:19`), `prepare` (`:9`), `prepare_cef` (`:14`), `main` (`:66`) |
| `streaming-client-launcher.c` | Execs the streaming player with the video preload; prefers an advertised USB peer | `prefer_usb` (`streaming-client-launcher.c:12`), `main` (`:52`) |
| `streaming-drm.cpp` | Headless libdrm: one virtual 1280x720 connector and memfd-backed dumb buffers | `drmGetDevices2` (`streaming-drm.cpp:29`), `drmModeGetConnector` (`:45`), `drmIoctl` (`:77`) |
| `systemui-overlay-bridge.js` | Scopes overlay identity to `system.systemui` on the systemui page | overrides at `systemui-overlay-bridge.js:7-8` |
| `video-bridge.cpp` | Preload for the private V4L2 decoder: forwards packets to Android over a socket and copies frames into DMA-BUF captures | `Device::run` (`video-bridge.cpp:87`), `Device::exchange` (`:67`), `fakeOpen` (`:173`), `open` (`:213`), `ioctl` (`:216`), `epoll_wait` (`:277`), `poll` (`:283`), `SDL_LoadObject` (`:205`) |
| `video_image_layout.h` | Makes the decoder's linear NV12 planes match the player's expected layout | `linearVideoPlanes` (`video_image_layout.h:7`), `LinearVideoImage::prepare` (`:30`) |
| `video_sequence.h` | Reads HEVC SPS width and height from a bitstream without altering it | `hevcSpsDimensions` (`video_sequence.h:21`), `hevcDimensions` (`:39`) |
| `wine-pe-memory.c` | Preload: declines Wine's fixed, writable, private PE header mapping with `EACCES` | `private_pe` (`wine-pe-memory.c:11`), `mmap` (`:23`), `mmap64` (`:35`) |

### Interfaces
- **Inputs / outputs:**
  - Shared files under `/run/stearlight/quest/` (the Android app writes most of them):
    - `tracking`: read and mapped as `QuestTracking`, `quest_driver.cpp:204`; `quest_wsi.cpp:43`, `:119`, `:409`; `display-pulse.h:14`.
    - `tracking-motion` and `hands`: read and mapped, `quest_driver.cpp:32`, `:39`.
    - `gamepad`: created, sized and mapped read-write by the driver, `quest_driver.cpp:211-212`. Read by `sdl-gamepad.cpp:68` (`O_NOFOLLOW`).
    - `external-gamepad`: read-only map, `external-gamepad-reader.h:16` (override `STEARLIGHT_EXTERNAL_GAMEPAD_STATE`, `:15`).
    - `device.json`: battery and charging, `quest_driver.cpp:113`; `power-bridge.h:68`; `bluetooth-bridge.cpp:61` (radio flags).
    - `headset-profile`: `headset_profile.h:6`. `play-space.vrchap`: `quest_driver.cpp:79-80`.
    - `passthrough.supported`, `passthrough.enabled`, `passthrough.composition-ready`: `quest_driver.cpp:66`; `runtime-monitor.cpp:217`, `:304-305`; `quest_wsi.cpp:273`, `:306`, `:459`, `:467`.
    - `passthrough-style.tsv` (write-then-rename): `runtime-monitor.cpp:277-279`.
    - `desktop-mode.active`, `desktop-mode.ready`, `desktop-focus.request`: `runtime-monitor.cpp:154`, `:163`, `:322`.
    - `dashboard.ready`, `bootstrapper.ready`: `runtime-monitor.cpp:221-222`.
    - `local-vr.pid`, `local-vr-audio.paused`, `local-vr-audio.supported`: `local-vr-audio.h:13-15`.
    - `performance-boost.request`: `performance-boost.h:10`.
    - `share-mirror` (1280x720, read-write map): `share-mirror.h:16`.
    - `gpu.sock` (client, `SOCK_SEQPACKET`): `quest_wsi.cpp:262`.
    - `video.sock` (client, `SOCK_STREAM`; `QUEST_VIDEO_SOCKET` overrides): `video-bridge.cpp:65`.
    - `haptics.sock` (datagram send): `quest_driver.cpp:248-250`.
    - `network-interfaces.tsv`, `usb-network-scope`, `usb-network.sock`, all under the `QUEST_SOCKET_REGISTRY` directory: `network-interfaces.h:14`, `socket-report.c:41`, `:93`, `streaming-client-launcher.c:19`.
    - `network.tsv` (read): `network-bridge.h:108`. `network-scan.request`, `network-settings.request` (write): `network-bridge.h:57`.
    - `bluetooth-devices.tsv` (read): `bluetooth-bridge.cpp:288`. `bluetooth-command.tmp` then `.json` (write, rename): `bluetooth-bridge.cpp:143-148`. `bluetooth-reply.json` (poll): `bluetooth-bridge.cpp:153`.
  - Other paths: `/tmp/quest-pipewire.log`, `/tmp/quest-wireplumber.log` (`local-vr-audio.h:22`); `/tmp/stearlight-steamvr-native.log` (`runtime-monitor.cpp:120`); `/tmp/quest-native-updater.log` (`steam-update-ui.cpp:24`, `:65`); `/home/stearlight/.cache/stearlight/os-update/activated.json` renamed to `installed.json` (`runtime-monitor.cpp:374-376`); `/home/stearlight/.local/state/stearlight-desktop/api-token` (`desktop-pam.c:19`); `/home/stearlight/.local/share/Steam/logs/steam_output.log` (`runtime-monitor.cpp:143`); `/dev/quest-video-memory` (`streaming-drm.cpp:22`, `video-bridge.cpp:174`); `/dev/video0` (`video-bridge.cpp:175`); `/proc/net/tcp` (`lsof-launcher.c:23`).
  - Environment variables read: `QUEST_SOCKET_REGISTRY` (`socket-report.c:67`, `network-interfaces.h:11`, `streaming-client-launcher.c:14`); `QUEST_STREAM_SOCKET_BATCH` (`socket-report.c:147`, set at `streaming-client-launcher.c:66`); `QUEST_VIDEO_STATEFUL` (`video-bridge.cpp:51`, `quest_wsi.cpp:438`); `QUEST_VIDEO_SOCKET` (`video-bridge.cpp:65`); `QUEST_VIDEO_TRACE` (`video-bridge.cpp:223`); `QUEST_FRAME_FINAL_PASS` (`quest_wsi.cpp:466`, set at `compositor-launcher.c:8`); `QUEST_MANGO_EMPTY_SENSORS` (`mango-sensors.c:17`); `QUEST_PIPEWIRE_PID`, `QUEST_WIREPLUMBER_PID` (`local-vr-audio.h:31`); `STEARLIGHT_GAMEPAD_STATE` (`sdl-gamepad.cpp:67`); `STEARLIGHT_STEAM_INPUT` (`sdl-gamepad.cpp:77`); `STEARLIGHT_WINE_GAMEPAD` (`sdl-gamepad.cpp:145`); `STEARLIGHT_RENPY_SDL` (`sdl-gamepad.cpp:49`, `:162`); `STEARLIGHT_DESKTOP_ACCESS` (`desktop-access-runtime.c:15`); `STEARLIGHT_DESKTOP_PAM_RESERVE` (`desktop-pam.c:17`); `STEARLIGHT_PROTON_DIRECT` (`gamescopereaper.c:27`); `STEARLIGHT_VRLINK_PREFER_USB` (`streaming-client-launcher.c:13`); `STEARLIGHT_VRLINK_SUBMIT_DELAY_US` (`streaming-client-launcher.c:60`); `STEARLIGHT_NATIVE_STEAMVR_WAIT_FOR_STEAM`, `STEARLIGHT_DESKTOP_VR_RUNTIME` (`runtime-monitor.cpp:122-123`); `LD_PRELOAD` (`streaming-client-launcher.c:63`, `sdl3-gamepad.cpp:15`, `steam-update-ui.cpp:39`); `PIPEWIRE_RUNTIME_DIR` (`local-vr-audio.h:77`). Environment set for children: `VK_ICD_FILENAMES` (`compositor-launcher.c:7`, `runtime-monitor.cpp:127`, `:145`, `steam-update-ui.cpp:72`), `EGL_PLATFORM=surfaceless` (`streaming-client-launcher.c:65`), `DISPLAY=:0` default (`streaming-client-launcher.c:68`).
  - D-Bus: `bluetooth-bridge.cpp` takes `org.bluez`, `org.freedesktop.NetworkManager` and `org.freedesktop.UPower` on the system bus (`bluetooth-bridge.cpp:531-548`) and serves `/org/bluez/hci0` (`:234`), `/org/freedesktop/NetworkManager` (`network-bridge.h:6`) and `/org/freedesktop/UPower` (`power-bridge.h:9`). Calls out to the client: `org.freedesktop.DBus.Properties.GetAll` on the advertising object (`bluetooth-bridge.cpp:472-480`).
  - Localhost HTTP: `127.0.0.1:27771` POST with a bearer token, used by the desktop service (`desktop-pam.c:32`, `desktop-ui-bridge.js:8`, `frame-menu-bridge.js:9`). Operations include `status`, `performance-boost`, `developer`, `client-channel`, `frame-settings`, `focus-window`, `launch-app` (`desktop-ui-bridge.js:24`, `:72`, `:100`, `:155`; `frame-menu-bridge.js:75`, `:98`, `:109`, `:118`, `:127`).
  - SteamVR settings written: section `stearlight_quest`, keys `gamepad_left`, `gamepad_right` (`roomview-bridge.js:13-14`, read at `quest_driver.cpp:217-218`) and `passthrough_enabled` (`roomview-bridge.js:31`, read at `runtime-monitor.cpp:281`). Camera settings read at `runtime-monitor.cpp:269-270`.
  - Stdout markers (grep targets): `QUEST_BLUETOOTH_BRIDGE_READY` (`bluetooth-bridge.cpp:553`), `QUEST_DESKTOP_PROCESS_BUDGET` (`runtime-monitor.cpp:81`), `QUEST_NATIVE_DASHBOARD_TEXTURE` (`runtime-monitor.cpp:378`), `QUEST_REMOTE_DESKTOP_VR_RESTARTING` (`runtime-monitor.cpp:246`, then exit 75 at `:247`).
  - KWin and Steam UI: `desktop-windows.js` prints `STEARLIGHT_WINDOWS` on stdout (`desktop-windows.js:8`). Page scripts read `SteamClient`, `settingsStore`, `UpdateStore.m_updater` and `VRHTML` (`desktop-ui-bridge.js:48-49`; `frame-menu-bridge.js:77-78`; `steam-update-bridge.js:9`; `roomview-bridge.js:4`).
  - Android intents and JNI: none in this module.
- **Wire formats:**
  - `QuestTracking`, `QuestGamepadState`, `QuestExternalGamepad`, `QuestHaptic`, `QuestGpuHello`/`QuestGpuPresent`/`QuestGpuRelease`, `QuestVideoRequest`/`QuestVideoResponse`: defined in `packages/quest-runtime/app/src/main/cpp/` (`quest_bridge.h:16`, `:21`; `gamepad_state.h:7`; `external_gamepad.h:6`; `gpu_bridge.h:6`, `:9`, `:13`; `video_protocol.h:8`, `:13`). Read or written here at the lines above (`quest_driver.cpp:249`; `quest_wsi.cpp:262-266`; `video-bridge.cpp:67-71`).
  - `QuestShareMirror`: `magic`, `version`, `requested_ns`, `sequence`, `reserved`, `frame`, then 1280x720x4 bytes of pixels. `share-mirror.h:17-23`.
  - Mesa timeline payload: `magic` (u64), `value` (u64), `epoch` (u32) in a 4096-byte memfd, magic `0x5351544c00000001`. `mesa-shared-timeline.h:12-16`, `:42`, `:117`.
  - SDL3 virtual joystick descriptor: 136 bytes, asserted at `sdl3-gamepad.cpp:28-33`.
  - Bluetooth command file: `{"id":N,"operation":"...","properties":{...}}`, `bluetooth-bridge.cpp:144-145`. Reply is matched by `"id":N,` and `"success":true`, `bluetooth-bridge.cpp:154-156`.
  - Passthrough style file: `1 <style> <hue> <r> <g> <b> <a> <strength>`, one line, `runtime-monitor.cpp:272-275`.
  - USB scope file: `%u %15s %u %llu` (scope, local IPv4, prefix bits, generation), `socket-report.c:44`. USB request and reply are `int32` on `usb-network.sock`, `socket-report.c:99`, `:105`.
  - Network state TSV: `enabled`, `connected`, `validated`, `current`, and `ap` rows of six fields, `network-bridge.h:64-72`.

### Depends on / used by
- **Depends on:**
  - `quest-app-native`: the shared structs and headers above (`app/src/main/cpp/`), plus `device_profile.h` via `headset_profile.h:2`.
  - The Android app, through the `/run/stearlight/quest/` files it writes (the app side of the same contract is not in this module).
  - Platform libraries, looked up at runtime rather than linked: OpenVR (`quest_driver.cpp:2`, `runtime-monitor.cpp:2`), Vulkan, D-Bus (`bluetooth-bridge.cpp:12`), libdrm (`streaming-drm.cpp:1-2`), PAM (`desktop-pam.c:2-3`), X11 and Xext (`steam-capture.h:3-4`), SDL2 and SDL3 through `dlsym` (`sdl-gamepad.cpp:18-53`, `sdl3-gamepad.cpp:44-69`), Mesa Turnip internals (`mesa-shared-timeline.h:152-199`).
  - The desktop service on `127.0.0.1:27771` (quest-linux-session, not read here).
  - Launch and helper scripts run from here: `/opt/quest/prepare-steam-client.sh` and `/opt/quest/prepare-cef.sh` (`store-browser-watch.c:10`, `:15`; `runtime-monitor.cpp:181`), `/opt/steam/RUNSTEAM.sh` (`runtime-monitor.cpp:147`). The `.sh` files are outside this module.
- **Used by:**
  - Preloads loaded by path: `libquest_video.so` (`streaming-client-launcher.c:63`), `libquest_streaming_drm.so` (`video-bridge.cpp:209`), `libquest_socket.so` (`steam-update-ui.cpp:77`), `libquest_steam_update_ui.so` (`steam-update-ui.cpp:44`), `libquest_android_gamepad.so` (`sdl3-gamepad.cpp:19`), `libquest_vulkan.so` (`gpu-probe.c:12`).
  - Process wrappers exec'd by the session: `compositor-launcher.c` (execs `vrcompositor.bin`), `runtime-monitor.cpp:128` (execs `/usr/local/bin/stearlight-steamvr-native`), `game-launch-wrapper.c`, `gamescopereaper.c`, `shader-replay-launcher.c`, `streaming-client-launcher.c`, `lsof-launcher.c`.
  - `runtime-monitor.cpp` includes `store-browser-watch.c` (`:46`, with `QUEST_WATCH_EMBEDDED` at `:45`), `local-vr-audio.h` (`:47`), `share-mirror.h` (`:16`), `performance-boost.h` (`:17`); it starts `quest_services_run` in a thread (`:24`, `:193`) from `bluetooth-bridge.cpp:521`.
  - `bluetooth-bridge.cpp` includes `network-bridge.h` and `power-bridge.h` (`:518-519`).
  - `socket-report.c` includes `network-interfaces.h` (`:21`), `steam-capture.h` (`:22`) and `capture-matrix.h` with `QUEST_CAPTURE_MATRIX_EXPORTS` (`:23-24`).
  - `quest_wsi.cpp` includes `share-mirror.h`, `roomview_shaders.h`, `pcvr_color_shader.h`, `display-pulse.h`, `video_image_layout.h` and `mirror-readback.h` (`:25-69`).
  - `quest_driver.cpp` includes `controller_pose.h`, `eye_projection.h`, `headset_profile.h`, `hand_skeleton.h` (`:5-10`).
  - `sdl-gamepad.cpp` and `sdl3-gamepad.cpp` include `external-gamepad-reader.h` (`sdl-gamepad.cpp:4`, `sdl3-gamepad.cpp:3`).
  - `game-launch-wrapper.c` includes `performance-boost.h` (`:6`); `video-bridge.cpp` includes `video_sequence.h` (`:2`).
  - Page scripts are injected into Steam's UI by the session (injection code is not in this module). `desktop-windows.js` runs inside KWin.

### Open issues
- `#4` Send no frame payload after a failed video response (its `Where:` names `linux/video-bridge.cpp:69`)
- `#6` Close received DMA-BUF fds on every early return in swapchain setup
- `#7` Stop CheckConnectivity from inserting an empty value before the first sync
- `#8` Reject out-of-range image indices in vkQueuePresentKHR
- `#29` Stop the Mesa shared-timeline submit from blocking on the KGSL fence
- `#30` Wait for the release fence in vkQueuePresentKHR without holding the swapchain lock
- `#31` Read the socket batching switch once per process
- `#32` Back off the shared gamepad state lookup when the file is missing
- `#33` Copy decoded frames into the capture buffer outside the device lock
- `#34` Look up epoll registrations without copying the whole map
- `#35` Stop the emulated poll() from waking every millisecond while idle
- `#36` Skip re-parsing bluetooth-devices.tsv when its text is unchanged
- `#37` Send the developer-mode setting only when it changes
- `#45` Stop the Bluetooth radio request from blocking the D-Bus loop
- `#46` Read advertisement properties without calling back into the client
- `#60` Run the Bluetooth and power bridge tests in check.sh
- `#62` Build and run the linear NV12 plane layout test in CI
- `#84` Open the update log with O_NOFOLLOW and O_EXCL
- `#109` Steam signs in with phone approval and shows my library
- `#111` A game plays 30 minutes with no visible jitter or crash
- `#113` Quest controllers drive a game as a gamepad
- `#114` A Bluetooth keyboard or gamepad pairs from the headset

### Notes
- Shims must stay ABI-exact. Android's seccomp policy traps real `setresuid`/`setresgid`, so `audio-identity.c:5-7` accepts only unchanged IDs and never simulates a change (`audio-identity.c:8-21`). `video-bridge.cpp:30-31` limits adaptation to the private decoder.
- The shared tracking files use a seqlock. The writer makes `sequence` odd while it updates, and readers retry (`quest_driver.cpp:44`, `display-pulse.h:18-21`, `quest_wsi.cpp:126-129`). Odd or changing sequences are never used as data.
- Some locks are held across slow work. `video-bridge.cpp:125-169` holds `Device::mutex` across the DMA-BUF sync and frame copy. `quest_wsi.cpp:330` takes `swap->lock` before the fence waits at `:341` and `:362`. Both are open issues (`#33`, `#30`).
- `network-bridge.h` and `power-bridge.h` depend on names defined only in `bluetooth-bridge.cpp`: `directory` (`bluetooth-bridge.cpp:18`) and `read()` (`:56`). `network-interfaces.h:21` depends on `quest_fscanf`, declared in `socket-report.c:20`. Neither header compiles alone.
- `runtime-monitor.cpp:247` returns 75 after a remote-desktop handover. The Android owner must start a new Linux session, because the Valve bootstrap IPC cannot be reused (`runtime-monitor.cpp:243-246`).

## quest-linux-session
**Path:** `packages/quest-runtime/linux/`   **Status:** present   **Serves:** M1, M3, M4, M5, M6   **Platforms:** Quest 2 runtime (Snapdragon XR2 Gen 1, Adreno 650; ARM64 Linux guest under PRoot)
**Purpose:** This module starts the Linux side of the app. It brings up the X server, audio, D-Bus and the GPU and IPC probes, then starts SteamVR and the desktop manager. It also holds the launchers that run Steam's Proton, FEX and Flatpak games and desktop apps, and the adapters that patch Valve's ARM64 binaries after each Steam update.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `start-session.sh` | Session entry point. Sets the environment, runs the GPU and IPC probes, starts D-Bus, Xvfb, PulseAudio, PipeWire and WireLumber, and applies the SteamVR and Steam adapters. Ends by replacing itself with the runtime monitor. | script body (`start-session.sh:4`), probes (`start-session.sh:48`, `:56`), Xvfb (`start-session.sh:85`), exec (`start-session.sh:172`) |
| `desktop-session.sh` | Starts the Plasma workspace. The `headset` mode runs `kwin_wayland` nested; the `remote` mode starts the core session. | `desktop-session.sh:137` (headset branch), `:160` (kwin_wayland exec), `:166` (remote exec) |
| `plasma-core-session.sh` | Runs the KDE splash, the KDE config setup stages, and `plasmashell`. Writes the shell environment file. | `plasma-core-session.sh:19` (ksplashqml), `:40` (env file writer), `:55` (plasmashell) |
| `desktop-app-session.sh` | Runs one desktop application inside the Plasma environment, with native single-window switches for Dolphin, Konsole and VLC. | `desktop-app-session.sh:20` (switches), `:26` (exec) |
| `desktop-run-app.sh` | Drops the app id and name arguments, then calls `desktop-app-session.sh`. | `desktop-run-app.sh:3` |
| `desktop-headset.sh` | Runs the nested Gamescope compositor for the headset desktop on the OpenVR backend. | `desktop-headset.sh:12` (gamescope exec) |
| `desktop-remote.sh` | Remote Desktop (XRDP) session entry. Calls `stearlight-desktop remote-start`, then runs the core session. | `desktop-remote.sh:8`, `:10` |
| `desktop-shell.sh` | Wrapper for shells opened inside the desktop. Loads the shell environment file when the instance variable is not set. | `desktop-shell.sh:7` (env load), `:16` (exec) |
| `desktop-launcher.sh` | Shortcut that starts the desktop manager in `start` mode. | `desktop-launcher.sh:3` |
| `desktop-device-settings.sh` | Writes a request file for headset, Wi-Fi or Bluetooth settings. | `desktop-device-settings.sh:4` |
| `desktop-manager.py` | Owns the desktop: its loopback RPC server, the Plasma and display lifecycle, developer access (SSH, XRDP), the desktop password, and Frame menus. | `serve` (`desktop-manager.py:526`), `Manager.call` (`:434`), `Manager.poll` (`:198`), `Manager.set_password` (`:244`), `Manager.prepare_access` (`:262`), `accept_ssh` (`:417`), `atomic` (`:39`) |
| `frame_menus.py` | Frame menu data: launchable apps, launch history, open windows, performance settings, the MangoHud overlay, and KWin script loading. | `applications` (`frame_menus.py:74`), `FrameMenus.call` (`:365`), `FrameMenus.poll` (`:264`), `FrameMenus.poll_performance` (`:308`), `start_app` (`:410`), `app_number` (`:28`) |
| `gamescope-perf.py` | Short-lived X11 client that writes Gamescope scaling properties and tags game windows with the `STEAM_GAME` atom. | `apply` (`gamescope-perf.py:14`), `main` (`:100`) |
| `desktop-defaults.py` | Sets Plasma and KDE defaults without overwriting user layouts. Prints the locale exports used by the session. | `configure` (`desktop-defaults.py:24`), `locale` (`:86`), `main` (`:97`) |
| `flatpak-launcher.py` | Replaces the `flatpak` command. Keeps the native installer for setup and sends `run` requests to the desktop manager through the request directory. | `run_arguments` (`flatpak-launcher.py:27`), `consent` (`:66`), `request` (`:138`), `launch` (`:177`), `main` (`:208`) |
| `prepare-flatpak.py` | Installs the `flatpak` wrapper and the empty system repository, and adds the Flathub remote per user. | `prepare` (`prepare-flatpak.py:13`) |
| `proton-game-launcher.py` | Runs Valve's ARM64 Proton. Applies per-game profiles (VTOL, Outer Wilds, Garden of Witches), sets the Proton environment, and runs flat Unity games under Gamescope. | `prepare_platform` (`proton-game-launcher.py:20`), `prepare_vtol_textures` (`:87`), `backup_original` (`:140`), `prepare_outerwilds_textures` (`:168`), `launch_environment` (`:282`), `launch_flat_panel` (`:358`), `exec_proton` (`:385`), `main` (`:411`) |
| `proton-runtime-entry.sh` | Replaces Valve's SteamLinuxRuntime entry point. Runs the Proton launcher with the system Python. | `proton-runtime-entry.sh:7` |
| `fex-game-launcher.py` | Runs x86 games through FEX in the installed Steam runtime. Builds a per-game rootfs, applies the Celeste renderer and Ren'Py native-engine profiles, and runs FEX under Gamescope. | `prepare_rootfs` (`fex-game-launcher.py:33`), `prepare_celeste_memory` (`:171`), `native_renpy` (`:240`), `main` (`:261`) |
| `chromium-launcher.sh` | Starts the bundled Chromium with Quest-specific flags. Renderer and utility processes are re-run through this script. | `chromium-launcher.sh:14` (child re-exec), `:30` (browser exec) |
| `cef-arguments.sh` | Sourced by the two CEF launchers. Adds the feature flags Quest needs to the Chromium switches. | `cef-arguments.sh:4` |
| `steamwebhelper-launcher.sh` | Replaces Valve's `steamwebhelper`. Sets its process limits and log path. | `steamwebhelper-launcher.sh:11` |
| `webhelper-launcher.sh` | Replaces the SteamVR web helper. Runs it on ANGLE with Vulkan. | `webhelper-launcher.sh:12` |
| `audio-namespace-launcher.sh` | Replaces Steam's PipeWire audio namespace helper. Runs the wrapped command directly. | `audio-namespace-launcher.sh:7` |
| `steam-channel-args.sh` | Sourced by Valve's `RUNSTEAM.sh`. Adds `-noshaders`, chooses the Steam feed from the channel file, and handles the forced-update trigger. | `steam-channel-args.sh:5` (shader flag), `:16` (argument rewrite), `:34` (feed file), `:37` (trigger) |
| `prepare-desktop.sh` | Desktop setup run at each session start. Removes Baloo plugins, patches KIO, writes the Chromium desktop entry, adds symlinks into `/usr`, and runs the Flatpak setup. | `prepare-desktop.sh:18` (KIO patch), `:19` (Chromium entry), `:40` (manager symlink), `:43` (settings entries), `:83` (Flatpak setup) |
| `prepare-desktop-cli.sh` | Installs the pinned command-line tool packages once, with `apk --usermode`. | `prepare-desktop-cli.sh:8` |
| `prepare-desktop-kio.py` | Patches the KIO library so idle worker processes are reaped after 5 seconds. | `prepare` (`prepare-desktop-kio.py:25`), `PATCHES` (`:14`) |
| `prepare-desktop-ui.py` | Writes the desktop API bridge into Steam's `sp.js` or `library.js`, with a begin and end marker. Creates the desktop token file. | module body (`prepare-desktop-ui.py:9`), markers (`:17`), write (`:32`) |
| `prepare-frame-controls.sh` | Patches the SteamVR dashboard painter and the control panel binding to the systemui atlas. Each patch needs exactly one match. | `prepare-frame-controls.sh:8` (painter), `:25` (panel), `:54` (write) |
| `prepare-game-runtime.sh` | Installs the Quest launcher, shader-replay, Proton entry and audio namespace adapters into the Steam runtime, and the FEX tool. | `prepare-game-runtime.sh:10` (launch wrapper), `:25` (shader replay), `:41` (Proton entry), `:54` (audio), `:64` (FEX tool) |
| `prepare-steam-client.sh` | Steam-client setup run before each Steam start. Restores the web helper launcher, patches `RUNSTEAM.sh`, and runs the other `prepare-*` steps and `steam_channels.py`. | `prepare-steam-client.sh:10` (web helper), `:20` (channel hook), `:50` (update UI hook), `:62` (frame-steam-ipc), `:65` (steam_channels), `:66` (desktop UI) |
| `prepare-store-browser.sh` | Inserts the store-origin bridge and the update-capabilities bridge into Steam's `library.js`. | `prepare-store-browser.sh:11`, `:27` |
| `prepare-streaming-client.sh` | Replaces the streaming client and VRLink entry points with the Quest launcher. Keeps the Valve binary as `.real`. | `prepare-streaming-client.sh:12` (swap), `:20` (`.real` check), `:29` (input adapter) |
| `prepare-streaming-input.py` | Rewrites VRLink's controller type and input source table so Frame controls look like Oculus Touch. Restores the original on request. | `prepare` (`prepare-streaming-input.py:57`), `transform` (`:18`), `LENGTHS` (`:13`), `main` (`:112`) |
| `prepare-steam-input.py` | Returns the SDL HIDAPI detection routine immediately, so the unavailable Linux raw-HID poller stops retrying. | `prepare` (`prepare-steam-input.py:40`), `BUILDS` (`:12`), `main` (`:72`) |
| `prepare-steam-integrity.py` | Repairs the Steam UI library (`steamui.so`) from the matching Valve package when its CRC does not match. Downloads the package only if it is missing or fails its SHA-256 check. | `prepare` (`prepare-steam-integrity.py:32`), `MEMBER` (`:12`), `main` (`:99`) |
| `prepare-vrclient.sh` | Patches SteamVR's `vrclient.so` cleanup loop for null shared-resource entries. Exits 1 on an unknown build. | `prepare-vrclient.sh:5` (checks), `:28` (stub) |
| `prepare-cef.sh` | Adds a null guard to Steam's `libcef.so` udev enumeration. Exits 1 on an unknown build. | `prepare-cef.sh:4` (checks), `:21` (patch) |
| `prepare-fex.py` | Patches the Steam FEX build's signal delegator so the fault page access is accepted. | `prepare` (`prepare-fex.py:47`), `PATCHES` (`:23`), `main` (`:76`) |
| `prepare-gamepad-ui.py` | Refreshes the room-view and input bridge in the installed SteamVR `systemui.js`. | `refresh` (`prepare-gamepad-ui.py:7`), `main` (`:24`) |
| `adb-command.py` | Decodes a base64 command argument and runs it with `bash -lc` through `desktop-shell.sh`. | `adb-command.py:6` (decode), `:7` (exec) |

### Interfaces
- **Inputs / outputs:**
  - Environment in: `STEARLIGHT_QUEST_RUNTIME` (`start-session.sh:6`), `STEARLIGHT_LINUX_HIDAPI` (`start-session.sh:13`), `QUEST_SOCKET_REGISTRY` (`start-session.sh:18`, `desktop-headset.sh:10`), `QUEST_NATIVE_PULSE` (`start-session.sh:72`), `STEAM_EXTRA_ARGS` (`start-session.sh:166`), `STEARLIGHT_FAKE_TRACKING` (`start-session.sh:167`), `STEARLIGHT_STEAMVR_ROOT` and `STEARLIGHT_STEAM_ROOT` (`prepare-streaming-client.sh:5`, `prepare-vrclient.sh:4`, `prepare-steam-client.sh:3`).
  - Environment for games: `SteamAppId` (`proton-game-launcher.py:422`, `fex-game-launcher.py:245`), `STEAM_COMPAT_INSTALL_PATH` and `STEAM_COMPAT_DATA_PATH` (`proton-game-launcher.py:441`, `fex-game-launcher.py:249`, `fex-game-launcher.py:282`), `STEARLIGHT_QUEST_GAME_PROFILE` (`proton-game-launcher.py:368`, `fex-game-launcher.py:336`), `STEARLIGHT_STEAM_INPUT` (`proton-game-launcher.py:288`, `fex-game-launcher.py:285`), `STEARLIGHT_SHADER_CACHE_MAX_SIZE` (`proton-game-launcher.py:303`).
  - Shared state under `/run/stearlight/quest/`: `linux-status` written (`start-session.sh:32`, `:49`, `:53`, `:57`, `:168`); stale markers removed (`start-session.sh:31`); `desktop-mode.active`, `desktop-mode.ready`, `desktop-focus.request` (`desktop-manager.py:31-33`); `performance-boost.request` and `interaction-boost.request` (`desktop-manager.py:34-35`, written at `:440`, `:456`); `desktop-shell.env` (written `plasma-core-session.sh:43-53`, removed `desktop-manager.py:194`); `desktop-app-requests/` (`flatpak-launcher.py:180`); `desktop-device-settings.request` (`desktop-device-settings.sh:4`); `local-vr.pid`, `local-vr-audio.supported`, `local-vr-audio.paused` (`proton-game-launcher.py:310-320`, `fex-game-launcher.py:19-30`); `performance-profile` (`frame_menus.py:159`); `tracking` (read, `frame_menus.py:220`); `desktop-services/*.service` symlinks (`desktop-session.sh:152-154`, `desktop-manager.py:61-62`).
  - Sockets: `/tmp/.X11-unix/X*` (`frame_menus.py:314`, `gamescope-perf.py:31`); `$XDG_RUNTIME_DIR/bus` (`start-session.sh:64`, `desktop-session.sh:151`); `$XDG_RUNTIME_DIR/pulse/native` (`start-session.sh:65`); `$XDG_RUNTIME_DIR/pipewire-0` (`start-session.sh:102`); `/run/stearlight/quest/socket-registry.sock` (`start-session.sh:18`).
  - D-Bus: `org.kde.KWin` `/Scripting` via `dbus-send` (`frame_menus.py:249-262`); `org.kde.KSplash` and `org.kde.plasmashell` (`plasma-core-session.sh:27-37`, `:60`); system bus config `/opt/quest/system-bus.conf` (`start-session.sh:63`).
  - TCP: `127.0.0.1:27771` RPC (`desktop-manager.py:36`, `:582`); `0.0.0.0:2222` SSH (`desktop-manager.py:290`, `sshd_config` at `:267-283`); `tcp://:3389` XRDP (`desktop-manager.py:326`).
  - Files written in the guest: `/etc/hostname`, `/etc/hosts`, `/etc/passwd` (`start-session.sh:26`, `:28-30`, `:45-46`); `/etc/shadow` (`desktop-manager.py:255-259`); `/etc/pam.d/xrdp-sesman` (`desktop-manager.py:315-318`); `/etc/xrdp/rsakeys.ini` symlink (`desktop-manager.py:308-310`); `/usr/lib/security` symlinks (`desktop-manager.py:311-314`); `/usr/bin/flatpak` and `/usr/local/bin/stearlight-desktop` (`prepare-flatpak.py:22-24`, `prepare-desktop.sh:40`).
  - Manager state under `/home/stearlight/.local/state/stearlight-desktop/`: `settings.json` (`desktop-manager.py:28`, `:92`), `api-token` (`desktop-manager.py:27`, `:527-530`; `prepare-desktop-ui.py:13-16`), `sshd_config`, `xrdp.ini`, `sesman.ini`, `xorg.conf`, RDP and SSH keys (`desktop-manager.py:265-266`, `:303-307`, `:319-325`, `:359-399`); per-process logs `<name>.log` (`desktop-manager.py:130`).
  - Log files: `/tmp/quest-desktop-manager.log` (`start-session.sh:69`), `/tmp/xvfb.log` (`start-session.sh:85`), `/tmp/quest-audio.log` (`start-session.sh:74`), `/tmp/quest-pipewire.log` (`start-session.sh:99`), `/tmp/quest-runtime-monitor.log` (`start-session.sh:172`), `/tmp/quest-proton-<appid>.log` (`proton-game-launcher.py:427`).
  - Xvfb runs as `:0` with `-ac -nolisten tcp` (`start-session.sh:85`), so the local display has access control off.
  - Flatpak request files `<uuid>.request` and result files `<uuid>.result` (`flatpak-launcher.py:183-202`).
  - Android: no JNI or intent in this module. The APK starts `/bin/bash /opt/quest/start-session.sh` under PRoot (`QuestActivity.java:172`).
  - Binary patch targets, all in place: Steam `libSDL3.so.0` and `libSDL2-2.0.so.0` (`prepare-steam-input.py:74-75`), Steam FEX `usr/bin/FEX` (`prepare-fex.py:79`), SteamVR `vrclient.so` (`prepare-vrclient.sh:4`), `libcef.so` (`prepare-cef.sh:4`), `libKF6KIOCore.so.6` (`prepare-desktop-kio.py:58`), Steam `sp.js` or `library.js` (`prepare-desktop-ui.py:19-23`).
  - Fallback download: `https://client-update.akamai.steamstatic.com/` for a matching Steam package (`prepare-steam-integrity.py:67`).
  - Files referenced but not in this directory: `frame-steam-ipc` (`prepare-steam-client.sh:62`, `|| true`), `stearlight-steamvr-native` (`start-session.sh:126`), `stearlight-frame-vrwebhelper` (`start-session.sh:131`), `/opt/quest/gpu-probe`, `ipc-probe`, `glx-probe`, `runtime-monitor` (`start-session.sh:48`, `:56`, `:119`, `:172`).
- **Wire formats:**
  - Desktop RPC (`desktop-manager.py:532-580`, `:610-617`): HTTP POST to `127.0.0.1:27771`. Header `Authorization: Bearer <token>`. Body is JSON `{"operation": str, ...args}` with 1 to 8192 bytes. Reply is `{"ok": true, "value": ...}` or `{"ok": false, "error": "..."}`. Accepted `Origin` values are `steamloopback.host` and `127.0.0.1` (`desktop-manager.py:540`).
  - Flatpak run request (`flatpak-launcher.py:173-174`): JSON `{root, bindings: [{source, target}], environment: {...}, command: [...], cwd}`. Result (`flatpak-launcher.py:193-202`): JSON `{state: "running" | "exited", code?, error?}`.
  - Tracking file (`frame_menus.py:220-224`): at least 24 bytes. Little-endian u32 magic `0x53515231` and u32 version `2`. Float32 refresh rate at offset 20, accepted range 50 to 150 Hz.
  - Window log line (`frame_menus.py:291-301`): a line containing `STEARLIGHT_WINDOWS ` followed by a JSON list of `{id, title, app_id}`. At most 128 entries; titles are cut to 512 characters.
  - X11 properties (`gamescope-perf.py:40-87`): 32-bit CARDINAL. `GAMESCOPE_NEW_SCALING_FILTER` maps 1, 2, 3 to 0, 1, 2. `GAMESCOPE_NEW_SCALING_SCALER` is scaler minus 1. `GAMESCOPE_SHARPNESS` is 0 to 20. `STEAM_GAME` on each client window holds the app number (`frame_menus.py:28-29`, `:323`).
  - Overlay preset map (`frame_menus.py:350-351`): Steam levels 4, 1, 2, 3 map to MangoHud presets 1, 2, 3, 4.
  - Binary patch tables: `prepare-fex.py:23-44` (20 `(offset, before, after)` hex instruction words, file offsets); `prepare-steam-input.py:12-35` (SHA-256 pairs and offsets); `prepare-streaming-input.py:13` (four `(offset, old, new)` length words); `prepare-desktop-kio.py:14-22` (five instruction words in `.text`); `proton-game-launcher.py:103` and `:183-185` (VTOL and Outer Wilds byte offsets); `fex-game-launcher.py:175-176` (Celeste renderer SHA-256 pair).
  - Steam UI bridge markers: `/* STEARLIGHT_DESKTOP_BEGIN */` and `/* STEARLIGHT_DESKTOP_END */` (`prepare-desktop-ui.py:17-18`, `:25-32`).
  - FEX config (`fex-game-launcher.py:286`): JSON `{"Config": {}, "ThunksDB": {"GL": 1, "Vulkan": 1}}`.
  - Shell environment file (`plasma-core-session.sh:49-53`): lines `export KEY='value'`, mode 0600.

### Depends on / used by
- **Depends on:**
  - `steam-update`: `desktop-manager.py:23` imports `steam_channels`, which feeds `status` (`desktop-manager.py:100`) and `client-channel` (`desktop-manager.py:444`). `prepare-steam-client.sh:65` runs `steam_channels.py`. `start-session.sh:124` runs `activate-os-update.py`. `steam-os-update.py` calls `prepare-vrclient.sh` and `prepare-frame-controls.sh` (`steam-os-update.py:315-316`).
  - `quest-linux-bridges`: `start-session.sh` runs the probes and preload libraries it names (`start-session.sh:48-59`, `:169`, `:172`). `prepare-desktop-ui.py:28-29` reads the bridge files `desktop-ui-bridge.js` and `frame-menu-bridge.js` and writes them into Steam's UI library.
  - `quest-app-java`: `QuestActivity.java:172` runs `start-session.sh`.
- **Used by:**
  - `quest-app-java`: `QuestActivity.java:172` (start), `DesktopAppBridge.java:26` (creates the same `desktop-app-requests` directory name).
  - `build-and-ci`: `build_files/quest/prepare-payload.py:352` lists these scripts for the payload. `prepare-payload.py:465` and `:507` copy `start-session.sh`.
  - `tests`: `packages/quest-runtime/tests/desktop-manager.test.py:6`, `frame-menus.test.py:49`, `:67`, `:105` load `desktop-manager.py` directly.

### Open issues
- #9 S1.09: keep the desktop manager loop running when `poll()` raises (`desktop-manager.py`)
- #10 S1.10: log a failed optional Flatpak setup step instead of ending the session (`prepare-desktop.sh`, `prepare-flatpak.py`, `start-session.sh`)
- #12 S1.12: write the VTOL graphics backup only through the verified helper (`proton-game-launcher.py`)
- #13 S1.13: launch Celeste when the capped renderer has no valid backup (`fex-game-launcher.py`)
- #14 S1.14: refuse to rename an existing launcher to the Valve binary name (`prepare-streaming-client.sh`)
- #15 S1.15: read an overlong window-list log line in full (`frame_menus.py`)
- #37 S2.13: send the developer-mode setting only when it changes (`desktop-manager.py`)
- #47 S3.03: refresh per-game FEX rootfs copies when the FEX runtime changes (`fex-game-launcher.py`)
- #48 S3.04: decode octal escapes in Steam manifest names as UTF-8 (`fex-game-launcher.py`, `proton-game-launcher.py`)
- #66 S4.18: reject a NUL byte in the current desktop password (`desktop-manager.py`)
- #67 S4.19: make the updated-game Celeste test check a real game tree (`fex-game-launcher.py`)
- #70 S4.22: scope the gamepad adapter test to its one path (`proton-game-launcher.py`)
- #71 S4.23: test the Celeste renderer checksum path with real bytes (`fex-game-launcher.py`)
- #86 S5.10: limit password guessing against developer-mode SSH and RDP (`desktop-manager.py`)
- #87 S5.11: create the atomic-write temporary file without following links (`desktop-manager.py`)
- #88 S5.12: refuse a symlink at the Proton game log path (`proton-game-launcher.py`)
- #108 S0.01: release APK installs and first-run extraction shows the dashboard (`desktop-manager.py`, `prepare-desktop.sh`)
- #110 S0.03: a library game installs and the install finishes (`fex-game-launcher.py`)
- #112 S0.05: game and desktop audio play from the headset (`prepare-desktop.sh`)
- #115 S0.08: an APK and Steam update keeps the account and installed games (`fex-game-launcher.py`, `proton-game-launcher.py`)

### Notes
- `start-session.sh:172` replaces the shell with `runtime-monitor`. The `EXIT` trap set at `start-session.sh:87` therefore does not run on that path. The comment at `start-session.sh:170-171` says PRoot's `--kill-on-exit` owns cleanup.
- `desktop-manager.py:594-600` runs one HTTP request, then `manager.poll()`, in a single loop. `call()` waits up to 15 seconds for `READY` (`desktop-manager.py:463-468`), and `ensure_display()` waits up to 15 seconds (`desktop-manager.py:111-125`). Both stall the poll loop and the SSH accepts while they wait.
- The RPC listens only on `127.0.0.1` (`desktop-manager.py:582`) and compares the bearer token before reading the body (`desktop-manager.py:560`). `atomic()` writes `<name>.next` with `O_CREAT | O_TRUNC` and no `O_EXCL` or `O_NOFOLLOW` (`desktop-manager.py:39-46`).
- Once developer access is enabled and a password is set, sshd binds `0.0.0.0:2222` (`desktop-manager.py:290`) with `PasswordAuthentication yes` (`desktop-manager.py:273`). XRDP binds `tcp://:3389` (`desktop-manager.py:326`). At most four SSH sessions run at once (`desktop-manager.py:426-427`).
- Each `prepare-*` step checks a SHA-256 of the Valve binary before patching it. Unknown builds are usually left alone (`prepare-fex.py:54-56`, `prepare-steam-input.py:44-47`). `prepare-cef.sh:9` and `prepare-vrclient.sh:25` exit 1 instead.

## steam-update
**Path:** `packages/quest-runtime/linux/` (`steam-os-update.py`, `steam_channels.py`, `activate-os-update.py`, `prepare-os-runtime.py`)   **Status:** present   **Serves:** M1, M8   **Platforms:** Quest 2 runtime (Snapdragon XR2 Gen 1, Adreno 650; ARM64 Linux guest under PRoot)
**Purpose:** This module keeps the headset's SteamVR runtime current. It downloads Valve's signed SteamOS image, checks the signature and every chunk, and extracts the runtime beside the running one. Quest adapters are applied to the staged copy, which is swapped in at the next session start. It also selects the Steam client and OS update channels.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `steam-os-update.py` | Steam's OS-update command, adapted for the unprivileged guest. Reads the channel metadata, verifies the bundle, rebuilds the root image from casync chunks, extracts `/opt/steamvr`, and stages it as `/opt/steamvr.next`. | `main` (`steam-os-update.py:327`), `stage` (`:293`), `verified_bundle` (`:118`), `reconstruct` (`:198`), `candidate` (`:76`), `fetch` (`:51`), `index_chunks` (`:146`), `reclaim_previous` (`:42`) |
| `steam_channels.py` | Client channel (`rel` or `beta`) and OS channel selection. Maintains the Steam manifest alias for the selected feed. Reports the installed Frame OS version. | `client_channel` (`steam_channels.py:19`), `os_channel` (`:24`), `select_client` (`:36`), `prepare_manifest_alias` (`:52`), `prepare_client` (`:78`), `status` (`:89`) |
| `activate-os-update.py` | Swaps the staged runtime into `/opt/steamvr` before the Linux VR session starts. Restores the previous runtime if the last start did not finish. | `activate` (`activate-os-update.py:6`), entry (`:27`) |
| `prepare-os-runtime.py` | Re-applies the Quest room-view and systemui bridges and the Quest compositor and driver files to a staged runtime. Takes the runtime directory as its argument. | module body (`prepare-os-runtime.py:7`), bridge write (`:22-23`), compositor copy (`:24-26`) |

### Interfaces
- **Inputs / outputs:**
  - Network: channel metadata `https://holo-atomupd.steamos.cloud/meta/holo/steamos/aarch64/vr/<channel>.json` (`steam-os-update.py:24`, `:77`); bundles and chunks from `https://holo-images.steamos.cloud/` (`steam-os-update.py:25`, `:119`); chunk store path `<store>/<xx>/<hex>.cacnk` (`steam-os-update.py:226`).
  - Pinned signing certificates: `/opt/quest/steamdeck-images.pem` always, and `steamos-dev-images.pem` only for `beta` (`steam-os-update.py:103-115`). Their SHA-256 pins are at `steam-os-update.py:26-27`.
  - Channel files under `/opt/steam/package/`: `stearlight-os-channel` and `stearlight-channel` (`steam-os-update.py:337-340`; `steam_channels.py:20`, `:26`, `:43`, `:58`); `beta` (`steam_channels.py:40`, `:45-47`); `stearlight-channel-update` written as the trigger (`steam_channels.py:49`) and consumed by `steam-channel-args.sh:37-39`; `stearlight-frame-beta` (`steam_channels.py:60`, `:83`); `steam_client_<feed>_linuxarm64.manifest` and the legacy alias (`steam_channels.py:63-75`).
  - Steam root from `STEARLIGHT_STEAM_ROOT`, default `/opt/steam` (`steam_channels.py:8`).
  - Cache directory `/home/stearlight/.cache/stearlight/os-update` (`steam-os-update.py:23`; `activate-os-update.py:28`): `lock` (`steam-os-update.py:333`), `progress.json` (`:37-39`), `available.json` (`:345`), `installed.json` (read at `:342-343`), `pending.json` (`:321`, `:335`), `activated.json` (`activate-os-update.py:7`, `:21`), `trusted-certificates.pem`, `bundle.sqfs`, `bundle.sig`, `bundle/` (`:125-135`), `rootfs.img` (`:199`), `extracted/` (`:297-300`).
  - Runtime directories under `/opt`: `/opt/steamvr`, `/opt/steamvr.next` (staged, `steam-os-update.py:317-320`), `/opt/steamvr.previous` (`activate-os-update.py:19-23`, `steam-os-update.py:43`).
  - External tools run through the glibc loader: `/opt/quest/update-tools/{openssl,unsquashfs,btrfs}` (`steam-os-update.py:96-100`, `:130-135`, `:303`).
  - Child scripts run during staging: `/usr/bin/python3 prepare-os-runtime.py` with `STEARLIGHT_STEAMVR_ROOT` set (`steam-os-update.py:313-314`), then `prepare-vrclient.sh` and `prepare-frame-controls.sh` (`steam-os-update.py:315-316`).
  - Command line: `check`, `--beta`, `-d`, `--enable-duplicate-detection`, and `--supports-duplicate-detection` (`steam-os-update.py:328-331`).
  - Exit codes: `0` success, `1` failure (`steam-os-update.py:364`), `7` already installed (`:344`), `8` update pending on `check` (`:336`).
  - Runtime paths for `prepare-os-runtime.py`: `/opt/quest/systemui-overlay-bridge.js` and `roomview-bridge.js` (`prepare-os-runtime.py:22-23`); `/opt/steamvr/bin/linuxarm64/vrcompositor` (`:26`); `/usr/local/bin/stearlight-frame-vrwebhelper` (`:27`); `drivers/stearlight-fake` and `resources/stearlight-session` (`:28-31`).
- **Wire formats:**
  - Channel metadata JSON (`steam-os-update.py:77-93`): `minor.candidates[]`, each with `image` `{arch, product, variant, buildid}` (`buildid` matches `YYYYMMDD.N`), plus `update_path` and `chunks_store_path` (both must begin with `vr/`).
  - Signed bundle (`steam-os-update.py:118-129`): a squashfs payload, then a DER CMS signature, then an 8-byte big-endian signature length at the end.
  - `manifest.raucm` (`steam-os-update.py:136-143`): INI with `[update] compatible=steamos-aarch64, version=<buildid>` and `[image.rootfs] filename=rootfs.img.caibx, sha256, size`.
  - casync index (`steam-os-update.py:146-166`): bytes 0 to 47 hold six u64 values: header `48` at offset 0, magic `0x96824D9C7B129FF9` at offset 8, then flags, minimum, average and maximum. Bytes 48 to 63 hold the table size and magic `0xE75B9E112F17417D`. Records start at byte 64 and are 40 bytes each: u64 end offset plus a 32-byte `sha512_256` digest. The last 8 bytes must equal `0x4B4F050E5549ECD1`.
  - Chunk payload (`steam-os-update.py:224-234`): zstd-compressed chunk, decompressed with `libzstd.so.1` and checked against its digest.
  - Progress file (`steam-os-update.py:37-39`): JSON `{title, detail, fraction, error}`.
  - Steam client manifest (`steam_channels.py:63-64`, `prepare-steam-integrity.py:56-57`): text with a `"version"` field, and a `bins_linuxarm64_linuxarm64` section with `file`, `sha2`, and `size`.
  - Frame OS version record (`steam_channels.py:97-100`): `installed.json` fields `version` (`\d+\.\d+\.\d+`) and `buildid` (`\d{8}\.\d+`).

### Depends on / used by
- **Depends on:**
  - `quest-linux-session`: `prepare-vrclient.sh` and `prepare-frame-controls.sh` (`steam-os-update.py:315-316`); the Steam client channel and client feed files written by `steam_channels.py`; `prepare-steam-client.sh:65` runs `steam_channels.py`.
  - `quest-linux-bridges`: the bridge files `systemui-overlay-bridge.js` and `roomview-bridge.js` read at `prepare-os-runtime.py:22-23`.
  - External: Valve's `holo-atomupd` and `holo-images` servers (`steam-os-update.py:24-25`), and the `/opt/quest/update-tools` binaries, which are not in this directory.
- **Used by:**
  - `quest-linux-session`: `start-session.sh:124` runs `activate-os-update.py`. `desktop-manager.py:23` imports `steam_channels`, and `desktop-manager.py:100` and `:444` call it. `prepare-steam-client.sh:65` runs `steam_channels.py`.
  - `build-and-ci`: `build_files/quest/prepare-payload.py:251` ships these scripts.
  - `tests`: `packages/quest-runtime/tests/steam-os-update.test.py:11` and `os-update-activation.test.py:7` load the two scripts directly. `build_files/quest/check.sh:18` runs the update test.

### Open issues
- #11 S1.11: report a busy SteamOS update lock without writing a failure (`steam-os-update.py:333-336`, `:354-364`)
- #38 S2.14: stream the SteamOS update bundle to disk instead of holding it in memory (`steam-os-update.py:119-129`)
- #59 S4.11: run the Steam channel tests in `check.sh` (`steam_channels.py`)
- #85 S5.09: unpack only the bytes that the signature check read (`steam-os-update.py:118-135`)
- #115 S0.08: an APK and Steam update keeps the account and installed games (`steam-os-update.py:334`)

### Notes
- Staging never touches the running runtime. `stage()` extracts into the cache, runs the Quest adapters on the copy, then renames it to `/opt/steamvr.next` (`steam-os-update.py:297-320`). The swap happens only at session start, when `activate-os-update.py` runs (`start-session.sh:124`).
- Trust order: the CMS signature is checked before the payload is unpacked (`steam-os-update.py:130-135`). Each chunk must match its digest (`steam-os-update.py:225`, `:234`). The whole root image must match its signed SHA-256 (`steam-os-update.py:276-277`) before extraction.
- `fetch()` returns the complete response as bytes (`steam-os-update.py:64-65`), and `verified_bundle()` reads the whole bundle into memory before writing it (`steam-os-update.py:119-129`). This is the subject of #38.
- Recovery: if `activated.json` still exists at the next start, `activate-os-update.py` restores `/opt/steamvr.previous` (`activate-os-update.py:8-16`). `reclaim_previous()` removes `/opt/steamvr.previous` only while `activated.json` is absent (`steam-os-update.py:45-48`).
- `prepare-os-runtime.py:24-26` moves the staged `vrcompositor` to `vrcompositor.bin` and copies the installed `/opt/steamvr` compositor into its place. The new Valve compositor is therefore kept only as `vrcompositor.bin`.

## stearlight-runtime
**Path:** `packages/stearlight-runtime/`   **Status:** present   **Serves:** M1, M2, M3, M4, M6   **Platforms:** Quest 2 runtime (ARM64 Linux guest); x86_64 Linux build host (cross-built by the Containerfile)
**Purpose:** This module holds the native pieces that sit between Valve's SteamVR and Gamescope in the ARM64 guest. A Vulkan layer adapts the guest's Vulkan stack to what SteamVR and Gamescope expect: a display, a compute queue, present-wait and timeline semaphores. Small helpers set up the Steam dashboard and feed fake headset and controller input. The guest GPU path does not offer everything SteamVR and Gamescope ask for (see `vulkan_wsi_shim.c:1515-1516` and `xcb_shm_present.c:13-15`), so these pieces supply the gaps in user space.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `vulkan_wsi_shim.c` | LD_PRELOAD Vulkan layer. Wraps loader entry points, advertises synthetic display and sync extensions, adds a compute queue family, and routes queue calls through a lock when the queue is aliased. Includes the timeline bridge. | exported and hooked: `vkGetInstanceProcAddr` (`vulkan_wsi_shim.c:2559`), `vkGetDeviceProcAddr` (`:2671`), `vkCreateInstance` (`:2058`), `vkCreateDevice` (`:2198`), `vkEnumerateInstanceExtensionProperties` (`:717`), `vkEnumerateDeviceExtensionProperties` (`:777`), `vkGetPhysicalDeviceFeatures2` (`:1003`), `vkGetPhysicalDeviceFeatures2KHR` (`:1025`), `vkGetPhysicalDeviceQueueFamilyProperties` (`:1485`), `vkGetPhysicalDeviceQueueFamilyProperties2` (`:1529`), `vkGetPhysicalDeviceQueueFamilyProperties2KHR` (`:1570`), `vkGetDeviceQueue` (`:1577`), `vkGetDeviceQueue2` (`:1595`), `vkCreateCommandPool` (`:1619`), `vkWaitForPresentKHR` (`:1029`), `vkQueuePresentKHR` (`:1055`), `vkQueueSubmit` (`:1317`), `vkQueueSubmit2` (`:1347`), `vkQueueSubmit2KHR` (`:1353`), `vkQueueBindSparse` (`:1360`), `vkQueueWaitIdle` (`:1372`), `vkDeviceWaitIdle` (`:1383`), `vkCreateSemaphore` (`:1165`), `vkGetSemaphoreFdKHR` (`:1244`), `vkImportSemaphoreFdKHR` (`:1282`), `vkCreateXlibSurfaceKHR` (`:1897`), libc `dlsym` interposer (`:2404`), constructor `stearlight_wsi_shim_init` (`:2743`). Route tables: `wrap_queue_api` (`:1124`), `wrap_semaphore_fd_api` (`:1143`), `wrap_semaphore_create_api` (`:1152`), `display_proc` (`:2008`, match table `:2010-2031` for the `vkGetPhysicalDeviceDisplay*KHR`, `vkGetDisplay*`, `vkAcquire*`, `vkRelease*` and `vkRegisterDisplayEventEXT` names, mapped to `fake_*` functions at `:1634-1895`). Internal: `resolve_vulkan_loader` (`:468`), `refresh_compute_queue_alias` (`:1420`), `lock_aliased_queue_operations` (`:1083`), `shim_log` (`:618`). |
| `vulkan_timeline_bridge.inc` | Included by the shim (`vulkan_wsi_shim.c:1122`). Exports a binary semaphore as a memfd-backed 64-bit counter and imports one back. Off unless `STEARLIGHT_TIMELINE_BRIDGE=1`. | `timeline_export` (`vulkan_timeline_bridge.inc:153`), `timeline_import` (`:185`), `timeline_register` (`:121`), `timeline_worker` (`:57`), `timeline_release` (`:98`), `timeline_external_properties` (`:252`), `timeline_destroy_semaphore` (`:239`), `timeline_destroy_device` (`:245`) |
| `fake_tracking.cpp` | OpenVR server driver `stearlight-fake`. Registers one HMD and two controllers (`STEARLIGHT-FAKE-HMD`, `STEARLIGHT-FAKE-CONTROLLER-L/R`). Reads QEMU input nodes without grabbing them and drives the right controller's pose and buttons. | `HmdDriverFactory` (`fake_tracking.cpp:683`), `FakeProvider::Init` (`:614`), `FakeHmd::Activate` (`:113`), `FakeController::Activate` (`:334`), `FakeController::GetPose` (`:500`), `FakeController::RunFrame` (`:536`), `FakeProvider::RunFrame` (`:662`), `VmInput::Open` (`:40`), `VmInput::Read` (`:66`) |
| `dashboard_ready.c` | Waits until Valve's gamepad-UI overlays are present and sized, then calls `ShowDashboard` once. Reads the per-frame menu overlay key from the webhelper log. Prints a READY line. | `main` (`dashboard_ready.c:39`), `frame_menu_ready` (`:13`), `ShowDashboard` call (`:68`) |
| `vrcompositor_wsi_launcher.c` | Replaces `vrcompositor`. Prepends the XCB SHM preload and the WSI shim to `LD_PRELOAD`, then execs the real `vrcompositor.bin`, through the bundled glibc loader when `STEARLIGHT_VULKAN_LIBRARY_PATH` is set. | `main` (`vrcompositor_wsi_launcher.c:9`), `execv` calls (`:74`, `:80`) |
| `xcb_shm_present.c` | LD_PRELOAD for libxcb. Sends `xcb_put_image` and `xcb_put_image_checked` through an X MIT-SHM segment. Falls back to the real call for any other format. | `xcb_put_image` (`xcb_shm_present.c:100`), `xcb_put_image_checked` (`:108`), `xcb_disconnect` (`:116`), `upload` (`:77`), `get_pool` (`:55`), `initialize` (`:36`) |
| `angle_visual_interposer.c` | LD_PRELOAD hook for ANGLE's EGL library. Reports the requested ARGB visual for BGRA8 configs when the EGL library's real path matches the expected path. | `dlsym` (`angle_visual_interposer.c:116`), `adapted_config` (`:83`), `adapted_platform` (`:61`), `adapted_platform_ext` (`:72`), `adapted_terminate` (`:105`), `remember_visual` (`:50`), `compatible_argb_visual` (`:35`) |
| `stearlight-fake/driver.vrdrivermanifest` | Driver manifest for `stearlight-fake`: `alwaysActivate` true, `resourceOnly` false, `hmd_presence` `*.*`. | `driver.vrdrivermanifest:2-7` |
| `mesa/0001-complete-x11-software-presents.patch` | Patch for Mesa 26.1.6 `src/vulkan/wsi/wsi_common_x11.c`, applied in the Containerfile venus stage (`Containerfile:35`). After a successful PutImage it sends a GetInputFocus round trip and advances `present_id`. Also changes an `ETIMEDOUT` comparison to `thrd_timedout`. | hunk at patch lines `8-27` (added round trip, `:13`), hunk at `31-39` (`:36`) |

### Interfaces
- **Inputs / outputs:**
  - Env read by the shim: `STEARLIGHT_VM_LOW_RESOLUTION` (`vulkan_wsi_shim.c:16`), `STEARLIGHT_VULKAN_TRACE` (`:1042`, `:1073`, `:2072`, `:2673`), `STEARLIGHT_VULKAN_WSI_SHIM` (`:2718`), `LD_PRELOAD` (`:2716`, `:2736-2738`).
  - Env read by the timeline bridge: `STEARLIGHT_TIMELINE_BRIDGE` (`vulkan_timeline_bridge.inc:42`), `STEARLIGHT_TIMELINE_IDLE_BACKOFF` (`:59`).
  - Env read by the other helpers: `STEARLIGHT_XCB_SHM_PRESENT` (`xcb_shm_present.c:41`), `STEARLIGHT_ANGLE_EGL_PATH` (`angle_visual_interposer.c:123`, default `/opt/steam/steamrtarm64/libEGL.so` at `:124`), `STEARLIGHT_VULKAN_WSI_SHIM`, `STEARLIGHT_VULKAN_LIBRARY_PATH`, `LD_LIBRARY_PATH` (`vrcompositor_wsi_launcher.c:10`, `:14`, `:54`, `:57`), `STEARLIGHT_VM_LOW_RESOLUTION` (`fake_tracking.cpp:27`), `STEARLIGHT_FAKE_AUTO_SELECT` (`fake_tracking.cpp:463`), `STEARLIGHT_FAKE_OPEN_DASHBOARD` (`:465`).
  - Log file written: `/opt/steam/logs/stearlight-vulkan-wsi.log`, appended on every `shim_log` call (`vulkan_wsi_shim.c:619-625`).
  - Console written: `/dev/ttyAMA0`, prefix `STEARLIGHT WSI SHIM:` (`vulkan_wsi_shim.c:626-631`).
  - Shared memory: memfd `stearlight-timeline`, `MFD_CLOEXEC | MFD_ALLOW_SEALING`, size `sizeof(TimelineShared)`, sealed against shrink and grow (`vulkan_timeline_bridge.inc:162-169`). SysV segment for XCB SHM, `IPC_PRIVATE`, 32 MiB (`xcb_shm_present.c:16`, `:65`).
  - Shared libraries opened: `libvulkan.so.1` (`vulkan_wsi_shim.c:471-473`), `libX11-xcb.so.1` (`:1915`), `libxcb.so.1` and `libxcb-shm.so.0` (`xcb_shm_present.c:37`, `:43`), `libX11.so.6` (`angle_visual_interposer.c:36`), `libopenvr_api.so` (`dashboard_ready.c:42`).
  - X display: `XOpenDisplay(NULL)` via `dlsym(RTLD_DEFAULT)` (`vulkan_wsi_shim.c:1964-1965`). Creates a backing window of `DISPLAY_WIDTH` x `DISPLAY_HEIGHT` titled `SteamVR virtual display` (`:1983-1995`).
  - Synthetic extensions advertised: `VK_KHR_display` (`:750`), `VK_KHR_present_id` (`:904`), `VK_KHR_present_wait` (`:915`), `VK_EXT_global_priority` (`:926`), `VK_KHR_external_semaphore_fd` when the timeline bridge is on (`:895`). `VK_KHR_timeline_semaphore` is hidden when the bridge is off (`:442`, `:848`).
  - Reads `/opt/steam/logs/webhelper.txt` (`dashboard_ready.c:18`). Prints `STEARLIGHT ARM64 STEAM SURFACES READY ...` on success (`:69`).
  - Scans `/dev/input/event0` to `event31`, keeping devices whose name contains `QEMU` (`fake_tracking.cpp:42-48`).
- **Wire formats:**
  - `TimelineShared`: `uint64_t magic` (must equal `0x53544c54494d4501`, `vulkan_timeline_bridge.inc:37`), then `uint64_t value`. 16 bytes, checked on import (`:19-22`, `:188`).
  - `TimelineSignalInfo`: `uint32_t sType` (`1000207005`), `const void *pNext`, `uint64_t semaphore`, `uint64_t value` (`:13-18`, `:75`).
  - Compat layouts for the Vulkan structs the shim reads or writes: `VkPresentInfoCompat` (`vulkan_wsi_shim.c:287-296`), `VkSemaphoreGetFdInfoCompat` (`:328-333`), `VkImportSemaphoreFdInfoCompat` (`:354-361`), `VkXcbSurfaceCreateInfoCompat` (`:320-326`), `VkVulkan12FeaturesCompat` (`:275-280`, 23 words ahead of `timelineSemaphore`), `VkQueueFamilyProperties2Compat` (`:115-119`).
  - Vulkan `sType` constants the shim matches: present id `1000294000u` (`:300`), present-id features `1000294001u` (`:301`), present-wait features `1000248000u` (`:298`), global-priority create info `1000174000u` (`:303`), export semaphore `1000077000u` (`:1193`), semaphore type create info `1000207002u` (`:1196`).
  - Error codes returned on import and export failures: `-1000072003` (`vulkan_wsi_shim.c:1257`, `:1294`, `vulkan_timeline_bridge.inc:154`).
  - `dashboard_ready` stdout line: `STEARLIGHT ARM64 STEAM SURFACES READY main=WxH bar=WxH frame-menu=WxH` (`dashboard_ready.c:69-70`).

### Depends on / used by
- **Depends on:**
  - The Vulkan loader and the guest ICD under it, reached through the real `vkGetInstanceProcAddr` and `vkGetDeviceProcAddr` (`vulkan_wsi_shim.c:468-521`).
  - Xlib and XCB for the X surface path (`vulkan_wsi_shim.c:1897-1953`; `xcb_shm_present.c:36-54`).
  - Valve's `libopenvr_api.so` and the OpenVR driver headers, for `dashboard_ready.c:42` and `fake_tracking.cpp:6`.
  - Mesa 26.1.6 WSI X11 code, for the patch above.
- **Used by:**
  - `system-files`: the preload and env paths in `system_files/etc/local.d/arm64-vm.start:55-64`, `system_files/usr/local/libexec/stearlight/frame-gamescope:34-36`, `frame-vrwebhelper:37-39`, `frame-browser:27-28`, `frame-browser:46`, and `steamframe-session:113` and `:434` (runs `dashboard-ready`).
  - `build-and-ci`: the Containerfile compiles every file here (`Containerfile:54-73`), installs the outputs (`:140-147`), and applies the Mesa patch (`:25`, `:35`).
  - `tests`: `tests/steamvr-native-test.sh:18`, and the ANGLE probe in `tests/angle-visual-test.c` (per issue #75). `tests/vulkan-queue-family-test.c:2` includes `../driver/vulkan_wsi_shim.c`; no `driver/` directory exists in the repository.

### Open issues
- #108 Acceptance: release APK installs and first-run extraction shows the dashboard (`dashboard_ready.c:18`)
- #109 Acceptance: Steam signs in with phone approval and shows my library (`dashboard_ready.c:18`)
- #110 Acceptance: a library game installs and the install finishes (`dashboard_ready.c:18`)
- #111 Acceptance: a game plays 30 minutes with no visible jitter or crash (`vulkan_wsi_shim.c:1066`)
- #113 Acceptance: Quest controllers drive a game as a gamepad (`fake_tracking.cpp:397`)
- #16 Keep the Vulkan 1.2 timeline bit at its real offset (`vulkan_wsi_shim.c:278`, `:976`)
- #17 Stop writing into the app's const semaphore create info (`vulkan_wsi_shim.c:1186`, `:1210-1217`)
- #18 Set sType and pNext on the appended queue family element (`vulkan_wsi_shim.c:1557-1559`)
- #19 Keep the registered HMD alive when a later registration fails (`fake_tracking.cpp:632-639`)
- #20 Check component creation results in the fake controller (`fake_tracking.cpp:397-399`)
- #21 Reopen the Steam web log and drop the stale menu key (`dashboard_ready.c:15-18`, `:30`)
- #39 Make the synthetic vkWaitForPresentKHR honour present_id and timeout (`vulkan_wsi_shim.c:1031-1033`, `:809-811`)
- #40 Retry the timeline backing signal instead of stopping the worker (`vulkan_timeline_bridge.inc:65`, `:74-78`)
- #41 Log the stripped present id once, not on every present (`vulkan_wsi_shim.c:1066`, `:618-632`)
- #42 Block waiters on the aliased queue lock instead of spinning (`vulkan_wsi_shim.c:1060-1088`, `:1377-1390`)
- #43 Remove the per-frame X round trip from the Mesa PutImage patch (`mesa/0001-complete-x11-software-presents.patch:8-27`)
- #44 Cache the driver vkQueueSubmit pointer per device (`vulkan_wsi_shim.c:1100-1110`, `:1320-1322`)
- #75 ANGLE visual probe finds dlsym on current glibc (`angle_visual_interposer.c:27`; `tests/angle-visual-test.c:51-52`)
- #89 Escape control bytes in names written to the shim log (`vulkan_wsi_shim.c:618-632`, `:2559-2563`)
- #90 Reject timeline fds that are not sealed against shrinking (`vulkan_timeline_bridge.inc:169`, `:185-189`)

### Notes
- Most shim state is plain `static` data. The `real_*` pointers and `synthetic_*` flags are written in the resolvers and in `dlsym` with no lock (`vulkan_wsi_shim.c:468-521`, `:1100-1110`, `:2404-2557`). The only locks are the queue-alias lock (`:1083-1098`) and the timeline table lock (`vulkan_timeline_bridge.inc:38`, `:155`, `:196`).
- The timeline bridge publishes a value only after the backing semaphore has completed. `timeline_worker` reads the counter, then raises the shared value and signals the backing semaphore to match (`vulkan_timeline_bridge.inc:63-80`). It polls every 2 ms, or every 8 ms when idle backoff is on (`:88-93`). On release it publishes the last completed value before unmapping (`:104-115`).
- The constructor removes the shim from `LD_PRELOAD` for child processes (`vulkan_wsi_shim.c:2747`, `:2715-2741`). The comment gives the reason: Alpine's musl helpers cannot resolve `dlvsym`. The launchers scope the preload per process instead (`vrcompositor_wsi_launcher.c:30-50`, `frame-gamescope:32-37`).
- With synthetic present-wait active, `vkWaitForPresentKHR` returns 0 at once (`vulkan_wsi_shim.c:1031-1034`). `vkQueuePresentKHR` strips the present-id chain and logs on every call that has one (`:1062-1067`). `shim_log` reopens and closes two files on every call (`:618-632`).
- The backing window is created at `DISPLAY_WIDTH` x `DISPLAY_HEIGHT` (`vulkan_wsi_shim.c:1983-1984`), but its log line says `1280x720` (`:1998`). `fake_tracking.cpp` says it is "VM-only" for QEMU (`fake_tracking.cpp:1-4`). `SPEC.md` lists the QEMU VM runtime as out of 1.0 scope (W1), yet issue #113 points at this file.

## system-files
**Path:** `system_files/`   **Status:** present   **Serves:** M1, M2, M4, M7, M8   **Platforms:** Quest 2 runtime (ARM64 Linux guest); x86_64 Linux build host (copied into the image by the Containerfile and the payload build)
**Purpose:** This tree holds the guest-side files that overlay the base Alpine image. They are the Steam and Gamescope session launchers, the boot script for the ARM64 QEMU guest, OpenRC files for an opt-in standalone OpenXR runtime, and small stand-ins for the SteamOS commands that Steam calls during first run. The stand-ins exist because Steam expects SteamOS and systemd behaviour that Alpine does not provide.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `etc/inittab` | OpenRC init table: sysinit, boot, default and shutdown runs; Ctrl-Alt-Del reboots. | `::sysinit:/sbin/openrc -q sysinit` (`etc/inittab:1`), `::ctrlaltdel:/sbin/reboot` (`:4`) |
| `etc/steamos-oobe-image` | One-line marker containing `1`. No reader in this repository. | `steamos-oobe-image:1` |
| `etc/udev/rules.d/90-stearlight-vm-network.rules` | Marks the QEMU NIC `eth0` as managed by NetworkManager. | `90-stearlight-vm-network.rules:2` |
| `etc/NetworkManager/system-connections/stearlight-vm.nmconnection` | NetworkManager profile `VM Ethernet` on `eth0`, autoconnect, DHCP for IPv4 and IPv6. | `stearlight-vm.nmconnection:2-5`, `:11`, `:14` |
| `etc/fonts/conf.d/66-stearlight-cjk.conf` | Fontconfig: prefers Noto Sans CJK JP for `ja` and Noto Sans CJK KR for `ko`. | `66-stearlight-cjk.conf:6-13` |
| `etc/gamescope/scripts/stearlight-windows.lua` | Gamescope script: turns on `vr_use_modifiers` when `STEARLIGHT_GAMESCOPE_VM_UPLOAD=1`. | `stearlight-windows.lua:3-4` |
| `etc/init.d/stearlight-xr` | OpenRC service for `xr-service`. Refuses to start unless `STEARLIGHT_XR_ENABLE=1` and mode is `standalone`. Respawn limit 5. | `start_pre` (`etc/init.d/stearlight-xr:20`), gates (`:24-31`), `respawn_max=5` (`:13`), `command` (`:4`) |
| `etc/conf.d/stearlight-xr` | Opt-in OpenXR settings. Disabled by default; Steam Frame streaming stays with Valve's client. | `STEARLIGHT_XR_ENABLE=0` (`etc/conf.d/stearlight-xr:4`), `STEARLIGHT_XR_AUTOSTART=1` (`:16`), `STEARLIGHT_XR_OPENVR_RUNTIME=` (`:21`), `STEARLIGHT_XR_ACTIVE_CONFIG=` (`:35`) |
| `etc/local.d/arm64-vm.start` | OpenRC `local.d` boot script for the ARM64 QEMU guest (392 lines). Runs the whole boot in one background subshell that writes to `/dev/ttyAMA0`. | kernel switches (`:8`, `:25`, `:31`, `:52`, `:77`, `:133`, `:145`, `:317`, `:324`, `:358`), Steam archive step (`:122-131`), Xorg (`:252`), PulseAudio null sink (`:344-349`), Steam Frame session start (`:385-388`) |
| `usr/bin/steamos-update` | Runs `/opt/quest/steam-os-update.py` when present. Otherwise prints a message and exits 7. | `steamos-update:4-5`, `:8` |
| `usr/bin/localectl` | Answers `status` and `get-locale` from `LANG`. `set-locale` and other calls exit 0. | `localectl:5-9` |
| `usr/bin/timedatectl` | Timezone list, show and status for Steam's first-run setup. Writes go to the polkit helper. Reads state from `$XDG_STATE_HOME/stearlight/timezone`. | `list-timezones` (`timedatectl:22`), `set-timezone` (`:29-31`), `show` (`:35`), `status` (`:52`), state path (`:8-9`) |
| `usr/bin/gamescope-session-plus` | Wrapper that execs the session script in `usr/share`. | `gamescope-session-plus:2` |
| `usr/bin/steamos-session-select` | Prints that desktop mode is unavailable. Exits 0 so the Steam menu does not error. | `steamos-session-select:5-6` |
| `usr/bin/jupiter-biosupdate` | Prints that no firmware is configured. Exits 0. | `jupiter-biosupdate:4-5` |
| `usr/bin/jupiter-dock-updater` | No-op that exits 0. | `jupiter-dock-updater:5` |
| `usr/bin/steamos-devkit-mode` | Execs the polkit helper of the same name. | `steamos-devkit-mode:2` |
| `usr/bin/steamos-select-branch` | Channel selector: lists `rel beta` (`:7`), prints the current channel (`:8-16`), and writes `package/stearlight-os-channel` (`:26-27`). Accepts `rel`/`stable` and `beta`/`publicbeta`. | `steamos-select-branch:7`, `:17-18`, `:26-27` |
| `usr/bin/pkexec` | Non-root stand-in for pkexec. Drops `--disable-internal-agent`, `--keep-cwd` and `--user=` options, then runs only commands matching a path allowlist. | options loop (`pkexec:8-15`), allowlist (`:19-20`), `exec "$@"` (`:21`), refusal (`:24-25`) |
| `usr/bin/steamos-set-timezone` | Execs the polkit helper of the same name. | `steamos-set-timezone:2` |
| `usr/bin/steamos-polkit-helpers/jupiter-biosupdate` | Execs `/usr/bin/jupiter-biosupdate`. | `jupiter-biosupdate:2` |
| `usr/bin/steamos-polkit-helpers/jupiter-dock-updater` | Execs `/usr/bin/jupiter-dock-updater`. | `jupiter-dock-updater:2` |
| `usr/bin/steamos-polkit-helpers/steamos-devkit-mode` | Accepts any arguments and exits 0. | `steamos-devkit-mode:7-9` |
| `usr/bin/steamos-polkit-helpers/steamos-priv-write` | Writes `$1` to `$2` only when run as root and `$2` is under `/etc/stearlight/` or `/var/lib/stearlight/`. Otherwise exits 0. | uid check (`steamos-priv-write:7`), allowlist (`:10-15`), exit (`:17`) |
| `usr/bin/steamos-polkit-helpers/steamos-select-branch` | Execs `/usr/bin/steamos-select-branch`. | `steamos-select-branch:2` |
| `usr/bin/steamos-polkit-helpers/steamos-set-timezone` | Validates the zone name, then as root links `/etc/localtime`. As a user it writes the state file. Exits 2 for an invalid zone name, otherwise 0. | validation (`steamos-set-timezone:10-15`), root branch (`:19-21`), user branch (`:26-28`) |
| `usr/bin/steamos-polkit-helpers/steamos-update` | Execs `/usr/bin/steamos-update`. | `steamos-update:2` |
| `usr/share/gamescope-session-plus/gamescope-session-plus` | Session coordinator (239 lines). Starts Gamescope, waits for its startup FIFO, starts the client, then handles reboot and shutdown sentinels. | config precedence (`gamescope-session-plus:27-40`), Gamescope args (`:99-134`), FIFO handshake (`:159-176`), client start (`:220`), wait (`:229`), sentinels (`:233-239`) |
| `usr/share/gamescope-session-plus/sessions.d/steam` | Session profile for the Steam client: client environment, sentinel paths, default screen sizes, default `CLIENTCMD`. | sentinels (`sessions.d/steam:37-40`), screen defaults (`:42-51`), `CLIENTCMD` default (`:54-61`) |
| `usr/share/gamescope-session-plus/sessions.d/steamframe` | Steam Frame profile. Sources `steam`, uses the `openvr` backend with `/opt/steamvr`, and sets `CLIENTCMD` to the session client. | `steamframe:4`, `:6-7`, `:8-10`, `:13` (`STEARLIGHT_NATIVE_STEAMVR=0`), `:14` |
| `usr/share/wayland-sessions/gamescope-session-steam.desktop` | Desktop entry for the Steam session. | `Exec=/usr/bin/gamescope-session-plus steam` (`gamescope-session-steam.desktop:4`) |
| `usr/local/libexec/stearlight/steamvr-native` | Launcher for Valve's `vrstartup`, `vrserver`, `vrcompositor` and `vrdashboard`. Sets the environment, registers drivers with `vrpathreg`, seeds `steamvr.vrsettings` for the fake HMD, and waits for Steam when asked. | root detection (`steamvr-native:20-34`), env (`:47-64`), `vrpathreg` setup (`:161-180`), driver registration (`:178-191`), settings seed (`:196-281`), `prepare` (`:289-292`), Steam wait (`:328-349`), dispatch (`:378-397`) |
| `usr/local/libexec/stearlight/steamframe-session` | Steam Frame session client (549 lines). Starts SteamVR, starts `RUNSTEAM.sh`, restarts Steam on exit 0 or 42 (at most twice), waits for the dashboard, then waits for SteamVR daemons. | D-Bus wrap (`steamframe-session:108-110`), SteamVR start (`:113`, `:138`), Steam start (`:192-193`), webhelper stability (`:228`), restart budget (`:238-240`), dashboard wait (`:432-449`), scanout refresh (`:452-473`), exit handling (`:483-522`) |
| `usr/local/libexec/stearlight/frame-steam-ipc` | Patches a copy of `chromehtml.so` (MasterStream reply wait) for each known Steam build. Fails on an unknown build. | known SHA-256 table (`frame-steam-ipc:9-45`), patch (`:50-51`), unknown-build exit (`:44`), success line (`:57`) |
| `usr/local/libexec/stearlight/frame-gamescope` | Gamescope wrapper: sets the glibc library path and the ICD. Can build a patched copy of Gamescope for VM uploads. Preloads the shim when the timeline bridge is on. | library path (`frame-gamescope:4-5`), VM upload patch (`:11-31`), preload exec (`:32-37`) |
| `usr/local/libexec/stearlight/frame-vrwebhelper` | Wrapper for `vrwebhelper`. `prepare` patches a copy of the binary; normal runs add the shim to `LD_PRELOAD` when VM upload is on. | `prepare` (`frame-vrwebhelper:6-31`), patch offset (`:21-22`), preload (`:34-39`), exec (`:41`) |
| `usr/local/libexec/stearlight/frame-browser` | Switches Steam's web helper between its original launcher and a wrapper that uses ANGLE over Vulkan with the two preload hooks. | mode check (`frame-browser:10`), backup and restore (`:12-18`), ANGLE hash check (`:23-26`), wrapper body (`:35-49`), preload (`:46`) |
| `usr/local/libexec/stearlight/frame-bluetooth` | Attaches the host Bluetooth radio named on the kernel command line over USB/IP, starts `bluetooth`, and powers it on. | bus ID (`frame-bluetooth:5-8`), validation (`:9`), `usbip attach` (`:12`), `rc-service` (`:13`), `bluetoothctl` (`:20-21`) |
| `usr/local/libexec/stearlight/gamescope-preview` | Diagnostic client. Plays the Steam spinner with mpv under Gamescope and reports READY on `/dev/ttyAMA0`. | mpv (`gamescope-preview:3-6`), READY line (`:13`) |
| `usr/local/libexec/stearlight/boot-animation` | Plays Valve's startup movie, then the spinner, as a stereo pair sized to the display. Writes its state to `$XDG_RUNTIME_DIR/stearlight-boot-animation.state`. | assets (`boot-animation:27-33`), stereo layout (`:53-56`), `play` (`:57-67`), state writes (`:26`, `:94`, `:102`) |
| `usr/local/libexec/stearlight/launch-xr-game` | Steam launch-option prefix for OpenXR titles. Sets `STEARLIGHT_XR_STEAM_LAUNCH=1` and execs `xr-run`. | `launch-xr-game:21-23`, `:25-28`, `:33-34` |
| `usr/local/libexec/stearlight/xr-run` | Per-application wrapper (450 lines). Checks configuration, resolves an optional OpenVR bridge, starts Monado on demand under a startup lock and lease files, runs the application, then stops only the Monado it started. | config (`xr-run:9-20`), bridge (`:125-187`), Monado start (`:404-424`), cleanup (`:330-376`), run (`:449-450`) |
| `usr/local/libexec/stearlight/xr-service` | Body of the OpenRC service. Checks `STEARLIGHT_XR_ENABLE` and mode, finds `monado-service`, and execs it. | gates (`xr-service:9-16`), monado path (`:17-21`), exec (`:62`) |

### Interfaces
- **Inputs / outputs:**
  - Kernel command line switches read by the boot script: `stearlight.boot-epoch=` (`etc/local.d/arm64-vm.start:8`), `stearlight.low-resolution=1` (`:25`), `stearlight.debug=1` (`:31`), `stearlight.windows-gpu=1` (`:52`, `:133`, `:358`), `stearlight.capture=1` (`:77`), `stearlight.browser-gpu=1` (`:145`), `stearlight.animations=1` (`:317`), `stearlight.gamescope-preview=1` (`:324`). Also `stearlight.bluetooth-busid=` (`frame-bluetooth:6`).
  - Devices: `/dev/vdb` as the Steam archive, override `STEARLIGHT_FRAME_STEAM_ARCHIVE` (`arm64-vm.start:122`); `/dev/vdc` as runtime extras (`:151`, `:165`); `/dev/ttyAMA0` as the boot console (`:98`, `:392`); `/dev/hvc0` as the optional debug console (`:33-34`); `/dev/input/event*` (`:115`); `/dev/dri/*` (`:109`).
  - Environment set by the boot script for the session: `DISPLAY=:0` (`:39`), `XDG_RUNTIME_DIR=/run/user/1000` (`:40`), `VK_ICD_FILENAMES` (`:41`), `GAMESCOPE_BIN` (`:42`), `STEARLIGHT_GAMESCOPE_STARTUP_SECONDS=120` (`:43`), `STEARLIGHT_FAKE_TRACKING=1` (`:44`), `STEARLIGHT_TIMELINE_BRIDGE` and related (`:53-54`), `STEARLIGHT_XCB_SHM_PRESENT=1` (`:64`), `STEAM_EXTRA_ARGS` (`:70`), `PULSE_SERVER` (`:343`).
  - Xorg: writes `/tmp/stearlight-xorg.conf` (`:224-244`), runs `Xorg :0` (`:252`), logs to `/tmp/stearlight-xorg.log` (`:253`).
  - Sockets and runtime paths: `$XDG_RUNTIME_DIR/monado_comp_ipc` (`xr-run:70`), `$XDG_RUNTIME_DIR/stearlight-monado.pid` and `.owner` and `.leases` (`xr-run:71-73`), `$XDG_RUNTIME_DIR/pulse/native` (`arm64-vm.start:343`), `$XDG_RUNTIME_DIR/stearlight-boot-animation.stop` (`:292`, `boot-animation:7`), `/run/stearlight/quest/dashboard.ready` (`steamframe-session:440`).
  - Sentinels: `/tmp/steamos-reboot-sentinel` (`gamescope-session-plus:233`, `sessions.d/steam:37`) and `/tmp/steamos-shutdown-sentinel` (`:236`, `sessions.d/steam:39`).
  - Persistent files: `$HOME/.steam/steam/config/steamvr.vrsettings` (`steamvr-native:196`), `$XDG_CONFIG_HOME/openvr/openvrpaths.vrpath` (`xr-run:107-115`), `$XDG_CACHE_HOME/stearlight/monado-service.log` (`xr-run:88-89`), `$XDG_STATE_HOME/stearlight/timezone` (`timedatectl:8-9`, `steamos-set-timezone:26-28`), `$STEAM_ROOT/package/stearlight-os-channel` (`steamos-select-branch:9`, `:26-27`), `/etc/localtime` and `/etc/timezone` (`steamos-set-timezone:20-21`), `/etc/stearlight/*` and `/var/lib/stearlight/*` (`steamos-priv-write:11-13`), `/var/log/stearlight-xr.log` (`etc/init.d/stearlight-xr:8`), `/var/log/stearlight-bluetooth.log` (`arm64-vm.start:208`), `/opt/steam/logs/stearlight-vulkan-wsi.log` (`steamframe-session:392-394`).
  - Network: `usbip attach --remote=10.0.2.2` (`frame-bluetooth:12`), `127.0.0.1 steamloopback.host` appended to `/etc/hosts` (`arm64-vm.start:90-91`), NetworkManager profile `VM Ethernet` (`nmconnection:2`).
  - Processes: `dbus-run-session` (`steamframe-session:108-110`), `dbus-launch --exit-with-session` (`steamvr-native:370`), `pulseaudio --exit-idle-time=-1` with a null sink (`arm64-vm.start:345-348`), `su -p stearlight` for user-level steps (`arm64-vm.start:291`, `:303`, `:331`, `:344`, `:362`, `:385`).
- **Wire formats:** None defined in this tree. The shell scripts communicate through text markers on stdout and stderr (for example `STEARLIGHT ARM64 STEAM SURFACES READY` in `steamframe-session`, `STEARLIGHT ARM64 STEAMVR DIAGNOSTICS COMPLETE` at `steamframe-session:417`) and through one-word state files. The boot-animation state file holds `starting`, `loop`, `failed` or `stopped` (`boot-animation:26`, `:94`, `:102`, `:29`). The timezone state file holds one zone name (`steamos-set-timezone:28`).

### Depends on / used by
- **Depends on:**
  - `stearlight-runtime`: the Vulkan shim, the compositor launcher, `dashboard-ready`, and the XCB and ANGLE preloads (`frame-gamescope:34`, `frame-vrwebhelper:38`, `frame-browser:27-28`, `arm64-vm.start:55`, `:64`, `steamframe-session:434`).
  - `steam-update`: `steamos-update` execs `/opt/quest/steam-os-update.py` (`usr/bin/steamos-update:4-5`).
  - `quest-linux-session`: `steamframe-session:26` runs `/opt/quest/prepare-steam-client.sh` when `STEARLIGHT_QUEST_RUNTIME=1`, and `steamframe-session:440` waits for `/run/stearlight/quest/dashboard.ready`.
  - Valve's Steam, SteamVR and Gamescope bundles under `/opt/steam`, `/opt/steamvr` and `/opt/frame-gamescope` (`steamframe-session:17`, `steamvr-native:21`, `frame-gamescope:3`).
- **Used by:**
  - `build-and-ci`: the Containerfile copies these files into the image (`Containerfile:140-200`). `build_files/quest/prepare-payload.py` reads `steamframe-session` (`:462`) and copies `frame-steam-ipc` (`:496-497`, `:565`) and `steamframe-session` (`:566`).
  - `quest-linux-session`: `packages/quest-runtime/linux/start-session.sh:126-134` calls `/usr/local/bin/stearlight-steamvr-native prepare` and `vrpathreg`.
  - `tests`: `tests/steamvr-native-test.sh:18`, `:86`; `tests/frame-browser-test.sh:31`; `tests/xr-lifecycle-test.sh` and `tests/xr-bridge-env-test.sh` (both reference `libexec/stearlight`).

### Open issues
- #108 Acceptance: release APK installs and first-run extraction shows the dashboard (`etc/local.d/arm64-vm.start:128`)
- #109 Acceptance: Steam signs in with phone approval and shows my library (`usr/share/gamescope-session-plus/gamescope-session-plus:61`)
- #22 Stop the READY banner when Steam archive extraction fails (`etc/local.d/arm64-vm.start:122-131`)
- #23 Keep reboot and shutdown requests when the Steam client exits non-zero (`gamescope-session-plus:8`, `:229-239`)
- #24 Point the steam session at a client the image actually installs (`gamescope-session-plus:61`, `:229`; `sessions.d/steam:59`; `gamescope-session-steam.desktop:4`; `Containerfile:132-137`)
- #59 Run the Steam channel tests in check.sh (`usr/bin/steamos-select-branch`, named in the Where line)
- #74 frame browser test checks the invalid-mode message (`usr/local/libexec/stearlight/frame-browser:10`)
- #91 Stop the tester console giving an unauthenticated root shell (`etc/local.d/arm64-vm.start:31-35`)
- #92 Refuse `..` in steamos-priv-write destinations (`usr/bin/steamos-polkit-helpers/steamos-priv-write:10-15`)
- #93 Stop root writing fixed names in /tmp at boot (`etc/local.d/arm64-vm.start:224`, `:253`, `:281`, `:353`)
- #94 Stop making every input event node world-writable (`etc/local.d/arm64-vm.start:115`)
- #95 Refuse `..` in pkexec command paths (`usr/bin/pkexec:18-22`)
- #96 Log when steamos-priv-write drops a non-root write (`usr/bin/steamos-polkit-helpers/steamos-priv-write:7-17`)
- #97 Accept only real zone files in steamos-set-timezone (`usr/bin/steamos-polkit-helpers/steamos-set-timezone:17-18`)
- #98 Turn X access control back on in the VM boot script (`etc/local.d/arm64-vm.start:215`, `:252`)
- #99 Stop the serial console being writable by every local user (`etc/local.d/arm64-vm.start:98`, comment at `:23`)

### Notes
- `pkexec` checks its allowlist with a shell `case` pattern (`usr/bin/pkexec:19-20`). In a `case` pattern `*` also matches `/`, so a path that contains `..` passes the prefix test and reaches `exec "$@"` (`:21`). Issue #95 tracks this.
- The default session client, `/usr/local/libexec/stearlight/launch-steam`, is named at `gamescope-session-plus:61` and `sessions.d/steam:59`. No file of that name exists in this repository. The Containerfile installs the session helpers as `/usr/local/bin/stearlight-*` (`Containerfile:148-156`). The `-x` test at `gamescope-session-plus:223` names `/usr/local/libexec/stearlight/steamvr-native`, which is not installed at that path. That branch runs only when `STEARLIGHT_NATIVE_STEAMVR` is non-zero (`:222`). `sessions.d/steamframe:13` sets it to 0.
- `gamescope-session-plus` runs with `set -euo pipefail` (`:8`) and waits on the client with a bare `wait` (`:229`). A non-zero exit from Steam ends the script before the reboot and shutdown sentinel checks (`:233-239`). Issue #23 tracks this.
- `arm64-vm.start` has no `set -e`. The Steam archive checks (`:126-130`) therefore do not stop the script, and the READY line is printed at `:131` either way. The script runs as root (it remounts `/` at `:29`). With `stearlight.debug=1` it also starts `/bin/sh -i` on `/dev/hvc0` (`:31-35`). Issues #22 and #91 track these.
- Four scripts patch copies of Valve binaries at fixed offsets after a SHA-256 check: `frame-gamescope` (`:14-29`), `frame-vrwebhelper` (`:10-28`), `frame-steam-ipc` (`:8-45`), and `frame-browser` (`:23-26`, which checks `libEGL.so`). Each refuses an unknown build (`frame-steam-ipc:44`, `frame-gamescope:19-21`, `frame-vrwebhelper:15-17`, `frame-browser:24-25`). A Steam or SteamVR update therefore needs these hashes checked again.

## build-and-ci
**Path:** `build_files/` (except `*arm64*` and `*.ps1`), `post_process/` (except `*.ps1`), `.github/workflows/`, `Containerfile`, `Justfile`, `generate_compatibility.py`, `disk_config/`   **Status:** present   **Serves:** M1, M8 (the release APK under test and its download set); the host checks in `build_files/quest/check.sh` gate every Must   **Platforms:** linux build host (x86_64 Ubuntu 24.04 runners; the rootfs job runs on ARM64) / Quest 2 runtime (produces its payload) / windows (archived VM path only)
**Purpose:** This module builds the Quest 2 APK. CI makes an ARM64 rootfs from the pinned recovery image, builds the APK payload and the signed download files, and publishes them to the `continuous` release. It also runs the host-side test gate. The Windows VM image path (`build-image.sh`, the `Justfile` recipes `build`, `packages`, `package` and `run-vm`, and `post_process/start-vm.cmd` and `README.md`) is archived under W1 and no workflow runs it. `Containerfile` is shared: the Quest rootfs uses it too.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `.github/workflows/build.yml` | Quest APK pipeline: source checks, rootfs, APK, Continuous release, local signing recovery | `source-checks` (:32), `quest-rootfs` (:48), `quest-apk` (:74), `continuous-release` (:168), `recover-local-signing` (:192) |
| `.github/workflows/pr-size.yml` | Labels a PR `size:XS` to `size:XXL` from non-test changed lines | `label` job (:118); thresholds in `resolveSizeLabel` (:177) |
| `.github/workflows/pr-vouch.yml` | Labels PRs by author trust; re-check on `/recheck-vouch` | `collect-targets` (:22), `label` (:66), `/recheck-vouch` (:41) |
| `Justfile` | Recipes: `check`, `apk`, `build`, `packages`, `package`, `run-vm` | `check` (:8-9), `apk` (:12-13), `build` (:16-17, archived), `packages` (:20-21), `package` (:24-25), `run-vm` (:28-29) |
| `build_files/quest/check.sh` | The CI test gate: shell syntax, Python AST parse, then each wired test | `bash -n` (:4), AST parse (:5-11), tests (:12-87) |
| `build_files/check.sh` | Older host gate for the Windows and VM-era tests; no workflow calls it | :5-14 |
| `build_files/quest/build-rootfs.sh` | Builds the ARM64 rootfs tarball from the recovery image; runs `Containerfile` through buildx | fetch (:21-23), mount (:26), buildx (:52-55), stage calls (:60-62), tar and `SHA256SUMS` (:65-69) |
| `build_files/quest/extract-rootfs.sh` | Unpacks the rootfs tarball into an empty directory | empty check (:9-12), `tar` (:13), `chmod -R u+rwX` (:17) |
| `build_files/quest/prepare-payload.py` | Builds the whole Quest payload: Mesa, FNA3D, PRoot, overlay, JNI libraries, source bundle | `LOCK` (:20), `run` (:24), `fetch` (:38), `build_mesa` (:129), `overlay_archive` (:184), `main` (:281), argument checks (:290-297), `quest-dependencies.json` (:544), entry (:581) |
| `build_files/quest/split-rootfs.py` | Splits the rootfs stream into 16 MiB APK assets | `main` (:7), chunk loop (:14-17), `rootfs.list` and `rootfs.sha256` (:19-20) |
| `build_files/quest/package-rootfs.py` | Writes the base rootfs as a gzip tar with uid, gid and mtime zeroed; skips overlay paths | input check (:17-18), excluded paths (:23), tar write (:25), normalisation (:30) |
| `build_files/quest/build-proot.py` | Builds the pinned PRoot with the Quest adapter and its own loader | `build` (:7), `make` call (:16-20), `patchelf` (:25) |
| `build_files/quest/patch-proot.py` | Applies the Quest app-policy adapter to the PRoot source | `replace` (:6), `patch` (:10), entry (:117) |
| `build_files/quest/build-fna3d.py` | Builds the FNA3D renderer for Celeste with the buffer-reuse repair; writes `profile.json` | `repair_buffer_reuse` (:11), `build` (:22), SDL import stub (:40-42), `cmake` (:44-49), `profile.json` (:55-57) |
| `build_files/quest/patch-mesa.py` | Applies Quest KGSL, A6xx depth and GL memory-import fixes to the Mesa tree | module-level script; tree path from argv (:8) |
| `build_files/quest/patch-gamescope.py` | Makes the Frame Gamescope refresh `wl_shm` uploads | `patch_image` (:27), `adapt_elf` (:39), entry (:62) |
| `build_files/quest/prepare-animation.py` | Decodes the OS startup assets for the loading layer | `prepare` (:9), entry (:38) |
| `build_files/quest/stage-chromium.py` | Downloads and stages the pinned ARM64 Chromium | `stage` (:13), download and checksum (:18-23), `dpkg-deb` (:25), entry (:73) |
| `build_files/quest/stage-desktop-icons.py` | Rasterises the installed Frame icons for OpenVR thumbnails | `stage` (:11), entry (:51) |
| `build_files/stage-frame-desktop.py` | Extracts the ARM64 Plasma workspace into a private prefix | `stage` (:60), entry (:228), `--append` (:232) |
| `build_files/fetch-recovery.py` | Downloads and checks the pinned recovery image, writes a sparse raw disk, finds partition `rootfs-A` | `root_partition` (:12, name at :26), `fetch` (:35, download at :43, cleanup at :65-67), CLI (:71-75) |
| `build_files/extract-gamescope-runtime.sh` | Copies gamescope and mangoapp and resolves their ELF dependencies | `extract_frame_gamescope` (:3), `scanelf` (:17-18), `libvulkan.so.1` (:20) |
| `build_files/sanitize-steam-profile.sh` | Removes account and session files from the build-stage Steam tree | `rm -f` list (:11-15), `userdata` (:16), `ssfn*` (:17) |
| `build_files/build-image.sh` | Archived: builds the ARM64 VM qcow2, kernel and initramfs, then checksums them | fetch (:21), mount (:26), buildx (:56-59), disk size (:70), qcow2 (:75), `SHA256SUMS` (:84) |
| `build_files/quest/dependencies.json` | Pins for the Quest build: 14 top-level groups (`fna3d`, `mesa`, `android`, `linux`, `fonts`, `openxr`, `sources`, `audio`, `gaming`, `fex_libraries`, `updates`, `chromium`, `desktop_cli`, `renpy`) | read at `prepare-payload.py:20` and `stage-chromium.py:14` |
| `build_files/quest/requirements.txt` | Build tool pins: meson 1.9.1, Mako 1.3.10, PyYAML 6.0.2 | :1-3 |
| `Containerfile` | Multi-stage ARM64 rootfs: Debian glibc runtime, Mesa virtio build, shims, Alpine base, Steam and SteamVR overlay, verification | stages (:2, :17, :24, :50, :75, :80), COPY from frame runtime (:120), COPY from Steam client (:127), verification (:172-199), `FROM scratch` (:201-202) |
| `disk_config/disk.json` | Rootfs size in GiB (8) for the archived VM disk | :2, read by `build-image.sh:70` |
| `generate_compatibility.py` | Writes `STANDALONE_COMPATIBILITY.md` from `games.json`; game names come from the Steam store API | `steam_name` (:23, 8 s timeout at :28, fallback at :37), `escape_cell` (:39), `main` (:42), write (:89), entry (:92) |
| `post_process/quest/package-apk.py` | Checks the APK's required entries and rootfs parts, then writes the download set | `verify` (:22), `package` (:100), `supported_devices` (:123), entry (:132) |
| `post_process/quest/publish-continuous.sh` | Moves the `continuous` tag and release to a verified default-branch build; deletes other assets | environment (:4), branch guard (:6-9), superseded skip (:11-12), checksums (:13-15), commit check (:16-19), tag (:20-24), release (:30-34), upload (:36), asset cleanup (:38-43) |
| `post_process/quest/shell.sh` | Developer ADB shell into the installed app's PRoot rootfs | `ADB` (:3), install check (:5-6), launch string (:16), `exec adb` (:18, :20) |
| `post_process/quest/socket-table-monitor.sh` | ADB developer path: writes this package's `/proc/net` rows into app files for Steam's peer checks | package allowlist (:7), UID filter (:18), loop (:16-23), ready line (:21) |
| `post_process/start-vm.cmd` | Archived: launcher wrapper for `start-vm.ps1` | :3 |
| `post_process/README.md` | Archived: user guide for the Windows VM (download, controls, saved data) | download steps (:5-6) |

### Interfaces
- **Inputs / outputs:**
  - Environment read by `publish-continuous.sh`: `GH_REPO`, `GITHUB_SHA`, `GITHUB_REF`, `GITHUB_EVENT_NAME` (:3-4), `GITHUB_RUN_ID` (:29). The workflow sets `GH_TOKEN` and `GH_REPO` (`build.yml:187-189`).
  - Secret `QUEST_SIGNING_KEYSTORE_BASE64`: read at `build.yml:130` and `build.yml:202`; decoded to `$RUNNER_TEMP/quest-continuous.keystore` (`build.yml:133-134`) and exported as `QUEST_SIGNING_STORE` (`build.yml:135`).
  - Workflow inputs: `publish_continuous` (`build.yml:11-14`), `recover_signing_public_key` (`build.yml:15-18`), `sign_test_apk` (`build.yml:19-22`).
  - Gradle properties passed to `:app:assembleDebug`: `questPayload`, `questBuildDir`, and `questSigningStore` when set (`build.yml:139-142`).
  - Recovery image: URL and SHA-256 from `packages/sources.lock.json` (`fetch-recovery.py:36`); the partition is found by GPT name `rootfs-A` (`fetch-recovery.py:26`).
  - Pins: `build_files/quest/dependencies.json` read at `prepare-payload.py:20` and `stage-chromium.py:14`, and copied into the APK as `assets/quest-dependencies.json` (`prepare-payload.py:544`).
  - Docker build contexts: `frame-runtime`, `steam-client`, `openvr-headers` (`build-rootfs.sh:53-54`).
  - Rootfs job output: `rootfs-output/frame-rootfs.tar.zst` and `SHA256SUMS` (`build-rootfs.sh:65-69`).
  - Package job output in `dist/`: `stearlight-quest.apk`, `stearlight-quest.apk.sha256`, `stearlight-quest-sources.zip`, `BUILD.json`, `SHA256SUMS`, `README.md`, `LICENSE.md` (`package-apk.py:116-128`).
  - Download cache: `quest-work/downloads` (`build.yml:109`). Android SDK tool path: `$ANDROID_HOME/build-tools/35.0.0/apksigner` (`build.yml:145`).
- **Wire formats:**
  - Rootfs parts: `rootfs/part-NNN.bin`, 16 MiB each (`split-rootfs.py:16`), listed in `rootfs.list` (`split-rootfs.py:19`), with a whole-stream SHA-256 in `rootfs.sha256` (`split-rootfs.py:20`). `package-apk.py:43-56` checks the list and the digest.
  - Base rootfs archive: gzip level 1, PAX tar, owner 0 and mtime 0 (`package-rootfs.py:25`, `:30`).
  - `encrypted-keystore.json` (`build.yml:216-222`): JSON `{"version": 1, "key", "nonce", "ciphertext"}`, each field base64. `key` is an AES-256 key wrapped with RSA-OAEP (SHA-256, label = the context string); `nonce` is 12 bytes; `ciphertext` is AES-256-GCM over the keystore with associated data `Stearlight local signing recovery v1`. The destination RSA key must be at least 3072 bits (`build.yml:211`).
  - `BUILD.json` (`package-apk.py:123-124`): `commit`, `target`, `supported_devices`, `rootfs_parts`, `rootfs_sha256`.

### Depends on / used by
- **Depends on:** `packages/quest-runtime` (Gradle project `:app`, C/C++ sources and `linux/`, read by `prepare-payload.py` and `build.yml:140`); `packages/stearlight-runtime` (`Containerfile:25`, `:54-60`); `packages/openvr/headers` (`build-rootfs.sh:54`); `system_files/` (`Containerfile:121-170`); `packages/quest-runtime/README.md` (copied into the download set at `package-apk.py:121`); `LICENSE.md`; `packages/sources.lock.json` (recovery and QEMU pins).
- **Used by:** `tests/quest-build-test.py` loads `post_process/quest/package-apk.py` (`tests/quest-build-test.py:14-16`); `packages/quest-runtime` uses the payload that `prepare-payload.py` writes; the Windows VM scripts under `post_process/*.ps1` read the output of `build-image.sh` (`build-image.sh:77` copies `start-vm.ps1` next to the image).

### Open issues
Posted drafts whose `Where:` line names a file in this module (numbers from `docs/issue-drafts/posted.tsv`; I did not check GitHub for closed state):
- #49 Fail the image build when a Steam runtime edit matches nothing (`Containerfile`)
- #50 Make the Windows VM download steps match what the Continuous release publishes (`post_process/README.md`, `publish-continuous.sh`)
- #51 Cache the Mesa, FNA3D and PRoot build trees in the Quest APK workflow (`build.yml`, `prepare-payload.py`)
- #52 Pin the package versions installed in the Containerfile stages (`Containerfile`)
- #53 Verify Chromium archives before they take their final name (`stage-chromium.py`)
- #54 Let a rerun recover after a killed recovery download (`fetch-recovery.py`)
- #55 Remove the Steam account config file the sanitizer misses (`sanitize-steam-profile.sh`)
- #56 Escape quotes in the compatibility table's cover image attributes (`generate_compatibility.py`)
- #57 Pick duplicate shared libraries in a fixed order when staging (`stage-frame-desktop.py`, `stage-chromium.py`)
- #58 Run the desktop password test in check.sh (`build_files/quest/check.sh`)
- #59 Run the Steam channel tests in check.sh (`build_files/quest/check.sh`)
- #60 Run the Bluetooth and power bridge tests in check.sh (`build_files/quest/check.sh`, `build.yml`)
- #61 Run the remaining Quest JavaScript bridge tests in check.sh (`build_files/quest/check.sh`)
- #62 Build and run the linear NV12 plane layout test in CI (`build_files/quest/check.sh`, `build.yml`)
- #68 Bound the tracking publication test so a hang fails (`build_files/quest/check.sh`)
- #69 Run the FNA3D buffer reuse test against a pinned source (`build-fna3d.py`, `build_files/quest/check.sh`, `build.yml`)
- #72 Layout test reads COPY flags and JSON-array sources (`Containerfile`)
- #73 Publish failure tests assert the failure reason (`publish-continuous.sh`)
- #78 Read the signing passwords from build inputs, not from source (`build.yml`)
- #79 Pin third-party GitHub Actions to commit SHAs (`pr-vouch.yml`, `build.yml`)
- #80 Sign manual test APKs with the continuous key only from the default branch (`build.yml`)
- #81 Check the Windows QEMU files against the hash list before packaging (`build-image.sh`)
- #83 Reject Frame desktop symlinks that resolve outside the image (`stage-frame-desktop.py`)
- #108 Acceptance: release APK installs and first-run extraction shows the dashboard (`publish-continuous.sh`)
- #112 Acceptance: game and desktop audio play from the headset (`publish-continuous.sh`)

### Notes
- `build_files/quest/check.sh` runs with `set -euo pipefail` (`:2`), so the first failing test stops the job and later tests do not run.
- Only `build_files/quest/check.sh` runs in CI (`build.yml:44-46`). `build_files/check.sh` is documented in `tests/README.md:6` but no workflow or Justfile recipe calls it.
- `Containerfile` serves two builds: the Quest rootfs (`build-rootfs.sh:55`) and the archived VM (`build-image.sh:59`). A change to it reaches the Quest APK.
- `publish-continuous.sh` deletes every release asset outside its allowlist (`:38-43`), and skips a build that is not the current default-branch head (`:11-12`).
- `package-apk.py:123` lists Quest 3 and Quest 3S as `supported_devices` in `BUILD.json`. `SPEC.md` (W2) says Quest 3 tuning is out of scope. The metadata and the spec disagree.

## tests
**Path:** `tests/`, `packages/quest-runtime/tests/`   **Status:** present   **Serves:** M2, M3 (Steam and game-runtime tests), M4 (frame, motion, video and present tests), M5 (audio tests), M6 (gamepad and hand-input tests), M7 (Bluetooth bridge test), M8 (OS-update and Steam-update tests). I found no test of the M9 free-space check; `frame-menus.test.py` mentions uninstall but is not a storage test.   **Platforms:** linux build host (most tests run with host Python, Node, g++ or cc and no headset) / Quest 2 runtime (device-only tests, listed below) / windows (`tests/launcher-test.ps1`, `tests/test-arm64.ps1`)
**Purpose:** Host-runnable checks for the Quest runtime's Python, C, C++ and JavaScript bridges, plus shell and C checks for the image, OpenXR and Vulkan layers. Each `*.test.*` file is meant to be wired into `build_files/quest/check.sh` (SPEC.md, Testing decisions). Only 47 of the 89 `*.test.*` files are wired. The `tests/` shell and C programs are mostly not run by CI.

### Files
Columns: what the test targets; how it runs; whether `build_files/quest/check.sh` runs it (line). "Not run by CI" means no workflow or check script reaches it.

| File | Role (targets) | Key entry points (how it runs; check.sh) |
|---|---|---|
| `packages/quest-runtime/tests/audio-identity.test.py` | Native audio adapter acknowledges only existing process identities | python3; check.sh:21 |
| `packages/quest-runtime/tests/audio-queue.test.py` | Live-audio backlog recovery and shutdown without Android hardware | python3; check.sh:20 |
| `packages/quest-runtime/tests/battery-snapshot.test.py` | Battery values across charging and unavailable Android readings | python3; check.sh:17 |
| `packages/quest-runtime/tests/bluetooth-bridge.test.py` | Bluetooth D-Bus bridge against Android radio snapshots (`linux/bluetooth-bridge.cpp`) | python3; not run by CI (S4.12 #60) |
| `packages/quest-runtime/tests/capture-matrix-abi.test.py` | Unknown capture libraries keep their original row implementation | python3; check.sh:84 |
| `packages/quest-runtime/tests/capture-matrix.test.c` | Capture matrix; takes an optional reference-code path in argv[1] | cc -std=c11; check.sh:82 (run without argv[1]) |
| `packages/quest-runtime/tests/celeste-memory.test.py` | Celeste memory and renderer restore, and updated-game cases | python3; not run by CI (S4.19 #67, S4.23 #71) |
| `packages/quest-runtime/tests/clean-build.test.py` | Regressions for clean, unprivileged Quest builds (issue #14) | python3; check.sh:13 |
| `packages/quest-runtime/tests/clock-bridge.test.py` | Android tzdata extraction and Linux timezone updates, with a real JVM | python3; check.sh:16 |
| `packages/quest-runtime/tests/controller-input.test.cpp` | Controller input (`controller_input.h`) | manual compile; not run by CI |
| `packages/quest-runtime/tests/controller-pose.test.cpp` | Grip component on the unrotated controller model | g++; check.sh:66 |
| `packages/quest-runtime/tests/desktop-apps.test.py` | Desktop app defaults, file forwarding, locale choice, Flatpak install rejection | python3; not run by CI |
| `packages/quest-runtime/tests/desktop-manager.test.py` | Desktop password: invalid password, change needs the old one, status hides the hash | python3; not run by CI (S4.10 #58, S4.18 #66) |
| `packages/quest-runtime/tests/desktop-update-ui.test.cjs` | Desktop update UI bridge (`linux/desktop-ui-bridge.js`) in a Node VM | node; not run by CI (S4.13 #61) |
| `packages/quest-runtime/tests/device-profile.test.cpp` | Device profile (`device_profile.h`, `quest_bridge.h`, `controller_pose.h`) | g++; check.sh:60 |
| `packages/quest-runtime/tests/display-pulse.test.cpp` | Display pulse over a shared `QuestTracking` memfd | g++; check.sh:69 |
| `packages/quest-runtime/tests/external-gamepad.test.cpp` | External gamepad state (`external_gamepad.h`) | g++; check.sh:75 |
| `packages/quest-runtime/tests/eye-projection.test.cpp` | Eye projection with unequal vertical and horizontal half-angles | g++; check.sh:63 |
| `packages/quest-runtime/tests/fex-signal.test.py` | FEX signal handling: exact-byte adaptation, refusal of unknown builds, restore | python3; check.sh:55 |
| `packages/quest-runtime/tests/fna-buffer-reuse.test.py` | Pinned upstream FNA3D `SetBufferData` (built by `build-fna3d.py`) | python3; not run by CI (S4.21 #69) |
| `packages/quest-runtime/tests/frame-controls.test.py` | Frame atlas coordinates stay paired with pixels across UI transitions | python3; check.sh:29 |
| `packages/quest-runtime/tests/frame-menu-ui.test.cjs` | Frame menu bridge (`linux/frame-menu-bridge.js`) in a Node VM | node, only if Node is installed (check.sh:30-34) |
| `packages/quest-runtime/tests/frame-menus.test.py` | Desktop entries, stale-window handling, scoped UI gating | python3; check.sh:27 |
| `packages/quest-runtime/tests/game-launch-wrapper.test.py` | Argument boundaries, exit propagation, update-safe installation of the launch wrapper | python3; check.sh:51 |
| `packages/quest-runtime/tests/game-reaper.test.py` | Leaving a local game leaves no background children | python3; check.sh:54 |
| `packages/quest-runtime/tests/game-runtime.test.py` | Content-addressed runtime files, gamepad preload scope, Gamescope panel, launch identity | python3; check.sh:52 |
| `packages/quest-runtime/tests/gamepad-ui.test.py` | Existing OS bridge refresh; unknown bridge left unchanged | python3; not run by CI |
| `packages/quest-runtime/tests/gamescope-shm.test.py` | `patch-gamescope.py` ARM branches, mapping preservation, unknown runtime rejected | python3; not run by CI |
| `packages/quest-runtime/tests/gpu-bridge-lifecycle.test.cpp` | GPU bridge lifecycle (`gpu_bridge.cpp`) with EGL and GLES | NDK build on an Android device; not run by CI |
| `packages/quest-runtime/tests/gpu-frames.test.cpp` | `FramePool` and `FrameLeases` producer and consumer handoff | g++ -pthread; check.sh:71 |
| `packages/quest-runtime/tests/hand-input.test.cpp` | Hand input (`gamepad_state.h`, `hand_input.h`, `hand_math.h`); asserts the 384-byte `QuestTracking` ABI | g++; not run by CI |
| `packages/quest-runtime/tests/hand-skeleton.test.cpp` | Hand bone positions against an independent rotation matrix | g++ with `packages/openvr/headers`; check.sh:58 |
| `packages/quest-runtime/tests/hostname.test.c` | Guest `uname -r` and `-v` on the installed Quest image | device only; not run by CI |
| `packages/quest-runtime/tests/loading-boost.test.py` | Loading-boost behaviour (the file has no module docstring) | python3; check.sh:22 |
| `packages/quest-runtime/tests/lsof-launcher.test.py` | Steam owner query against live sockets (`linux/lsof-launcher.c`) | python3; not run by CI |
| `packages/quest-runtime/tests/mesa-kgsl-alloc.test.py` | Patched Mesa KGSL allocator and capability probe against KGSL ABIs | python3; not run by CI |
| `packages/quest-runtime/tests/mesa-kgsl-merge.test.py` | Patched Mesa KGSL helper with mocked ioctls and file descriptors | python3; not run by CI |
| `packages/quest-runtime/tests/mesa-kgsl-poll.test.py` | Patched Mesa KGSL helper, poll path, with mocked ioctls | python3; not run by CI |
| `packages/quest-runtime/tests/motion.test.cpp` | `questPublishMotion` writes a `QuestMotion` sample into shared memory | g++; check.sh:73 |
| `packages/quest-runtime/tests/mountinfo-cache.test.py` | Mount snapshots, namespace isolation, invalidation, bounded lifetime | python3; check.sh:24 |
| `packages/quest-runtime/tests/network-bridge.test.py` | Wi-Fi observations over D-Bus and delegated controls, no radio | python3; check.sh:85 |
| `packages/quest-runtime/tests/network-interfaces.test.py` | Network interface enumeration (`ifaddrs.h`) | python3; check.sh:86 |
| `packages/quest-runtime/tests/os-update-activation.test.py` | Confirmed OS update survives the next start; an incomplete start restores the old runtime | python3; check.sh:19 |
| `packages/quest-runtime/tests/pcvr-color-shader.test.cpp` | PCVR colour shader (`pcvr_color_shader.h`) with its `.spv` fixture | g++; not run by CI |
| `packages/quest-runtime/tests/play-space.test.cpp` | Play-space helper (`play_space.h`) | g++; not run by CI |
| `packages/quest-runtime/tests/play-space.test.py` | OpenXR stage becomes valid seated and floor origins | python3; not run by CI |
| `packages/quest-runtime/tests/power-bridge.test.py` | UPower contract against changing Android battery readings | python3; not run by CI (S4.12 #60) |
| `packages/quest-runtime/tests/presentation-color.test.cpp` | Presentation shader colour path (`presentation_shader.h`) with EGL and GLES | NDK build on an Android device; not run by CI |
| `packages/quest-runtime/tests/proton-runtime.test.py` | Adapter backups, failed backup leaves settings untouched, flat-panel settings | python3; check.sh:53 |
| `packages/quest-runtime/tests/robust-wait.test.c` | Robust wait helper (pthread) | cc -pthread; check.sh:80 |
| `packages/quest-runtime/tests/roomview-bridge.test.cjs` | Room view bridge (`linux/roomview-bridge.js`) in a Node VM | node; not run by CI (S4.13 #61) |
| `packages/quest-runtime/tests/roomview-floor.test.py` | Native floor branches follow room view; unknown runtime rejected | python3; not run by CI |
| `packages/quest-runtime/tests/roomview-stars.test.cpp` | Room-view star shaders (`roomview_shaders.h`) over a directory of `.spv` files | g++; takes argv[1]; not run by CI |
| `packages/quest-runtime/tests/rootfs-archive.test.py` | APK overlay extraction with and without an installed OS update | python3; check.sh:15 |
| `packages/quest-runtime/tests/sdl-gamepad.test.cpp` | SDL gamepad adapter (`libquest_gamepad_x86_64.so` via LD_PRELOAD) | run on device or with an SDL host; not run by CI |
| `packages/quest-runtime/tests/sdl-gamepad.test.py` | SDL gamepad adapter against real SDL2, including embedded-SDL dispatch | python3; check.sh:36 |
| `packages/quest-runtime/tests/sdl2-delta.test.cpp` | Calls made by the SDL2 feed, including rejected updates | g++; check.sh:43 |
| `packages/quest-runtime/tests/sdl3-delta.test.cpp` | SDL3 feed loop with the real shared-memory reader | g++; check.sh:39 |
| `packages/quest-runtime/tests/sdl3-gamepad.test.cpp` | Installed Frame SDL3 with LD_PRELOAD (`libquest_android_gamepad.so`) | run on device; not run by CI (`linux/sdl3-gamepad.cpp` is only syntax-checked, check.sh:77) |
| `packages/quest-runtime/tests/sdl3-resolver.test.py` | ELF global lookup for SDL3 without a host SDL3 | python3; check.sh:37 |
| `packages/quest-runtime/tests/services-lifecycle.test.py` | Embedded services release their D-Bus names on shutdown | python3; not run by CI |
| `packages/quest-runtime/tests/share-mirror.test.c` | Real capture hook (`linux/share-mirror.h`) while the dashboard is visible | device only (uses `/opt/quest/libquest_socket.so`); not run by CI |
| `packages/quest-runtime/tests/socket-registry.test.py` | Socket and credential bridge on Linux, including close cleanup | python3; check.sh:87 |
| `packages/quest-runtime/tests/steam-capture.test.cpp` | GPU capture works without `gpu.sock` or OpenXR (`/opt/quest/libquest_vulkan.so`) | on-device integration; not run by CI |
| `packages/quest-runtime/tests/steam-channel.test.py` | Launcher arguments keep an explicit channel; native contract and branch persistence (`steamos-select-branch`) | python3; not run by CI (S4.11 #59) |
| `packages/quest-runtime/tests/steam-channels-state.test.py` | Channel state recovery, client change, frame profile, confirmed versions (`linux/steam_channels.py`) | python3; not run by CI (S4.11 #59) |
| `packages/quest-runtime/tests/steam-client-update.test.py` | Steam client update restores adapters without rewriting unchanged files | python3; not run by CI |
| `packages/quest-runtime/tests/steam-gamepad-launch.test.py` | Physical input stays in Steam across repeated runtime preparation | python3; check.sh:35 |
| `packages/quest-runtime/tests/steam-input.test.py` | Steam input adaptation: exact-byte, refusal of unknown builds, restore | python3; check.sh:25 |
| `packages/quest-runtime/tests/steam-integrity.test.py` | Recovery of damaged Steam code, keeping adapters and user data | python3; check.sh:26 |
| `packages/quest-runtime/tests/steam-os-update.test.py` | Chunked download reuse, reconnect, duplicate detection, beta key trust | python3; check.sh:18 |
| `packages/quest-runtime/tests/steam-startup.test.py` | Native loader adapter: exec, IPC and ownership paths | python3; check.sh:28 |
| `packages/quest-runtime/tests/steam-update.test.cjs` | Steam update bridge (`linux/steam-update-bridge.js`) in a Node VM | node; not run by CI (S4.13 #61) |
| `packages/quest-runtime/tests/store-browser-bridge.test.cjs` | Store browser bridge (`linux/store-browser-bridge.js`) in a Node VM | node; not run by CI (S4.13 #61) |
| `packages/quest-runtime/tests/streaming-input.test.py` | Coupled Touch identity and axis adaptation, restore, update safety | python3; check.sh:48 |
| `packages/quest-runtime/tests/streaming-socket.test.py` | UDP fast path of the streaming preload and its libc fallbacks | python3; check.sh:49 |
| `packages/quest-runtime/tests/syscall-fast-path.test.c` | PRoot syscall fast-path prefix; reaching the end means it ran | cc; check.sh:78 |
| `packages/quest-runtime/tests/systemui-overlay-bridge.test.cjs` | System UI overlay bridge (`linux/systemui-overlay-bridge.js`) in a Node VM | node; not run by CI (S4.13 #61) |
| `packages/quest-runtime/tests/tracee-cache.test.c` | PRoot tracee cache (`proot/tracee-cache.h`) | cc; not run by CI |
| `packages/quest-runtime/tests/tracking-publication.test.cpp` | `QuestTracking` publication between a forked writer and reader | g++; not run by CI (S4.20 #68) |
| `packages/quest-runtime/tests/video-codec.test.py` | Decoder backpressure through the bridge, with a mock codec | python3; check.sh:47 |
| `packages/quest-runtime/tests/video-decoder.test.cpp` | Video decoder path (device path `/opt/quest/libquest_streaming_drm.so`) | device-side; not run by CI |
| `packages/quest-runtime/tests/video-format.test.cpp` | Sequence header handling (`linux/video_sequence.h`, `videodev2.h`) | g++; not run by CI |
| `packages/quest-runtime/tests/video-format.test.py` | Adapter announces sequence headers before it requires a picture | python3; check.sh:50 |
| `packages/quest-runtime/tests/video-image-layout.test.cpp` | NV12 plane layout (`video_image_layout.h`) | g++; not run by CI (S4.14 #62) |
| `packages/quest-runtime/tests/video-queue.test.cpp` | Video queue | g++; not run by CI |
| `packages/quest-runtime/tests/video-queue.test.py` | Real V4L2 adapter with a deterministic decoder transport | python3; check.sh:46 |
| `packages/quest-runtime/tests/wine-pe-memory.test.c` | Page-mapping check for the Wine PE memory helper (no docstring) | cc; not run by CI |
| `packages/quest-runtime/tests/wsi-events.test.py` | Production WSI event waits over a socketpair, no GPU | python3; check.sh:23 |
| `packages/quest-runtime/tests/fex-signal-stress.c` | Manual Quest regression for FEX signals | `x86_64-linux-gnu-gcc -O1 -static -pthread`, by hand; not run by CI |
| `tests/quest-build-test.py` | Fresh-install archives and continuous-release failure paths (`package-apk.py`, `publish-continuous.sh`) | python3; quest check.sh:12 |
| `tests/recovery-test.py` | `fetch-recovery.py` verified downloads, without the multi-GB image | python3; quest check.sh:14 and build_files/check.sh:9 |
| `tests/layout-test.sh` | Repository layout: Containerfile COPY sources and required files | sh; build_files/check.sh:10 only, not run by CI |
| `tests/steamvr-native-test.sh` | `steamvr-native` launcher platform selection | sh; build_files/check.sh:11 only, not run by CI |
| `tests/frame-browser-test.sh` | `frame-browser` preparation, saved-launcher restore, invalid-mode check | sh; build_files/check.sh:12 only, not run by CI |
| `tests/xr-bridge-env-test.sh` | XR bridge environment; skips cleanly where Unix sockets are missing | sh; build_files/check.sh:13 only, not run by CI |
| `tests/xr-lifecycle-test.sh` | XR bridge lifecycle; same clean skip | sh; build_files/check.sh:14 only, not run by CI |
| `tests/openxr-runtime-test.sh` | Compiles `tests/openxr-runtime-test.c` with cc against the shipped OpenXR loader, then runs it | bash, by hand; not run by CI |
| `tests/openxr-runtime-test.c` | OpenXR runtime test program run by the script above | compiled by `openxr-runtime-test.sh`; not run by CI |
| `tests/angle-visual-test.c` | ANGLE visual-interposer version lookup (`dlsym`) | no runner; not run by CI (S4.27 #75) |
| `tests/vulkan-present-test.c` | Vulkan present probe; holds 15 s when asked | no runner; not run by CI (S4.28 #76) |
| `tests/vulkan-external-buffer-test.c` | 400-byte host-visible external uniform buffer, GPU writes both ways across two guest processes | no runner; not run by CI |
| `tests/vulkan-external-image-test.c` | External image sharing between guest processes (no docstring) | no runner; not run by CI |
| `tests/vulkan-timeline-bridge-test.c` | Timeline bridge between two processes and GPU devices | no runner; not run by CI |
| `tests/vulkan-queue-family-test.c` | Queue family enumeration; needs no Vulkan device | no runner; not run by CI |
| `tests/launcher-test.ps1` | Windows launcher paths with the bundled QEMU; `layout-test.sh` checks the file exists | PowerShell, by hand (`tests/README.md:12`); not run by CI |
| `tests/test-arm64.ps1` | Developer capture helper for the Windows VM (window, cursor, capture) | PowerShell, by hand (`tests/README.md:22`); not run by CI |

### Interfaces
- **Inputs / outputs:** most tests read module source files by relative path and write temporary files with `mktemp` or `tempfile`. Device-only tests open paths under `/opt/quest/` (`packages/quest-runtime/tests/steam-capture.test.cpp`, `share-mirror.test.c`, `video-decoder.test.cpp`). `tests/recovery-test.py` and `tests/quest-build-test.py` build fake archives in temporary directories and never download the real image.
- **Wire formats:** `QuestTracking` is asserted to be 384 bytes (`packages/quest-runtime/tests/hand-input.test.cpp`, `static_assert`). `QuestMotion` is written through `questPublishMotion` (`packages/quest-runtime/tests/motion.test.cpp`). The NV12 layout is checked in `video-image-layout.test.cpp`.

### Depends on / used by
- **Depends on:** `packages/quest-runtime/app/src/main/cpp` (headers for the C++ tests), `packages/quest-runtime/linux` (the bridges, launchers and `.js` files the Node and Python tests load), `packages/quest-runtime/proot`, `build_files/quest/*.py` (`patch-*.py`, `build-fna3d.py`, `fetch-recovery.py`), `post_process/quest/package-apk.py` and `publish-continuous.sh`, `system_files/`, `Containerfile`, and `packages/openvr/headers`.
- **Used by:** `build_files/quest/check.sh` (CI, `build.yml:44-46`); `build_files/check.sh` (documented in `tests/README.md:6`, not called by CI); `Justfile:8-9` (`check` recipe).

### Open issues
Posted drafts whose `Where:` line names a file in this module (numbers from `docs/issue-drafts/posted.tsv`; not checked against GitHub):
- #53 Verify Chromium archives before they take their final name (new `tests/chromium-download-test.py`)
- #54 Let a rerun recover after a killed recovery download (`tests/recovery-test.py:41-47`)
- #56 Escape quotes in the compatibility table's cover image attributes (new `tests/generate-compatibility-test.py`)
- #58 Run the desktop password test in check.sh (new `tests/quest-check-wiring-test.py`)
- #59 Run the Steam channel tests in check.sh (new `tests/quest-check-wiring-test.py`)
- #60 Run the Bluetooth and power bridge tests in check.sh (`bluetooth-bridge.test.py:92`, `power-bridge.test.py:48`)
- #61 Run the remaining Quest JavaScript bridge tests in check.sh (new `tests/quest-check-wiring-test.py`)
- #62 Build and run the linear NV12 plane layout test in CI (`video-image-layout.test.cpp`)
- #63 Fail the Frame controls test when Node is missing (`frame-controls.test.py`)
- #64 Test the hardlink fallback in rootfs extraction (`rootfs-archive.test.py`)
- #65 Test that rootfs extraction rejects escaping archive paths (`rootfs-archive.test.py`)
- #66 Reject a NUL byte in the current desktop password (`desktop-manager.test.py`)
- #67 Make the updated-game Celeste test check a real game tree (`celeste-memory.test.py`)
- #68 Bound the tracking publication test so a hang fails (`tracking-publication.test.cpp`)
- #69 Run the FNA3D buffer reuse test against a pinned source (`fna-buffer-reuse.test.py`)
- #70 Scope the gamepad adapter test to its one path (`proton-runtime.test.py`)
- #71 Test the Celeste renderer checksum path with real bytes (`celeste-memory.test.py`)
- #72 Layout test reads COPY flags and JSON-array sources (`tests/layout-test.sh`)
- #73 Publish failure tests assert the failure reason (`tests/quest-build-test.py`)
- #74 Frame browser test checks the invalid-mode message (`tests/frame-browser-test.sh`)
- #75 ANGLE visual probe finds dlsym on current glibc (`tests/angle-visual-test.c`)
- #76 Vulkan present probe holds for 15 seconds only when asked (`tests/vulkan-present-test.c`)
- #83 Reject Frame desktop symlinks that resolve outside the image (new `tests/frame-desktop-symlink-test.py`)
- #91 Stop the tester console giving an unauthenticated root shell (`tests/test-arm64.ps1`)
- #105 Quote QEMU arguments that contain spaces (`tests/test-arm64.ps1`)
- #107 Restore window z-order and cursor after the arm64 capture (`tests/test-arm64.ps1`)

### Notes
- Only 47 of the 89 `*.test.*` files are in `build_files/quest/check.sh`. The other 42 are not run by CI. `SPEC.md` (Testing decisions) requires each test file to be wired in the same change that adds it. Several of the 42 are device-only and cannot run on the host.
- The five `tests/*.sh` checks listed under `build_files/check.sh` are reached only through that script, which no workflow calls. The other `tests/` programs (`openxr-runtime-test.*`, `angle-visual-test.c`, the `vulkan-*` programs, the two `.ps1` files) have no runner in the repository. In CI the only `tests/` programs that run are `tests/recovery-test.py` and `tests/quest-build-test.py`.
- Of the `.cjs` tests, only `frame-menu-ui.test.cjs` is wired, and it is skipped with a message when Node is absent (`check.sh:30-34`). The other five are not wired.
- `tests/quest-check-wiring-test.py`, which several drafts ask for, does not exist yet. The `(new)` files named in the open-issue list are the same.
- `packages/quest-runtime/tests/PERFORMANCE.md` and `STREAMING.md` are notes, not tests.

## windows-runtime
**Path:** `packages/windows-runtime/`, `post_process/*.ps1` (including `post_process/quest/*.ps1`), `build_files/build-arm64.ps1`, `build_files/extract-frame-runtime.ps1`   **Status:** present   **Serves:** None for 1.0. This module is out of scope under W1 (the Windows and QEMU VM runtime is no longer maintained).   **Platforms:** windows (MSYS2 UCRT64 host build, PowerShell launchers, Docker Desktop or WSL for the image step) / the guest it boots is ARM64 Linux
**Purpose:** Builds and runs the Windows QEMU VM that hosted the ARM64 Linux guest. The `post_process/quest/*.ps1` scripts are the Windows-side developer tools for the Quest build (APK build, ADB shell, USB network, linux debug run). The module is listed for completeness. SPEC.md says Windows build and test scripts are kept working, but W1 takes the VM runtime out of 1.0, so this section lists files only.

### Files
| File | Role | Key entry points (file:line) |
|---|---|---|
| `packages/windows-runtime/build-runtime.sh` | Builds Windows GTK QEMU and the Venus renderer in MSYS2 UCRT64; applies patches; copies DLLs, licences and sources into the output | pins (:10-11), `checkout` (:12-18), patch hash check (:20-25), renderer patch loop (:26-28), renderer build (:29-32), QEMU patch loop (:36), QEMU build (:37-44), outputs (:46-47), DLL closure (:49-55), resources and sources (:56-67), smoke tests (:68-70) |
| `packages/windows-runtime/windows-venus/build.sh` | Builds an already patched Venus renderer tree | :12-14 |
| `packages/windows-runtime/windows-venus/sources.lock.json` | Pins the renderer repository and commit `e80354b8...`, and the SHA-256 of 8 patches | `commit` (:2), `patches` list |
| `packages/windows-runtime/windows-venus/README.md` | Describes the renderer, its patches, the build entry and known limits | n/a |
| `packages/windows-runtime/windows-venus/patches/0001-resolve-windows-handle-tokens-before-crt.patch` | Resolves Windows handle tokens before the CRT | applied at `build-runtime.sh:26-28` |
| `packages/windows-runtime/windows-venus/patches/0002-import-windows-host-memory-for-internal-resources.patch` | Imports Windows host memory for internal resources | same |
| `packages/windows-runtime/windows-venus/patches/0003-preserve-device-local-resources-until-memory-binding.patch` | Keeps device-local resources until memory binding | same |
| `packages/windows-runtime/windows-venus/patches/0004-preserve-replies-and-filter-mapped-memory.patch` | Preserves replies and filters mapped memory | same |
| `packages/windows-runtime/windows-venus/patches/0005-share-vulkan-images-with-allocation-metadata.patch` | Shares Vulkan images with allocation metadata | same |
| `packages/windows-runtime/windows-venus/patches/0006-recheck-pending-commands-in-idle-windows-rings.patch` | Rechecks pending commands in idle Windows rings | same |
| `packages/windows-runtime/windows-venus/patches/0007-share-host-visible-buffers-through-windows-sections.patch` | Shares host-visible buffers through Windows sections | same |
| `packages/windows-runtime/windows-venus/patches/0008-preserve-tiling-for-opaque-vulkan-images.patch` | Preserves tiling for opaque Vulkan images | same |
| `packages/windows-runtime/qemu/patches/0001-guard-gtk-wgl-context.patch` | Guards the GTK GL area WGL context in QEMU `ui/gtk.c` | applied at `build-runtime.sh:36` |
| `build_files/build-arm64.ps1` | Archived: Windows wrapper for the ARM64 image build through Docker Desktop or WSL | params (:2-6, WSL distribution default at :5), `docker import` (:129, :131), buildx (:133), artifact copies (:144-148), e2fsprogs step (:155-164) |
| `build_files/extract-frame-runtime.ps1` | Archived: Windows wrapper that extracts the Frame runtime from the recovery image through WSL | params (:2-6), WSL path helper (:20), shell literal helper (:35) |
| `post_process/package-windows.ps1` | Archived: zips the extracted VM package as `stearlight-frame-windows.zip` after checking listed hashes | params (:1-3), checksum loop (:14-19), `7z` archive (:20) |
| `post_process/start-vm.ps1` | Archived: starts the bundled QEMU with the account disk and an optional USB/IP Bluetooth bus | params (:2-6: `VmDirectory`, `MemoryMegabytes` 4096, `CpuCount` 6, `BluetoothBusId`), required files (:18), `Start-Process` (:84-89) |
| `post_process/quest/build-apk.ps1` | Windows Gradle build of the APK from a payload folder, with an optional signing store | param block (:1-5) |
| `post_process/quest/run-linux-debug.ps1` | ADB developer run: restarts the app and starts a network monitor on the device | `$Adb` and switches (:1), `Run-Adb` (:4), monitor start (:56) |
| `post_process/quest/shell.ps1` | ADB developer shell into the installed app (PowerShell twin of `shell.sh`) | param (:2), install check (:5-6) |
| `post_process/quest/usb-network.ps1` | Shares the Windows network to a Quest over the `UsbNcm` adapter; `-Undo` reverses it | param (:2), adapter selection (:4-6), `SupportsShouldProcess` (:1) |

### Interfaces
- **Inputs / outputs:**
  - `start-vm.ps1` takes `-VmDirectory`, `-MemoryMegabytes` (2048 to 8192), `-CpuCount` (1 to 12) and `-BluetoothBusId` (`post_process/start-vm.ps1:3-6`). It requires `qemu/qemu-system-aarch64.exe` and `qemu/qemu-img.exe` and more (`:18`).
  - `build-runtime.sh` writes `qemu-system-aarch64.exe`, `qemu-img.exe`, `libvirglrenderer-1.dll` and `vulkan-1.dll`, then the DLL closure found by `ldd` (`:46-55`). It also writes `share/`, `licenses/` and `sources/` (`:56-67`).
  - `build-runtime.sh` reads the QEMU repository and commit from `packages/sources.lock.json` (`:10`) and the renderer pins from `windows-venus/sources.lock.json` (`:11`).
  - `shell.ps1`, `run-linux-debug.ps1` and `usb-network.ps1` take an `-Adb` path (default `adb`) and, for USB networking, `-Serial`.
- **Wire formats:** none defined in this module. The Venus patches change the guest-to-host command stream; `sources.lock.json` lists each patch by SHA-256 (`windows-venus/sources.lock.json`).

### Depends on / used by
- **Depends on:** MSYS2 UCRT64 packages (`build-runtime.sh:56-65`), the QEMU and renderer repositories at the pinned commits (`build-runtime.sh:19`, `:33`), Docker or WSL (`build_files/build-arm64.ps1:129-164`), and the ADB tool (`post_process/quest/*.ps1`).
- **Used by:** `Justfile:20-21` (`packages` recipe runs `build-runtime.sh`), `Justfile:24-25` (`package` runs `package-windows.ps1`), `Justfile:28-29` (`run-vm` runs `start-vm.ps1`), `build_files/build-image.sh:77` (copies `start-vm.ps1` into the VM output), `tests/layout-test.sh` (checks that the listed files exist), and `tests/launcher-test.ps1`.

### Open issues
Posted drafts whose `Where:` line names a file in this module (numbers from `docs/issue-drafts/posted.tsv`; not checked against GitHub):
- #78 Read the signing passwords from build inputs, not from source (`post_process/quest/build-apk.ps1:25-32`)
- #81 Check the Windows QEMU files against the hash list before packaging (`post_process/package-windows.ps1:14-19`)
- #82 Pin the Alpine image and e2fsprogs version in the ARM64 disk step (`build_files/build-arm64.ps1:160-161`)
- #91 Stop the tester console giving an unauthenticated root shell (`post_process/start-vm.ps1:44`)
- #100 Close the received descriptor after a Venus resource import (`windows-venus/patches/0005-...patch:70-78`)
- #101 Decide what mmap does with a raw HANDLE fildes (`windows-venus/patches/0001-...patch`)
- #102 Refuse or import a non-SHM resource with export allowed (`windows-venus/patches/0007-...patch:~158-170`)
- #103 Apply only the Venus patches listed in the lock file (`build-runtime.sh:23-27`)
- #104 Make the Windows runtime build rerunnable in the same directory (`build-runtime.sh:27`, `:36-37`)
- #106 Fix the missed wakeup on idle Windows rings instead of polling (`windows-venus/patches/0006-...patch`)

### Notes
- `build-runtime.sh:20-25` checks each patch's SHA-256 against the lock file, but the apply loop at `:26-28` uses a glob over `patches/*.patch`, not the lock list. A patch file that is not in the lock file would still be applied (see #103).
- `build-runtime.sh:37` runs `mkdir "$work/qemu-build"` without `-p`, so a second run in the same work directory stops there (see #104).
- `post_process/package-windows.ps1:14-19` checks only the hashes listed in `SHA256SUMS`; files outside that list are not checked (see #81).
- The tests that drive this module (`tests/launcher-test.ps1`, `tests/test-arm64.ps1`) are listed in the `tests` section. They are run by hand, not by CI.
