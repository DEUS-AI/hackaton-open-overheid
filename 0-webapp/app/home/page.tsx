"use client";

import { RoomContext } from "@livekit/components-react";
import { Room, RoomEvent } from "livekit-client";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ConnectionDetails } from "../api/connection-details/route";
import PageContent from "../page-content";
import { MindmapData } from "../utils/types";
import { notifications } from "@mantine/notifications";

// NOTE: Providers (ThemeProvider, I18nProvider) are applied at root layout.

const EXAMPLE_DATA: MindmapData = {
  summary: "op hoeveel compensatie heb ik recht als slachtoffer van de toeslagaffaire",
  documents: [
    {
      name: "Het bericht 'Afhandeling toeslagenaffaire loopt opnieuw vast, slachtoffers in geldnood'",
      id: "oep-2fc4554bf97671a76196bcbaac93264f55fd58d7",
      reasons: [
        'It directly addresses the topic of the "toeslagenaffaire" (allowance affair) mentioned in the user\'s query.',
        "The title indicates that it discusses the challenges faced by victims of the affair, which aligns with the user's concern about compensation.",
        "It provides insights into the current status of the compensation process, potentially offering information on the rights and support available to victims.",
      ],
      tags: ["Kamervraag zonder antwoord", "ruimte en infrastructuur"],
      confidence: 0.6306155666441334,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2021/09/oep-2fc4554bf97671a76196bcbaac93264f55fd58d7/kv-tk-2021Z15715.pdf",
    },
    {
      name: "Het bericht ‘Compensatie ouders toeslagenaffaire kan zomaar tot 2030 duren’ en het bericht ‘Rutte bestrijdt vrees trage afhandeling toeslagenaffaire’",
      id: "oep-840589da4d2afe667434a84beefbc119b6695497",
      reasons: [
        "It directly addresses the issue of compensation for victims of the toeslagenaffaire, which aligns with the user's query about their entitlement to compensation.",
        "The document contains information about the potential timeline for the compensation process, providing insights into the duration mentioned in the user's query.",
        "The document includes statements from Prime Minister Rutte regarding the handling of the toeslagenaffaire, offering perspectives on the government's response that may interest the user.",
      ],
      tags: ["Kamervraag zonder antwoord", "belasting"],
      confidence: 0.5976258548477631,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2023/01/oep-840589da4d2afe667434a84beefbc119b6695497/kv-tk-2023Z01148.pdf",
    },
    {
      name: "Het bericht dat de compensatie van toeslagenschandaal soms verkeerd terecht komt",
      id: "oep-2ef0725619848d4a53a747b0fdfc315a151be8a6",
      reasons: [
        "It addresses the issue of compensation related to the toeslagenaffaire, which aligns with the user's query about compensation as a victim of the toeslagaffaire.",
        "The document discusses cases where compensation from the toeslagenaffaire is not reaching the intended recipients, providing insights into potential challenges or discrepancies in compensation distribution.",
        "The document's focus on the toeslagenaffaire and compensation aligns closely with the user's specific concern about their entitlement to compensation in the aftermath of the toeslagaffaire.",
      ],
      tags: ["Kamervraag zonder antwoord", "belasting"],
      confidence: 0.5883690379912394,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2021/12/oep-2ef0725619848d4a53a747b0fdfc315a151be8a6/kv-tk-2021Z24254.pdf",
    },
    {
      name: "Regeling van werkzaamheden",
      id: "oep-92f234fe39c9836784f84a0bec3ff482014eb476",
      reasons: [
        "It may contain information about compensation measures related to the toeslagaffaire.",
        'The title "Regeling van werkzaamheden" suggests it could outline procedures or regulations, possibly including compensation details.',
        "As a government document, it likely provides official guidelines or policies regarding compensation for victims of the toeslagaffaire.",
      ],
      tags: ["Handelingen", "organisatie en bedrijfsvoering"],
      confidence: 0.5882277111591734,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2022/12/oep-92f234fe39c9836784f84a0bec3ff482014eb476/h-tk-20222023-31-22.pdf",
    },
    {
      name: "31066, nr. 1474 - Belastingdienst",
      id: "oep-ad5b3287f5f38dc69e5d3b81409de168663a54b0",
      reasons: [
        "It pertains to the toeslagenaffaire, which is the subject of your query.",
        "It involves a motion related to broadening the tasks of the Government Commissioner for the recovery of allowances.",
        "It discusses the involvement of the Tax Authorities (Belastingdienst) in the matter, which directly relates to your question about compensation.",
      ],
      tags: ["Kamerstuk", "belasting"],
      confidence: 0.5853667529608514,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2025/04/oep-ad5b3287f5f38dc69e5d3b81409de168663a54b0/kst-31066-1474.pdf",
    },
    {
      name: "Regeling van werkzaamheden",
      id: "oep-fd293621a24b3d6682df878fe22b61ce86091299",
      reasons: [
        'It may contain information about compensation measures related to the "toeslagaffaire" that the user is inquiring about.',
        'The title "Regeling van werkzaamheden" suggests it could outline procedures or regulations regarding compensations.',
        "It might provide details on the eligibility criteria or process for victims seeking compensation in such cases.",
      ],
      tags: ["Handelingen", "organisatie en bedrijfsvoering"],
      confidence: 0.5840318271516052,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2022/06/oep-fd293621a24b3d6682df878fe22b61ce86091299/h-tk-20212022-97-28.pdf",
    },
    {
      name: "36502, nr. 2 - Initiatiefnota van het lid Inge van Dijk over bescherming van de rechten van belastingbetalers en toeslagontvangers",
      id: "oep-4bd9c6f0bb5961cc177c1b1fded585601f53e2cd",
      reasons: [
        "It addresses the rights of taxpayers and recipients of allowances, which is directly related to the user's query about compensation as a victim of the allowance scandal.",
        "The document focuses on protecting the rights of individuals affected by tax issues, indicating a potential discussion on compensation measures.",
        "It is an initiative note from a specific member of the government, suggesting insights or proposals regarding compensations for victims of tax-related injustices.",
      ],
      tags: ["Kamerstuk", "belasting"],
      confidence: 0.5821883312878251,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2024/02/oep-4bd9c6f0bb5961cc177c1b1fded585601f53e2cd/kst-36502-2.pdf",
    },
    {
      name: "Regeling van werkzaamheden",
      id: "oep-14ac9ad37b16fd9d6a195fb28d92e644b7857279",
      reasons: [
        'It may contain information about compensation schemes related to the "toeslagaffaire" that the user is inquiring about.',
        'The title "Regeling van werkzaamheden" suggests it could outline procedures or regulations regarding compensations.',
        "Even though the summary is not available, the document might provide details on the rights and entitlements of victims in such cases.",
      ],
      tags: ["Handelingen", "organisatie en bedrijfsvoering"],
      confidence: 0.5777762810307857,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2022/04/oep-14ac9ad37b16fd9d6a195fb28d92e644b7857279/h-tk-20212022-74-40.pdf",
    },
    {
      name: "Water",
      id: "oep-2a68a2da79a3812cad46e1630fcbb5263a880286",
      reasons: [
        "It might contain information related to compensations for victims of government-related issues.",
        "The government often publishes documents related to compensations and financial matters.",
        "It could potentially address policies or actions taken in response to similar situations like the toeslagaffaire.",
      ],
      tags: ["Handelingen", "organisatie en bedrijfsvoering"],
      confidence: 0.5754171158603444,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2023/08/oep-2a68a2da79a3812cad46e1630fcbb5263a880286/h-tk-20222023-103-5.pdf",
    },
    {
      name: "31066, nr. 924 - Jaarplan Toeslagen 2022",
      id: "oep-5ba6acea9c3780858ca4fa398c633149c101fcf4",
      reasons: [
        'It pertains to the topic of "Toeslagen" which is directly related to the user\'s query about compensation in the toeslagenaffaire.',
        "The document is a government publication, indicating authority and official information on the subject.",
        "It specifically addresses the year 2022, potentially containing updated information on compensations and related matters.",
      ],
      tags: ["Kamerstuk", "Onbekend"],
      confidence: 0.5750132181963298,
      link: "https://hackathon-open-overheid.s3.eu-central-1.amazonaws.com/2021/12/oep-5ba6acea9c3780858ca4fa398c633149c101fcf4/blg-1008591.pdf",
    },
  ],
};

