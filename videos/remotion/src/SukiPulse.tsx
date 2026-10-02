import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { useVideoConfig } from "remotion";
import { EndCard } from "./scenes/EndCard";
import { Evidence } from "./scenes/Evidence";
import { FixBothSides } from "./scenes/FixBothSides";
import { Impact } from "./scenes/Impact";
import { JevRace } from "./scenes/JevRace";
import { JevReads } from "./scenes/JevReads";
import { RootCauses } from "./scenes/RootCauses";
import { Symptoms } from "./scenes/Symptoms";

// Draft A: complaint, root cause, fix. 8 scenes, 7 fades of 12 frames: 1680 - 84 = 1596 frames.
export const SukiPulse = () => {
  const { fps } = useVideoConfig();

  return (
    <TransitionSeries>
      <TransitionSeries.Sequence name="Symptoms" durationInFrames={180} premountFor={fps}>
        <Symptoms
          headline="Every complaint is a symptom."
          subline="Suki Pulse lets Hermes find the operational cause behind each one, then fix both sides."
        />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="Jev reads" durationInFrames={240} premountFor={fps}>
        <JevReads title="Six yes or no checks, one call" />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="Jev race" durationInFrames={210} premountFor={fps}>
        <JevRace headline="Jev finished 40 while Haiku did 8." />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="Root causes" durationInFrames={240} premountFor={fps}>
        <RootCauses />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="Evidence" durationInFrames={210} premountFor={fps}>
        <Evidence headline="Each cause has a record behind it." />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="Fix both sides" durationInFrames={270} premountFor={fps}>
        <FixBothSides />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="Impact" durationInFrames={150} premountFor={fps}>
        <Impact headline="Fixed on both sides." />
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: 12 })} />
      <TransitionSeries.Sequence name="End card" durationInFrames={180} premountFor={fps}>
        <EndCard />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
