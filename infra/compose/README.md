# Local Infrastructure

The development dependency stack is defined by
`docker-compose.dev.yml` and includes Kafka, Redis, PostgreSQL, and WireMock.
It validates without starting containers:

```bash
docker compose -f infra/compose/docker-compose.dev.yml config --quiet
```

`services.yml` contains the backend service definitions and can be validated
independently:

```bash
docker compose -f infra/compose/services.yml config --quiet
```

The service definitions use the repository root `services/` directory as their
build context and `infra/compose/.env` for local-only development settings.
Starting either stack is intentionally separate from unit-test CI; production
credentials, populated databases, and live provider integrations are not
required for these configuration checks.
