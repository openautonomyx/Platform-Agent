# Platform Agent - Cloudflare R2 Registry

## Deploy serverless registry to Cloudflare

```bash
# 1. Clone
git clone https://github.com/cloudflare/serverless-registry.git
cd serverless-registry

# 2. Add R2 bucket
wrangler r2 bucket create r2-registry

# 3. Configure
cat > wrangler.toml << EOF
name = "platform-registry"
compatibility_date = "2024-01-01"

[[r2_buckets]]
binding = "REGISTRY"
bucket_name = "r2-registry"

[env.production.vars]
REGISTRIES_JSON = '[{"registry": "docker.io"}]'
EOF

# 4. Deploy
wrangler deploy --env production
```

## Push to your R2 registry

```bash
# Login
echo "$R2_TOKEN" | docker login registry.YOUR_SUBDOMAIN.workers.dev -u _ --password-stdin

# Tag
docker tag platform-agent:latest registry.YOUR_SUBDOMAIN.workers.dev/platform-agent:latest

# Push
docker push registry.YOUR_SUBDOMAIN.workers.dev/platform-agent:latest
```

## Pull from K3s

```yaml
image: registry.YOUR_SUBDOMAIN.workers.dev/platform-agent:latest
```