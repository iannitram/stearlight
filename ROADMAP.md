# Roadmap

116 issues in 7 stages, all posted on this fork. The code map is `docs/code-map.md`, the spec is `SPEC.md`. Sizes follow the pipeline rubric (Easy up to about 80 changed lines and checkable on the build host, Medium about 80 to 300 lines or anything checkable only on the headset, Hard over about 300 or cross-cutting). Easy issues carry a brief for a local model and locked tests. Draft ids (S1.04) are in each issue title; `docs/issue-drafts/posted.tsv` maps them to numbers.

## Feature list

Each feature is a Must from `SPEC.md`. The acceptance issue closes the feature once the issues that gate it land.

| Feature | Must | What I can do when it is done | Acceptance issue | Gated by |
|---|---|---|---|---|
| F1 First-run install | M1 | The release APK installs on a Quest 2 and shows the SteamOS dashboard. | #108 | #22, #21, #24, #9, #10 |
| F2 Steam sign-in and library | M2 | Phone approval signs me in and my library shows. | #109 | #24, #21, #45 |
| F3 Game install | M3 | A library game installs with no endless spinner. | #110 | #21, #22, #24, #47 |
| F4 30-minute play | M4 | Smooth head turns and no crash for 30 minutes. | #111 | #6, #8, #16, #17, #18, #29, #30, #33, #34, #39, #40, #41, #42, #43 |
| F5 Sound | M5 | Game and desktop audio plays from the headset. | #112 | none found in the review |
| F6 Controllers | M6 | The Quest controllers work as a gamepad. | #113 | #20, #32 |
| F7 Bluetooth | M7 | A Bluetooth keyboard or gamepad pairs from the headset. | #114 | #2, #27, #45, #46 |
| F8 Updates keep data | M8 | Updating the APK or Steam keeps my account and games. | #115 | #11, #12, #13, #14, #22, #47 |
| F9 Clean uninstall | M9 | Uninstalling leaves no data behind. | #116 | #1, #3, #5 |

## Dev stages

Order: stage 1, then 2, then 3. Stage 4 (CI and tests) can run beside stage 1 because it touches only CI and test files. Stage 5 follows the Musts work. Stage 0 closes each Must when its blockers land. Stage 6 waits until after 1.0.

### Stage 1: Runtime correctness and session start

Crashes, wrong behaviour, leaks and silent failures in the app, the Linux bridges, the Vulkan shim and session start.

**Exit:** Every stage-1 issue closed; the build host check passes; acceptance M1 passes on a Quest 2.  
**Platform:** Quest 2 runtime (Linux code), built on the x86_64 Linux build host and in GitHub CI.  
**Size:** 24 issues: Easy 3, Medium 21, Hard 0.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #1 | S1.01 | Bound the Linux session stop so a missing pid cannot hold the session lock | Medium | M1 |  |
| #2 | S1.02 | Clear the advertise callback when a start request fails | Medium | M7 |  |
| #3 | S1.03 | Wait for and kill desktop app processes when the desktop bridge closes | Medium | M1 |  |
| #4 | S1.04 | Send no frame payload after a failed video response | Medium | M4 |  |
| #5 | S1.05 | Keep onDestroy from polling for the Linux pid on the UI thread | Medium | M1 | #1 |
| #6 | S1.06 | Close received DMA-BUF fds on every early return in swapchain setup | Medium | M4 |  |
| #7 | S1.07 | Stop CheckConnectivity from inserting an empty value before the first sync | Medium | M4 |  |
| #8 | S1.08 | Reject out-of-range image indices in vkQueuePresentKHR | Medium | M4 |  |
| #9 | S1.09 | Keep the desktop manager loop running when poll() raises | Medium | M1 |  |
| #10 | S1.10 | Log a failed optional Flatpak setup step instead of ending the Linux session | Medium | M1 |  |
| #11 | S1.11 | Report a busy SteamOS update lock without writing a failure | Easy | M8 |  |
| #12 | S1.12 | Write the VTOL graphics backup only through the verified helper | Easy | M3 |  |
| #13 | S1.13 | Launch Celeste when the capped renderer has no valid backup | Medium | M3 |  |
| #14 | S1.14 | Refuse to rename an existing launcher to the Valve binary name | Medium | none (cleanup) |  |
| #15 | S1.15 | Read an overlong window-list log line in full | Easy | M3 |  |
| #16 | S1.16 | Keep the Vulkan 1.2 timeline bit at its real offset | Medium | M4 |  |
| #17 | S1.17 | Stop writing into the app's const semaphore create info | Medium | M4 |  |
| #18 | S1.18 | Set sType and pNext on the appended queue family element | Medium | M4 |  |
| #19 | S1.19 | Keep the registered HMD alive when a later registration fails | Medium | M4 |  |
| #20 | S1.20 | Check component creation results in the fake controller | Medium | M4 |  |
| #21 | S1.21 | Reopen the Steam web log and drop the stale menu key | Medium | M4 |  |
| #22 | S1.22 | Stop the READY banner when Steam archive extraction fails | Medium | M1 |  |
| #23 | S1.23 | Keep reboot and shutdown requests when the Steam client exits non-zero | Medium | M1 |  |
| #24 | S1.24 | Point the steam session at a client the image actually installs | Medium | M1 |  |

