FROM golang:1.23-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /deployment-service ./cmd/api

# ── Runtime image ─────────────────────────────────────────────────────────────
FROM gcr.io/distroless/static-debian12

COPY --from=builder /deployment-service /deployment-service

EXPOSE 8005

ENTRYPOINT ["/deployment-service"]
