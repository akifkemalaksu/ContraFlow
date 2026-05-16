# ContraFlow

FastAPI tabanlı, Domain-Driven Design (DDD) mimarisiyle inşa edilmiş Python mikroservisi.

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Framework | FastAPI + Uvicorn |
| Veritabanı | PostgreSQL + SQLAlchemy async (asyncpg) |
| Migration | Alembic |
| Cache | Redis + fastapi-cache2 |
| Task Queue | Celery + Redis |
| Auth | JWT (Access + Refresh) & API Key |
| Config | pydantic-settings |
| Test | pytest + httpx (smoke) |
| Exchange | Hyperliquid (hyperliquid-python-sdk) |

## Mimari

```
src/
├── domain/           # Saf iş mantığı — dışa bağımlılık yok
│   ├── entities/         # User, Role, Permission, Account, Asset, Order, Fill, CopyStrategy, CrossAssetTrigger
│   ├── value_objects/    # APIKey
│   ├── events/
│   ├── services/         # Soyut servis interface'leri (IExchangeClient, IExchangeClientFactory, ICacheService, ICacheServiceFactory)
│   └── repositories/     # Soyut repository interface'leri (ABC)
│
├── application/      # Use case'ler ve orkestrasyon
│   ├── use_cases/        # RegisterUser, LoginUser, CreateAPIKey, RevokeAPIKey
│   ├── dtos/
│   └── services/
│
├── infrastructure/   # Teknik implementasyonlar
│   ├── database/
│   │   ├── models/       # SQLAlchemy ORM modelleri
│   │   ├── repositories/ # Concrete repo impl.
│   │   └── session.py    # Async engine + session factory
│   ├── cache/
│   │   ├── redis_cache.py    # RedisCacheService (ICacheService impl.)
│   │   └── factory.py        # RedisCacheServiceFactory
│   ├── hyperliquid/      # Hyperliquid SDK entegrasyonu
│   │   ├── client.py             # Info client (market data, WS)
│   │   ├── exchange_client.py    # Exchange client (order imzalama, IExchangeClient impl.)
│   │   ├── exchange_client_factory.py  # HyperliquidExchangeClientFactory
│   │   ├── ws_manager.py         # WebSocket abonelik yöneticisi
│   │   └── copy_trading/
│   │       └── engine.py         # Copy trading motoru
│   └── tasks/            # Celery worker'ları
│       └── workers/
│           ├── hl_sync.py        # Asset & fill senkronizasyonu
│           └── copy_trading.py   # Copy watch başlatma/durdurma
│
└── interfaces/       # Dış dünyayla temas noktaları
    ├── api/v1/
    │   ├── routers/      # FastAPI router'ları
    │   ├── dependencies/ # DI: auth, JWT, password
    │   └── middleware/   # Logging, CORS
    └── schemas/          # Pydantic request/response
```

## Veritabanı Şeması

```
users               roles               user_roles (n:n)
──────────────      ──────────────      ──────────────────────
id (PK, UUID)       id (PK)             user_id (FK → users)
email               name (unique)       role_id (FK → roles)
hashed_password     description
is_active           created_at
created_at
updated_at

permissions                     role_permissions (n:n)
────────────────────            ──────────────────────────
id (PK, UUID)                   role_id (FK → roles)
name (unique)                   permission_id (FK → permissions)
description
created_at

api_keys                        accounts
────────────────────────        ────────────────────────────────
id (PK, UUID)                   address (PK, VARCHAR 42)
owner_id (FK → users)           user_id (FK → users)
prefix                          account_type  (master/sub/vault)
hashed_key                      agent_address
scopes[]                        is_active
expires_at
is_active
created_at

assets                          copy_strategies
──────────────────              ──────────────────────────────────
asset_id (PK, INT)              id (PK, SERIAL)
symbol                          user_wallet (FK → accounts.address)
sz_decimals                     target_wallet
is_perp                         direction  (forward/reverse)
                                copy_ratio
                                markup_pct
                                pnl_control_enabled

cross_asset_triggers            orders
──────────────────────────      ────────────────────────────────────
id (PK, SERIAL)                 oid (PK, BIGINT — Hyperliquid ID)
strategy_id (FK →               owner_address (FK → accounts.address)
  copy_strategies)              asset_id (FK → assets)
ref_asset_id (FK → assets)      strategy_id (FK → copy_strategies, nullable)
operator  (GT/LT)               is_buy
threshold_px                    limit_px
close_pct                       sz
                                status  (open/filled/canceled/rejected)

fills
──────────────────────────
fill_id (PK, UUID string)
oid (FK → orders)
owner_address (FK → accounts.address)
px
sz
timestamp (ms epoch)
```

