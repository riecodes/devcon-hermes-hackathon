import type React from "react";
import { Easing, Interactive, interpolate, useCurrentFrame, type InteractivitySchema } from "remotion";
import { D } from "../data";
import { Eyebrow, Pill, rise, Stage } from "../theme";

type Props = {
  readonly headline: string;
  readonly style?: React.CSSProperties;
};

// Each cause, the operational record root_cause_rollup puts next to it, and the fix tool.
const EvidenceInner: React.FC<Props> = ({ headline, style }) => {
  const frame = useCurrentFrame();
  const b = D.branch;
  const r = b.rider;
  const rows = [
    {
      cause: "Late delivery",
      count: b.causes.late_delivery,
      evidence: (
        <>
          {r.rider}: <b>{r.late_all_branches} late</b> of {r.deliveries_all_branches} deliveries across {r.branches_served} branches in{" "}
          {r.days} days.
        </>
      ),
      tool: "flag_rider_for_coaching",
    },
    {
      cause: "Out of stock",
      count: b.causes.out_of_stock,
      evidence: (
        <>
          <b>{b.scorecard_before.reorder_without_po} items</b> at or under their reorder point with no open purchase order.
        </>
      ),
      tool: "draft_purchase_orders",
    },
    {
      cause: "Loyalty points",
      count: b.causes.loyalty,
      evidence: (
        <>
          <b>{b.scorecard_before.loyalty_mismatches} points balances</b> that don&rsquo;t match their own ledger.
        </>
      ),
      tool: "fix_loyalty_balance",
    },
  ];

  return (
    <Stage style={style}>
      <Eyebrow style={{ position: "absolute", left: 140, top: 100 }}>
        {b.code} &middot; {b.name} &middot; root cause rollup
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
        name="Evidence table"
        style={{
          position: "absolute",
          left: 140,
          right: 140,
          top: 340,
          backgroundColor: "var(--surface)",
          borderRadius: 20,
          boxShadow: "inset 0 0 0 1px var(--line)",
          padding: "8px 40px",
        }}
      >
        {rows.map((row, i) => (
          <div
            key={row.cause}
            style={{
              ...rise(frame, 24 + i * 16),
              display: "flex",
              alignItems: "center",
              gap: 40,
              minHeight: 190,
              borderTop: i === 0 ? "none" : "1px solid var(--line)",
            }}
          >
            <div style={{ width: 330 }}>
              <div style={{ fontSize: 40, fontWeight: 700 }}>{row.cause}</div>
              <div style={{ fontSize: 28, color: "var(--muted)", marginTop: 6 }}>
                <span style={{ fontVariantNumeric: "tabular-nums" }}>{row.count}</span> complaints
              </div>
            </div>
            <div style={{ flex: 1, fontSize: 40, lineHeight: 1.3 }}>{row.evidence}</div>
            <Pill tone="accent" size={24}>
              {row.tool}
            </Pill>
          </div>
        ))}
      </Interactive.Div>
    </Stage>
  );
};

const schema = {
  headline: { type: "text-content", default: "Each cause has a record behind it.", description: "Headline" },
} as const satisfies InteractivitySchema;

export const Evidence = Interactive.withSchema({
  Component: EvidenceInner,
  componentName: "<Evidence>",
  schema,
  wrapInSequence: true,
});
