import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { D } from "../data";
import { Eyebrow, rise, Stage } from "../theme";

type Props = {
  readonly headline: string;
  readonly style?: React.CSSProperties;
};

const LABELS: Record<string, string> = {
  open_tickets: "Open tickets",
  never_answered: "Never answered",
  unreplied_low_reviews: "Unreplied 1-2★ reviews",
  loyalty_mismatches: "Loyalty mismatches",
  reorder_without_po: "Low stock, no PO",
};

// Before: the real baseline scorecard. After: fix_run.scorecard_after (a second
// pulse_scorecard once the live fix run lands).
const ImpactInner: React.FC<Props> = ({ headline, style }) => {
  const frame = useCurrentFrame();
  const before = D.branch.scorecard_before as Record<string, number>;
  const after = D.fix_run.scorecard_after as Record<string, number>;

  return (
    <Stage style={style}>
      <Eyebrow style={{ position: "absolute", left: 140, top: 100 }}>
        Before and after &middot; {D.branch.code} &middot; {D.fix_run.actions.length} actions
      </Eyebrow>
      <Interactive.Div
        name="Headline"
        style={{
          position: "absolute",
          left: 140,
          top: 150,
          fontFamily: "var(--font-display)",
          fontWeight: 800,
          fontSize: 110,
          letterSpacing: "-0.035em",
          lineHeight: 1.02,
          opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [0, 20], ["0px 16px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {headline}
      </Interactive.Div>

      <Interactive.Div
        name="Scorecard"
        style={{ position: "absolute", left: 140, right: 140, top: 390, display: "flex", gap: 16 }}
      >
        {Object.keys(LABELS).map((key, i) => {
          const swap = 40 + i * 10;
          const moved = after[key] !== before[key];
          return (
            <div
              key={key}
              style={{
                ...rise(frame, 10 + i * 6),
                flex: 1,
                backgroundColor: "var(--surface-2)",
                borderRadius: 14,
                padding: "26px 26px 30px",
                minHeight: 330,
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={{ fontSize: 28, fontWeight: 700, color: "var(--muted)", minHeight: 72 }}>{LABELS[key]}</div>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: 800,
                  fontSize: 150,
                  lineHeight: 1,
                  letterSpacing: "-0.04em",
                  fontVariantNumeric: "tabular-nums",
                  marginTop: 18,
                  color: frame >= swap && moved ? "var(--accent)" : "var(--ink)",
                  translate: interpolate(frame, [swap, swap + 14], ["0px 12px", "0px 0px"], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                    easing: Easing.bezier(0.16, 1, 0.3, 1),
                  }),
                }}
              >
                {frame >= swap ? after[key] : before[key]}
              </div>
              <div
                style={{
                  fontSize: 28,
                  color: "var(--faint)",
                  marginTop: "auto",
                  opacity: interpolate(frame, [swap, swap + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                }}
              >
                was {before[key]}
              </div>
            </div>
          );
        })}
      </Interactive.Div>

      <Interactive.Div
        name="Footnote"
        style={{ ...rise(frame, 100), position: "absolute", left: 140, bottom: 100, fontSize: 34, color: "var(--muted)" }}
      >
        Hermes planned it, asked first, then acted through the suki MCP tools.
      </Interactive.Div>
    </Stage>
  );
};

const schema = {
  headline: { type: "text-content", default: "Fixed on both sides.", description: "Headline" },
} as const satisfies InteractivitySchema;

export const Impact = Interactive.withSchema({
  Component: ImpactInner,
  componentName: "<Impact>",
  schema,
  wrapInSequence: true,
});
