#!/usr/bin/env node

/**
 * Look up ACM wildcard certificate ARN for the spellcheck API domain.
 *
 * Queries ACM for the wildcard certificate matching the stage domain and writes
 * the ARN to scripts/cert-info.json for use by Serverless Framework (serverless-domain-manager).
 *
 * Usage:
 *   node scripts/get-cert-arn.js --stage staging --profile my-profile
 *
 * Certificates looked up:
 *   staging:    *.kiyanaw.dev
 *   production: *.kiyanaw.net
 *
 * Note: ACM certs for CloudFront/API Gateway must be in us-east-1.
 */

import { ACMClient, ListCertificatesCommand, DescribeCertificateCommand } from '@aws-sdk/client-acm';
import { fromIni } from '@aws-sdk/credential-providers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Parse CLI args
const args = process.argv.slice(2);
let stage = 'staging';
let profile;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--stage' && args[i + 1]) stage = args[++i];
  else if (args[i] === '--profile' && args[i + 1]) profile = args[++i];
}

const domainSuffix = { staging: 'dev', production: 'net' };
if (!domainSuffix[stage]) {
  console.error(`Unknown stage: "${stage}". Valid stages: staging, production`);
  process.exit(1);
}

const wildcardDomain = `*.kiyanaw.${domainSuffix[stage]}`;
console.log(`Looking up ACM certificate for: ${wildcardDomain}`);

// ACM certs for API Gateway custom domains must be in us-east-1
const clientConfig = { region: 'us-east-1' };
if (profile) {
  clientConfig.credentials = fromIni({ profile });
}

const acmClient = new ACMClient(clientConfig);

async function getCertArn() {
  try {
    // List all issued certificates
    let nextToken;
    let certificateArn;

    do {
      const response = await acmClient.send(
        new ListCertificatesCommand({
          CertificateStatuses: ['ISSUED'],
          NextToken: nextToken,
        })
      );

      for (const cert of response.CertificateSummaryList ?? []) {
        // Check if the domain name matches our wildcard
        if (cert.DomainName === wildcardDomain) {
          certificateArn = cert.CertificateArn;
          break;
        }

        // Also check SANs via DescribeCertificate if primary domain doesn't match
        if (!certificateArn && cert.CertificateArn) {
          const detail = await acmClient.send(
            new DescribeCertificateCommand({ CertificateArn: cert.CertificateArn })
          );
          const sans = detail.Certificate?.SubjectAlternativeNames ?? [];
          if (sans.includes(wildcardDomain)) {
            certificateArn = cert.CertificateArn;
            break;
          }
        }
      }

      nextToken = response.NextToken;
    } while (nextToken && !certificateArn);

    if (!certificateArn) {
      console.error(`No ISSUED certificate found for ${wildcardDomain} in us-east-1`);
      console.error('Create the certificate in ACM (us-east-1) and validate it before running this script.');
      process.exit(1);
    }

    console.log(`Found certificate: ${certificateArn}`);

    const certInfo = { certificateArn, domain: wildcardDomain, stage };
    const outputPath = path.join(__dirname, 'cert-info.json');
    fs.writeFileSync(outputPath, JSON.stringify(certInfo, null, 2));

    console.log('Certificate ARN written to scripts/cert-info.json');
  } catch (error) {
    console.error('Error looking up certificate:', error.message);
    process.exit(1);
  }
}

getCertArn();
