# {{APP_NAME}}

Template for a small Flask app with PostgreSQL, tests, Docker, and automated VPS deployment.

## Project details

- App name: {{APP_NAME}}
- VPS host: {{VPS_HOST}}
- Deployment mode: {{DEPLOY_MODE}}
- Public endpoint: {{PUBLIC_ENDPOINT}}

## What’s included

- App factory pattern
- Route and extension modules
- PostgreSQL support
- Pytest test suite
- Docker and Docker Compose
- GitHub Actions CI
- VPS deployment over SSH with nginx

## Project structure

```text
.
├── backend/                 Python service (canonical NeoSuite layout)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py
│   ├── scripts/wait_for_db.py
│   ├── tests/
│   ├── gunicorn.conf.py
│   ├── manage.py
│   ├── wsgi.py
│   ├── pyproject.toml
│   └── requirements.txt
├── deploy/
│   ├── Dockerfile           build from repo root: docker build -f deploy/Dockerfile .
│   ├── compose.yaml
│   ├── docker/entrypoint.sh
│   └── vps/
│       ├── docker-compose.vps.yml
│       └── nginx/site.conf.template
├── docs/DEPLOYMENT_GUIDE.md
├── scripts/setup_project.py
├── .github/workflows/
│   ├── ci.yml
│   └── deploy-digitalocean.yml
└── Makefile
```

## Quick start

1. Run the one-time bootstrap script:

```bash
python scripts/setup_project.py
```

It asks a short Q/A flow, fills this README with your app name and VPS host, writes the project config files, and then asks at the very end whether it should delete itself.

2. Start the app locally:

```bash
docker compose -f deploy/compose.yaml up --build
```

3. Check the endpoints:

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

Expected responses:

```json
{"message":"running"}
```

```json
{"status":"ok"}
```

## Run tests

```bash
python -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
pytest
```

## Database migrations

Initial migration setup:

```bash
export FLASK_APP=wsgi:app
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

After model changes:

```bash
flask db migrate -m "describe change"
flask db upgrade
```

## CI/CD overview

- `.github/workflows/ci.yml`
  - Runs on push and pull request
  - Starts PostgreSQL service
  - Installs dependencies
  - Runs pytest

- `.github/workflows/deploy-digitalocean.yml`
  - Runs on push to `main`
  - Loads project settings from `.project.env` when present
  - Builds the Docker image using the repository name or configured app name
  - Pushes image to GitHub Container Registry (GHCR)
  - SSHes into the VPS
  - Uploads the compose file and rendered nginx config
  - Restarts the app and reloads nginx

## VPS setup

This template deploys to a shared VPS. The `deployer` user is already assumed to exist.

### First-time VPS setup

Install Docker, Docker Compose, and nginx on the VPS.

For Ubuntu:

```bash
apt-get update
apt-get install -y docker.io docker-compose-plugin nginx
systemctl enable --now docker nginx
```

For CentOS:

```bash
yum install -y docker docker-compose-plugin nginx
systemctl enable --now docker nginx
```

Create a project directory for this app:

```bash
mkdir -p /opt/{{APP_NAME}}
chmod 755 /opt/{{APP_NAME}}
```

### SSH key setup

Generate a deploy key locally:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/vps_deploy -C "github-actions-deploy"
```

Copy the public key to the VPS as `deployer`:

```bash
ssh deployer@VPS_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys" < ~/.ssh/vps_deploy.pub
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

Add the private key to GitHub as `VPS_SSH_PRIVATE_KEY`.

### GitHub secrets

Add these secrets in the repository settings:

- `VPS_HOST`
- `VPS_USER` (usually `deployer`)
- `VPS_PORT` (optional, defaults to `22`)
- `VPS_SSH_PRIVATE_KEY`
- `GHCR_USERNAME`
- `GHCR_TOKEN` with `read:packages`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `FLASK_SECRET_KEY`

### Bootstrap questions

The setup script will ask:

1. App name
2. VPS host/IP
3. Whether a domain is available
4. If a domain is available, the domain name to use with nginx
5. If no domain is available, it scans the server for empty ports and assigns:
   - a free host port for the Docker container bind
   - a free public port for nginx
6. Whether the script should delete itself at the end

### Deployment flow

Each push to `main`:

1. Runs tests in CI.
2. Builds and pushes the image to GHCR.
3. Connects to the VPS.
4. Uploads `deploy/vps/docker-compose.vps.yml` to `/opt/{{APP_NAME}}/`.
5. Renders `deploy/vps/nginx/site.conf.template` using the chosen host port and public port.
6. Pulls the new image and restarts the stack.
7. Installs the nginx config into `/etc/nginx/conf.d/{{APP_NAME}}.conf` and reloads nginx.

## Multiple apps on one VPS

To run multiple apps without domains, give each app a unique public port and a unique Docker bind port.

Example:

| App | Docker bind port | nginx public port | URL |
| --- | --- | --- | --- |
| app-one | 9000 | 8000 | `http://VPS_IP:8000` |
| app-two | 9001 | 8001 | `http://VPS_IP:8001` |
| app-three | 9002 | 8002 | `http://VPS_IP:8002` |

If a domain is available, nginx can listen on port 80 and route by `server_name`, while each app still keeps its own Docker bind port.

Each app keeps its own:

- `/opt/<app-name>/` directory
- Docker Compose project
- nginx config in `/etc/nginx/conf.d/`
- PostgreSQL database name

## Useful commands

```bash
make install
make test
make docker-up
make docker-down
```
