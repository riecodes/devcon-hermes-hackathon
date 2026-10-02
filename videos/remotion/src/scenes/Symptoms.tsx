import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { D } from "../data";
import { Pill, rise, Stage } from "../theme";

type Props = {
  readonly headline: string;
  readonly subline: string;
  readonly style?: React.CSSProperties;
};

// Real complaints from store.db, then the real count from the Jev run, then the thesis.
const SymptomsInner: React.FC<Props> = ({ headline, subline, style }) => {
  const frame = useCurrentFrame();
  const count = Math.round(
    interpolate(frame, [30, 90], [0, D.jev_run.items], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    }),
  );

  return (
    <Stage style={style}>
      <Interactive.Div
        name="Complaints"
        style={{
          position: "absolute",
          left: 140,
          top: 140,
          width: 1000,
          display: "flex",
          flexDirection: "column",
          gap: 18,
          opacity: interpolate(frame, [100, 116], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [100, 120], ["0px 0px", "0px -24px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {D.complaints.slice(0, 4).map((c, i) => (
          <div
            key={c.ref}
            style={{
              ...rise(frame, 4 + i * 12),
              backgroundColor: "var(--surface)",
              borderRadius: 16,
              boxShadow: "inset 0 0 0 1px var(--line)",
              padding: "22px 28px",
              display: "flex",
              flexDirection: "column",
              gap: 12,
            }}
          >
            <div style={{ display: "flex", gap: 10 }}>
              <Pill>{c.ref}</Pill>
              <Pill>{"stars" in c ? `${c.stars} star review` : `${c.priority} priority ticket`}</Pill>
            </div>
            <div style={{ fontSize: 40, lineHeight: 1.25 }}>&ldquo;{c.text}&rdquo;</div>
          </div>
        ))}
      </Interactive.Div>

      <Interactive.Div
        name="Open complaints"
        style={{
          position: "absolute",
          right: 140,
          top: 300,
          width: 560,
          textAlign: "right",
          opacity: interpolate(frame, [100, 116], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: 250,
            lineHeight: 1,
            letterSpacing: "-0.04em",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {count}
        </div>
        <div style={{ fontSize: 44, lineHeight: 1.25, color: "var(--muted)", marginTop: 12 }}>
          open complaints across {D.jev_run.branches} Suki Mart branches
        </div>
      </Interactive.Div>

      <Interactive.Div
        name="Headline"
        style={{
          position: "absolute",
          left: 140,
          top: 330,
          width: 1500,
          opacity: interpolate(frame, [112, 128], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [112, 136], ["0px 28px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: 150,
            lineHeight: 1.02,
            letterSpacing: "-0.035em",
          }}
        >
          {headline}
        </div>
        <div style={{ fontSize: 52, lineHeight: 1.3, color: "var(--muted)", marginTop: 36, maxWidth: 1300 }}>
          {subline}
        </div>
      </Interactive.Div>
    </Stage>
  );
};

const schema = {
  headline: { type: "text-content", default: "Every complaint is a symptom.", description: "Headline" },
  subline: { type: "text-content", default: "", description: "Subline" },
} as const satisfies InteractivitySchema;

export const Symptoms = Interactive.withSchema({
  Component: SymptomsInner,
  componentName: "<Symptoms>",
  schema,
  wrapInSequence: true,
});
