"""Launch the KuKu Promo Finder product prototype.

Usage:
  python run_prototype.py
  python run_prototype.py --port 8787
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def _port_free(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _kill_port_windows(port: int) -> list[int]:
    """Kill PIDs listening on port (Windows). Returns killed PIDs."""
    killed: list[int] = []
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"],
            text=True,
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return killed

    my_pid = os.getpid()
    for line in out.splitlines():
        if f":{port}" not in line or "LISTENING" not in line.upper():
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid <= 0 or pid == my_pid:
            continue
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            killed.append(pid)
        except Exception:
            pass
    return killed


def main():
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    ap = argparse.ArgumentParser(description="KuKu Promo Finder prototype")
    ap.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.getenv("PORT", "8787")))
    ap.add_argument("--reload", action="store_true")
    ap.add_argument(
        "--no-kill",
        action="store_true",
        help="Do not free the port if something else is listening",
    )
    args = ap.parse_args()

    host, port = args.host, args.port

    if not _port_free(host, port):
        if args.no_kill:
            print(f"ERROR: port {port} is in use. Close that process or use --port N")
            sys.exit(1)
        print(f"Port {port} busy — stopping old listener…")
        killed = _kill_port_windows(port)
        if killed:
            print(f"  killed PID(s): {', '.join(map(str, killed))}")
        # wait until free
        for _ in range(20):
            time.sleep(0.25)
            if _port_free(host, port):
                break
        else:
            # fall back to next free port
            for alt in range(port + 1, port + 20):
                if _port_free(host, alt):
                    print(f"  still busy — using port {alt} instead")
                    port = alt
                    break
            else:
                print("ERROR: could not free a port. Try: restart_web.bat")
                sys.exit(1)

    import uvicorn

    print("")
    print(f"  KuKu Promo Finder  ->  http://{host}:{port}")
    print("  Modes: rule | hybrid (recommended) | llm")
    print("  Hard-refresh browser (Ctrl+F5) after start")
    print("")
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
