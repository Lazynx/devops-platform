package config

import "fmt"

type Config struct {
	HTTPPort int `envconfig:"HTTP_PORT" default:"8005"`

	PostgresHost     string `envconfig:"POSTGRES_DEPLOYMENT_HOST" default:"localhost"`
	PostgresPort     int    `envconfig:"POSTGRES_DEPLOYMENT_PORT" default:"5432"`
	PostgresUser     string `envconfig:"POSTGRES_DEPLOYMENT_LOGIN" default:"postgres"`
	PostgresPassword string `envconfig:"POSTGRES_DEPLOYMENT_PASSWORD" default:"postgres"`
	PostgresDB       string `envconfig:"POSTGRES_DEPLOYMENT_DATABASE" default:"deployment_db"`

	KafkaBrokers  string `envconfig:"KAFKA_BOOTSTRAP_SERVERS" default:"localhost:9094"`
	KafkaUsername string `envconfig:"KAFKA_USERNAME" default:"devops_platform"`
	KafkaPassword string `envconfig:"KAFKA_PASSWORD" default:"platform-secret"`

	NomadURL string `envconfig:"NOMAD_URL" default:"http://localhost:4646"`

	RegistryURL      string `envconfig:"NEXUS_REGISTRY_URL" default:"localhost:8082"`
	RegistryRepo     string `envconfig:"NEXUS_DOCKER_REPOSITORY" default:"docker-hosted"`
	RegistryUser     string `envconfig:"NEXUS_USER" default:"admin"`
	RegistryPassword string `envconfig:"NEXUS_PASSWORD" default:"admin123"`

	AuthServiceURL    string `envconfig:"AUTH_SERVICE_URL" default:"http://localhost:8000"`
	SecretsServiceURL string `envconfig:"SECRETS_SERVICE_URL" default:"http://localhost:8003"`

	Env string `envconfig:"ENV" default:"development"`
}

func (c *Config) PostgresDSN() string {
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%d/%s?sslmode=disable",
		c.PostgresUser, c.PostgresPassword,
		c.PostgresHost, c.PostgresPort, c.PostgresDB,
	)
}
