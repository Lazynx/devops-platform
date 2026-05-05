package metrics

import "github.com/prometheus/client_golang/prometheus"

var (
	DeploymentTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "deployments_total",
			Help: "Total number of deployments by final status and environment.",
		},
		[]string{"status", "environment"},
	)

	DeploymentDurationSeconds = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "deployment_duration_seconds",
			Help:    "Time spent in each deployment phase.",
			Buckets: []float64{10, 30, 60, 120, 300, 600, 900},
		},
		[]string{"phase"},
	)

	ActiveDeployments = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "active_deployments",
			Help: "Number of currently running deployments.",
		},
		[]string{"environment"},
	)
)

func Register() {
	prometheus.MustRegister(
		DeploymentTotal,
		DeploymentDurationSeconds,
		ActiveDeployments,
	)
}
