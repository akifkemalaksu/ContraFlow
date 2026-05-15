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

## Mimari

```
src/
├── domain/           # Saf iş mantığı — dışa bağımlılık yok
│   ├── entities/         # User, Role
│   ├── value_objects/    # APIKey
│   ├── events/
│   └── repositories/     # Soyut interface'ler (ABC)
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
│   ├── cache/            # Redis bağlantısı
│   └── tasks/            # Celery worker'ları
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
users          roles          user_roles (n:n)
─────────      ──────         ────────────────
id (PK)        id (PK)        user_id (FK)
email          name           role_id (FK)
hashed_pw      description
is_active      created_at
created_at
updated_at

api_keys
────────
id (PK)
owner_id (FK → users)
prefix
hashed_key
scopes[]
expires_at
is_active
created_at
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

```bash
ENVIRONMENT=development alembic revision --autogenerate -m "açıklama"
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