## API Endpoint'leri

### Auth
| Method | Path | Auth | Açıklama |
|--------|------|------|----------|
| `POST` | `/api/v1/auth/register` | — | Yeni kullanıcı kaydı |
| `POST` | `/api/v1/auth/login` | — | JWT access + refresh token |
| `POST` | `/api/v1/auth/refresh` | — | Token yenileme |
| `GET`  | `/api/v1/auth/me` | JWT veya API Key | Mevcut kullanıcı |

### API Keys
| Method | Path | Auth | Açıklama |
|--------|------|------|----------|
| `POST`   | `/api/v1/api-keys/` | JWT | Yeni key oluştur |
| `GET`    | `/api/v1/api-keys/` | JWT | Key listesi |
| `DELETE` | `/api/v1/api-keys/{id}` | JWT | Key iptal et |

### Sistem
| Method | Path | Açıklama |
|--------|------|----------|
| `GET` | `/health` | Sağlık kontrolü |
| `GET` | `/docs` | OpenAPI (development/test) |

## Factory Pattern

Dış servis istemcileri doğrudan instantiate edilmez; domain'de tanımlı interface ve factory sözleşmeleri üzerinden bağlanır.

| Interface | Factory Interface | Concrete Factory | Concrete Implementation |
|-----------|------------------|-----------------|------------------------|
| `IExchangeClient` | `IExchangeClientFactory` | `HyperliquidExchangeClientFactory` | `HyperliquidExchangeClient` |
| `ICacheService` | `ICacheServiceFactory` | `RedisCacheServiceFactory` | `RedisCacheService` |

**Avantajlar:**
- `CopyTradingEngine` Hyperliquid SDK'ya doğrudan bağımlı değildir — test ortamında `IExchangeClientFactory` mock'lanabilir
- Cache katmanı değiştirilebilir (örn. in-memory, Memcached) — uygulama kodu `ICacheService` ile çalışır
- Farklı exchange backend'leri aynı `IExchangeClient` sözleşmesini implement ederek sisteme eklenebilir

```python
# Use case / servis içinde — concrete tipe bağımlılık yok
class SomeUseCase:
    def __init__(self, cache: ICacheService, exchange_factory: IExchangeClientFactory): ...

# Composition root (main.py / DI container) — sadece burada concrete tipler
cache = RedisCacheServiceFactory(settings.REDIS_URL).create()
exchange_factory = HyperliquidExchangeClientFactory()
```

## Hyperliquid Entegrasyonu

### Bileşenler

| Bileşen | Sınıf | Açıklama |
|---------|-------|----------|
| Market data | `HyperliquidInfoClient` | Asset listesi, mid fiyatlar, order book, fill ve open order sorgulama |
| Order yönetimi | `HyperliquidExchangeClient` | Limit/market order açma, iptal, pozisyon kapatma, agent approve (`IExchangeClient` impl.) |
| Exchange factory | `HyperliquidExchangeClientFactory` | Per-wallet exchange client üretir (`IExchangeClientFactory` impl.) |
| WebSocket | `HyperliquidWSManager` | `userFills`, `allMids`, `orderUpdates` aboneliklerini yönetir |
| Copy trading | `CopyTradingEngine` | Target wallet filllerini dinler, strateji kurallarını uygular, emir açar |

### Copy Trading Akışı

```
Target wallet fill (WebSocket)
  → CopyStrategy listesi sorgulanır
  → Her strateji için:
      1. CrossAssetTrigger kontrol edilir (ref asset fiyatı eşiği aştıysa pozisyon kapatılır)
      2. Direction uygulanır  — FORWARD: aynı yön, REVERSE: ters yön
      3. Boyut hesaplanır    — sz × copy_ratio
      4. Fiyat hesaplanır    — limit_px × (1 ± markup_pct%)
      5. Kullanıcı cüzdanında limit order açılır
      6. Order & fill DB'ye kaydedilir
```

### Celery Task'ları

| Task | Tetikleyici | Açıklama |
|------|-------------|----------|
| `hl.sync_assets` | Beat (saatlik) | Tüm perp ve spot asset'leri HL'den çekip DB'ye yazar |
| `hl.sync_fills` | Manuel / cron | Bir adrese ait geçmiş filleri senkronize eder |
| `hl.sync_open_orders` | Manuel / cron | Açık order durumlarını günceller |
| `hl.start_copy_watch` | Manuel | Long-lived task; target wallet'ı WebSocket ile izler |
| `hl.stop_copy_watch` | Manuel | Aktif copy_watch task'ını revoke eder |

### Private Key Yönetimi

