# Stage 1: Build the UI
FROM public.ecr.aws/docker/library/node:22-alpine AS ui-builder
WORKDIR /ui
RUN npm install -g pnpm
COPY ui/package.json ui/pnpm-lock.yaml* ./
RUN pnpm install
COPY ui/ ./
RUN pnpm build

# Stage 2: Build the Go server
FROM public.ecr.aws/docker/library/golang:1.25-alpine AS go-builder
WORKDIR /app
COPY server/go.mod server/go.sum ./
RUN go mod download
COPY server/ ./
# Copy the built UI into the directory expected by go:embed (ui/dist relative to main.go)
COPY --from=ui-builder /ui/dist ./cmd/swe-ai/ui/dist
RUN CGO_ENABLED=0 GOOS=linux go build -o main ./cmd/swe-ai/main.go

# Stage 3: Final runtime
FROM gcr.io/distroless/static-debian12
WORKDIR /
COPY --from=go-builder /app/main /main

EXPOSE 8000
CMD ["/main", "server"]
