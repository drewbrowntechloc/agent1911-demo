import http.server, socketserver, sys, os, gzip, io
root=sys.argv[1]; port=int(sys.argv[2])
os.chdir(root)
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.wasm':'application/wasm','.webmanifest':'application/manifest+json','.js':'text/javascript','.pck':'application/octet-stream'}
    def end_headers(self):
        if self.path.split('?')[0].endswith(('sw.js','index.html','manifest.webmanifest','/')):
            self.send_header('Cache-Control','no-cache')
        super().end_headers()
    def log_message(self,*a): pass
class T(socketserver.ThreadingMixIn,http.server.HTTPServer): daemon_threads=True
T(('127.0.0.1',port),H).serve_forever()