### Stage 2: Frame pacing and the present path

Blocking waits, locks, per-frame logging and copies on the submit and present path. Likely cause of the head-turn jitter (upstream issue 34); not proven.

**Exit:** No wait without a timeout on the submit or present thread; a 10-minute frame-time capture on the Quest 2 has no stall over 100 ms; acceptance M4 passes.  
**Platform:** Quest 2 runtime; headset capture needed.  
**Size:** 20 issues: Easy 0, Medium 19, Hard 1.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #25 | S2.01 | Publish the socket registry table only when it changes | Medium | M4 |  |
| #26 | S2.02 | Decode boot animation frames off the render thread | Medium | M4 |  |
| #27 | S2.03 | Stop publishing the Bluetooth device list on every discovery result | Medium | M7 |  |
| #28 | S2.04 | Run the Linux session outside the poller thread pool | Medium | M4 |  |
| #29 | S2.05 | Stop the Mesa shared-timeline submit from blocking on the KGSL fence | Hard | M4 |  |
| #30 | S2.06 | Wait for the release fence in vkQueuePresentKHR without holding the swapchain lock | Medium | M4 | #8 |
| #31 | S2.07 | Read the socket batching switch once per process | Medium | M4 |  |
| #32 | S2.08 | Back off the shared gamepad state lookup when the file is missing | Medium | M4 |  |
| #33 | S2.09 | Copy decoded frames into the capture buffer outside the device lock | Medium | M4 |  |
| #34 | S2.10 | Look up epoll registrations without copying the whole map | Medium | M4 |  |
| #35 | S2.11 | Stop the emulated poll() from waking every millisecond while idle | Medium | M4 |  |
| #36 | S2.12 | Skip re-parsing bluetooth-devices.tsv when its text is unchanged | Medium | M4 |  |
| #37 | S2.13 | Send the developer-mode setting only when it changes | Medium | M4 |  |
| #38 | S2.14 | Stream the SteamOS update bundle to disk instead of holding it in memory | Medium | M4 |  |
| #39 | S2.15 | Make the synthetic vkWaitForPresentKHR honour present_id and timeout | Medium | M4 |  |
| #40 | S2.16 | Retry the timeline backing signal instead of stopping the worker | Medium | M4 |  |
| #41 | S2.17 | Log the stripped present id once, not on every present | Medium | M4 |  |
| #42 | S2.18 | Block waiters on the aliased queue lock instead of spinning | Medium | M4 |  |
| #43 | S2.19 | Remove the per-frame X round trip from the Mesa PutImage patch | Medium | M4 |  |
| #44 | S2.20 | Cache the driver vkQueueSubmit pointer per device | Medium | M4 |  |

### Stage 3: Steam installs, sound, controllers, Bluetooth, updates

The gaps between a running session and Musts M2, M3, M5, M6, M7 and M8.

