# Platform Agent - Cloudflare Workers

## Quick Deploy

```bash
# Install wrangler
npm install -g wrangler

# Deploy
wrangler deploy
```

## Config (wrangler.toml)

```toml
name = "platform-agent"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[vars]
LLM_PROVIDER = "openai"
```

## Environment (.dev.vars)

```
SURREALDB_URL=ws://your-db.surreal.cloud/ns/db
SURREALDB_USER=root
SURREALDB_PASS=password
LLM_API_KEY=sk-...
```

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/signin | Sign in |
| POST | /auth/signup | Sign up |
| POST | /invites | Create invite |
| POST | /invites/:token | Accept |
| GET | /knowledge | List KB |
| POST | /knowledge | Create doc |
| GET/POST | /conversations | List/Create |
| POST | /conversations/:id/messages | Add msg |
| POST | /chat | Chat |
| GET | /stats | Stats |