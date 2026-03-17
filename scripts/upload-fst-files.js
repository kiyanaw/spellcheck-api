#!/usr/bin/env node

/**
 * Script to upload hfstol files to S3
 *
 * Usage:
 *   node scripts/upload-fst-files.js <environment> [aws-profile] [--verbose] [--update]
 *
 * Examples:
 *   node scripts/upload-fst-files.js staging
 *   node scripts/upload-fst-files.js staging my-profile
 *   node scripts/upload-fst-files.js staging my-profile --verbose
 *   node scripts/upload-fst-files.js staging my-profile --update
 *
 * Flags:
 *   --verbose  Show detailed logging
 *   --update   Re-upload existing files (by default, existing files are skipped)
 *
 * The bucket name follows the convention: spellcheck-fsts-<AccountId>-<environment>
 * You can override it by setting the BUCKET_NAME environment variable.
 */

import { STSClient, GetCallerIdentityCommand } from '@aws-sdk/client-sts';
import { S3Client, PutObjectCommand, HeadObjectCommand } from '@aws-sdk/client-s3';
import { fromIni } from '@aws-sdk/credential-providers';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readdir, readFile } from 'fs/promises';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Parse CLI args
const CLI_ARGS = process.argv.slice(2);

const environment = CLI_ARGS[0];
let awsProfile;
let isVerbose = false;
let shouldUpdate = false;

for (let i = 1; i < CLI_ARGS.length; i++) {
  const arg = CLI_ARGS[i];
  if (arg === '--verbose') isVerbose = true;
  else if (arg === '--update') shouldUpdate = true;
  else if (!awsProfile) awsProfile = arg;
}

if (!environment || !['staging', 'production'].includes(environment)) {
  console.error('Error: Please provide an environment (staging, production)');
  console.error('Usage: node scripts/upload-fst-files.js <environment> [aws-profile] [--verbose] [--update]');
  process.exit(1);
}

const logVerbose = (...args) => { if (isVerbose) console.log(...args); };

const LOCAL_FST_FOLDER = join(__dirname, 'fsts-to-upload');
const AWS_REGION = 'us-east-1';

const clientConfig = { region: AWS_REGION };
if (awsProfile) clientConfig.credentials = fromIni({ profile: awsProfile });

const s3Client = new S3Client(clientConfig);

async function resolveBucketName() {
  if (process.env.BUCKET_NAME) return process.env.BUCKET_NAME;

  const stsClient = new STSClient(clientConfig);
  const identity = await stsClient.send(new GetCallerIdentityCommand({}));
  const accountId = identity.Account;
  return `spellcheck-api-fsts-${accountId}-${environment}`;
}

async function fileExistsInS3(bucketName, key) {
  try {
    await s3Client.send(new HeadObjectCommand({ Bucket: bucketName, Key: key }));
    return true;
  } catch (error) {
    if (error.name === 'NotFound' || error.$metadata?.httpStatusCode === 404) return false;
    throw error;
  }
}

async function uploadFileToS3(bucketName, key, filePath) {
  const fileContent = await readFile(filePath);
  await s3Client.send(new PutObjectCommand({ Bucket: bucketName, Key: key, Body: fileContent }));
}

async function getLocalHfstolFiles(folderPath) {
  if (!existsSync(folderPath)) throw new Error(`Local folder does not exist: ${folderPath}`);
  const files = await readdir(folderPath);
  return files
    .filter((f) => f.endsWith('.hfstol'))
    .map((f) => ({ filename: f, localPath: join(folderPath, f), s3Key: f }));
}

async function processFile(fileInfo, bucketName) {
  const { filename, localPath, s3Key } = fileInfo;
  const exists = await fileExistsInS3(bucketName, s3Key);

  if (exists && !shouldUpdate) {
    return { filename, action: 'skipped', success: true };
  }

  const action = exists ? 'Replacing' : 'Uploading';
  console.log(`${action} ${filename}...`);
  await uploadFileToS3(bucketName, s3Key, localPath);
  return { filename, action: exists ? 'replaced' : 'uploaded', success: true };
}

async function main() {
  const BUCKET_NAME = await resolveBucketName();

  logVerbose(`\nProcessing FST files for environment: ${environment}`);
  logVerbose(`Bucket: ${BUCKET_NAME}`);
  logVerbose(`Local folder: ${LOCAL_FST_FOLDER}`);
  if (awsProfile) logVerbose(`AWS Profile: ${awsProfile}`);
  logVerbose(`Update mode: ${shouldUpdate ? 'ON (will replace existing files)' : 'OFF (will skip existing files)'}`);
  logVerbose('');

  try {
    console.log(`Scanning local folder: ${LOCAL_FST_FOLDER}`);
    const localFiles = await getLocalHfstolFiles(LOCAL_FST_FOLDER);

    if (localFiles.length === 0) {
      console.log(`No .hfstol files found in ${LOCAL_FST_FOLDER}`);
      return;
    }

    console.log(`Found ${localFiles.length} .hfstol file(s) to process\n`);

    const results = [];
    for (const fileInfo of localFiles) {
      try {
        const result = await processFile(fileInfo, BUCKET_NAME);
        results.push(result);
        if (result.action === 'skipped') {
          console.log(`  ${result.filename}: skipped (already exists, use --update to replace)`);
        } else {
          console.log(`  ${result.filename}: ${result.action}`);
        }
      } catch (error) {
        results.push({ filename: fileInfo.filename, action: 'error', success: false, error: error.message });
        console.log(`  ${fileInfo.filename}: ERROR - ${error.message}`);
      }
    }

    console.log('\n' + '='.repeat(60));
    console.log('Processing complete!');
    const uploaded = results.filter((r) => r.action === 'uploaded').length;
    const replaced = results.filter((r) => r.action === 'replaced').length;
    const skipped = results.filter((r) => r.action === 'skipped').length;
    const errors = results.filter((r) => !r.success).length;
    if (uploaded) console.log(`  Uploaded: ${uploaded}`);
    if (replaced) console.log(`  Replaced: ${replaced}`);
    if (skipped) console.log(`  Skipped:  ${skipped}`);
    if (errors) console.log(`  Errors:   ${errors}`);
  } catch (error) {
    console.error('\nError:', error.message);
    process.exit(1);
  }
}

main().catch(console.error);
