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
- AWS CLI with a profile for each account you deploy to (`aws configure list-profiles`)

### AWS profile

Every command that talks to AWS reads the profile from `AWS_PROFILE`, and exits with an
error if it isn't set. Set it for one command, or export it for your shell session:

```sh
AWS_PROFILE=<your-profile> npm run deploy:staging

# or, for every command in this shell:
export AWS_PROFILE=<your-profile>
npm run deploy:staging
```

Use the environment variable rather than `npm run deploy:staging -- --profile <your-profile>`.
The deploy commands run several steps in a row, and a flag after `--` only reaches the last one.

### Commands

| Command | Needs `AWS_PROFILE` | Example |
|---------|:---:|---------|
| `deploy:staging`, `deploy:production` | yes | `AWS_PROFILE=<your-profile> npm run deploy:staging` |
| `upload-fsts` | yes | `AWS_PROFILE=<your-profile> npm run upload-fsts -- staging [--update] [--verbose]` |
| `create-api-key` | yes | `AWS_PROFILE=<your-profile> npm run create-api-key -- --name <consumer> --stage staging` |
| `test:integration:staging`, `test:integration:production` | yes | `AWS_PROFILE=<your-profile> npm run test:integration:staging` |
| `test` | no | `npm run test` (ruff and unit tests, in Docker) |
| `lint` | no | `npm run lint` (ruff only, in Docker) |

The setup steps below walk through deploying, uploading FSTs and creating API keys in order.

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

Place `.hfstol` or `.foma` files in `scripts/fsts-to-upload/`. `.foma` files are converted
to `.hfstol` before uploading, which needs HFST installed locally (`hfst-fst2fst`, e.g.
`apt install hfst`).

For Border Lakes Ojibwe (`ojbl`), build [ishkodens-fst](https://github.com/wawiingetoontech/ishkodens-fst)
(`cd src && bash compile.sh`) and copy these builds with an `ojbl-` prefix (filenames are
S3 keys, so the prefix keeps them from clashing with other foma-built languages):

```sh
for f in full_lexicon_generate full_lexicon_generate_relaxed full_lexicon_analyze; do
  cp <ishkodens-fst>/src/$f.foma scripts/fsts-to-upload/ojbl-$f.foma
done
```

Then upload:

```sh
AWS_PROFILE=<your-profile> npm run upload-fsts -- staging
```

Use `--update` to re-upload existing files, `--verbose` for detailed output.

### 4. Create API keys

API keys are managed manually so each service or user gets their own key. Use a descriptive `--name` that identifies the consumer.

```sh
AWS_PROFILE=<your-profile> npm run create-api-key -- --name transcribe --stage staging
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
