// Bundle once, render stills of SukiPulse at the given frames (half size) into out/stills.
// Usage: node scripts/stills.mjs 60 150 228 ...
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";

const frames = process.argv.slice(2).map(Number);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: "SukiPulse" });
for (const frame of frames) {
  const output = path.resolve(`out/stills/f${String(frame).padStart(4, "0")}.png`);
  await renderStill({ composition, serveUrl, frame, output, scale: 0.5 });
  console.log("frame", frame);
}
