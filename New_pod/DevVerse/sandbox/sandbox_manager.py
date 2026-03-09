"""
Sandbox Manager — Docker-based isolated preview for generated apps.
─────────────────────────────────────────────────────────────────────────
Builds and manages Docker containers for the AI-generated Flask apps.
Provides isolated, safe execution environments like a mini Claude sandbox.

References:
  Docker SDK    → https://docker-py.readthedocs.io/
  Docker docs   → https://docs.docker.com/
"""

from __future__ import annotations

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).parent.parent.absolute()
_PROJ_DIR     = _PROJECT_ROOT / "generated_project"
_SANDBOX_PORT = 5000
_IMAGE_NAME   = "devverse-sandbox"
_CONTAINER_NAME = "devverse-sandbox-app"


class SandboxManager:
    """
    Manages Docker sandbox containers for the generated Flask app.
    Falls back to direct process execution if Docker is not available.
    """

    def __init__(self):
        self._docker_available = self._check_docker()
        self._process = None

    @staticmethod
    def _check_docker() -> bool:
        """Check if Docker is installed and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @property
    def is_docker_available(self) -> bool:
        return self._docker_available

    def build_sandbox(self) -> bool:
        """
        Build Docker image for the generated project.

        Returns:
            True if build succeeded.
        """
        if not self._docker_available:
            print("⚠️  Docker not available. Using direct execution mode.")
            return False

        if not (_PROJ_DIR / "app.py").exists():
            raise FileNotFoundError("No generated project found to sandbox.")

        # Write Dockerfile into the generated project
        dockerfile_content = self._generate_dockerfile()
        (_PROJ_DIR / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

        # Build image
        result = subprocess.run(
            ["docker", "build", "-t", _IMAGE_NAME, "."],
            cwd=str(_PROJ_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"⚠️  Docker build failed: {result.stderr}")
            return False

        return True

    def start_sandbox(self) -> bool:
        """
        Start the sandbox container.
        Falls back to direct execution if Docker is unavailable.

        Returns:
            True if the app is running and accessible.
        """
        # Stop any existing sandbox
        self.stop_sandbox()

        if self._docker_available:
            return self._start_docker()
        else:
            return self._start_direct()

    def _start_docker(self) -> bool:
        """Start via Docker container."""
        if not self.build_sandbox():
            return self._start_direct()

        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", _CONTAINER_NAME,
                "-p", f"{_SANDBOX_PORT}:5000",
                "--restart", "unless-stopped",
                _IMAGE_NAME,
            ],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            print(f"⚠️  Docker run failed: {result.stderr}")
            return self._start_direct()

        # Wait for container to be healthy
        for _ in range(10):
            time.sleep(1)
            if self._is_running():
                return True

        return False

    def _start_direct(self) -> bool:
        """Start via direct Python process (fallback)."""
        app_file = _PROJ_DIR / "app.py"
        req_file = _PROJ_DIR / "requirements.txt"

        if not app_file.exists():
            raise FileNotFoundError("generated_project/app.py not found.")

        # Kill existing processes on port 5000
        self._kill_port_5000()

        # Install deps
        if req_file.exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
                cwd=str(_PROJ_DIR), check=False,
            )

        # Start
        log_file = open(_PROJ_DIR / "flask_error.log", "w")
        self._process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=str(_PROJ_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        time.sleep(2)
        if self._process.poll() is not None:
            raise RuntimeError("Flask server crashed! Check flask_error.log")

        return True

    def stop_sandbox(self) -> None:
        """Stop the running sandbox (Docker or direct)."""
        if self._docker_available:
            subprocess.run(
                ["docker", "rm", "-f", _CONTAINER_NAME],
                capture_output=True,
            )

        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process = None

        self._kill_port_5000()

    def _is_running(self) -> bool:
        """Check if the sandbox is running and responding."""
        try:
            import urllib.request
            resp = urllib.request.urlopen(
                f"http://127.0.0.1:{_SANDBOX_PORT}/",
                timeout=3,
            )
            return resp.status == 200
        except Exception:
            return False

    def get_status(self) -> dict:
        """Get sandbox status info."""
        running = self._is_running()
        mode = "docker" if self._docker_available else "direct"
        return {
            "running": running,
            "mode": mode,
            "port": _SANDBOX_PORT,
            "url": f"http://127.0.0.1:{_SANDBOX_PORT}",
            "docker_available": self._docker_available,
        }

    @staticmethod
    def _kill_port_5000():
        """Kill any processes on port 5000."""
        try:
            subprocess.run(
                ["powershell", "-Command",
                 "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue "
                 "| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force "
                 "-ErrorAction SilentlyContinue }"],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass

    @staticmethod
    def _generate_dockerfile() -> str:
        """Generate a Dockerfile for the sandbox container."""
        return """# DevVerse Sandbox Container
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install flask

# Copy app files
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \\
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Run
CMD ["python", "app.py"]
"""
