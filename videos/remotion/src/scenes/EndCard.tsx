import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { D } from "../data";
import { Eyebrow, Pill, rise, Stage } from "../theme";

type Props = {
  readonly style?: React.CSSProperties;
};

// The site's signature: a green band with the sheet overlapping it by 24px.
const ONE_LINERS = [
  "Pick a branch, click once.",
  "Triage, root cause, plan, ask, fix.",
  "Ten domain tools on the store data.",
  "Six cause checks per complaint, for a fraction of a cent.",
];

const EndCardInner: React.FC<Props> = ({ style }) => {
  const frame = useCurrentFrame();

  return (
    <Stage style={style}>
      <Interactive.Div
        name="Band"
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          backgroundColor: "var(--band)",
          height: interpolate(frame, [0, 22], [0, 560], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      />
      <Interactive.Div
        name="Wordmark"
        style={{
          position: "absolute",
          left: 160,
          top: 110,
          color: "var(--on-band)",
          opacity: interpolate(frame, [12, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [12, 34], ["0px 16px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            padding: "6px 18px",
            borderRadius: 999,
            backgroundColor: "rgb(0 0 0 / 22%)",
            fontSize: 26,
            fontWeight: 600,
          }}
        >
          <span style={{ width: 10, height: 10, borderRadius: 99, backgroundColor: "var(--accent)" }} />
          {D.badge}
        </div>
        <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 200, letterSpacing: "-0.045em", lineHeight: 1.05 }}>
          {D.product}
        </div>
        <div style={{ fontSize: 48, opacity: 0.85 }}>{D.tagline}</div>
      </Interactive.Div>

      <Interactive.Div
        name="Sheet"
        style={{
          position: "absolute",
          left: 100,
          right: 100,
          top: 536,
          bottom: 0,
          backgroundColor: "var(--surface)",
          borderRadius: "24px 24px 0 0",
          padding: "44px 60px 0",
          translate: interpolate(frame, [16, 40], ["0px 80px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          opacity: interpolate(frame, [16, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        <Eyebrow>How Hermes runs it</Eyebrow>
        <div style={{ display: "flex", gap: 40, marginTop: 26 }}>
          {D.layers.map((l, i) => (
            <div key={l.name} style={{ ...rise(frame, 34 + i * 8), flex: 1, display: "flex", gap: 16 }}>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 64, lineHeight: 1, color: "var(--accent)" }}>
                {l.n}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ fontSize: 34, fontWeight: 700, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                  {l.name}
                  {l.code ? <Pill size={18}>{l.code}</Pill> : null}
                </div>
                <div style={{ fontSize: 26, lineHeight: 1.35, color: "var(--muted)" }}>{ONE_LINERS[i]}</div>
              </div>
            </div>
          ))}
        </div>
        <div
          style={{
            ...rise(frame, 76),
            position: "absolute",
            left: 60,
            right: 60,
            bottom: 56,
            display: "flex",
            justifyContent: "space-between",
            fontSize: 26,
            color: "var(--faint)",
          }}
        >
          <span>{D.credits}</span>
          <span style={{ color: "var(--ink)", fontWeight: 600 }}>{D.url}</span>
        </div>
      </Interactive.Div>
    </Stage>
  );
};

const schema = {} as const satisfies InteractivitySchema;

export const EndCard = Interactive.withSchema({
  Component: EndCardInner,
  componentName: "<EndCard>",
  schema,
  wrapInSequence: true,
});