**Exit:** Acceptance M2, M3, M5, M6, M7 and M8 pass.  
**Platform:** Quest 2 runtime.  
**Size:** 4 issues: Easy 1, Medium 1, Hard 2.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #45 | S3.01 | Stop the Bluetooth radio request from blocking the D-Bus loop | Hard | M7 |  |
| #46 | S3.02 | Read advertisement properties without calling back into the client | Hard | M7 |  |
| #47 | S3.03 | Refresh per-game FEX rootfs copies when the FEX runtime changes | Medium | M3 |  |
| #48 | S3.04 | Decode octal escapes in Steam manifest names as UTF-8 | Easy | M3 |  |

### Stage 4: CI and test coverage

Tests that exist but never run, tests that cannot fail, build and CI fixes. Every test file must be wired into `build_files/quest/check.sh`.

**Exit:** A guard test fails when a test file is not run by `check.sh`; CI is green; the Easy issues' locked tests run in CI.  
**Platform:** Linux build host and GitHub CI. Windows scripts kept working.  
**Size:** 28 issues: Easy 13, Medium 15, Hard 0.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #49 | S4.01 | Fail the image build when a Steam runtime edit matches nothing | Medium | none (cleanup) |  |
| #50 | S4.02 | Make the Windows VM download steps match what the Continuous release publishes | Medium | none (cleanup) |  |
| #51 | S4.03 | Cache the Mesa, FNA3D and PRoot build trees in the Quest APK workflow | Medium | none (cleanup) |  |
| #52 | S4.04 | Pin the package versions installed in the Containerfile stages | Medium | none (cleanup) |  |
| #53 | S4.05 | Verify Chromium archives before they take their final name | Easy | none (cleanup) |  |
| #54 | S4.06 | Let a rerun recover after a killed recovery download | Medium | none (cleanup) |  |
| #55 | S4.07 | Remove the Steam account config file the sanitizer misses | Medium | none (cleanup) |  |
| #56 | S4.08 | Escape quotes in the compatibility table's cover image attributes | Easy | none (cleanup) |  |
| #57 | S4.09 | Pick duplicate shared libraries in a fixed order when staging | Medium | none (cleanup) |  |
| #58 | S4.10 | Run the desktop password test in check.sh | Easy | none (cleanup) |  |
| #59 | S4.11 | Run the Steam channel tests in check.sh | Easy | none (cleanup) | #58 |
| #60 | S4.12 | Run the Bluetooth and power bridge tests in check.sh | Medium | none (cleanup) | #58 |
| #61 | S4.13 | Run the remaining Quest JavaScript bridge tests in check.sh | Easy | none (cleanup) | #58 |
| #62 | S4.14 | Build and run the linear NV12 plane layout test in CI | Medium | none (cleanup) | #58 |
| #63 | S4.15 | Fail the Frame controls test when Node is missing | Easy | none (cleanup) |  |
| #64 | S4.16 | Test the hardlink fallback in rootfs extraction | Easy | none (cleanup) |  |
| #65 | S4.17 | Test that rootfs extraction rejects escaping archive paths | Easy | none (cleanup) | #64 |
| #66 | S4.18 | Reject a NUL byte in the current desktop password | Easy | none (cleanup) |  |
| #67 | S4.19 | Make the updated-game Celeste test check a real game tree | Easy | none (cleanup) |  |
| #68 | S4.20 | Bound the tracking publication test so a hang fails | Medium | none (cleanup) | #58 |
| #69 | S4.21 | Run the FNA3D buffer reuse test against a pinned source | Medium | none (cleanup) | #58 |
| #70 | S4.22 | Scope the gamepad adapter test to its one path | Medium | none (cleanup) |  |
| #71 | S4.23 | Test the Celeste renderer checksum path with real bytes | Easy | none (cleanup) | #67 |
| #72 | S4.24 | layout test reads COPY flags and JSON-array sources | Easy | none (cleanup) |  |
| #73 | S4.25 | publish failure tests assert the failure reason | Medium | none (cleanup) |  |
| #74 | S4.26 | frame browser test checks the invalid-mode message | Easy | none (cleanup) |  |
| #75 | S4.27 | ANGLE visual probe finds dlsym on current glibc | Medium | none (cleanup) |  |
| #76 | S4.28 | Vulkan present probe holds for 15 seconds only when asked | Medium | none (cleanup) |  |

### Stage 5: Security hardening and cleanups