export default function HomePage() {
  const [room] = useState(new Room());
  const [mindmapData, setMindmapData] = useState<MindmapData>();
  const { t } = useTranslation();

  const onVoiceActivation = useCallback(
    async (isVoiceActive: boolean) => {
      await room.localParticipant.setMicrophoneEnabled(isVoiceActive);
    },
    [room]
  );

  const onConnectButtonClicked = useCallback(async () => {
    const url = new URL(
      process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? "/api/connection-details",
      window.location.origin
    );
    const response = await fetch(url.toString());
    const connectionDetailsData: ConnectionDetails = await response.json();

    await room.connect(connectionDetailsData.serverUrl, connectionDetailsData.participantToken);
  }, [room]);

  useEffect(() => {
    try {
      room.registerTextStreamHandler("mindmap-data", async (reader, participantInfo) => {
        const text = await reader.readAll();
        try {
          setMindmapData(JSON.parse(text));
        } catch (error) {
          setMindmapData(EXAMPLE_DATA);
        }
      });

      room.registerTextStreamHandler("chat", () => {
        /* chat stream ignored for now */
      });
    } catch (error) {
      console.error("error registering text stream handler", error);
    }
  }, [room]);

  useEffect(() => {
    room.on(RoomEvent.MediaDevicesError, onDeviceFailure);
    return () => {
      room.off(RoomEvent.MediaDevicesError, onDeviceFailure);
    };
  }, [room]);

  return (
    <main data-lk-theme="default" className="h-full flex flex-col">
      <RoomContext.Provider value={room}>
        <PageContent
          onConnectButtonClicked={onConnectButtonClicked}
          onVoiceActivation={onVoiceActivation}
          mindmapData={mindmapData}
        />
      </RoomContext.Provider>
    </main>
  );
}

function onDeviceFailure(error: Error) {
  console.error(error);
  import("../../providers/I18nProvider").then((mod) => {
    const msg = (mod as any).getInstance?.().t("alert.deviceError") || "Device error";
    notifications.show({
      color: "red",
      title: msg,
      message: error.message,
    });
  });
}
