package logger

import (
	"log/slog"
	"os"
)

func New(serviceName, env string) *slog.Logger {
	level := slog.LevelInfo
	if env == "development" {
		level = slog.LevelDebug
	}
	return slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: level,
	})).With(
		slog.String("service", serviceName),
		slog.String("env", env),
	)
}
