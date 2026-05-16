# Docker Operations Skill

## Purpose
Manage Docker containers, images, networks, and volumes for OCE deployment and development environments.

## When to Use
- Setting up OCE backend in a container
- Running isolated test environments
- Deploying SRRA-OPH components
- Managing development dependencies (Redis, PostgreSQL, etc.)

## Prerequisites
```bash
# Check if Docker is installed
docker --version

# If not installed on Windows:
# Install Docker Desktop from https://docs.docker.com/desktop/install/windows-install/
# Or via winget:
winget install Docker.DockerDesktop
```

## Core Operations

### Container Management
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Start a container
docker start <container_name>

# Stop a container
docker stop <container_name>

# Restart a container
docker restart <container_name>

# Remove a container
docker rm <container_name>

# View container logs
docker logs <container_name>
docker logs -f <container_name>  # Follow mode

# Execute command in running container
docker exec -it <container_name> /bin/sh

# Inspect container details
docker inspect <container_name>
```

### Image Management
```bash
# List images
docker images

# Pull an image
docker pull <image>:<tag>

# Build an image
docker build -t <name>:<tag> .

# Remove an image
docker rmi <image_id>

# Remove unused images
docker image prune -f
```

### Docker Compose (Multi-Container)
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Rebuild and restart
docker compose up -d --build

# Scale a service
docker compose up -d --scale <service>=<count>
```

### Volume Management
```bash
# List volumes
docker volume ls

# Create a volume
docker volume create <name>

# Remove a volume
docker volume rm <name>

# Remove unused volumes
docker volume prune -f
```

### Network Management
```bash
# List networks
docker network ls

# Create a network
docker network create <name>

# Inspect network
docker network inspect <name>
```

## OCE Docker Setup

### Dockerfile for OCE Backend
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY oce/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY oce/backend/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for OCE Stack
```yaml
version: '3.8'

services:
  oce-backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  oce-frontend:
    build:
      context: ./oce/frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - oce-backend
    restart: unless-stopped

volumes:
  redis_data:
```

### Build and Run OCE
```bash
# Build all services
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f oce-backend

# Stop everything
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

## Windows-Specific Notes

- Docker Desktop is required for Windows (not Docker Engine directly)
- Use WSL2 backend for better performance
- File sharing: Ensure the workspace directory is shared in Docker Desktop settings
- Line endings: Use `.gitattributes` to handle LF/CRLF
- Volume mounts: Use forward slashes in paths even on Windows

## Troubleshooting

```bash
# Check Docker Desktop is running
docker info

# Check container resource usage
docker stats

# Clean up everything (nuclear option)
docker system prune -a --volumes

# Check port conflicts
netstat -ano | findstr :8000
```

## Security
- Never run containers as root in production
- Use `.dockerignore` to exclude secrets
- Don't bake API keys into images — use env vars
- Scan images: `docker scout cves <image>`
