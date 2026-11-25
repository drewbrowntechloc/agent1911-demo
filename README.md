# Agent 1911 — Mission Nupe (PWA demo)

Playable 3D test demo, installable as an app. Open the GitHub Pages link in Safari (iPhone) or Chrome, then Add to Home Screen / Install.

- Site files are in the repo root (`index.html`, `sw.js`, `manifest.webmanifest`, `index.wasm`, `index.pck`, …).
- `tools/make_pwa.py` re-wraps a fresh Godot web export as this PWA: `python3 tools/make_pwa.py <godot_export_dir> <output_dir>`.
- This repo holds the compiled web export only, not the Godot project source.
