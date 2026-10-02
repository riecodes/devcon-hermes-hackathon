import { loadFont } from "@remotion/fonts";
import type React from "react";
import { AbsoluteFill, Easing, interpolate, staticFile } from "remotion";

// Self-hosted Inter, the same files suki-pulse.vercel.app ships (suki-pulse-site/fonts).
loadFont({ family: "Inter", url: staticFile("fonts/inter-regular.woff2"), weight: "400" });
loadFont({ family: "Inter", url: staticFile("fonts/inter-semibold.woff2"), weight: "600" });
loadFont({ family: "Inter", url: staticFile("fonts/inter-bold.woff2"), weight: "700" });
loadFont({ family: "Inter Display", url: staticFile("fonts/inter-display-extrabold.woff2"), weight: "800" });

// Dark scheme from .agent-bus/design-system.md section 3 (the demo laptop runs dark).
// Every style reads these as var(--name), so a restyle is one edit here.
const tokens = {
  "--band": "#0d5c33",
  "--on-band": "#eafff2",
  "--bg": "#0b0c0d",
  "--surface": "#131416",
  "--surface-2": "#191b1d",
  "--line": "#25282b",
  "--line-2": "#34383c",
  "--ink": "#eceae4",
  "--muted": "#a4a6a8",
  "--faint": "#8c9094",
  "--accent": "#2fbf6f",
  "--accent-fill": "#0a7a3a",
  "--tint": "#123524",
  "--tint-2": "#184a31",
  "--amber": "#ff9f0a",
  "--danger": "#ff8a80",
  "--font-ui": '"Inter", "Segoe UI Variable Text", system-ui, sans-serif',
  "--font-display": '"Inter Display", "Inter", system-ui, sans-serif',
  "--font-mono": '"Cascadia Mono", Consolas, ui-monospace, monospace',
} as React.CSSProperties;

export const Stage: React.FC<{
  readonly children: React.ReactNode;
  readonly style?: React.CSSProperties;
}> = ({ children, style }) => (
  <AbsoluteFill
    style={{
      ...tokens,
      backgroundColor: "var(--bg)",
      color: "var(--ink)",
      fontFamily: "var(--font-ui)",
      fontFeatureSettings: '"cv11"',
      ...style,
    }}
  >
    {children}
  </AbsoluteFill>
);

// Brand motion: cubic-bezier(.16,1,.3,1); rows rise 12px and fade in once.
export const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const rise = (frame: number, start: number): React.CSSProperties => ({
  opacity: interpolate(frame, [start, start + 12], [0, 1], { ...clamp, easing: easeOut }),
  translate: interpolate(frame, [start, start + 18], ["0px 12px", "0px 0px"], { ...clamp, easing: easeOut }),
});

export const Pill: React.FC<{
  readonly children: React.ReactNode;
  readonly tone?: "neutral" | "accent" | "amber";
  readonly size?: number;
}> = ({ children, tone = "neutral", size = 22 }) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      padding: `${size * 0.3}px ${size * 0.6}px`,
      borderRadius: 999,
      fontFamily: "var(--font-mono)",
      fontSize: size,
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      whiteSpace: "nowrap",
      backgroundColor: tone === "accent" ? "var(--tint)" : tone === "amber" ? "rgb(255 159 10 / 14%)" : "var(--surface-2)",
      color: tone === "accent" ? "var(--accent)" : tone === "amber" ? "var(--amber)" : "var(--muted)",
      boxShadow: tone === "neutral" ? "inset 0 0 0 1px var(--line-2)" : "none",
    }}
  >
    {children}
  </span>
);

export const Eyebrow: React.FC<{ readonly children: React.ReactNode; readonly style?: React.CSSProperties }> = ({
  children,
  style,
}) => (
  <div
    style={{
      fontSize: 28,
      fontWeight: 700,
      letterSpacing: "0.06em",
      textTransform: "uppercase",
      color: "var(--muted)",
      ...style,
    }}
  >
    {children}
  </div>
);
