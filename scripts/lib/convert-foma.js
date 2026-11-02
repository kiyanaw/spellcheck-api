/**
 * Convert foma FST builds (`.foma`) into HFST optimized-lookup files (`.hfstol`),
 * which is the format the Lambda loads.
 *
 * foma saves its binaries gzipped, and hfst-fst2fst only reads them unzipped, so each
 * file is gunzipped to a temp file first. Needs `hfst-fst2fst` on the PATH.
 *
 * The output keeps the input's name with a `.hfstol` extension and is written next to
 * it. A file is only converted when its `.hfstol` is missing or older than the `.foma`.
 */

import { spawnSync } from 'child_process';
import { gunzipSync } from 'zlib';
import { mkdtemp, readdir, readFile, rm, stat, writeFile } from 'fs/promises';
import { existsSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

export function hfstolNameFor(fomaFilename) {
  return fomaFilename.replace(/\.foma$/, '.hfstol');
}

function isGzipped(data) {
  return data.length >= 2 && data[0] === 0x1f && data[1] === 0x8b;
}

async function needsConversion(fomaPath, hfstolPath) {
  if (!existsSync(hfstolPath)) return true;
  const [foma, hfstol] = await Promise.all([stat(fomaPath), stat(hfstolPath)]);
  return foma.mtimeMs > hfstol.mtimeMs;
}

export async function convertFomaFile(fomaPath, hfstolPath) {
  let data = await readFile(fomaPath);
  if (isGzipped(data)) data = gunzipSync(data);

  const tempDir = await mkdtemp(join(tmpdir(), 'foma-convert-'));
  const rawPath = join(tempDir, 'unzipped.foma');
  try {
    await writeFile(rawPath, data);
    const result = spawnSync('hfst-fst2fst', ['-w', '-i', rawPath, '-o', hfstolPath], { encoding: 'utf8' });
    if (result.error?.code === 'ENOENT') {
      throw new Error('hfst-fst2fst not found. Install HFST (e.g. `apt install hfst`) to convert .foma files');
    }
    if (result.error) throw result.error;
    if (result.status !== 0) {
      await rm(hfstolPath, { force: true });
      throw new Error(`hfst-fst2fst failed on ${fomaPath}: ${result.stderr.trim()}`);
    }
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
}

/**
 * Convert every `.foma` file in a folder that needs it. Returns one result per file.
 */
export async function convertFomaFiles(folderPath, logVerbose = () => {}) {
  const fomaFiles = (await readdir(folderPath)).filter((f) => f.endsWith('.foma'));
  const results = [];

  for (const filename of fomaFiles) {
    const fomaPath = join(folderPath, filename);
    const hfstolName = hfstolNameFor(filename);
    const hfstolPath = join(folderPath, hfstolName);

    if (!(await needsConversion(fomaPath, hfstolPath))) {
      logVerbose(`  ${filename}: ${hfstolName} is up to date`);
      results.push({ filename, hfstolName, action: 'up-to-date' });
      continue;
    }

    console.log(`Converting ${filename} -> ${hfstolName}...`);
    await convertFomaFile(fomaPath, hfstolPath);
    results.push({ filename, hfstolName, action: 'converted' });
  }

  return results;
}
