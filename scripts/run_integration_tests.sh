#!/usr/bin/env bash
# Helper script to start the stack, wait for healthchecks, run integration tests, and collect logs
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

command_exists() { command -v "$1" >/dev/null 2>&1; }

echo -e "${BLUE}Run integration tests helper${NC}"

if ! command_exists docker; then
  echo -e "${RED}docker CLI not found. Please install Docker and try again.${NC}"
  exit 1
fi

if ! command_exists pytest; then
  echo -e "${YELLOW}pytest not found. Installing test requirements...${NC}"
  pip install -r tests/requirements-test.txt
fi

echo -e "${BLUE}Starting docker compose stack...${NC}"
docker compose up --build -d

echo -e "${BLUE}Waiting for services to become healthy...${NC}"

# Services and endpoints to poll (path and port)
declare -A SERVICES
SERVICES[task]='http://localhost:8080/tasks'
SERVICES[project]='http://localhost:8082/projects'
SERVICES[user]='http://localhost:8081/users'
SERVICES[auth]='http://localhost:8086/health'
SERVICES[notification]='http://localhost:8084/notifications?user_id=test'
SERVICES[report]='http://localhost:8090/health'

wait_for_url() {
  local url=$1
  local timeout=${2:-60}
  local sleep_interval=2
  local elapsed=0
  while true; do
    if curl -s -f -m 5 "$url" >/dev/null 2>&1; then
      return 0
    fi
    if [ "$elapsed" -ge "$timeout" ]; then
      return 1
    fi
    sleep $sleep_interval
    elapsed=$((elapsed + sleep_interval))
  done
}

failed=0
for name in "${!SERVICES[@]}"; do
  url=${SERVICES[$name]}
  echo -n -e "Checking $name at $url ... "
  if wait_for_url "$url" 120; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${RED}FAILED to reach $url after timeout${NC}"
    failed=1
  fi
done

if [ "$failed" -ne 0 ]; then
  echo -e "${RED}One or more services failed healthchecks. Dumping docker compose ps and recent logs.${NC}"
  mkdir -p ./.logs
  docker compose ps > ./.logs/compose_ps.txt || true
  docker compose logs --no-color --tail=400 > ./.logs/compose_logs_pretest.txt || true
  echo -e "Logs written to ./.logs/"
  exit 2
fi

echo -e "${GREEN}All services healthy. Running tests...${NC}"

# Support modes: all (default), integration, unit
MODE=${1:-all}
case "$MODE" in
  integration)
    echo -e "${BLUE}Running integration tests only...${NC}"
    TEST_CMD=(pytest tests/ -v -k "Integration")
    ;;
  unit)
    echo -e "${BLUE}Running unit tests only...${NC}"
    TEST_CMD=(pytest tests/ -v -k "not Integration")
    ;;
  all)
    echo -e "${BLUE}Running all tests...${NC}"
    TEST_CMD=(pytest tests/ -v)
    ;;
  *)
    echo -e "${YELLOW}Unknown mode '$MODE', defaulting to all tests.${NC}"
    TEST_CMD=(pytest tests/ -v)
    ;;
esac

"${TEST_CMD[@]}" || test_exit_code=$?

test_exit_code=${test_exit_code:-0}

if [ "$test_exit_code" -ne 0 ]; then
  echo -e "${RED}Integration tests failed (exit $test_exit_code). Collecting logs...${NC}"
  mkdir -p ./.logs
  ts=$(date +%Y%m%d_%H%M%S)
  out=./.logs/integration_logs_${ts}.txt
  echo "Docker compose ps:" > "$out"
  docker compose ps >> "$out" 2>&1 || true
  echo -e "\n==== Docker compose logs ====" >> "$out"
  docker compose logs --no-color --tail=1000 >> "$out" 2>&1 || true
  echo -e "Logs collected: $out"
  exit "$test_exit_code"
else
  echo -e "${GREEN}Integration tests passed.${NC}"
  exit 0
fi
