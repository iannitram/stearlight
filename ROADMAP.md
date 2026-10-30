# Roadmap

116 issues in 7 stages, written as files in `docs/issue-drafts/` (none posted yet). Sizes follow the pipeline rubric: Easy 23, Medium 86, Hard 7. Easy issues carry a local-model brief and locked tests. Each issue names the Must it serves (see `SPEC.md`). `Blocked by` uses draft ids; they become issue numbers when posted.

Order: stage 1, then 2, then 3, then 4. Stage 5 follows the Musts work, stage 0 closes each Must when its blockers land, and stage 6 waits until after 1.0. Stage 4 can start in parallel with stage 1 because the test-wiring issues touch only CI.

## Stage 0: Acceptance

One repeatable check per Must (M1 to M9), run on a Quest 2 with the release APK. These close last; they are blocked by the fixes that gate them.

9 issues (Easy 0, Medium 9, Hard 0).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S0.01 | Acceptance: release APK installs and first-run extraction shows the dashboard | Medium | M1 | S1.22, S1.21, S1.24, S1.09, S1.10 |
| S0.02 | Acceptance: Steam signs in with phone approval and shows my library | Medium | M2 | S1.24, S1.21, S3.01 |
| S0.03 | Acceptance: a library game installs and the install finishes | Medium | M3 | S1.21, S1.22, S1.24, S3.03 |
| S0.04 | Acceptance: a game plays 30 minutes with no visible jitter or crash | Medium | M4 | S1.06, S1.08, S1.16, S1.17, S1.18, S2.05, S2.06, S2.09, S2.10, S2.15, S2.16, S2.17, S2.18, S2.19 |
| S0.05 | Acceptance: game and desktop audio play from the headset | Medium | M5 |  |
| S0.06 | Acceptance: Quest controllers drive a game as a gamepad | Medium | M6 | S1.20, S2.08 |
| S0.07 | Acceptance: a Bluetooth keyboard or gamepad pairs from the headset | Medium | M7 | S1.02, S2.03, S3.01, S3.02 |
| S0.08 | Acceptance: an APK and Steam update keeps the account and installed games | Medium | M8 | S1.11, S1.12, S1.13, S1.14, S1.22, S3.03 |
| S0.09 | Acceptance: uninstalling the app removes its data and leaves no processes | Medium | M9 | S1.01, S1.03, S1.05 |

## Stage 1: Runtime correctness and session start

Crashes, wrong behaviour, leaks and silent failures in the Android app, the Linux bridges, the Vulkan shim and session start. Without these the 30-minute play test cannot pass.

24 issues (Easy 3, Medium 21, Hard 0).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S1.01 | Bound the Linux session stop so a missing pid cannot hold the session lock | Medium | M1 |  |
| S1.02 | Clear the advertise callback when a start request fails | Medium | M7 |  |
| S1.03 | Wait for and kill desktop app processes when the desktop bridge closes | Medium | M1 |  |
| S1.04 | Send no frame payload after a failed video response | Medium | M4 |  |
| S1.05 | Keep onDestroy from polling for the Linux pid on the UI thread | Medium | M1 | S1.01 |
| S1.06 | Close received DMA-BUF fds on every early return in swapchain setup | Medium | M4 |  |
| S1.07 | Stop CheckConnectivity from inserting an empty value before the first sync | Medium | M4 |  |
| S1.08 | Reject out-of-range image indices in vkQueuePresentKHR | Medium | M4 |  |
| S1.09 | Keep the desktop manager loop running when poll() raises | Medium | M1 |  |
| S1.10 | Log a failed optional Flatpak setup step instead of ending the Linux session | Medium | M1 |  |
| S1.11 | Report a busy SteamOS update lock without writing a failure | Easy | M8 |  |
| S1.12 | Write the VTOL graphics backup only through the verified helper | Easy | M3 |  |
| S1.13 | Launch Celeste when the capped renderer has no valid backup | Medium | M3 |  |
| S1.14 | Refuse to rename an existing launcher to the Valve binary name | Medium | none (cleanup) |  |
| S1.15 | Read an overlong window-list log line in full | Easy | M3 |  |
| S1.16 | Keep the Vulkan 1.2 timeline bit at its real offset | Medium | M4 |  |
| S1.17 | Stop writing into the app's const semaphore create info | Medium | M4 |  |
| S1.18 | Set sType and pNext on the appended queue family element | Medium | M4 |  |
| S1.19 | Keep the registered HMD alive when a later registration fails | Medium | M4 |  |
| S1.20 | Check component creation results in the fake controller | Medium | M4 |  |
| S1.21 | Reopen the Steam web log and drop the stale menu key | Medium | M4 |  |
| S1.22 | Stop the READY banner when Steam archive extraction fails | Medium | M1 |  |
| S1.23 | Keep reboot and shutdown requests when the Steam client exits non-zero | Medium | M1 |  |
| S1.24 | Point the steam session at a client the image actually installs | Medium | M1 |  |