Root writes through predictable names, a verified file that is reread, open developer-mode services, unpinned actions, smaller cleanups.

**Exit:** No root-owned write goes through a predictable name; the update bundle is verified and used from one place; workflows pin their actions.  
**Platform:** Linux code and CI.  
**Size:** 23 issues: Easy 6, Medium 15, Hard 2.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #77 | S5.01 | Honor the developer-runtime extra only in debuggable builds | Medium | none (cleanup) |  |
| #78 | S5.02 | Read the signing passwords from build inputs, not from source | Medium | none (cleanup) |  |
| #79 | S5.03 | Pin third-party GitHub Actions to commit SHAs | Medium | none (cleanup) |  |
| #80 | S5.04 | Sign manual test APKs with the continuous key only from the default branch | Medium | none (cleanup) |  |
| #81 | S5.05 | Check the Windows QEMU files against the hash list before packaging | Medium | none (cleanup) |  |
| #82 | S5.06 | Pin the Alpine image and e2fsprogs version in the ARM64 disk step | Medium | none (cleanup) |  |
| #83 | S5.07 | Reject Frame desktop symlinks that resolve outside the image | Easy | none (cleanup) |  |
| #84 | S5.08 | Open the update log with O_NOFOLLOW and O_EXCL | Medium | none (cleanup) |  |
| #85 | S5.09 | Unpack only the bytes that the signature check read | Hard | none (cleanup) |  |
| #86 | S5.10 | Limit password guessing against developer-mode SSH and RDP | Hard | none (cleanup) |  |
| #87 | S5.11 | Create the atomic-write temporary file without following links | Easy | none (cleanup) |  |
| #88 | S5.12 | Refuse a symlink at the Proton game log path | Easy | none (cleanup) |  |
| #89 | S5.13 | Escape control bytes in names written to the shim log | Medium | none (cleanup) |  |
| #90 | S5.14 | Reject timeline fds that are not sealed against shrinking | Medium | none (cleanup) |  |
| #91 | S5.15 | Stop the tester console giving an unauthenticated root shell | Medium | none (cleanup) |  |
| #92 | S5.16 | Refuse .. in steamos-priv-write destinations | Medium | none (cleanup) |  |
| #93 | S5.17 | Stop root writing fixed names in /tmp at boot | Medium | none (cleanup) |  |
| #94 | S5.18 | Stop making every input event node world-writable | Medium | none (cleanup) |  |
| #95 | S5.19 | Refuse .. in pkexec command paths | Easy | none (cleanup) |  |
| #96 | S5.20 | Log when steamos-priv-write drops a non-root write | Easy | none (cleanup) | #92 |
| #97 | S5.21 | Accept only real zone files in steamos-set-timezone | Easy | none (cleanup) |  |
| #98 | S5.22 | Turn X access control back on in the VM boot script | Medium | none (cleanup) |  |
| #99 | S5.23 | Stop the serial console being writable by every local user | Medium | none (cleanup) |  |

### Stage 6: After 1.0: Windows VM runtime

Kept, not built. Won't W1.

**Exit:** Not scheduled.  
**Platform:** Windows and QEMU.  
**Size:** 8 issues: Easy 0, Medium 6, Hard 2.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #100 | S6.01 | close the received descriptor after a Venus resource import | Medium | none (cleanup) |  |
| #101 | S6.02 | decide what mmap does with a raw HANDLE fildes | Medium | none (cleanup) |  |
| #102 | S6.03 | refuse or import a non-SHM resource with export allowed | Hard | none (cleanup) |  |
| #103 | S6.04 | apply only the Venus patches listed in the lock file | Medium | none (cleanup) |  |
| #104 | S6.05 | make the Windows runtime build rerunnable in the same directory | Medium | none (cleanup) | #103 |
| #105 | S6.06 | quote QEMU arguments that contain spaces | Medium | none (cleanup) |  |
| #106 | S6.07 | fix the missed wakeup on idle Windows rings instead of polling | Hard | none (cleanup) |  |
| #107 | S6.08 | restore window z-order and cursor after the arm64 capture | Medium | none (cleanup) |  |

### Stage 0: Acceptance

