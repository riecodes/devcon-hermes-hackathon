import { Composition, Folder } from "remotion";
import { EndCard } from "./scenes/EndCard";
import { Evidence } from "./scenes/Evidence";
import { FixBothSides } from "./scenes/FixBothSides";
import { Impact } from "./scenes/Impact";
import { JevRace } from "./scenes/JevRace";
import { JevReads } from "./scenes/JevReads";
import { RootCauses } from "./scenes/RootCauses";
import { Symptoms } from "./scenes/Symptoms";
import { SukiPulse } from "./SukiPulse";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="SukiPulse" component={SukiPulse} durationInFrames={1596} fps={30} width={1920} height={1080} />
      <Folder name="Scenes">
        <Composition
          id="Symptoms"
          component={Symptoms}
          durationInFrames={180}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            headline: "Every complaint is a symptom.",
            subline: "Suki Pulse lets Hermes find the operational cause behind each one, then fix both sides.",
          }}
        />
        <Composition
          id="JevReads"
          component={JevReads}
          durationInFrames={240}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ title: "Six yes or no checks, one call" }}
        />
        <Composition
          id="JevRace"
          component={JevRace}
          durationInFrames={210}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ headline: "Jev finished 40 while Haiku did 8." }}
        />
        <Composition id="RootCauses" component={RootCauses} durationInFrames={240} fps={30} width={1920} height={1080} />
        <Composition
          id="Evidence"
          component={Evidence}
          durationInFrames={210}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ headline: "Each cause has a record behind it." }}
        />
        <Composition id="FixBothSides" component={FixBothSides} durationInFrames={270} fps={30} width={1920} height={1080} />
        <Composition
          id="Impact"
          component={Impact}
          durationInFrames={150}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{ headline: "Fixed on both sides." }}
        />
        <Composition id="EndCard" component={EndCard} durationInFrames={180} fps={30} width={1920} height={1080} />
      </Folder>
    </>
  );
};
