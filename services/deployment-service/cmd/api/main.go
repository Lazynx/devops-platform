package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"deployment-service/internal/app/usecase/command"
	"deployment-service/internal/app/usecase/query"
	"deployment-service/internal/config"
	"deployment-service/internal/infra/authclient"
	infraKafka "deployment-service/internal/infra/kafka"
	"deployment-service/internal/infra/nomad"
	"deployment-service/internal/infra/postgres"
	"deployment-service/internal/infra/secretsclient"
	"deployment-service/internal/metrics"
	httpServer "deployment-service/internal/transport/http"
	"deployment-service/internal/transport/http/handler"
	transportKafka "deployment-service/internal/transport/kafka"
	"deployment-service/pkg/logger"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/kelseyhightower/envconfig"
	"github.com/twmb/franz-go/pkg/kgo"
	"github.com/twmb/franz-go/pkg/sasl/plain"
	"golang.org/x/sync/errgroup"
)

func main() {
	var cfg config.Config
	if err := envconfig.Process("", &cfg); err != nil {
		slog.Error("failed to load config", "err", err)
		os.Exit(1)
	}

	log := logger.New("deployment-service", cfg.Env)
	slog.SetDefault(log)

	metrics.Register()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	pool, err := pgxpool.New(ctx, cfg.PostgresDSN())
	if err != nil {
		slog.Error("failed to connect to postgres", "err", err)
		os.Exit(1)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		slog.Error("postgres ping failed", "err", err)
		os.Exit(1)
	}

	producer, err := kgo.NewClient(
		kgo.SeedBrokers(cfg.KafkaBrokers),
		kgo.SASL(plain.Auth{User: cfg.KafkaUsername, Pass: cfg.KafkaPassword}.AsMechanism()),
	)
	if err != nil {
		slog.Error("failed to create kafka producer", "err", err)
		os.Exit(1)
	}
	defer producer.Close()

	consumer, err := kgo.NewClient(
		kgo.SeedBrokers(cfg.KafkaBrokers),
		kgo.SASL(plain.Auth{User: cfg.KafkaUsername, Pass: cfg.KafkaPassword}.AsMechanism()),
		kgo.ConsumerGroup("deployment-service-consumers"),
		kgo.ConsumeTopics("secrets.bulk_created", "project.deleted"),
		kgo.DisableAutoCommit(),
	)
	if err != nil {
		slog.Error("failed to create kafka consumer", "err", err)
		os.Exit(1)
	}
	defer consumer.Close()

	deployRepo := postgres.NewDeploymentRepo(pool)
	configRepo := postgres.NewConfigRepo(pool)
	nomadClient := nomad.NewClient(cfg.NomadURL)
	publisher := infraKafka.NewPublisher(producer)
	authClient := authclient.NewClient(cfg.AuthServiceURL)
	secretsClient := secretsclient.NewClient(cfg.SecretsServiceURL)
	jobBuilder := nomad.NewJobBuilder()

	registry := command.RegistryConfig{
		URL:      cfg.RegistryURL,
		Repo:     cfg.RegistryRepo,
		User:     cfg.RegistryUser,
		Password: cfg.RegistryPassword,
	}

	deploySvc := command.NewDeployCommand(
		deployRepo, configRepo, nomadClient, publisher,
		jobBuilder, jobBuilder, registry, ctx,
	)
	createConfigSvc := command.NewCreateConfigCommand(configRepo, authClient)
	stopSvc := command.NewStopCommand(deployRepo, nomadClient)
	retrySvc := command.NewRetryCommand(
		deployRepo, configRepo, nomadClient, publisher, authClient,
		secretsClient, jobBuilder, jobBuilder, registry, ctx,
	)
	deleteProjectSvc := command.NewDeleteProjectCommand(deployRepo, configRepo, nomadClient)

	getDeploymentSvc := query.NewGetDeployment(deployRepo)
	listDeploymentsSvc := query.NewListDeployments(deployRepo)
	getLogsSvc := query.NewGetLogs(deployRepo, nomadClient)

	deploymentHandler := handler.NewDeployment(
		deploySvc, createConfigSvc, stopSvc, retrySvc,
		getDeploymentSvc, listDeploymentsSvc, getLogsSvc,
	)
	srv := httpServer.NewServer(cfg.HTTPPort, deploymentHandler)
	kafkaConsumer := transportKafka.NewConsumer(consumer, producer, deploySvc, deleteProjectSvc)

	g, gCtx := errgroup.WithContext(ctx)
	g.Go(func() error { return srv.Run(gCtx) })
	g.Go(func() error { return kafkaConsumer.Run(gCtx) })

	slog.Info("deployment-service started", "http_port", cfg.HTTPPort)

	serveErr := g.Wait()
	deploySvc.Wait()
	retrySvc.Wait()
	if serveErr != nil {
		slog.Error("service stopped with error", "err", serveErr)
		os.Exit(1)
	}
}
