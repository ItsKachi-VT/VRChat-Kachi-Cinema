import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from flask import Flask, request


BASE_DIR = Path(__file__).resolve().parent
MOVIES_DIR = BASE_DIR / "movies"

app = Flask(__name__)


def find_mp4() -> Path:
	if not MOVIES_DIR.exists():
		return None
	candidates = sorted(MOVIES_DIR.glob("*.mp4"))
	return candidates[0] if candidates else None


@app.get("/video.mp4")
def video():
	movie = find_mp4()
	if not movie or not movie.exists():
		return "No hay .mp4 disponible", 404
	
	file_size = movie.stat().st_size
	range_header = request.headers.get("Range", None)
	
	if range_header:
		try:
			range_value = range_header.replace("bytes=", "")
			if "-" in range_value:
				start_str, end_str = range_value.split("-", 1)
				start = int(start_str) if start_str else 0
				end = int(end_str) if end_str else file_size - 1
				
				if start < 0:
					start = 0
				if end >= file_size:
					end = file_size - 1
				
				def stream_range():
					with open(movie, "rb") as f:
						f.seek(start)
						remaining = end - start + 1
						while remaining > 0:
							chunk = f.read(min(262144, remaining))
							if not chunk:
								break
							remaining -= len(chunk)
							yield chunk
				
				headers = {
					"Content-Type": "video/mp4",
					"Content-Range": f"bytes {start}-{end}/{file_size}",
					"Content-Length": str(end - start + 1),
					"Accept-Ranges": "bytes",
				}
				return (stream_range(), 206, headers)
		except:
			pass
	
	def stream_file():
		with open(movie, "rb") as f:
			while True:
				chunk = f.read(262144)
				if not chunk:
					break
				yield chunk
	
	headers = {
		"Content-Type": "video/mp4",
		"Content-Length": str(file_size),
		"Accept-Ranges": "bytes",
	}
	return (stream_file(), 200, headers)


def main() -> int:
	if not MOVIES_DIR.exists():
		MOVIES_DIR.mkdir(parents=True, exist_ok=True)

	port = 5000

	def _find_cloudflared_exe() -> str | None:
		# First try PATH
		exe = shutil.which("cloudflared")
		candidates = [exe]
		# Virtual environment scripts folder (when cloudflared was downloaded there)
		candidates += [str(BASE_DIR / ".venv" / "Scripts" / "cloudflared.exe")]
		# Common install paths on Windows
		candidates += [
			r"C:\\Program Files\\Cloudflare\\Cloudflared\\cloudflared.exe",
			str(Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Cloudflare" / "Cloudflared" / "cloudflared.exe"),
			str(Path.home() / "AppData" / "Local" / "Programs" / "Cloudflare" / "Cloudflared" / "cloudflared.exe"),
		]
		for c in candidates:
			if c and os.path.isfile(c):
				return c
		return None

	def _spawn_cloudflared(exe: str, args: list[str]) -> subprocess.Popen | None:
		for _ in range(3):
			try:
				return subprocess.Popen(
					[exe, *args],
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT,
					text=True,
				)
			except PermissionError as e:
				if getattr(e, "winerror", None) == 32:
					time.sleep(0.5)
					continue
				raise

		# Fallback for WinError 32: run a temporary copy if the original file is locked.
		try:
			tmp_exe = os.path.join(tempfile.gettempdir(), f"cloudflared-run-{int(time.time() * 1000)}.exe")
			shutil.copy2(exe, tmp_exe)
			return subprocess.Popen(
				[tmp_exe, *args],
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT,
				text=True,
			)
		except Exception:
			return None

	def start_cloudflare_quick_tunnel(port: int) -> tuple[str | None, subprocess.Popen | None]:
		exe = _find_cloudflared_exe()
		if not exe:
			return None, None
		# Quick Tunnel: ephemeral public URL via trycloudflare.com
		proc = _spawn_cloudflared(exe, ["tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"])
		if not proc:
			return None, None
		# Read lines until the public URL appears or timeout
		public_url = None
		deadline = time.time() + 20
		url_re = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)
		while time.time() < deadline:
			line = proc.stdout.readline()
			if not line:
				time.sleep(0.25)
				continue
			m = url_re.search(line)
			if m:
				public_url = m.group(0)
				break
		if public_url:
			# Keep process alive in background; do not wait
			return public_url, proc
		# Could not obtain URL; terminate
		try:
			proc.terminate()
		except Exception:
			pass
		return None, None

	def start_cloudflare_named_tunnel(name: str, hostname: str | None) -> tuple[str | None, subprocess.Popen | None]:
		exe = shutil.which("cloudflared")
		if not exe:
			return None, None
		proc = _spawn_cloudflared(exe, ["tunnel", "run", name, "--no-autoupdate"])
		if not proc:
			return None, None
		# For named tunnels, the URL is your hostname (DNS routed in Cloudflare dashboard)
		url = f"https://{hostname}" if hostname else None
		return url, proc

	# Cloudflare-only: prefer named tunnel if env provided, otherwise Quick Tunnel
	cf_tunnel_name = os.environ.get("CF_TUNNEL_NAME")
	cf_hostname = os.environ.get("CF_HOSTNAME")  # ej: video.tudominio.com
	public_url = None
	proc: subprocess.Popen | None = None
	if cf_tunnel_name:
		public_url, proc = start_cloudflare_named_tunnel(cf_tunnel_name, cf_hostname)
		if not public_url and cf_hostname:
			public_url = f"https://{cf_hostname}"
	else:
		public_url, proc = start_cloudflare_quick_tunnel(port)

	if not public_url:
		print("No se pudo iniciar Cloudflare Tunnel. Asegúrate de tener 'cloudflared' instalado y en PATH.")
		return 1

	print(f"Túnel activo: {public_url}/video.mp4")

	app.run(host="0.0.0.0", port=port, use_reloader=False)
	return 0


if __name__ == "__main__":  
	raise SystemExit(main())
