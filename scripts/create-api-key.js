#!/usr/bin/env node

/**
 * Provision a new API key for the spellcheck API.
 *
 * Creates the key, associates it with the usage plan for the given stage,
 * and prints the key value.
 *
 * Usage:
 *   node scripts/create-api-key.js --name <consumer-name> --stage <stage> [--profile <profile>]
 *
 * Examples:
 *   node scripts/create-api-key.js --name kiyanaw-backend --stage staging
 *   node scripts/create-api-key.js --name kiyanaw-backend --stage production --profile my-profile
 */

import { APIGatewayClient, CreateApiKeyCommand, CreateUsagePlanKeyCommand, GetApiKeyCommand } from '@aws-sdk/client-api-gateway';
import { CloudFormationClient, DescribeStackResourceCommand } from '@aws-sdk/client-cloudformation';
import { fromIni } from '@aws-sdk/credential-providers';

const args = process.argv.slice(2);
let name, stage, profile;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--name' && args[i + 1]) name = args[++i];
  else if (args[i] === '--stage' && args[i + 1]) stage = args[++i];
  else if (args[i] === '--profile' && args[i + 1]) profile = args[++i];
}

if (!name || !stage) {
  console.error('Usage: node scripts/create-api-key.js --name <consumer-name> --stage <stage> [--profile <profile>]');
  console.error('  --name    Descriptive name for the consumer (e.g. kiyanaw-backend)');
  console.error('  --stage   staging or production');
  process.exit(1);
}

if (!['staging', 'production'].includes(stage)) {
  console.error(`Unknown stage "${stage}". Valid values: staging, production`);
  process.exit(1);
}

const clientConfig = { region: 'us-east-1' };
if (profile) clientConfig.credentials = fromIni({ profile });

const apigw = new APIGatewayClient(clientConfig);
const cfn = new CloudFormationClient(clientConfig);

const stackName = `spellcheck-api-${stage}`;
const keyName = `${name}-${stage}`;

async function main() {
  // Look up usage plan ID from the CloudFormation stack
  console.log(`Looking up usage plan in stack: ${stackName}`);
  let usagePlanId;
  try {
    const res = await cfn.send(new DescribeStackResourceCommand({
      StackName: stackName,
      LogicalResourceId: 'ApiGatewayUsagePlan',
    }));
    usagePlanId = res.StackResourceDetail.PhysicalResourceId;
  } catch (err) {
    console.error(`Could not find usage plan in stack "${stackName}".`);
    console.error('Make sure the stack is deployed before creating API keys.');
    console.error(err.message);
    process.exit(1);
  }
  console.log(`Found usage plan: ${usagePlanId}`);

  // Create the API key
  console.log(`Creating API key: ${keyName}`);
  let keyId;
  try {
    const res = await apigw.send(new CreateApiKeyCommand({ name: keyName, enabled: true }));
    keyId = res.id;
  } catch (err) {
    console.error(`Failed to create API key: ${err.message}`);
    process.exit(1);
  }

  // Associate the key with the usage plan
  try {
    await apigw.send(new CreateUsagePlanKeyCommand({
      usagePlanId,
      keyId,
      keyType: 'API_KEY',
    }));
  } catch (err) {
    console.error(`Failed to associate key with usage plan: ${err.message}`);
    process.exit(1);
  }

  // Retrieve and print the key value
  const res = await apigw.send(new GetApiKeyCommand({ apiKey: keyId, includeValue: true }));

  console.log('\nAPI key created successfully.');
  console.log(`  Name:  ${res.name}`);
  console.log(`  ID:    ${res.id}`);
  console.log(`  Value: ${res.value}`);
  console.log('\nStore this value securely — it cannot be retrieved again from this script.');
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
