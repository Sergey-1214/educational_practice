#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_PREFIX="${API_PREFIX:-/api/v1}"
EMAIL="${INIT_USER_EMAIL:-devops-demo@example.com}"
PASSWORD="${INIT_USER_PASSWORD:-devops-demo-password}"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-.tmp/init-docs}"

PDF_URLS=(
  "https://arxiv.org/pdf/1706.03762.pdf"
  "https://arxiv.org/pdf/1409.0473.pdf"
  "https://arxiv.org/pdf/1512.03385.pdf"
  "https://arxiv.org/pdf/1606.03798.pdf"
  "https://arxiv.org/pdf/1312.6114.pdf"
  "https://arxiv.org/pdf/1412.6980.pdf"
  "https://arxiv.org/pdf/1406.2661.pdf"
  "https://arxiv.org/pdf/1506.01497.pdf"
  "https://arxiv.org/pdf/1810.04805.pdf"
  "https://arxiv.org/pdf/2005.14165.pdf"
)

wait_for_backend() {
  echo "Waiting for backend at ${BASE_URL}/health ..."
  for _ in $(seq 1 30); do
    if curl -fsS "${BASE_URL}/health" >/dev/null; then
      echo "Backend is healthy."
      return 0
    fi
    sleep 2
  done

  echo "Backend did not become healthy in time." >&2
  return 1
}

register_user() {
  echo "Registering demo user ${EMAIL} ..."
  local payload
  payload=$(printf '{"email":"%s","password":"%s"}' "${EMAIL}" "${PASSWORD}")

  local status_code
  status_code=$(curl -sS -o /tmp/init-register-response.json -w "%{http_code}" \
    -X POST "${BASE_URL}${API_PREFIX}/auth/register" \
    -H "Content-Type: application/json" \
    -d "${payload}")

  if [[ "${status_code}" != "201" && "${status_code}" != "409" ]]; then
    echo "Registration failed with status ${status_code}." >&2
    cat /tmp/init-register-response.json >&2
    return 1
  fi
}

login_user() {
  echo "Logging in demo user ..."
  local payload
  payload=$(printf '{"email":"%s","password":"%s"}' "${EMAIL}" "${PASSWORD}")

  curl -sS -o /tmp/init-login-response.json \
    -X POST "${BASE_URL}${API_PREFIX}/auth/login" \
    -H "Content-Type: application/json" \
    -d "${payload}"

  ACCESS_TOKEN=$(
    python -c "import json; print(json.load(open('/tmp/init-login-response.json', encoding='utf-8'))['access_token'])"
  )
}

download_pdfs() {
  mkdir -p "${DOWNLOAD_DIR}"

  echo "Downloading test PDF files ..."
  local index=1
  for url in "${PDF_URLS[@]}"; do
    curl -LfsS "${url}" -o "${DOWNLOAD_DIR}/lecture-${index}.pdf"
    index=$((index + 1))
  done
}

upload_pdfs() {
  echo "Uploading PDF files through the API ..."
  for file in "${DOWNLOAD_DIR}"/*.pdf; do
    echo "Uploading ${file} ..."
    curl -sS \
      -X POST "${BASE_URL}${API_PREFIX}/documents/upload" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -F "file=@${file};type=application/pdf" \
      >/dev/null
  done
}

main() {
  wait_for_backend
  register_user
  login_user
  download_pdfs
  upload_pdfs
  echo "Initialization complete."
}

main "$@"