## Stage 2: Frame pacing and the present path

Locking, blocking waits, per-frame logging and copies on the present and submit path. This is the likely cause of the head-turn jitter (upstream issue 34).

20 issues (Easy 0, Medium 19, Hard 1).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S2.01 | Publish the socket registry table only when it changes | Medium | M4 |  |
| S2.02 | Decode boot animation frames off the render thread | Medium | M4 |  |
| S2.03 | Stop publishing the Bluetooth device list on every discovery result | Medium | M7 |  |
| S2.04 | Run the Linux session outside the poller thread pool | Medium | M4 |  |
| S2.05 | Stop the Mesa shared-timeline submit from blocking on the KGSL fence | Hard | M4 |  |
| S2.06 | Wait for the release fence in vkQueuePresentKHR without holding the swapchain lock | Medium | M4 | S1.08 |
| S2.07 | Read the socket batching switch once per process | Medium | M4 |  |
| S2.08 | Back off the shared gamepad state lookup when the file is missing | Medium | M4 |  |
| S2.09 | Copy decoded frames into the capture buffer outside the device lock | Medium | M4 |  |
| S2.10 | Look up epoll registrations without copying the whole map | Medium | M4 |  |
| S2.11 | Stop the emulated poll() from waking every millisecond while idle | Medium | M4 |  |
| S2.12 | Skip re-parsing bluetooth-devices.tsv when its text is unchanged | Medium | M4 |  |
| S2.13 | Send the developer-mode setting only when it changes | Medium | M4 |  |
| S2.14 | Stream the SteamOS update bundle to disk instead of holding it in memory | Medium | M4 |  |
| S2.15 | Make the synthetic vkWaitForPresentKHR honour present_id and timeout | Medium | M4 |  |
| S2.16 | Retry the timeline backing signal instead of stopping the worker | Medium | M4 |  |
| S2.17 | Log the stripped present id once, not on every present | Medium | M4 |  |
| S2.18 | Block waiters on the aliased queue lock instead of spinning | Medium | M4 |  |
| S2.19 | Remove the per-frame X round trip from the Mesa PutImage patch | Medium | M4 |  |
| S2.20 | Cache the driver vkQueueSubmit pointer per device | Medium | M4 |  |

## Stage 3: Steam installs, sound, controllers, Bluetooth, updates

The gaps between a working session and the Musts M2, M3, M5, M6, M7 and M8: stale per-game copies, non-ASCII names, blocking Bluetooth calls.

4 issues (Easy 1, Medium 1, Hard 2).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S3.01 | Stop the Bluetooth radio request from blocking the D-Bus loop | Hard | M7 |  |
| S3.02 | Read advertisement properties without calling back into the client | Hard | M7 |  |
| S3.03 | Refresh per-game FEX rootfs copies when the FEX runtime changes | Medium | M3 |  |
| S3.04 | Decode octal escapes in Steam manifest names as UTF-8 | Easy | M3 |  |

## Stage 4: CI and test coverage

Tests that exist but never run, tests that cannot fail, and build and CI fixes. Every test file must be wired into build_files/quest/check.sh.

28 issues (Easy 13, Medium 15, Hard 0).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S4.01 | Fail the image build when a Steam runtime edit matches nothing | Medium | none (cleanup) |  |
| S4.02 | Make the Windows VM download steps match what the Continuous release publishes | Medium | none (cleanup) |  |
| S4.03 | Cache the Mesa, FNA3D and PRoot build trees in the Quest APK workflow | Medium | none (cleanup) |  |
| S4.04 | Pin the package versions installed in the Containerfile stages | Medium | none (cleanup) |  |
| S4.05 | Verify Chromium archives before they take their final name | Easy | none (cleanup) |  |
| S4.06 | Let a rerun recover after a killed recovery download | Medium | none (cleanup) |  |
| S4.07 | Remove the Steam account config file the sanitizer misses | Medium | none (cleanup) |  |
| S4.08 | Escape quotes in the compatibility table's cover image attributes | Easy | none (cleanup) |  |
| S4.09 | Pick duplicate shared libraries in a fixed order when staging | Medium | none (cleanup) |  |
| S4.10 | Run the desktop password test in check.sh | Easy | none (cleanup) |  |
| S4.11 | Run the Steam channel tests in check.sh | Easy | none (cleanup) | S4.10 |
| S4.12 | Run the Bluetooth and power bridge tests in check.sh | Medium | none (cleanup) | S4.10 |
| S4.13 | Run the remaining Quest JavaScript bridge tests in check.sh | Easy | none (cleanup) | S4.10 |
| S4.14 | Build and run the linear NV12 plane layout test in CI | Medium | none (cleanup) | S4.10 |
| S4.15 | Fail the Frame controls test when Node is missing | Easy | none (cleanup) |  |
| S4.16 | Test the hardlink fallback in rootfs extraction | Easy | none (cleanup) |  |
| S4.17 | Test that rootfs extraction rejects escaping archive paths | Easy | none (cleanup) | S4.16 |
| S4.18 | Reject a NUL byte in the current desktop password | Easy | none (cleanup) |  |
| S4.19 | Make the updated-game Celeste test check a real game tree | Easy | none (cleanup) |  |
| S4.20 | Bound the tracking publication test so a hang fails | Medium | none (cleanup) | S4.10 |
| S4.21 | Run the FNA3D buffer reuse test against a pinned source | Medium | none (cleanup) | S4.10 |
| S4.22 | Scope the gamepad adapter test to its one path | Medium | none (cleanup) |  |
| S4.23 | Test the Celeste renderer checksum path with real bytes | Easy | none (cleanup) | S4.19 |
| S4.24 | layout test reads COPY flags and JSON-array sources | Easy | none (cleanup) |  |
| S4.25 | publish failure tests assert the failure reason | Medium | none (cleanup) |  |
| S4.26 | frame browser test checks the invalid-mode message | Easy | none (cleanup) |  |
| S4.27 | ANGLE visual probe finds dlsym on current glibc | Medium | none (cleanup) |  |
| S4.28 | Vulkan present probe holds for 15 seconds only when asked | Medium | none (cleanup) |  |

