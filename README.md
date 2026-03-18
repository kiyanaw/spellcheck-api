# spellcheck-api

kiyânaw spellcheck API — standalone serverless repo.

Deploys the spellcheck Lambda as a **container image** via Serverless Framework, along with EFS (for FST file caching), S3 (for FST file storage), and API Gateway.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/spellcheck/suggest` | Get spelling suggestions for unknown words |
| POST | `/spellcheck/bulk-lookup` | Analyze multiple words (known/unknown + suggestions) |

Both endpoints require an API key (`x-api-key` header).

Request body:
```json
{ "languageCode": "crk", "words": ["word1", "word2"] }
```

## Custom domains

- **Staging**: `api.kiyanaw.dev/spellcheck/...`
- **Production**: `api.kiyanaw.net/spellcheck/...`

## Setup

### Prerequisites

- Docker (for building/testing the container locally)
- Node.js 24+
- AWS CLI configured with appropriate profile

### 1. Install dependencies

```sh
npm install
```

### 2. Deploy

```sh
AWS_PROFILE=<your-profile> npm run deploy:staging
# or
AWS_PROFILE=<your-profile> npm run deploy:production
```

### 3. Upload FST files

Place `.hfstol` files in `scripts/fsts-to-upload/`, then:

```sh
AWS_PROFILE=<your-profile> npm run upload-fsts -- staging
```

Use `--update` to re-upload existing files, `--verbose` for detailed output.

### 4. Create API keys

API keys are managed manually so each service or user gets their own key. Use a descriptive `--name` that identifies the consumer.

```sh
AWS_PROFILE=<your-profile> npm run create-api-key -- --name kiyanaw-backend --stage staging
```

The script creates the key, associates it with the usage plan, and prints the key value. Store the value securely — to revoke access, delete the key from **API Gateway > API Keys** in the AWS console.

## Local development

Run tests and linting inside the Lambda Docker image:

```sh
npm run test
npm run lint
```

## Production DNS

The Route53 hosted zone for `kiyanaw.net` is in a different AWS account, so the DNS record must be created manually after deploying to production.

After `AWS_PROFILE=<your-profile> npm run deploy:production`:

1. Find the API Gateway custom domain's regional domain name in the AWS console (API Gateway > Custom Domain Names > `api.kiyanaw.net` > Configurations).
2. In the `kiyanaw.net` hosted zone, create an **A record** (alias) for `api.kiyanaw.net` pointing to that regional domain name.
