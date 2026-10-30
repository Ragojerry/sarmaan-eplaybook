#!/bin/bash
# Runs on the EC2 host (via SSM Run Command) to install or update the stack.
#
#   bootstrap.sh <s3-bucket> <cors-origins-json>
#
# 1. installs Docker + the Compose plugin (first run only)
# 2. downloads and unpacks the app bundle from s3://<bucket>/bundle.tar.gz
# 3. generates /opt/sarmaan/.env.prod with random secrets (first run only)
# 4. restores s3://<bucket>/db.dump into an empty database (first run only)
# 5. builds and (re)starts the containers
set -euo pipefail

BUCKET="$1"
CORS_ORIGINS="$2"
APP=/opt/sarmaan
COMPOSE_VERSION=v2.32.4

if ! command -v docker >/dev/null; then
  dnf install -y docker
  systemctl enable --now docker
fi
if ! docker compose version >/dev/null 2>&1; then
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

mkdir -p "$APP" "$APP/restore"
aws s3 cp "s3://${BUCKET}/bundle.tar.gz" /tmp/bundle.tar.gz
tar -xzf /tmp/bundle.tar.gz -C "$APP"
rm -f /tmp/bundle.tar.gz

if [ ! -f "$APP/.env.prod" ]; then
  umask 077
  cat > "$APP/.env.prod" <<EOF
POSTGRES_PASSWORD=$(openssl rand -hex 24)
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=$(openssl rand -hex 48)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=../content/media
RELEASE_STORAGE_PATH=../content/releases
AI_ONLINE_PROVIDER=none
CORS_ALLOW_ORIGINS=[]
EOF
fi
# CORS can change between runs (e.g. once the admin URL is known).
sed -i "s|^CORS_ALLOW_ORIGINS=.*|CORS_ALLOW_ORIGINS=${CORS_ORIGINS}|" "$APP/.env.prod"

cd "$APP/deploy/aws"
COMPOSE=(docker compose --env-file "$APP/.env.prod" -p sarmaan -f docker-compose.prod.yml)

"${COMPOSE[@]}" up -d db
until "${COMPOSE[@]}" exec -T db pg_isready -U sarmaan -d sarmaan_eplaybook >/dev/null 2>&1; do sleep 2; done

# Restore only into an empty database, so re-running never overwrites live data.
TABLES=$("${COMPOSE[@]}" exec -T db psql -U sarmaan -d sarmaan_eplaybook -Atc \
  "select count(*) from information_schema.tables where table_schema='public'")
if [ "$TABLES" = "0" ] && aws s3 cp "s3://${BUCKET}/db.dump" "$APP/restore/db.dump" 2>/dev/null; then
  # pg_restore exits non-zero on harmless warnings (e.g. COMMENT ON EXTENSION),
  # so judge success by what landed rather than by its exit code.
  "${COMPOSE[@]}" exec -T db pg_restore -U sarmaan -d sarmaan_eplaybook --no-owner --no-privileges /restore/db.dump \
    || echo "pg_restore reported warnings (see above)"
  rm -f "$APP/restore/db.dump"
  "${COMPOSE[@]}" exec -T db psql -U sarmaan -d sarmaan_eplaybook -Atc \
    "select 'restored: ' || (select count(*) from modules) || ' modules, ' || (select count(*) from users) || ' users'"
fi

"${COMPOSE[@]}" up -d --build backend
for i in $(seq 1 30); do
  if curl -fsS http://localhost/ >/dev/null; then echo "backend healthy"; exit 0; fi
  sleep 3
done
"${COMPOSE[@]}" logs --tail 80 backend
exit 1
