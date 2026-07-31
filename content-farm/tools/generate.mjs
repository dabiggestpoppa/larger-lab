#!/usr/bin/env node
/**
 * Content Farm — Standalone Media Generator
 * 
 * Generates images via free APIs (Pollinations.ai) or OpenRouter (if credits available).
 * No app needed — run from terminal or call from agents.
 * 
 * Usage:
 *   node tools/generate.mjs --prompt "a cat" --output cat.png
 *   node tools/generate.mjs --prompt "a cat" --width 1920 --height 1080 --output cat.png
 *   node tools/generate.mjs --prompt "a cat" --provider openrouter --model google/gemini-2.5-flash-image --output cat.png
 * 
 * Providers:
 *   pollinations  (free, default) — Pollinations.ai
 *   openrouter    (needs credits) — OpenRouter API
 * 
 * Environment:
 *   OPENROUTER_API_KEY — for OpenRouter provider (optional)
 */

import { writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');

// ─── Parse CLI args ───────────────────────────────────────────────
const args = process.argv.slice(2);
const flags = {};
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (!a.startsWith('--')) continue;
  const key = a.slice(2);
  const next = args[i + 1];
  if (next && !next.startsWith('--')) {
    flags[key] = next;
    i++;
  } else {
    flags[key] = true;
  }
}

const prompt = flags.prompt || flags._?.[0] || '';
const output = flags.output || 'output.png';
const provider = flags.provider || 'pollinations';
const width = flags.width || '1024';
const height = flags.height || '1024';
const model = flags.model || 'google/gemini-2.5-flash-image';
const seed = flags.seed || String(Math.floor(Math.random() * 2147483647));
const apiKey = process.env.OPENROUTER_API_KEY;

if (!prompt) {
  console.error('Usage: node tools/generate.mjs --prompt "your prompt" [--output result.png] [--width 1024] [--height 1024] [--provider pollinations|openrouter]');
  process.exit(1);
}

// ─── Providers ────────────────────────────────────────────────────

async function generatePollinations(prompt, width, height, seed) {
  // Pollinations.ai — free, no API key, no rate limits
  const encodedPrompt = encodeURIComponent(prompt);
  const url = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&seed=${seed}&nologo=true&model=flux`;
  
  console.log(`  [pollinations] Generating ${width}x${height} (seed: ${seed})...`);
  
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`Pollinations API error: ${resp.status} ${resp.statusText}`);
  }
  
  const contentType = resp.headers.get('content-type') || '';
  if (!contentType.startsWith('image/')) {
    const text = await resp.text();
    throw new Error(`Pollinations returned non-image: ${text.substring(0, 200)}`);
  }
  
  return Buffer.from(await resp.arrayBuffer());
}

async function generateOpenRouter(prompt, model) {
  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY not set. Get a key at https://openrouter.ai/settings/keys');
  }
  
  // Strip "openrouter/" prefix if present
  let wireModel = model;
  if (wireModel.startsWith('openrouter/')) {
    wireModel = wireModel.slice('openrouter/'.length);
  }
  
  console.log(`  [openrouter] Using model: ${wireModel}...`);
  
  const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://content-farm.local',
      'X-Title': 'Content Farm',
    },
    body: JSON.stringify({
      model: wireModel,
      messages: [{ role: 'user', content: prompt }],
      modalities: ['image', 'text'],
    }),
  });
  
  if (!resp.ok) {
    const text = await resp.text();
    let error;
    try { error = JSON.parse(text); } catch { error = { message: text }; }
    throw new Error(`OpenRouter error (${resp.status}): ${error?.error?.message || error?.message || text}`);
  }
  
  const data = await resp.json();
  const choice = data.choices?.[0];
  if (!choice) throw new Error('No response from OpenRouter');
  
  // Extract image from response
  const images = choice.message?.images;
  if (images && images.length > 0) {
    const imageUrl = images[0]?.image_url?.url;
    if (imageUrl) {
      if (imageUrl.startsWith('data:')) {
        const base64Data = imageUrl.split(',')[1];
        return Buffer.from(base64Data, 'base64');
      }
      const imgResp = await fetch(imageUrl);
      if (!imgResp.ok) throw new Error(`Failed to fetch generated image: ${imgResp.status}`);
      return Buffer.from(await imgResp.arrayBuffer());
    }
  }
  
  throw new Error('No image in OpenRouter response. Model may not support image generation.');
}

// ─── Main ─────────────────────────────────────────────────────────
async function main() {
  const outputDir = path.resolve(PROJECT_ROOT, 'content');
  await mkdir(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, output);

  console.log(`[content-farm] Generating image...`);
  console.log(`  Provider: ${provider}`);
  console.log(`  Prompt:   ${prompt.slice(0, 80)}${prompt.length > 80 ? '...' : ''}`);
  console.log(`  Size:     ${width}x${height}`);
  console.log(`  Output:   ${outputPath}`);
  console.log('');

  try {
    let bytes;
    
    if (provider === 'pollinations') {
      bytes = await generatePollinations(prompt, width, height, seed);
    } else if (provider === 'openrouter') {
      bytes = await generateOpenRouter(prompt, model);
    } else {
      throw new Error(`Unknown provider: ${provider}. Use 'pollinations' or 'openrouter'.`);
    }

    await writeFile(outputPath, bytes);
    console.log(`✅ Done! ${bytes.length.toLocaleString()} bytes → ${outputPath}`);
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    process.exit(1);
  }
}

main();
