# Generic VeriPay service image (Render / Railway / Docker).
#
# IMPORTANT: build with the REPOSITORY ROOT as the build context so the COPY
# paths below resolve:
#
#   docker build -f infra/deploy/veripay.Dockerfile --build-arg SERVICE=ingress .
#
# The per-service Dockerfiles under services/<name>/ cannot build standalone:
# every service depends on the local `veripay-common` package, which is not on
# PyPI, so this image installs it from source first.

ARG SERVICE=ingress

FROM python:3.12-slim

ARG SERVICE
ARG EXTRAS=
ENV SERVICE=${SERVICE}

WORKDIR /veripay

# Shared contract package (not on PyPI) must come from source.
COPY libs/veripay_common ./libs/veripay_common
RUN pip install --no-cache-dir -e ./libs/veripay_common

COPY services/${SERVICE} ./services/${SERVICE}
# Optional extras (e.g., EXTRAS=model for ML serving, EXTRAS=llm for the
# investigation agent) install heavier inference dependencies.
RUN if [ -n "$EXTRAS" ]; then \
        pip install --no-cache-dir -e "./services/${SERVICE}[${EXTRAS}]"; \
    else \
        pip install --no-cache-dir -e "./services/${SERVICE}"; \
    fi

# Render/Railway inject PORT; fall back to the documented per-service port.
ENV HTTP_PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "HTTP_PORT=${PORT:-8000} veripay-${SERVICE}"]
