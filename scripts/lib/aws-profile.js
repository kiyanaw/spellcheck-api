/**
 * Exit with a clear message when no AWS profile has been chosen.
 *
 * Without this, the AWS SDK fails with a vague "Could not load credentials from any
 * providers" error. A profile passed as a script argument also counts, as do credentials
 * already exported in the environment (AWS_ACCESS_KEY_ID).
 */
export function requireAwsProfile(profileArg) {
  if (profileArg || process.env.AWS_PROFILE || process.env.AWS_ACCESS_KEY_ID) return;

  const npmScript = process.env.npm_lifecycle_event;
  const example = npmScript ? `npm run ${npmScript}` : 'npm run <command>';
  console.error(
    [
      'Error: AWS_PROFILE is not set.',
      '',
      'Set it to the AWS profile for the account you are targeting, for example:',
      `  AWS_PROFILE=<your-profile> ${example}`,
      '',
      'List your profiles with `aws configure list-profiles`. See "AWS profile" in README.md.',
    ].join('\n'),
  );
  process.exit(1);
}
