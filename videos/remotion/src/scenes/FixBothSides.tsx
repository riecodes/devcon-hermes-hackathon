import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { D } from "../data";
import { Pill, rise, Stage } from "../theme";

type Props = {
  readonly style?: React.CSSProperties;
};

// Labels and hints are the real ones from desktop-plugin/suki-pulse/plugin.js.
const BUTTONS = [
  ["Pulse check", "Jev triages complaints, root causes, ops evidence"],
  ["Fix top root cause", "Plans ops and customer fixes, asks before writing"],
  ["Recover riskiest customer", "Customer story, then resolve, reply, goodwill"],
  ["Branch scorecard", "Live health numbers for the branch"],
];
const PRESS = 46; // frame the cursor presses "Fix top root cause"
const PLAN_AT = 84;
const ASK_AT = 150;
const YES_AT = 166;
const TICK_AT = 184;

const FixBothSidesInner: React.FC<Props> = ({ style }) => {
  const frame = useCurrentFrame();
  const fix = D.fix_run;

  return (
    <Stage style={style}>
      <Interactive.Div
        name="Suki Pulse pane"
        style={{
          position: "absolute",
          left: 140,
          top: 130,
          width: 540,
          backgroundColor: "var(--surface)",
          borderRadius: 20,
          boxShadow: "inset 0 0 0 1px var(--line)",
          padding: 28,
          display: "flex",
          flexDirection: "column",
          gap: 18,
          opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [0, 22], ["-24px 0px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ fontSize: 34, fontWeight: 700 }}>Suki Pulse</div>
          <Pill size={18}>Jev x Hermes</Pill>
        </div>
        <div style={{ fontSize: 22, color: "var(--muted)", marginTop: -8 }}>
          Complaint, root cause, fix, across CX and operations.
        </div>
        <div style={{ fontSize: 22, color: "var(--muted)" }}>Branch</div>
        <div
          style={{
            marginTop: -10,
            padding: "12px 16px",
            borderRadius: 14,
            boxShadow: "inset 0 0 0 1.5px var(--line-2)",
            fontSize: 26,
          }}
        >
          TMR - Tomas Morato
        </div>
        {BUTTONS.map(([label, hint], i) => {
          const active = i === 1;
          return (
            <div key={label} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <div
                style={{
                  height: 58,
                  borderRadius: 14,
                  display: "flex",
                  alignItems: "center",
                  paddingLeft: 20,
                  fontSize: 26,
                  fontWeight: 700,
                  backgroundColor: active && frame >= PRESS ? "var(--accent-fill)" : "var(--surface-2)",
                  color: active && frame >= PRESS ? "#ffffff" : "var(--ink)",
                  boxShadow: active && frame >= PRESS ? "none" : "inset 0 0 0 1px var(--line-2)",
                  scale: active
                    ? interpolate(frame, [PRESS - 3, PRESS, PRESS + 8], [1, 0.98, 1], {
                        extrapolateLeft: "clamp",
                        extrapolateRight: "clamp",
                      })
                    : 1,
                }}
              >
                {label}
              </div>
              <div style={{ fontSize: 20, color: "var(--faint)", paddingLeft: 4 }}>{hint}</div>
            </div>
          );
        })}
      </Interactive.Div>

      <Interactive.Svg
        name="Cursor"
        width={44}
        height={44}
        viewBox="0 0 24 24"
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          translate: interpolate(frame, [8, PRESS - 4, PRESS + 30], ["900px 900px", "520px 506px", "560px 560px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          opacity: interpolate(frame, [8, 16, PRESS + 24, PRESS + 34], [0, 1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <path d="M4 2 L4 19 L8.5 14.8 L11.5 21.5 L14.2 20.3 L11.3 13.8 L17.5 13.8 Z" fill="#ffffff" stroke="#0b0c0d" strokeWidth={1.3} />
      </Interactive.Svg>

      <Interactive.Div
        name="Chat"
        style={{ position: "absolute", left: 740, right: 140, top: 130, display: "flex", flexDirection: "column", gap: 16 }}
      >
        <div
          style={{
            ...rise(frame, PRESS + 10),
            alignSelf: "flex-end",
            maxWidth: 860,
            backgroundColor: "var(--surface-2)",
            borderRadius: 20,
            padding: "18px 24px",
            fontSize: 28,
            lineHeight: 1.35,
          }}
        >
          {fix.prompt}
        </div>
        <div style={{ ...rise(frame, PLAN_AT - 8), fontSize: 30, fontWeight: 700, marginTop: 6 }}>
          Plan: {fix.actions.length} actions, operations and customers
        </div>
        {fix.actions.map((a, i) => {
          const tick = TICK_AT + i * 12;
          return (
            <div key={a.tool + a.target} style={{ ...rise(frame, PLAN_AT + i * 9), display: "flex", gap: 18, alignItems: "flex-start" }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 999,
                  flexShrink: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 22,
                  fontWeight: 700,
                  backgroundColor: frame >= tick ? "var(--accent)" : "var(--surface-2)",
                  color: frame >= tick ? "#0b0c0d" : "var(--muted)",
                  scale: interpolate(frame, [tick, tick + 4, tick + 10], [1, 1.15, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  }),
                }}
              >
                {frame >= tick ? "✓" : i + 1}
              </div>
              <div>
                <div style={{ fontSize: 28 }}>
                  <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{a.tool}</span>
                  <span style={{ color: "var(--muted)" }}> &rarr; </span>
                  {a.target}
                </div>
                <div
                  style={{
                    fontSize: 22,
                    color: "var(--muted)",
                    marginTop: 4,
                    opacity: interpolate(frame, [tick, tick + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                  }}
                >
                  {a.result}
                </div>
              </div>
            </div>
          );
        })}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 4 }}>
          <div style={{ ...rise(frame, ASK_AT), fontSize: 30, fontWeight: 700 }}>Proceed? (yes/no)</div>
          <div
            style={{
              ...rise(frame, YES_AT),
              marginLeft: "auto",
              backgroundColor: "var(--surface-2)",
              borderRadius: 20,
              padding: "10px 24px",
              fontSize: 28,
            }}
          >
            yes
          </div>
        </div>
      </Interactive.Div>
    </Stage>
  );
};

const schema = {} as const satisfies InteractivitySchema;

export const FixBothSides = Interactive.withSchema({
  Component: FixBothSidesInner,
  componentName: "<FixBothSides>",
  schema,
  wrapInSequence: true,
});
