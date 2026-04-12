# Konfiguracja serwera `basecamp` — 12 kwietnia 2026

Dokumentacja kompletnej konfiguracji serwera VPS przeprowadzonej 12.04.2026.  
System: **Ubuntu 24.04.4 LTS** · Kernel: 6.8.0-107-generic · Hostname: `basecamp`

---

## 1. Zabezpieczenia SSH

### Zmiany w `/etc/ssh/sshd_config`

| Parametr | Wartość | Opis |
|---|---|---|
| `Port` | `2222` | Niestandardowy port (ukrycie przed skanerami) |
| `PermitRootLogin` | `prohibit-password` | Root tylko przez klucz SSH |
| `PasswordAuthentication` | `no` | Wyłączone logowanie hasłem |
| `KbdInteractiveAuthentication` | `no` | Wyłączone logowanie interaktywne |
| `MaxAuthTries` | `3` | Maksymalnie 3 próby auth per połączenie |
| `PubkeyAuthentication` | `yes` | Uwierzytelnianie kluczem publicznym |

### Klucz SSH root

Dodano klucz publiczny do `/root/.ssh/authorized_keys`:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIOMLuYLeP5wk/byEgbjqVGGvm/kTr0TsabOBW3QzgCO
```

### Klucz SSH dla GitHub

Wygenerowany klucz ED25519 do autoryzacji z GitHub (`git@github.com:gresmopl`):
- Prywatny: `/root/.ssh/id_ed25519_github`
- Publiczny: `/root/.ssh/id_ed25519_github.pub`
- Dodany do GitHub: https://github.com/settings/keys

`~/.ssh/config`:
```
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github
  AddKeysToAgent yes
```

---

## 2. Firewall (UFW)

Stan: **aktywny**  
Domyślna polityka: `deny incoming`, `allow outgoing`

| Port | Protokół | Akcja | Opis |
|---|---|---|---|
| 2222 | tcp | ALLOW | SSH |
| 80 | tcp | ALLOW | HTTP |
| 443 | tcp | ALLOW | HTTPS |

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw enable
```

---

## 3. Fail2ban

Zainstalowany i aktywny. Chroni port SSH (2222) przed atakami brute-force.

Konfiguracja `/etc/fail2ban/jail.local`:
```ini
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
backend  = systemd

[sshd]
enabled  = true
port     = 2222
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
bantime  = 1h
```

Aktywne więzienie: `sshd`

---

## 4. Git

```bash
git config --global user.name "gresmopl"
git config --global user.email "gresmo.tlen.pl@gmail.com"
```

---

## 5. Docker

- **Docker**: 29.4.0
- **Docker Compose**: v5.1.2
- Zainstalowany ze źródeł oficjalnych (docker.com)

Usługi zarządzane przez Compose w `/home/services/`.

### `/home/services/docker-compose.yml`

```yaml
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
```

### `/home/services/.env`

```env
POSTGRES_USER=gresmo
POSTGRES_PASSWORD=<hasło>
POSTGRES_DB=maindb
```

> **Uwaga:** Plik `.env` nie jest wersjonowany. Przechowuj hasło w menedżerze haseł.

---

## 6. Nginx Proxy Manager (NPM)

- **Obraz**: `jc21/nginx-proxy-manager:latest` (v2.14.0)
- **Panel admina**: https://npm.gresmosoft.com (port 81 lokalnie)
- **Konto**: `gresmo.tlen.pl@gmail.com`
- **Dane**: wolumin Docker `services_npm_data` → `/data`
- **Certyfikaty**: wolumin Docker `services_npm_letsencrypt` → `/etc/letsencrypt`

### Skonfigurowane proxy hosty

| Domena | Cel | Certyfikat | SSL wymuś | HTTP/2 | HSTS |
|---|---|---|---|---|---|
| `npm.gresmosoft.com` | localhost:81 | Let's Encrypt | tak | tak | tak |
| `gresmosoft.com` | localhost:81 | Let's Encrypt | tak | tak | tak |
| `kumai.dev` | localhost:81 | Let's Encrypt | tak | tak | tak |

### Certyfikaty Let's Encrypt

| ID | Domena | Wystawiony | Wygasa |
|---|---|---|---|
| 1 | npm.gresmosoft.com | 12.04.2026 | 11.07.2026 |
| 2 | gresmosoft.com | 12.04.2026 | 11.07.2026 |
| 3 | kumai.dev | 12.04.2026 | 11.07.2026 |

Email rejestracyjny LE: `gresmo.tlen.pl@gmail.com`  
NPM automatycznie odnawia certyfikaty przed wygaśnięciem.

---

## 7. PostgreSQL

- **Obraz**: `postgres:16`
- **Port**: `5432` (dostępny z zewnątrz — rozważ ograniczenie UFW)
- **Użytkownik**: `gresmo`
- **Baza**: `maindb`
- **Dane**: wolumin Docker `services_postgres_data` → `/var/lib/postgresql/data`

Połączenie lokalne:
```bash
docker exec -it postgres psql -U gresmo -d maindb
```

---

## 8. Swap

- **Plik**: `/swapfile` — 2 GiB
- **Trwały**: wpis w `/etc/fstab` (`/swapfile none swap sw 0 0`)
- **Swappiness**: `vm.swappiness=10` (ustawiony w `/etc/sysctl.conf`)

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl vm.swappiness=10
```

> Swap aktywowany 12.04.2026. Swappiness=10 oznacza że system sięga po swap dopiero przy ~10% wolnego RAM.

---

## 9. Struktura katalogów

```
/home/services/
├── docker-compose.yml   # definicja usług
└── .env                 # zmienne środowiskowe (nie wersjonować!)

/root/.ssh/
├── authorized_keys      # klucze do logowania na serwer
├── config               # konfiguracja klienta SSH (GitHub)
├── id_ed25519_github    # klucz prywatny GitHub
└── id_ed25519_github.pub

/home/sandbox-claude/    # to repozytorium (git@github.com:gresmopl/sandbox-claude.git)
```

---

## 10. Szybka diagnostyka

```bash
# Status usług
docker ps
ufw status verbose
fail2ban-client status sshd
systemctl status ssh

# Logi
journalctl -u ssh -n 50
docker logs nginx-proxy-manager --tail 50
docker logs postgres --tail 50

# Restart wszystkiego
cd /home/services && docker compose restart
```
