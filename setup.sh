#!/usr/bin/env bash
# =============================================================================
# setup.sh — odtworzenie konfiguracji serwera basecamp na czystym Ubuntu 24.04
# Użycie: sudo bash setup.sh
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()     { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

[[ $EUID -ne 0 ]] && die "Uruchom jako root: sudo bash setup.sh"

# =============================================================================
# KONFIGURACJA — dostosuj przed uruchomieniem
# =============================================================================
SSH_PORT=2222
SERVICES_DIR="/home/services"
POSTGRES_USER="gresmo"
POSTGRES_DB="maindb"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"          # ustaw przez env lub zostaw puste (zostaniesz zapytany)
GIT_USER="gresmopl"
GIT_EMAIL="gresmo.tlen.pl@gmail.com"
DOMAINS_NPM="npm.gresmosoft.com"                   # domena panelu NPM
LE_EMAIL="gresmo.tlen.pl@gmail.com"

# =============================================================================
# 0. Podstawowe pakiety
# =============================================================================
info "Aktualizacja pakietów..."
apt-get update -q
apt-get upgrade -y -q
apt-get install -y -q curl wget git ufw fail2ban unattended-upgrades

# =============================================================================
# 1. SSH — zabezpieczenia
# =============================================================================
info "Konfiguracja SSH (port $SSH_PORT)..."

# Backup oryginału
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak."$(date +%Y%m%d)"

cat > /etc/ssh/sshd_config.d/99-hardening.conf << EOF
Port $SSH_PORT
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
MaxAuthTries 3
PubkeyAuthentication yes
X11Forwarding no
EOF

# Upewnij się że domyślny plik nie nadpisuje tych wartości
sed -i 's/^#\?Port .*//' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin .*//' /etc/ssh/sshd_config

systemctl restart ssh
info "SSH zrestartowany na porcie $SSH_PORT"
warn "Upewnij się że klucz SSH jest w /root/.ssh/authorized_keys przed wylogowaniem!"

# =============================================================================
# 2. UFW — firewall
# =============================================================================
info "Konfiguracja UFW..."

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow "$SSH_PORT"/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable

info "UFW aktywny. Reguły:"
ufw status verbose

# =============================================================================
# 3. Fail2ban
# =============================================================================
info "Konfiguracja fail2ban..."

cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
backend  = systemd

[sshd]
enabled  = true
port     = $SSH_PORT
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
bantime  = 1h
EOF

systemctl enable fail2ban
systemctl restart fail2ban
info "Fail2ban aktywny"

# =============================================================================
# 4. Git
# =============================================================================
info "Konfiguracja git..."
git config --global user.name "$GIT_USER"
git config --global user.email "$GIT_EMAIL"

# =============================================================================
# 5. Docker + Docker Compose
# =============================================================================
info "Instalacja Docker..."

if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    info "Docker zainstalowany: $(docker --version)"
else
    info "Docker już zainstalowany: $(docker --version)"
fi

# =============================================================================
# 6. Usługi: Nginx Proxy Manager + PostgreSQL
# =============================================================================
info "Tworzenie katalogu usług: $SERVICES_DIR"
mkdir -p "$SERVICES_DIR"

# Zapytaj o hasło postgres jeśli nie podano
if [[ -z "$POSTGRES_PASSWORD" ]]; then
    read -rsp "Podaj hasło dla PostgreSQL (user: $POSTGRES_USER): " POSTGRES_PASSWORD
    echo
    [[ -z "$POSTGRES_PASSWORD" ]] && die "Hasło nie może być puste"
fi

# .env dla docker compose
cat > "$SERVICES_DIR/.env" << EOF
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$POSTGRES_DB
EOF
chmod 600 "$SERVICES_DIR/.env"

# docker-compose.yml
cat > "$SERVICES_DIR/docker-compose.yml" << 'COMPOSE'
services:
  nginx-proxy-manager:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy-manager
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "81:81"
    volumes:
      - npm_data:/data
      - npm_letsencrypt:/etc/letsencrypt
    networks:
      - services_net

  postgres:
    image: postgres:16
    container_name: postgres
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - services_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  npm_data:
  npm_letsencrypt:
  postgres_data:

networks:
  services_net:
    driver: bridge
COMPOSE

info "Uruchamianie usług Docker..."
cd "$SERVICES_DIR"
docker compose pull
docker compose up -d

info "Czekam na gotowość usług (30s)..."
sleep 30

docker compose ps

# =============================================================================
# 7. Nginx Proxy Manager — konfiguracja przez API
# =============================================================================
info "Konfiguracja NPM przez API..."

NPM_URL="http://localhost:81"
NPM_EMAIL="$LE_EMAIL"

# Poczekaj aż NPM będzie gotowy
for i in $(seq 1 12); do
    if curl -sf "$NPM_URL/api/" &>/dev/null; then
        info "NPM gotowy"
        break
    fi
    warn "Czekam na NPM... ($i/12)"
    sleep 10
done

# Zaloguj się (pierwsze uruchomienie: admin@example.com / changeme)
TOKEN=$(curl -sf "$NPM_URL/api/tokens" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"identity\":\"admin@example.com\",\"secret\":\"changeme\"}" \
    | grep -o '"token":"[^"]*"' | cut -d'"' -f4 || true)

if [[ -z "$TOKEN" ]]; then
    warn "Nie można zalogować do NPM z domyślnymi danymi."
    warn "Otwórz http://IP_SERWERA:81 i skonfiguruj NPM ręcznie."
    warn "Następnie uruchom sekcję API ręcznie lub podaj token:"
    warn "  export NPM_TOKEN=<twój_token>"
else
    info "Zalogowano do NPM"

    # Zmień hasło i email admina
    read -rsp "Podaj nowe hasło dla NPM (email: $NPM_EMAIL): " NPM_PASS
    echo

    # Pobierz ID użytkownika
    USER_ID=$(curl -sf "$NPM_URL/api/users/me" \
        -H "Authorization: Bearer $TOKEN" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "1")

    # Aktualizuj profil
    curl -sf "$NPM_URL/api/users/$USER_ID" -X PUT \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Admin\",\"nickname\":\"Admin\",\"email\":\"$NPM_EMAIL\"}" >/dev/null

    # Zmień hasło
    curl -sf "$NPM_URL/api/users/$USER_ID/auth" -X PUT \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"password\",\"current\":\"changeme\",\"secret\":\"$NPM_PASS\"}" >/dev/null

    info "Dane logowania NPM zaktualizowane"
    info "Zaloguj się ponownie i skonfiguruj proxy hosty przez panel: http://IP_SERWERA:81"
    info "Lub użyj API (po zalogowaniu nowym hasłem):"
    cat << 'APIHELP'

# Utwórz certyfikat LE:
TOKEN=$(curl -s http://localhost:81/api/tokens -X POST \
  -H "Content-Type: application/json" \
  -d '{"identity":"EMAIL","secret":"HASLO"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

curl -s http://localhost:81/api/nginx/certificates -X POST \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"provider":"letsencrypt","domain_names":["DOMENA"],"meta":{"dns_challenge":false}}'

# Utwórz proxy host:
curl -s http://localhost:81/api/nginx/proxy-hosts -X POST \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"domain_names":["DOMENA"],"forward_scheme":"http","forward_host":"localhost",
       "forward_port":PORT,"certificate_id":CERT_ID,"ssl_forced":true,"http2_support":true,
       "block_exploits":true,"allow_websocket_upgrade":true,"hsts_enabled":true,
       "hsts_subdomains":false,"access_list_id":0,"advanced_config":"","locations":[],
       "meta":{"letsencrypt_agree":false,"dns_challenge":false}}'
APIHELP
fi

# =============================================================================
# 8. SSH klucz dla GitHub
# =============================================================================
info "Generowanie klucza SSH dla GitHub..."

if [[ ! -f /root/.ssh/id_ed25519_github ]]; then
    ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f /root/.ssh/id_ed25519_github -N ""

    # SSH config
    if ! grep -q "github.com" /root/.ssh/config 2>/dev/null; then
        cat >> /root/.ssh/config << EOF

Host github.com
  HostName github.com
  User git
  IdentityFile /root/.ssh/id_ed25519_github
  AddKeysToAgent yes
EOF
        chmod 600 /root/.ssh/config
    fi

    echo ""
    info "Klucz publiczny GitHub (dodaj na https://github.com/settings/ssh/new):"
    echo "---"
    cat /root/.ssh/id_ed25519_github.pub
    echo "---"
else
    info "Klucz GitHub już istnieje: /root/.ssh/id_ed25519_github"
fi

# =============================================================================
# Podsumowanie
# =============================================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Konfiguracja zakończona!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  SSH port:     $SSH_PORT"
echo "  UFW:          aktywny (porty: $SSH_PORT, 80, 443)"
echo "  Fail2ban:     aktywny"
echo "  Docker:       $(docker --version | cut -d' ' -f3 | tr -d ',')"
echo "  PostgreSQL:   $POSTGRES_USER@localhost:5432/$POSTGRES_DB"
echo "  NPM panel:    http://$(curl -sf ifconfig.me 2>/dev/null || echo 'IP_SERWERA'):81"
echo ""
echo -e "${YELLOW}  PAMIĘTAJ:${NC}"
echo "  1. Dodaj klucz SSH GitHub: https://github.com/settings/ssh/new"
echo "  2. Plik .env z hasłem Postgres: $SERVICES_DIR/.env"
echo "  3. Upewnij się że /root/.ssh/authorized_keys ma Twój klucz!"
echo "  4. Skonfiguruj domeny DNS (A record → IP serwera)"
echo ""