`HyperliquidExchangeClient` private key'i constructor'da alır, saklamaz. Varsayılan resolver env değişkeninden okur:

```
HL_PRIVATE_KEY_<WALLET_ADDRESS_BÜYÜK_HARF>
```

Production'da bunu Vault veya AWS Secrets Manager gibi bir backend ile değiştir:
`src/infrastructure/tasks/workers/copy_trading.py` içindeki `_resolve_private_key` fonksiyonunu override et.

### Ortam Konfigürasyonu

| Ortam | `HYPERLIQUID_USE_TESTNET` | API URL |
|-------|--------------------------|---------|
| development / docker / staging / test | `true` | `api.hyperliquid-testnet.xyz` |
| production | `false` | `api.hyperliquid.xyz` |

## Ortam Yapılandırması

`ENVIRONMENT` değişkeni hangi `.env` dosyasının yükleneceğini belirler:

| Ortam | Dosya | Kullanım |
|-------|-------|----------|
| `development` | `.env.development` | Local geliştirme |
| `docker` | `.env.docker` | Docker Compose |
| `test` | `.env.test` | pytest |
| `staging` | `.env.staging` | Staging |
| `production` | `.env.production` | Production |

## Kurulum ve Çalıştırma

### Docker Compose (önerilen)

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

- `app` → `http://localhost:8000`
- `postgres` ve `redis` yalnızca `contraflow_net` içinde erişilebilir (host'a port açık değil)

### Local Geliştirme

```bash
# Bağımlılıkları yükle
uv venv && uv pip install -e ".[dev]"

# Migration
ENVIRONMENT=development alembic upgrade head

# Uygulamayı başlat
ENVIRONMENT=development uvicorn src.main:app --reload
```

### Migration Oluşturma

Yeni bir entity veya model değişikliği yapıldığında:

```bash
# 1. alembic/env.py dosyasına yeni modeli import et (yoksa Alembic tabloyu görmez)
#    Örnek: import src.infrastructure.database.models.yeni_model  # noqa: F401

# 2. Değişiklikleri otomatik tespit ederek revision dosyası oluştur
ENVIRONMENT=development alembic revision --autogenerate -m "add yeni_tablo"

# 3. Oluşturulan dosyayı kontrol et (alembic/versions/ altında)
#    Alembic bazen Enum ya da özel tip değişikliklerini kaçırabilir — gözden geçir.

# 4. Migration'ı uygula
ENVIRONMENT=development alembic upgrade head
```

### Migration Geri Alma

```bash
# Son migration'ı geri al
ENVIRONMENT=development alembic downgrade -1

# Tüm migration'ları geri al (boş DB)
ENVIRONMENT=development alembic downgrade base

# Mevcut DB revision'ını göster
ENVIRONMENT=development alembic current

# Tüm migration geçmişini listele
ENVIRONMENT=development alembic history --verbose
```

### DB'yi Sıfırlayıp Baştan Oluşturma (Dev ortamı)

Migration'ları baştan oluşturmak gerektiğinde (örn. tüm şemayı tek bir initial migration'a toplamak):

```bash
# 1. DB şemasını sıfırla
psql -U postgres -d contraflow -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 2. Eski migration dosyalarını sil
rm alembic/versions/*.py

# 3. Tüm modeller env.py'de import edildiğinden emin ol, sonra yeniden oluştur
ENVIRONMENT=development alembic revision --autogenerate -m "initial"

# 4. Uygula
ENVIRONMENT=development alembic upgrade head
```

## Test

```bash
# Test DB'yi hazırla (ilk seferde)
ENVIRONMENT=test alembic upgrade head

# Smoke testleri çalıştır
ENVIRONMENT=test pytest tests/smoke/ -v
```

Her test çalıştırmasında `clean_db` fixture'ı ilgili tabloları otomatik olarak temizler.

## Auth Kullanımı

### JWT

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Secret123!"}'

# Korumalı endpoint
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### API Key

```bash
# Key oluştur (JWT gerekli)
curl -X POST http://localhost:8000/api/v1/api-keys/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"scopes":["read","write"]}'

# API Key ile istek
curl http://localhost:8000/api/v1/auth/me \
  -H "X-API-Key: <raw_key>"
```

> API Key yalnızca oluşturulduğu anda `raw_key` olarak döner, tekrar görüntülenemez.

## Yeni Bir Use Case Eklemek

1. `src/domain/entities/` → gerekirse yeni entity
2. `src/domain/repositories/` → soyut interface
3. `src/application/use_cases/` → use case sınıfı
4. `src/infrastructure/database/` → model + concrete repo
5. `src/interfaces/api/v1/routers/` → router
6. `alembic revision --autogenerate` → migration
