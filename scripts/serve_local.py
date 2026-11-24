"""Local static preview with correct gzip artifact MIME and bounded file streaming."""
import argparse, functools, http.server, pathlib, urllib.parse
class Handler(http.server.SimpleHTTPRequestHandler):
    packages=None
    def translate_path(self,path):
        if path.startswith('/downloads/packages/') and self.packages:
            name=urllib.parse.unquote(path.split('?',1)[0].removeprefix('/downloads/packages/'))
            target=(self.packages/name).resolve()
            if target.is_relative_to(self.packages):return str(target)
        return super().translate_path(path)
    extensions_map={**http.server.SimpleHTTPRequestHandler.extensions_map,'.gz':'application/gzip','.mjs':'text/javascript','.js':'text/javascript','.parquet':'application/octet-stream'}
    def end_headers(self):
        self.send_header('Cache-Control','no-cache' if '/catalog/' in self.path else 'public, max-age=3600')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
    def log_message(self,*args):pass
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=pathlib.Path('dist'));p.add_argument('--port',type=int,default=8768);p.add_argument('--packages',type=pathlib.Path);a=p.parse_args();Handler.packages=(a.packages or a.root.resolve().parent.parent/'Packages').resolve();print(f'Local: http://127.0.0.1:{a.port}/',flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1',a.port),functools.partial(Handler,directory=str(a.root.resolve()))).serve_forever()
