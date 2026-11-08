"""Reliable one-window Coffee Rush launcher for Windows, macOS, and Linux.
Runs the bundled server and opens the browser only after the game has started.
"""
from __future__ import annotations
import os
import sys
import webbrowser
from pathlib import Path
from http.server import ThreadingHTTPServer

os.chdir(Path(__file__).resolve().parent)
os.environ['COFFEE_RUSH_HOST'] = '127.0.0.1'
os.environ['COFFEE_RUSH_PORT'] = '18765'

try:
    import server
    server.init_db()
    httpd = ThreadingHTTPServer((server.HOST, server.PORT), server.Handler)
except OSError as exc:
    print('\nCoffee Rush cannot start its server:', exc)
    print('Another copy of Coffee Rush may already be running.')
    print('Close earlier Coffee Rush windows, or use Play_Offline_Demo.html instead.')
    input('\nPress Enter to close...')
    sys.exit(1)
except Exception as exc:
    print('\nCoffee Rush could not start:', exc)
    print('If you do not have Python 3.10 or later, run Play_Offline_Demo.html.')
    input('\nPress Enter to close...')
    sys.exit(1)

url = f'http://127.0.0.1:{server.PORT}/'
print('\n' + '='*56)
print('THE UNWRITTEN CAFÉ — COFFEE RUSH')
print('='*56)
print('Your game is running at:', url)
print('If Edge does not open, copy that address into its address bar.')
print('Leave this window OPEN while playing.')
print('Press Ctrl+C to stop the game.')
print('='*56 + '\n')
try:
    webbrowser.open(url)
    httpd.serve_forever(poll_interval=.25)
except KeyboardInterrupt:
    print('\nStopping Coffee Rush...')
finally:
    httpd.server_close()
