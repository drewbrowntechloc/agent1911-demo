#!/usr/bin/env python3
"""
make_pwa.py — wrap a Godot 4 Web export as an installable, offline-capable PWA.

    python3 make_pwa.py <godot_web_export_dir> <output_dir>

Input : the folder Godot's "Export Project (Web)" produced (index.html, index.js, index.wasm, index.pck, ...).
Output: a self-contained static site folder. Upload/serve it from any HTTPS static host.

It never touches the game data: index.wasm / index.pck / index.js / worklets are copied byte-for-byte.
It replaces index.html (with a custom shell: loading screen, touch hardening, SW registration),
and adds manifest.webmanifest, sw.js, icons/, .nojekyll and _headers.
Re-run it after every re-export from the Godot editor; the service-worker hashes are recomputed so
installed copies update themselves.
"""
import hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIG = {'index.wasm', 'index.pck'}          # cached on first load, not pre-cached at install

def sha(path_or_bytes):
    h = hashlib.sha256()
    if isinstance(path_or_bytes, bytes):
        h.update(path_or_bytes)
    else:
        with open(path_or_bytes, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
    return h.hexdigest()[:12]

def die(msg):
    sys.exit('make_pwa.py: ' + msg)

def main():
    if len(sys.argv) != 3:
        die(__doc__)
    src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if src == out:
        die('output_dir must differ from the export folder')
    html_path = os.path.join(src, 'index.html')
    if not os.path.isfile(html_path):
        die('no index.html in ' + src)
    html = open(html_path, encoding='utf-8').read()

    # ---- read the engine config Godot generated for this export ----
    m = re.search(r'const GODOT_CONFIG = (\{.*?\});', html, re.S)
    t = re.search(r'const GODOT_THREADS_ENABLED = (true|false);', html)
    if not m or not t:
        die('index.html does not look like a Godot 4 web export (GODOT_CONFIG not found)')
    config = json.loads(m.group(1))
    exe = config.get('executable', 'index')
    if exe != 'index':
        die('expected executable "index", got %r (rename export to index.html)' % exe)
    # PWA shell lives next to the engine; Godot's own service worker option must stay off.
    config.pop('serviceWorker', None)

    need = ['index.js', 'index.wasm', 'index.pck']
    for n in need:
        if not os.path.isfile(os.path.join(src, n)):
            die('missing ' + n)

    os.makedirs(out, exist_ok=True)
    for name in os.listdir(out):                 # clear contents, keep the folder itself (running servers keep working)
        if name == '.git':
            continue
        full = os.path.join(out, name)
        shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
    os.makedirs(os.path.join(out, 'icons'))

    # ---- copy engine + game files byte-for-byte ----
    engine_files = ['index.js', 'index.wasm', 'index.pck']
    engine_files += sorted(f for f in os.listdir(src) if re.fullmatch(r'index\..*worklet\.js', f))
    for f in engine_files:
        shutil.copy2(os.path.join(src, f), os.path.join(out, f))
    for lic in ('GODOT_LICENSE.txt',):
        if os.path.isfile(os.path.join(src, lic)):
            shutil.copy2(os.path.join(src, lic), os.path.join(out, lic))

    # ---- icons ----
    icon_dir = os.path.join(HERE, 'assets')
    icons = ['icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png', 'favicon-32.png']
    for i in icons:
        shutil.copy2(os.path.join(icon_dir, i), os.path.join(out, 'icons', i))

    # ---- manifest ----
    manifest = {
        'id': './',
        'name': 'Agent 1911 — Mission Nupe',
        'short_name': 'Agent 1911',
        'description': 'Agent 1911 — Mission Nupe. Playable 3D test demo. Works offline after the first load.',
        'start_url': './?source=pwa',
        'scope': './',
        'display': 'fullscreen',
        'display_override': ['fullscreen', 'standalone'],
        'orientation': 'landscape',
        'background_color': '#0b1019',
        'theme_color': '#0b1019',
        'lang': 'en',
        'categories': ['games', 'entertainment'],
        'icons': [
            {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': 'icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    open(os.path.join(out, 'manifest.webmanifest'), 'w', encoding='utf-8').write(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')

    # ---- build id (stable for identical inputs) ----
    shell_tpl = open(os.path.join(HERE, 'templates', 'shell.html'), encoding='utf-8').read()
    ids = [sha(shell_tpl.encode())] + [sha(os.path.join(out, f)) for f in engine_files] + [sha(os.path.join(out, 'manifest.webmanifest'))]
    ids += [sha(os.path.join(out, 'icons', i)) for i in icons]
    build = sha(''.join(ids).encode())

    # ---- shell ----
    shell = (shell_tpl
             .replace('@@GODOT_CONFIG@@', json.dumps(config, separators=(',', ':')))
             .replace('@@GODOT_THREADS@@', t.group(1))
             .replace('@@BUILD@@', build))
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(shell)

    # ---- service worker with per-file revisions ----
    listed = ['index.html', 'manifest.webmanifest'] + engine_files + ['icons/' + i for i in icons]
    assets = {}
    for rel in listed:
        p = os.path.join(out, rel)
        assets[rel] = {'rev': sha(p), 'size': os.path.getsize(p), 'precache': rel not in BIG}
    sw = (open(os.path.join(HERE, 'templates', 'sw.js'), encoding='utf-8').read()
          .replace('@@ASSETS@@', json.dumps(assets, indent=2))
          .replace('@@BUILD@@', build))
    open(os.path.join(out, 'sw.js'), 'w', encoding='utf-8').write(sw)

    # ---- host helpers ----
    open(os.path.join(out, '.nojekyll'), 'w').close()
    open(os.path.join(out, '_headers'), 'w').write(
        '# Netlify / Cloudflare Pages. Safe to delete on hosts that ignore it.\n'
        '/index.html\n  Cache-Control: no-cache\n'
        '/sw.js\n  Cache-Control: no-cache\n  Service-Worker-Allowed: /\n'
        '/manifest.webmanifest\n  Cache-Control: no-cache\n'
        '/*.wasm\n  Content-Type: application/wasm\n'
    )
    print('build', build)
    for rel, a in assets.items():
        print('  %-34s %10d  %s%s' % (rel, a['size'], a['rev'], '' if a['precache'] else '  (cached on first load)'))

if __name__ == '__main__':
    main()
