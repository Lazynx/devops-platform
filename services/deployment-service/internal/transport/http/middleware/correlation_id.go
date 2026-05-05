package middleware

import (
	"context"
	"net/http"

	"github.com/google/uuid"
)

type contextKey string

const correlationIDKey contextKey = "correlation_id"

func CorrelationID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		cid := r.Header.Get("X-Correlation-ID")
		if cid == "" {
			cid = uuid.New().String()
		}
		w.Header().Set("X-Correlation-ID", cid)
		next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), correlationIDKey, cid)))
	})
}

func FromContext(ctx context.Context) string {
	cid, _ := ctx.Value(correlationIDKey).(string)
	return cid
}
