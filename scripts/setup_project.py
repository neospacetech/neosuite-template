#!/usr/bin/env python3
"""Interactive one-time bootstrap for a new project based on this template."""

from __future__ import annotations

import re
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
GUIDE_PATH = ROOT / "docs" / "DEPLOYMENT_GUIDE.md"
PROJECT_ENV_PATH = ROOT / ".project.env"
LOCAL_ENV_PATH = ROOT / ".env"
SSH_USER = "deployer"
SSH_PORT = 22
APP_BIND_RANGE = range(9000, 10000)
PUBLIC_PORT_RANGE = range(8000, 9000)


def ask_text(prompt: str, default: str | None = None) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        answer = input(f"{prompt}{suffix}: ").strip()
        if answer:
            return answer
        if default is not None:
            return default
        print("Please enter a value.")


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        answer = input(f"{prompt}{suffix}: ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def run_ssh(host: str, ssh_key_path: Path, command: str) -> str:
    result = subprocess.run(
        [
            "ssh",
            "-i",
            str(ssh_key_path),
            "-p",
            str(SSH_PORT),
            f"{SSH_USER}@{host}",
            command,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def used_remote_ports(host: str, ssh_key_path: Path) -> set[int]:
    output = run_ssh(
        host,
        ssh_key_path,
        "ss -tlnH | awk '{print $4}' | sed 's/.*://' | sort -u",
    )
    ports: set[int] = set()
    for line in output.splitlines():
        line = line.strip()
        if line.isdigit():
            ports.add(int(line))
    return ports


def find_free_port(used_ports: set[int], port_range: range) -> int:
    for port in port_range:
        if port not in used_ports:
            return port
    raise RuntimeError(
        f"No free port found in range {port_range.start}-{port_range.stop - 1}"
    )


def render_document(path: Path, replacements: dict[str, str]) -> None:
    content = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        content = content.replace(old, new)
    path.write_text(content, encoding="utf-8")


def render_docs(replacements: dict[str, str]) -> None:
    for path in (README_PATH, GUIDE_PATH):
        render_document(path, replacements)


def write_project_env(values: dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in values.items()]
    PROJECT_ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_local_env(values: dict[str, str]) -> None:
    lines = [
        "FLASK_ENV=development",
        f"FLASK_SECRET_KEY={values['FLASK_SECRET_KEY']}",
        f"APP_BIND_PORT={values['APP_BIND_PORT']}",
        f"PUBLIC_PORT={values['PUBLIC_PORT']}",
        f"SERVER_NAME={values['SERVER_NAME']}",
        f"DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/{values['POSTGRES_DB']}",
        "POSTGRES_USER=postgres",
        "POSTGRES_PASSWORD=postgres",
        f"POSTGRES_DB={values['POSTGRES_DB']}",
    ]
    LOCAL_ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_self() -> None:
    Path(__file__).resolve().unlink(missing_ok=True)


def main() -> int:
    print("Project bootstrap")
    print(
        "Answer the questions below and the script will fill the README and"
        " config files."
    )

    app_name_raw = ask_text("What is the app name?")
    app_name = slugify(app_name_raw)
    vps_host = ask_text("What is the VPS host/IP?")
    domain_available = ask_yes_no("Is a domain available for this app?", default=False)

    if domain_available:
        server_name = ask_text("What domain should nginx use?")
        public_port = 80
        deploy_mode = "domain"
    else:
        server_name = "_"
        deploy_mode = "port"

    ssh_key_path = Path(
        ask_text(
            "Where is the SSH private key?",
            default=str(Path.home() / ".ssh" / "vps_deploy"),
        )
    ).expanduser()
    if not ssh_key_path.exists():
        raise FileNotFoundError(f"SSH private key not found: {ssh_key_path}")

    if not domain_available:
        print("Scanning the VPS for free ports...")
        used_ports = used_remote_ports(vps_host, ssh_key_path)
        app_bind_port = find_free_port(used_ports, APP_BIND_RANGE)
        used_ports.add(app_bind_port)
        public_port = find_free_port(used_ports, PUBLIC_PORT_RANGE)
    else:
        used_ports = used_remote_ports(vps_host, ssh_key_path)
        app_bind_port = find_free_port(used_ports, APP_BIND_RANGE)

    public_endpoint = (
        f"http://{server_name}"
        if domain_available
        else f"http://{vps_host}:{public_port}"
    )

    flask_secret_key = secrets.token_hex(32)
    postgres_db = app_name

    replacements = {
        "# whatdoibuy": f"# {app_name}",
        "# {{APP_NAME}}": f"# {app_name}",
        "{{APP_NAME}}": app_name,
        "{{VPS_HOST}}": vps_host,
        "{{DEPLOY_MODE}}": deploy_mode,
        "{{PUBLIC_ENDPOINT}}": public_endpoint,
    }

    render_docs(replacements)

    project_env = {
        "APP_NAME": app_name,
        "VPS_HOST": vps_host,
        "DEPLOY_MODE": deploy_mode,
        "SERVER_NAME": server_name,
        "APP_BIND_PORT": str(app_bind_port),
        "PUBLIC_PORT": str(public_port),
    }
    write_project_env(project_env)

    local_env = {
        "FLASK_SECRET_KEY": flask_secret_key,
        "APP_BIND_PORT": str(app_bind_port),
        "PUBLIC_PORT": str(public_port),
        "SERVER_NAME": server_name,
        "POSTGRES_DB": postgres_db,
    }
    write_local_env(local_env)

    print()
    print("Setup summary")
    print(f"App name: {app_name}")
    print(f"VPS host: {vps_host}")
    print(f"Deployment mode: {deploy_mode}")
    print(f"Public endpoint: {public_endpoint}")
    print(f"Docker bind port: {app_bind_port}")
    print(f"Public nginx port: {public_port}")
    print(f"README updated: {README_PATH}")
    print(f"Guide updated: {GUIDE_PATH}")
    print(f"Project config written: {PROJECT_ENV_PATH}")
    print(f"Local env written: {LOCAL_ENV_PATH}")

    delete_self = ask_yes_no("Delete this setup script now?", default=True)
    if delete_self:
        remove_self()
        print("Setup script deleted itself.")
    else:
        print("Setup script kept in place.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
