# Agent Development & Testing Guide

To develop and test the agents, follow these standards:

## 1. Technologies & Versions
- **Go**: Version 1.25 is used for the server. Built with Gin and embedded UI.
- **Python**: Version 3.12+ (managed by `uv`). Used for Agent/Workflow logic.
- **Node**: Version 22+ (managed by `pnpm`). Used for the React frontend.

## 2. Package Management
We use modern package managers for speed and reliability:
- **UI**: Use `pnpm` for all frontend operations.
- **Python/Agent**: Use `uv` for lightning-fast backend dependency management and virtual environments.

## 3. Docker Standards
- **Base Images**: Use `public.ecr.aws/docker/library/` for official base images (Node, Go, Python).
- **Runtime**: Use `gcr.io/distroless/static-debian12` for compiled Go binaries to ensure security and minimal image size.
- **Multi-stage Builds**: UI is built with Node, then embedded into the Go binary using `go:embed`.

## 4. Restart the Application
Always restart the environment after making changes to the code or configuration:
```bash
docker compose up -d --build
```

## 5. Execute Commands
To run commands (like migrations, tests, or manual scripts), use `docker exec` to run them inside the worker container.

Example:
```bash
docker exec swe-ai-worker-1 uv run pytest tests/
```

## 6. Verify Progress
Monitor the worker logs to verify sandbox creation and agent progress:
```bash
docker compose logs -f worker
```
