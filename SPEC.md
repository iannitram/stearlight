# Spec

**1.0 means:** I can open the app on a Quest 2, sign in to Steam, install a game from my library and play it for 30 minutes with no jitter and no crash.

**Approved by me:** not yet

A project is Spec'd only when the line above has a date and a link. Change a Must or a Won't after approval and the approval line goes back to "not yet" until I approve again.

## Musts

Each Must is something a person can do and see. Each one gets its own issue (`docs/issue-drafts/S0.nn.md`), and each issue names the check that proves it. Results are recorded in `docs/acceptance/M<n>.md` (date, release tag, pass or fail, one log excerpt).

| # | Must | Done looks like | Check |
|---|---|---|---|
| M1 | WHEN I sideload the release APK on a Quest 2 and open it, THE APP SHALL finish first-run extraction and show the SteamOS dashboard. | The dashboard is on screen in the headset; free storage on `/data` dropped by the unpacked size and no error dialog appeared. | S0.01: repeat the install steps on a clean headset and record free space before and after. |
| M2 | WHEN I sign in with the Steam Guard approval on my phone, THE APP SHALL show my Steam library. | My library list is on screen and survives a restart of the app. | S0.02: sign in, restart the app, check the library is still there. |
| M3 | WHEN I choose a game from my library and press install, THE APP SHALL download and install it. | The game shows as installed; no spinner runs longer than the download itself. | S0.03: install a small game and a large game; time both; no endless spinner. |
| M4 | WHEN I launch an installed game and play for 30 minutes, THE APP SHALL show no visible jitter when I turn my head and SHALL NOT crash. | 30 minutes of play, head turns smooth, no restart; frame-time log has no stall over 100 ms. | S0.04: play 30 minutes, capture the frame-time log and the system log, count stalls and crashes. |
| M5 | WHEN a game or the desktop plays sound, THE APP SHALL play it from the headset. | I hear it, at a usable volume, without crackle. | S0.05: play a known audio clip in a game and in the desktop. |
| M6 | WHEN I hold the Quest controllers in a game, THE APP SHALL pass them to the game as a gamepad. | Buttons, sticks and triggers move the game's cursor and character. | S0.06: run a gamepad-test page and a game, check every input. |
| M7 | WHEN I pair a Bluetooth keyboard or gamepad from the headset, THE APP SHALL connect it and pass its input to the game. | The device shows as connected and its keys or buttons register. | S0.07: pair one keyboard and one gamepad, press every key and button on a test page. |
| M8 | WHEN I update the APK or Steam, THE APP SHALL keep my account and my installed games. | After the update I am still signed in and the games are still installed. | S0.08: update from one release to the next; compare the library and installed list before and after. |
| M9 | WHEN I uninstall the app, THE APP SHALL leave no data behind. | The app is gone from the library and `/data` free space returns to its starting value (within the system's own overhead). | S0.09: record free space, uninstall, record again. |

## Won'ts

Things 1.0 will not do, so nobody builds them by accident.

- W1: The Windows and QEMU VM runtime. It is no longer maintained; its issues are kept as `after-1.0`.
- W2: Tuning for the Quest 3 and Quest 3S. The Quest 2 is the target; the newer headsets are the upstream author's to maintain.
- W3: Games that use anti-cheat, and local VRChat. They do not run under emulation.
- W4: Streaming PC VR to the headset. The headset runs everything locally.

## Prior art

Projects doing the same thing, approved by me at Spec and reviewed weekly. Their code comes in only when their license allows it, with credit; otherwise only their ideas.

peer: Producdevity/reframed-vr | none | Closest match: an independent SteamOS-style OS for standalone Meta Quest and Pico headsets; watch for native SteamVR progress. No licence file: ideas only.
peer: alvr-org/ALVR | MIT | Main PC-to-Quest wireless streaming project; watch its Quest client and tracking work.
peer: WiVRn/WiVRn | GPL-3.0 | Linux OpenXR streaming server to standalone headsets; the most mature open option on Linux.
peer: korejan/ALVR | MIT | Fork of ALVR that hosts the ALXR OpenXR client; watch for standalone-client work.
peer: Supreeeme/xrizer | GPL-3.0 | OpenVR-to-OpenXR layer so SteamVR games run without SteamVR.
peer: ClarkCheekyKent/OpenComposite | GPL-3.0 | Community fork of OpenComposite with newer interfaces and eye-gaze input.
peer: ptitSeb/box64 | MIT | x86_64 userspace emulator for ARM64 Linux; compare with FEX for Steam workloads.
peer: FEX-Emu/FEX | MIT | Fast x86 and x86-64 emulator for Arm64 Linux; the emulator this app already uses.
peer: brunodev85/winlator | LGPL-2.1 | Android app running Wine plus Box64 with an X server; watch its Vulkan and driver work.
peer: termux/termux-x11 | GPL-3.0 | X server add-on for Android; the display side of Linux-on-Android setups.
peer: waydroid/waydroid | GPL-3.0 | Container-based Android on Linux; the reverse direction, kept for container ideas.
peer: LizardByte/Sunshine | GPL-3.0 | Self-hosted game-stream host; PC-side alternative for flat games.
peer: olegos2/mobox | none | Archived Termux Wine/box project; historical reference only. No licence file: ideas only.

## Problem

The app runs Valve's Steam Frame software inside a Quest 2 with PRoot, so the headset can be a standalone Steam machine. In my own use it is slow and unfinished: head turns jitter, some game installs hang, and parts of the session start can fail without a message. I do not want to carry a PC to play a library game.

## Solution

Fix what breaks the 30-minute play test first, then the frame pacing and the present path, then the Steam, sound, controller, Bluetooth and update gaps, and keep the work covered by tests that really run. I fix it in this fork and offer the fixes back to the upstream project one at a time.

## User stories

1. As a Quest 2 owner, I want to install one APK and reach a SteamOS dashboard, so that I do not need a PC.
2. As a Steam player, I want my library and installs to work, so that I can play what I already own.
3. As a player, I want smooth head tracking for 30 minutes, so that I can play without feeling sick.
4. As a player, I want sound, controllers and Bluetooth devices to work, so that games are playable.
5. As an owner, I want updates to keep my data and uninstall to remove it, so that I stay in control of my headset's storage.

## Implementation decisions

- The app stays an ordinary sideloaded Quest APK. No bootloader unlock, exploit or firmware change, ever.
- The runtime layout is kept: Android activity and OpenXR loop (`packages/quest-runtime/app`), Linux bridges and launchers (`packages/quest-runtime/linux`), Vulkan shim (`packages/stearlight-runtime`). See `docs/code-map.md`.
- Fixes land as small commits in this fork; each upstream PR is offered separately with a video of the change working and names the AI model used, as the upstream contributing guide asks.
- No Valve files, no Steam account data and no APK ever go into this repository.
- Licence: the upstream FSL-1.1-ALv2 stays; every change keeps it.
- Platforms: the Quest 2 target is built on an x86_64 Linux build host and in GitHub CI; Windows build and test scripts are kept working. The Windows VM runtime is out of scope (W1).

## Testing decisions

- A good test runs on the Linux build host with no headset, fails against the bug, and passes once fixed. Tests go through the module's public entry point (script entry, function, wire format), not private state.
- Behaviour that can only be seen on the headset is covered by the acceptance checks M1 to M9, recorded in `docs/acceptance/`.
- Every test file must be wired into `build_files/quest/check.sh` in the same change that adds it.
- Prior tests to copy: `packages/quest-runtime/tests/*.test.py` (unittest, deep-frozen inputs), `tests/*.sh`.

## Further notes

- Upstream issues #34 (head-turn jitter) and #30 (some installs hang) are the two open problems that matter most to the 30-minute play test.
- The unpacked size of the app and its rootfs is not published; M1 records it.
