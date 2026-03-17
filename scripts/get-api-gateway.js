#!/usr/bin/env node

/**
 * Find or create the shared kiyanaw API Gateway.
 *
 * Looks for an existing REST API named `kiyanaw-api-<stage>`. Creates it if
 * absent. Writes the REST API ID and root resource ID to
 * scripts/api-gateway-info.json for use by Serverless Framework.
 *
 * Usage:
 *   node scripts/get-api-gateway.js --stage staging [--profile my-profile]
 */

import {
  APIGatewayClient,
  GetRestApisCommand,
  CreateRestApiCommand,
  GetResourcesCommand,
} from '@aws-sdk/client-api-gateway';
import { fromIni } from '@aws-sdk/credential-providers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const args = process.argv.slice(2);
let stage, profile;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--stage' && args[i + 1]) stage = args[++i];
  else if (args[i] === '--profile' && args[i + 1]) profile = args[++i];
}

if (!stage || !['staging', 'production'].includes(stage)) {
  console.error('Usage: node scripts/get-api-gateway.js --stage <stage> [--profile <profile>]');
  process.exit(1);
}

const apiName = `kiyanaw-api-${stage}`;
const clientConfig = { region: 'us-east-1' };
if (profile) clientConfig.credentials = fromIni({ profile });

const client = new APIGatewayClient(clientConfig);

async function getApiGatewayInfo() {
  // Check for an existing API with this name
  let restApiId;
  let position;

  do {
    const res = await client.send(new GetRestApisCommand({ position, limit: 500 }));
    const match = res.items?.find((api) => api.name === apiName);
    if (match) {
      restApiId = match.id;
      break;
    }
    position = res.position;
  } while (position);

  if (restApiId) {
    console.log(`Found existing API Gateway: ${apiName} (${restApiId})`);
  } else {
    console.log(`Creating API Gateway: ${apiName}`);
    const res = await client.send(new CreateRestApiCommand({
      name: apiName,
      description: `Shared kiyanaw API Gateway (${stage})`,
    }));
    restApiId = res.id;
    console.log(`Created API Gateway: ${restApiId}`);
  }

  // Get the root resource ID (path '/')
  const resources = await client.send(new GetResourcesCommand({ restApiId }));
  const root = resources.items?.find((r) => r.path === '/');
  if (!root) throw new Error('Could not find root resource for API Gateway');

  const info = { restApiId, restApiRootResourceId: root.id, apiName };
  const outputPath = path.join(__dirname, 'api-gateway-info.json');
  fs.writeFileSync(outputPath, JSON.stringify(info, null, 2));
  console.log(`API Gateway info written to scripts/api-gateway-info.json`);
}

getApiGatewayInfo().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
