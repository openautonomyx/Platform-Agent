# Platform Agent - Quick Start

## 1. Sign Up (Free)

1. Go to https://dash.cloudflare.com
2. Sign up with email
3. Verify email

## 2. Create R2 Bucket

```bash
# Install Wrangler (Cloudflare CLI)
npm install -g wrangler

# Login
wrangler login

# Create bucket
wrangler r2 bucket create platform-agent
```

## 3. Deploy Serverless Registry

```bash
git clone https://github.com/cloudflare/serverless-registry.git
cd serverless-registry

# Add R2 to wrangler.toml
echo 'r2_buckets = [{binding = "REGISTRY", bucket_name = "platform-agent"}]' >> wrangler.toml

# Deploy
wrangler deploy --env production
```

## 4. Build & Push Image

```bash
# Build with Stacker
stacker build -f stacker.yaml

# Tag for your registry
docker tag platform-agent:latest registry.YOUR_SUBDOMAIN.workers.dev/platform-agent:latest

# Push
docker push registry.YOUR_SUBDOMAIN.workers.dev/platform-agent:latest
```

## 5. Deploy to K3s

```bash
# Update k3s.yaml with your registry URL
sed 's/zot.example.com/registry.YOUR_SUBDOMAIN.workers.dev/' k3s.yaml

# Apply
kubectl apply -f k3s.yaml
```

## URLs

| Service | URL |
|---------|-----|
| Cloudflare Dash | https://dash.cloudflare.com |
| R2 Docs | https://developers.cloudflare.com/r2 |
| Workers Docs | https://developers.cloudflare.com/workers |