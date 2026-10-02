import type React from "react";
import { Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { D } from "../data";
import { Eyebrow, rise, Stage } from "../theme";

type Props = {
  readonly headline: string;
  readonly style?: React.CSSProperties;
};

const R = D.jev_race;
const RACE_FROM = 24; // frame the replay clock starts
const RACE_FRAMES = 132; // Jev's 27.5 s of real time, replayed in this many frames

// Replay of the measured benchmark: both models get the same 40 complaints one at a
// time; each dot lands at its real finish time on one shared (sped-up) clock.
const JevRaceInner: React.FC<Props> = ({ headline, style }) => {
  const frame = useCurrentFrame();
  const jevTotal = R.jev_finish_s[R.jev_finish_s.length - 1];
  const clock = interpolate(frame, [RACE_FROM, RACE_FROM + RACE_FRAMES], [0, jevTotal], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const lanes = [
    { name: R.jev_model, sub: "TypeSafe Jev", finish: R.jev_finish_s, color: "var(--accent)" },
    { name: R.llm_model, sub: "via OpenCode Zen", finish: R.llm_finish_s, color: "var(--muted)" },
  ];
  const stats = [
    [`${R.speedup_p50}x`, "faster per decision", `${Math.round(R.p50_ms.jev)} ms vs ${(R.p50_ms.llm / 1000).toFixed(2)} s median`],
    [`${R.cost_ratio}x`, "cheaper per decision", `$${R.cost_per_call.jev.toFixed(6)} vs $${R.cost_per_call.llm.toFixed(6)}`],
    [`${Math.round(R.agreement * 100)}%`, "same top cause", "agreement between the two, not accuracy"],
  ];

  return (
    <Stage style={style}>
      <Eyebrow style={{ position: "absolute", left: 140, top: 100 }}>
        Measured at the venue &middot; {R.n} complaints &middot; {R.questions_per_call} questions each
      </Eyebrow>
      <Interactive.Div
        name="Headline"
        style={{
          position: "absolute",
          left: 140,
          top: 150,
          fontFamily: "var(--font-display)",
          fontWeight: 800,
          fontSize: 96,
          letterSpacing: "-0.03em",
          lineHeight: 1.05,
          opacity: interpolate(frame, [0, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        {headline}
      </Interactive.Div>

      <Interactive.Div
        name="Race"
        style={{ position: "absolute", left: 140, right: 140, top: 330, display: "flex", flexDirection: "column", gap: 34 }}
      >
        {lanes.map((lane, li) => {
          const done = lane.finish.filter((t) => t <= clock).length;
          return (
            <div key={lane.name} style={{ ...rise(frame, 6 + li * 6), display: "flex", alignItems: "center", gap: 32 }}>
              <div style={{ width: 330 }}>
                <div style={{ fontSize: 36, fontWeight: 700 }}>{lane.name}</div>
                <div style={{ fontSize: 24, color: "var(--faint)" }}>{lane.sub}</div>
              </div>
              <div style={{ display: "flex", gap: 6, flex: 1 }}>
                {lane.finish.map((t, i) => (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      height: 56,
                      borderRadius: 3,
                      backgroundColor: t <= clock ? lane.color : "var(--surface-2)",
                    }}
                  />
                ))}
              </div>
              <div
                style={{
                  width: 120,
                  textAlign: "right",
                  fontFamily: "var(--font-display)",
                  fontWeight: 800,
                  fontSize: 64,
                  fontVariantNumeric: "tabular-nums",
                  color: li === 0 ? "var(--accent)" : "var(--ink)",
                }}
              >
                {done}
              </div>
            </div>
          );
        })}
        <div style={{ ...rise(frame, 12), fontFamily: "var(--font-mono)", fontSize: 26, color: "var(--muted)", marginLeft: 362 }}>
          {clock.toFixed(1)} s of real time{frame >= RACE_FROM + RACE_FRAMES ? `: Jev is done, Haiku has decided ${R.llm_done_when_jev_done}` : ""}
        </div>
      </Interactive.Div>

      <Interactive.Div
        name="Stats"
        style={{ position: "absolute", left: 140, right: 140, bottom: 100, display: "flex", gap: 16 }}
      >
        {stats.map(([big, label, small], i) => (
          <div
            key={label}
            style={{
              ...rise(frame, RACE_FROM + RACE_FRAMES + 6 + i * 8),
              flex: 1,
              backgroundColor: "var(--surface)",
              boxShadow: "inset 0 0 0 1px var(--line)",
              borderRadius: 16,
              padding: "22px 28px",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
              <span style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 80, color: "var(--accent)", lineHeight: 1 }}>
                {big}
              </span>
              <span style={{ fontSize: 34, fontWeight: 700 }}>{label}</span>
            </div>
            <div style={{ fontSize: 24, color: "var(--muted)", marginTop: 10 }}>{small}</div>
          </div>
        ))}
      </Interactive.Div>
    </Stage>
  );
};

const schema = {
  headline: { type: "text-content", default: "Jev finished 40 while Haiku did 8.", description: "Headline" },
} as const satisfies InteractivitySchema;

export const JevRace = Interactive.withSchema({
  Component: JevRaceInner,
  componentName: "<JevRace>",
  schema,
  wrapInSequence: true,
});
