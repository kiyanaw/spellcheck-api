#!/usr/bin/env node

/**
 * Discover Default VPC Information
 *
 * Discovers the default VPC, subnets, security groups, route tables,
 * and checks for an existing S3 Gateway Endpoint. Saves results to
 * scripts/vpc-info.json for use by Serverless Framework.
 *
 * Usage:
 *   node scripts/get-vpc-info.js --profile my-profile
 *
 * Region defaults to us-east-1. Set AWS_PROFILE env var instead of --profile if preferred.
 */

import {
  EC2Client,
  DescribeVpcsCommand,
  DescribeSubnetsCommand,
  DescribeSecurityGroupsCommand,
  DescribeRouteTablesCommand,
  DescribeVpcEndpointsCommand,
} from '@aws-sdk/client-ec2';
import { fromIni } from '@aws-sdk/credential-providers';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Parse CLI args: --profile
const args = process.argv.slice(2);
const region = 'us-east-1';
let profile;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--profile' && args[i + 1]) profile = args[++i];
}

const clientConfig = { region };
if (profile) {
  clientConfig.credentials = fromIni({ profile });
}

const ec2Client = new EC2Client(clientConfig);

async function getVpcInfo() {
  try {
    // Get default VPC
    const vpcsResponse = await ec2Client.send(
      new DescribeVpcsCommand({
        Filters: [{ Name: 'isDefault', Values: ['true'] }],
      })
    );

    if (!vpcsResponse.Vpcs || vpcsResponse.Vpcs.length === 0) {
      throw new Error('No default VPC found in this region');
    }

    const vpcId = vpcsResponse.Vpcs[0].VpcId;
    console.log(`Found default VPC: ${vpcId}`);

    // Get subnets in default VPC
    const subnetsResponse = await ec2Client.send(
      new DescribeSubnetsCommand({
        Filters: [{ Name: 'vpc-id', Values: [vpcId] }],
      })
    );

    const subnetIds = subnetsResponse.Subnets.map((s) => s.SubnetId);
    console.log(`Found ${subnetIds.length} subnets:`, subnetIds.join(', '));

    // Get default security group
    const securityGroupsResponse = await ec2Client.send(
      new DescribeSecurityGroupsCommand({
        Filters: [
          { Name: 'vpc-id', Values: [vpcId] },
          { Name: 'group-name', Values: ['default'] },
        ],
      })
    );

    const securityGroupId = securityGroupsResponse.SecurityGroups?.[0]?.GroupId;
    console.log(`Found default security group: ${securityGroupId}`);

    // Get main route table
    const routeTablesResponse = await ec2Client.send(
      new DescribeRouteTablesCommand({
        Filters: [
          { Name: 'vpc-id', Values: [vpcId] },
          { Name: 'association.main', Values: ['true'] },
        ],
      })
    );

    const routeTableId = routeTablesResponse.RouteTables?.[0]?.RouteTableId;
    console.log(`Found main route table: ${routeTableId}`);

    // Check for existing S3 Gateway Endpoint in this VPC
    const endpointsResponse = await ec2Client.send(
      new DescribeVpcEndpointsCommand({
        Filters: [
          { Name: 'vpc-id', Values: [vpcId] },
          { Name: 'service-name', Values: [`com.amazonaws.${region}.s3`] },
          { Name: 'vpc-endpoint-type', Values: ['Gateway'] },
          { Name: 'vpc-endpoint-state', Values: ['available', 'pending'] },
        ],
      })
    );

    const hasS3Endpoint = (endpointsResponse.VpcEndpoints?.length ?? 0) > 0;
    console.log(`S3 Gateway Endpoint exists: ${hasS3Endpoint}`);

    const vpcInfo = {
      vpcId,
      subnetIds,
      subnet1: subnetIds[0] || '',
      subnet2: subnetIds[1] || '',
      securityGroupId,
      routeTableId,
      hasS3Endpoint,
      region,
      discoveredAt: new Date().toISOString(),
    };

    const outputPath = path.join(__dirname, 'vpc-info.json');
    fs.writeFileSync(outputPath, JSON.stringify(vpcInfo, null, 2));

    console.log('\nVPC information written to scripts/vpc-info.json');
    return vpcInfo;
  } catch (error) {
    console.error('Error discovering VPC information:', error.message);
    process.exit(1);
  }
}

getVpcInfo();
