# Test-runner image for the memcached practice code.
# Used by the `tester` service in docker-compose.yaml:
#   docker compose -f pp_memcached/docker-compose.yaml run --rm tester
# It runs the integration tests against the `memcached` container, then the demo script.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MEMCACHED_HOST=memcached \
    MEMCACHED_PORT=11211

WORKDIR /app

# Dependencies first so this layer is cached when only the code changes.
COPY req.txt .
RUN pip install -r req.txt pytest

COPY main.py test_memcached.py ./

# Non-root user: good habit even for throwaway images.
RUN useradd --create-home runner
USER runner

CMD ["sh", "-c", "pytest -v -p no:cacheprovider && echo && echo '##### demo #####' && python main.py"]
