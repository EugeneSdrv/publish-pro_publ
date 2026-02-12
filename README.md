# Publish-pro project

This is a service for posting messages and discussing them

### Operating System

- __Linux:__ (Prefered) Ubuntu 22.04, Debian Latest
- __MacOS:__ 10.14 or later
- __Windows:__ (10, 11 + WSL2) Use WSL for development

### Tools

- __[Docker](https://docs.docker.com/engine/install/)__ latest

- __[Python](https://www.python.org/downloads/)__ >=3.11
- __[UV](https://docs.astral.sh/uv/getting-started/installation/)__ latest
- __[Ruff](https://docs.astral.sh/ruff/installation/)__ latest
- __[pre-commit](https://pre-commit.com/#install)__ latest

### Install tools

#### On macOS and Linux

```sh
# Install Docker
curl -sSL https://get.docker.com/ | sh
# Add the current user to the docker group
sudo usermod -aG docker $USER
# Restart the Docker daemon
sudo systemctl restart docker
```

```sh
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Ruff
curl -LsSf https://astral.sh/ruff/install.sh | sh

# Reload bash
exec bash

# Install python
uv python install 3.12

# Install pre-commit user wide
uv tool install pre-commit
```

#### On Windows

```ps1
# UV
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Ruff
powershell -c "irm https://astral.sh/ruff/install.ps1 | iex"

# Install python
uv python install 3.12

# Install pre-commit user wide
uv tool install pre-commit

# Set up the git hook scripts
pre-commit install

# Install deps
uv sync
```

### Fast start (Only for WSL, linux, macOs)

```sh
# Clone the project to the desired directory with the command 
git clone <project URL> <path to folder>

# Make sure that you are in the main branch
git switch main

cp .env.example .env
# Copy generated key by following command to the .env using the SECRET_KEY field
head -c 64 /dev/urandom | base64

docker compose -f docker-compose.dev.yml up -d
```

## API Documentation

After the restructuring, all API endpoints now follow the `/api/v1` base path.

You can access the interactive API documentation at:

- __Swagger UI__: `/api/v1/docs`
- __OpenAPI Schema__: `/openapi.json`

Example endpoints:

- `GET /api/v1/posts/get_posts`
- `POST /api/v1/auth/login`