## Stage 5: Security hardening and cleanups

Root writes through predictable names, unverified rereads, open developer-mode services, unpinned actions, and smaller cleanups. Done after the Musts work.

23 issues (Easy 6, Medium 15, Hard 2).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S5.01 | Honor the developer-runtime extra only in debuggable builds | Medium | none (cleanup) |  |
| S5.02 | Read the signing passwords from build inputs, not from source | Medium | none (cleanup) |  |
| S5.03 | Pin third-party GitHub Actions to commit SHAs | Medium | none (cleanup) |  |
| S5.04 | Sign manual test APKs with the continuous key only from the default branch | Medium | none (cleanup) |  |
| S5.05 | Check the Windows QEMU files against the hash list before packaging | Medium | none (cleanup) |  |
| S5.06 | Pin the Alpine image and e2fsprogs version in the ARM64 disk step | Medium | none (cleanup) |  |
| S5.07 | Reject Frame desktop symlinks that resolve outside the image | Easy | none (cleanup) |  |
| S5.08 | Open the update log with O_NOFOLLOW and O_EXCL | Medium | none (cleanup) |  |
| S5.09 | Unpack only the bytes that the signature check read | Hard | none (cleanup) |  |
| S5.10 | Limit password guessing against developer-mode SSH and RDP | Hard | none (cleanup) |  |
| S5.11 | Create the atomic-write temporary file without following links | Easy | none (cleanup) |  |
| S5.12 | Refuse a symlink at the Proton game log path | Easy | none (cleanup) |  |
| S5.13 | Escape control bytes in names written to the shim log | Medium | none (cleanup) |  |
| S5.14 | Reject timeline fds that are not sealed against shrinking | Medium | none (cleanup) |  |
| S5.15 | Stop the tester console giving an unauthenticated root shell | Medium | none (cleanup) |  |
| S5.16 | Refuse .. in steamos-priv-write destinations | Medium | none (cleanup) |  |
| S5.17 | Stop root writing fixed names in /tmp at boot | Medium | none (cleanup) |  |
| S5.18 | Stop making every input event node world-writable | Medium | none (cleanup) |  |
| S5.19 | Refuse .. in pkexec command paths | Easy | none (cleanup) |  |
| S5.20 | Log when steamos-priv-write drops a non-root write | Easy | none (cleanup) | S5.16 |
| S5.21 | Accept only real zone files in steamos-set-timezone | Easy | none (cleanup) |  |
| S5.22 | Turn X access control back on in the VM boot script | Medium | none (cleanup) |  |
| S5.23 | Stop the serial console being writable by every local user | Medium | none (cleanup) |  |

## Stage 6: After 1.0: Windows VM runtime

Kept, not sized for building, not built. The Windows and QEMU runtime is out of scope (Won't W1).

8 issues (Easy 0, Medium 6, Hard 2).

| Id | Issue | Size | Serves | Blocked by |
|---|---|---|---|---|
| S6.01 | close the received descriptor after a Venus resource import | Medium | none (cleanup) |  |
| S6.02 | decide what mmap does with a raw HANDLE fildes | Medium | none (cleanup) |  |
| S6.03 | refuse or import a non-SHM resource with export allowed | Hard | none (cleanup) |  |
| S6.04 | apply only the Venus patches listed in the lock file | Medium | none (cleanup) |  |
| S6.05 | make the Windows runtime build rerunnable in the same directory | Medium | none (cleanup) | S6.04 |
| S6.06 | quote QEMU arguments that contain spaces | Medium | none (cleanup) |  |
| S6.07 | fix the missed wakeup on idle Windows rings instead of polling | Hard | none (cleanup) |  |
| S6.08 | restore window z-order and cursor after the arm64 capture | Medium | none (cleanup) |  |
