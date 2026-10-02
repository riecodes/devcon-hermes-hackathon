import type React from "react";
import { Easing, Img, Interactive, interpolate, staticFile, useCurrentFrame, useVideoConfig, type InteractivitySchema } from "remotion";
import { causeLabel, D } from "../data";
import { Stage } from "../theme";

type Props = {
  readonly style?: React.CSSProperties;
};

// Camera move over the real dashboard (suki-pulse.vercel.app, dark scheme, 3200x2000 capture):
// the whole heatmap first, then a push into the Tomas Morato row.
const RootCausesInner: React.FC<Props> = ({ style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const b = D.branch;

  return (
    <Stage style={style}>
      <Interactive.Div
        name="Dashboard camera"
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 3200,
          height: 2000,
          transformOrigin: "0px 0px",
          scale: interpolate(frame, [0, 54, 160], [0.6, 0.62, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.45, 0, 0.2, 1),
          }),
          translate: interpolate(frame, [0, 54, 160], ["0px -40px", "-10px -50px", "-280px -983px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.45, 0, 0.2, 1),
          }),
        }}
      >
        <Img name="Dashboard" premountFor={fps} src={staticFile("shots/dark-fold.png")} style={{ width: 3200, height: 2000 }} />
        <div
          style={{
            position: "absolute",
            left: 832,
            top: 1496,
            width: 154,
            height: 94,
            borderRadius: 6,
            boxShadow: "0 0 0 5px var(--amber), 0 0 34px 6px rgb(255 159 10 / 55%)",
            opacity: interpolate(frame, [150, 166, 184, 200], [0, 1, 0.55, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />
      </Interactive.Div>

      <Interactive.Div
        name="Edge fade"
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          right: 0,
          width: 300,
          backgroundImage: "linear-gradient(90deg, rgb(11 12 13 / 0%), rgb(11 12 13 / 100%) 70%)",
          opacity: interpolate(frame, [90, 150], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      />
      <Interactive.Div
        name="Caption"
        style={{
          position: "absolute",
          left: 140,
          right: 140,
          bottom: 90,
          backgroundColor: "var(--surface)",
          borderRadius: 24,
          boxShadow: "inset 0 0 0 1px var(--line-2), 0 4px 14px rgb(0 0 0 / 35%)",
          padding: "30px 40px",
          opacity: interpolate(frame, [160, 176], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          translate: interpolate(frame, [160, 182], ["0px 24px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 64, letterSpacing: "-0.03em", lineHeight: 1.08 }}>
          {causeLabel(b.top_cause)} explains{" "}
          <span style={{ color: "var(--amber)" }}>{b.causes.late_delivery}</span> of {b.items} complaints at {b.name}.
        </div>
        <div style={{ fontSize: 32, color: "var(--muted)", marginTop: 12 }}>
          {D.jev_run.items} complaints, {D.jev_run.branches} branches, ranked by cause. A complaint can carry several causes.
        </div>
      </Interactive.Div>
    </Stage>
  );
};

const schema = {} as const satisfies InteractivitySchema;

export const RootCauses = Interactive.withSchema({
  Component: RootCausesInner,
  componentName: "<RootCauses>",
  schema,
  wrapInSequence: true,
});
