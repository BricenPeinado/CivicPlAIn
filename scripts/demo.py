"""Start a fresh, isolated synthetic demo without changing or deleting any existing DB.

Run with .venv/bin/python scripts/demo.py. Ctrl+C stops only these child processes.
Every run creates a new ignored directory; there is deliberately no reset/delete option.
"""
import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def port(value):
    number = int(value)
    if not 1024 <= number <= 65535:
        raise argparse.ArgumentTypeError('Use a local unprivileged port (1024–65535).')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-port', type=port, default=8000)
    parser.add_argument('--web-port', type=port, default=5173)
    parser.add_argument('--production', action='store_true', help='Build and serve the production frontend')
    args = parser.parse_args()
    if args.api_port == args.web_port:
        parser.error('API and web ports must differ.')
    if not shutil.which('npm') or not (ROOT/'apps/web/node_modules').is_dir():
        parser.error('Install the documented backend requirements and run npm ci --prefix apps/web first.')
    # Check availability; strictPort and Uvicorn still handle races safely.
    for number in (args.api_port, args.web_port):
        try:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', number))
        except PermissionError:
            parser.error('Loopback binding is restricted by this environment; run from a local terminal with network permission.')
        except OSError:
            parser.error(f'Loopback port {number} is unavailable. Choose other ports; existing processes are preserved.')
    parent = ROOT/'data/tmp'
    parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='m6-demo-', dir=parent))
    env = {k: v for k, v in os.environ.items() if not k.startswith('VITE_') and k not in {'OPENAI_API_KEY','OPENAI_BASE_URL','OPENAI_MODEL'}}
    env.update(PYTHONPATH=str(ROOT/'apps/api'), CIVICPLAIN_DATABASE_PATH=str(folder/'demo.sqlite3'),
               CIVICPLAIN_ALLOWED_ORIGINS=f'http://127.0.0.1:{args.web_port}',
               CIVICPLAIN_AI_PROVIDER='deterministic', CIVICPLAIN_AI_MAX_CALLS_PER_HOUR='0',
               VITE_API_BASE_URL=f'http://127.0.0.1:{args.api_port}/api/v1')
    # Explicit override takes precedence over frontend env files; reject secret-shaped VITE variables.
    for config in (ROOT/'apps/web').glob('.env*'):
        if config.is_file() and any('VITE_' in line and any(word in line.upper() for word in ('KEY','SECRET','TOKEN','PASSWORD')) for line in config.read_text().splitlines() if not line.lstrip().startswith('#')):
            parser.error('Remove credential variables from frontend environment files before building a demo.')
    children = []
    def stop(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        subprocess.run([sys.executable, '-m', 'app.seed'], cwd=ROOT, env=env, check=True)
        if args.production:
            subprocess.run(['npm', 'run', 'build', '--prefix', 'apps/web'], cwd=ROOT, env=env, check=True)
        api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(args.api_port), '--no-access-log'], cwd=ROOT, env=env, start_new_session=True)
        children.append(api)
        deadline = time.monotonic()+20
        while True:
            if api.poll() is not None:
                raise RuntimeError('API exited during startup. Check the local error above.')
            try:
                with urlopen(f'http://127.0.0.1:{args.api_port}/api/v1/health', timeout=1) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                if time.monotonic() >= deadline:
                    raise RuntimeError('API startup timed out. Check installed requirements and try unused ports.') from None
                time.sleep(.2)
        web = subprocess.Popen(['npm','run','preview' if args.production else 'dev','--prefix','apps/web','--','--port',str(args.web_port),'--strictPort'], cwd=ROOT, env=env, start_new_session=True)
        children.append(web)
        print(f'\nSYNTHETIC isolated demo: http://127.0.0.1:{args.web_port}/\nDatabase retained: {folder.relative_to(ROOT)}/demo.sqlite3\nExplore Demo → inspect road → rework → scenarios → Explain tradeoffs.\nCtrl+C stops this demo. Rerun for a fresh environment; no existing records are reset.\n', flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.25)
        raise RuntimeError('A demo server stopped. Its database is retained; fix the error and rerun for a fresh isolated demo.')
    except KeyboardInterrupt:
        print('\nStopping demo processes; databases retained.', flush=True)
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        for child in reversed(children):
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    return 0


if __name__ == '__main__':
    sys.exit(main())