One repeatable check per Must, run on a Quest 2 with the release APK.

**Exit:** All nine pass and are recorded in `docs/acceptance/`; that is 1.0.  
**Platform:** Quest 2 with the release APK.  
**Size:** 9 issues: Easy 0, Medium 9, Hard 0.

| Issue | Id | What | Size | Serves | Blocked by |
|---|---|---|---|---|---|
| #108 | S0.01 | Acceptance: release APK installs and first-run extraction shows the dashboard | Medium | M1 | #22, #21, #24, #9, #10 |
| #109 | S0.02 | Acceptance: Steam signs in with phone approval and shows my library | Medium | M2 | #24, #21, #45 |
| #110 | S0.03 | Acceptance: a library game installs and the install finishes | Medium | M3 | #21, #22, #24, #47 |
| #111 | S0.04 | Acceptance: a game plays 30 minutes with no visible jitter or crash | Medium | M4 | #6, #8, #16, #17, #18, #29, #30, #33, #34, #39, #40, #41, #42, #43 |
| #112 | S0.05 | Acceptance: game and desktop audio play from the headset | Medium | M5 |  |
| #113 | S0.06 | Acceptance: Quest controllers drive a game as a gamepad | Medium | M6 | #20, #32 |
| #114 | S0.07 | Acceptance: a Bluetooth keyboard or gamepad pairs from the headset | Medium | M7 | #2, #27, #45, #46 |
| #115 | S0.08 | Acceptance: an APK and Steam update keeps the account and installed games | Medium | M8 | #11, #12, #13, #14, #22, #47 |
| #116 | S0.09 | Acceptance: uninstalling the app removes its data and leaves no processes | Medium | M9 | #1, #3, #5 |

## Open-source candidates

From the prior-art list in `SPEC.md`. Code comes in only where the licence allows it, with credit; the rest is ideas.

| Project | Licence | Where it could help here | Use |
|---|---|---|---|
| FEX-Emu/FEX | MIT | The emulator this app already runs; compare its game-launch settings with mine (stages 1 and 3). | adopt upstream fixes with credit |
| ptitSeb/box64 | MIT | Alternative x86-64 emulator to benchmark against FEX for slow installs (stage 3). | learn, maybe adopt |
| Supreeeme/xrizer | GPL-3.0 | How an OpenVR-to-OpenXR layer handles input and frame timing (stage 2). | ideas only (GPL) |
| brunodev85/winlator | LGPL-2.1 | Android driver and Vulkan handling on ARM (stages 2 and 3). | ideas only |
| Producdevity/reframed-vr | none | The closest project; watch what it solves first. | ideas only (no licence) |
| termux/termux-x11, waydroid/waydroid | GPL-3.0 | Display and container ideas. | ideas only |
| alvr-org/ALVR, korejan/ALVR, WiVRn/WiVRn, LizardByte/Sunshine, ClarkCheekyKent/OpenComposite, olegos2/mobox | MIT / GPL-3.0 / none | Streaming and OpenVR projects, outside scope (Won't W4); reviewed weekly for ideas. | watch |

## Platforms

| Part | Quest 2 runtime | x86_64 Linux build host | Windows |
|---|---|---|---|
| App and bridges | runs here | built and tested here | not needed |
| Build and CI | produces the APK | runs here and in GitHub CI | scripts kept working, not extended |
| Windows VM runtime | not used | not used | out of scope (after 1.0) |

The newest Quest headsets and macOS are not targets for 1.0.

## Risks and unknowns

- The unpacked size of the app on the headset is not published. Acceptance M1 records it.
- The jitter cause is not proven. Stage 2 fixes the likely causes; the M4 frame-time capture decides whether more is needed.
- Behaviour on the Quest 2 can only be seen on the headset, so most fixes are Medium and cannot be tested on the build host.
- My day-to-day Linux build host has no C or C++ compiler installed, so the native host tests need a compiler added (a container or a toolchain package) before they can run. Two native issues were sized Medium instead of Easy for that reason.
- Quest system updates can change Android behaviour the app depends on; I recheck after each one.

## Upstream

Fixes land here first. I offer each one upstream on its own, with a video of the change working and the AI model named, as the upstream contributing guide asks.
