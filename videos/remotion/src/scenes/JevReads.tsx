import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { causeLabel, D } from "../data";
import { easeOut, Eyebrow, Pill, rise, Stage } from "../theme";

type Props = {
  readonly title: string;
  readonly style?: React.CSSProperties;
};

const BAR = 260;

// One real Jev call from the live pulse check (TKT-00585): six independent yes/no
// checks, then the scale of the full run.
const JevReadsInner: React.FC<Props> = ({ title, style }) => {
  const frame = useCurrentFrame();
  const f = D.live_pulse.featured;
  const rows = Object.entries(f.causes).sort((a, b) => b[1] - a[1]);
  const tiles = [
    ["Complaints read", D.jev_run.items.toLocaleString("en-US")],
    ["Jev cost", `$${D.jev_run.cost_usd.toFixed(4)}`],
    ["Seconds", D.jev_run.seconds.toFixed(1)],
    ["Fallbacks", String(D.jev_run.fallbacks)],
  ];

  return (
    <Stage style={style}>
      <Eyebrow style={{ position: "absolute", left: 140, top: 100 }}>What Jev reads</Eyebrow>

      <Interactive.Div
        name="Complaint"
        style={{
          position: "absolute",
          left: 140,
          top: 170,
          width: 760,
          backgroundColor: "var(--surface)",
          borderRadius: 20,
          boxShadow: "inset 0 0 0 1px var(--line)",
          padding: "32px 36px",
          display: "flex",
          flexDirection: "column",
          gap: 22,
          opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [0, 20], ["0px 12px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div style={{ display: "flex", gap: 10 }}>
          <Pill>{f.ref}</Pill>
          <Pill>Tomas Morato</Pill>
        </div>
        <div style={{ fontSize: 54, lineHeight: 1.22, fontWeight: 600 }}>&ldquo;{f.text}&rdquo;</div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 24, color: "var(--faint)" }}>
          {D.live_pulse.engine[0]} &middot; {f.input_tokens} tokens &middot; one call
        </div>
      </Interactive.Div>

      <Interactive.Div
        name="Checks"
        style={{
          position: "absolute",
          left: 980,
          top: 170,
          width: 800,
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        <div style={{ ...rise(frame, 16), fontSize: 38, fontWeight: 700, marginBottom: 14 }}>{title}</div>
        {rows.map(([key, p], i) => {
          const start = 24 + i * 7;
          const yes = p >= 0.5;
          return (
            <div
              key={key}
              style={{ ...rise(frame, start), display: "flex", alignItems: "center", gap: 20, height: 64 }}
            >
              <div style={{ width: 360, fontSize: 32, fontWeight: 600, whiteSpace: "nowrap", color: yes ? "var(--ink)" : "var(--muted)" }}>
                {causeLabel(key)}
              </div>
              <div style={{ width: BAR, height: 12, borderRadius: 99, backgroundColor: "var(--surface-2)" }}>
                <div
                  style={{
                    height: 12,
                    borderRadius: 99,
                    backgroundColor: yes ? "var(--accent)" : "var(--faint)",
                    width: interpolate(frame, [start + 4, start + 23], [0, p * BAR], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                      easing: easeOut,
                    }),
                  }}
                />
              </div>
              <div style={{ width: 76, fontSize: 32, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                {p.toFixed(2)}
              </div>
              <Pill tone={yes ? "accent" : "neutral"}>{yes ? "Yes" : "No"}</Pill>
            </div>
          );
        })}
        <div
          style={{ ...rise(frame, 72), fontFamily: "var(--font-mono)", fontSize: 24, color: "var(--muted)", marginTop: 18 }}
        >
          Churn {f.churn_risk.toFixed(2)} of 2 &middot; urgent {f.urgent.toFixed(2)}
        </div>
      </Interactive.Div>

      <Interactive.Div
        name="Run totals"
        style={{
          position: "absolute",
          left: 140,
          right: 140,
          bottom: 100,
          display: "flex",
          alignItems: "flex-end",
          gap: 16,
        }}
      >
        {tiles.map(([label, value], i) => (
          <div
            key={label}
            style={{
              ...rise(frame, 130 + i * 8),
              backgroundColor: "var(--tint)",
              borderRadius: 14,
              padding: "18px 28px",
              flexShrink: 0,
              whiteSpace: "nowrap",
            }}
          >
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>{label}</div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 800,
                fontSize: 72,
                lineHeight: 1.05,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {value}
            </div>
          </div>
        ))}
        <div style={{ ...rise(frame, 166), fontSize: 36, lineHeight: 1.3, color: "var(--muted)", marginLeft: 20, marginBottom: 12 }}>
          Every open complaint in all {D.jev_run.branches} branches.
        </div>
      </Interactive.Div>
    </Stage>
  );
};

const schema = {
  title: { type: "text-content", default: "Six yes or no checks, one call", description: "Checks title" },
} as const satisfies InteractivitySchema;

export const JevReads = Interactive.withSchema({
  Component: JevReadsInner,
  componentName: "<JevReads>",
  schema,
  wrapInSequence: true,
});
