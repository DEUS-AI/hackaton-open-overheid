"use client";
import { useEffect, useMemo, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import {
  Container,
  Title,
  Text,
  Button,
  Table,
  Badge,
  Paper,
  Group,
  Alert,
  ScrollArea,
  Code,
} from "@mantine/core";

type StageInfo = { status?: string; ts?: string; extra?: any };

// All pipeline stages in order
const ALL_PIPELINE_STAGES = [
  "ingestion",
  "validation", 
  "pii-scanning",
  "extractor",
  "embedding",
  "data-storage",
  "search-index",
  "notification"
] as const;

export default function StatusPage({ params }: { params: { doc_id: string } }) {
  const { doc_id } = params;
  const { t } = useTranslation();
  const [data, setData] = useState<{ states: Record<string, StageInfo>; updated_at?: string } | null>(null);
  const [notFound, setNotFound] = useState(false);
  const pollingStoppedRef = useRef(false);

  // Determine if pipeline is fully completed successfully
  const pipelineCompleted = useMemo(() => {
    if (!data) return false;
    const states = data.states || {};
    return ALL_PIPELINE_STAGES.every((stage) => {
      const st = states[stage]?.status;
      return st === "ok" || st === "completed"; // success states
    });
  }, [data]);

  // Polling logic with a tiny initial delay to avoid duplicate immediate fetches
  // in React StrictMode (development) where effects mount -> unmount -> remount.
  useEffect(() => {
    let timer: any;
    let aborted = false;
    let controller: AbortController | null = null;

    async function tick() {
      if (aborted) return;
      if (pollingStoppedRef.current) return; // do not continue if stopped
      controller?.abort(); // cancel previous in‑flight request if any
      controller = new AbortController();
      try {
        const r = await fetch(`/api/status/${encodeURIComponent(doc_id)}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        if (aborted) return; // component disposed while awaiting
        if (r.status === 404) {
          setNotFound(true);
          setData(null);
        } else {
          const j = await r.json();
          setData(j);
          setNotFound(false);
        }
      } catch (e: any) {
        if (e?.name === "AbortError") {
          // ignored abort
        }
      } finally {
        if (!aborted && !pollingStoppedRef.current) {
          timer = setTimeout(tick, 2000); // 2s polling interval
        }
      }
    }

    // Small delay so that the first (now cancelled) StrictMode effect run does
    // not fire an unnecessary network call; only the second mount executes.
    const initialDelay = 150; // ms
    timer = setTimeout(tick, initialDelay);

    return () => {
      aborted = true;
      if (timer) clearTimeout(timer);
      controller?.abort();
    };
  }, [doc_id]);

  // Stop polling once pipeline completes
  useEffect(() => {
    if (pipelineCompleted) {
      pollingStoppedRef.current = true;
    }
  }, [pipelineCompleted]);

  const rows = useMemo(() => {
    const states = data?.states || {};
    
    // Create rows for all pipeline stages, showing "not-started" for missing ones
    return ALL_PIPELINE_STAGES.map(stage => {
      const stageInfo = states[stage] || { status: "not-started" };
      return [stage, stageInfo] as [string, StageInfo];
    });
  }, [data]);

  function statusBadge(status?: string) {
    const normalizedStatus = status || "not-started";
    const color =
      normalizedStatus === "ok" || normalizedStatus === "completed"
        ? "govGreen"
        : normalizedStatus === "error" || normalizedStatus === "failed"
        ? "govRed"
        : normalizedStatus === "generating"
        ? "govBlue"
        : normalizedStatus === "started" || normalizedStatus === "queued" || normalizedStatus === "processing"
        ? "govAmber"
        : "govGray";
        
    return (
      <Badge color={color}>
  {t(`page.status.statuses.${normalizedStatus}`, normalizedStatus)}
      </Badge>
    );
  }

  function getStageName(stage: string): string {
  return t(`page.status.stages.${stage}`, stage);
  }

  return (
    <Container size="lg" py="lg">
      <Group justify="space-between" mb="sm">
        <Title order={2}>{t("page.status.documentPipelineStatus")}</Title>
        <Button variant="default" component="a" href="/ingest">
          {t("page.upload.navLabel")}
        </Button>
      </Group>
      <Text size="xs" c="dimmed" mb="xs" style={{ wordBreak: "break-all" }}>
  {t("page.status.id")}: {doc_id}
      </Text>
      {pipelineCompleted && (
        <Alert
          color="green"
            variant="light"
            title={t("page.status.completedTitle", "Pipeline completed successfully")}
            mb="md"
        >
          {t("page.status.completedMessage", "All processing stages finished successfully.")}
          <Button mt="sm" component="a" href="/home" variant="filled" color="green">
            {t("page.status.goHome", "Go to home")}
          </Button>
        </Alert>
      )}
      {notFound ? (
        <Alert color="yellow" variant="light" title={t("page.status.notFound")}> 
          {t("page.status.documentNotFoundYet")}
        </Alert>
      ) : (
        <Paper withBorder>
          <ScrollArea>
            <Table stickyHeader highlightOnHover verticalSpacing="xs">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>{t("page.status.stage")}</Table.Th>
                  <Table.Th>{t("page.status.status")}</Table.Th>
                  <Table.Th>{t("page.status.timestamp")}</Table.Th>
                  <Table.Th>{t("page.status.extra")}</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rows.map(([stage, info]) => (
                  <Table.Tr key={stage}>
                    <Table.Td>{getStageName(stage)}</Table.Td>
                    <Table.Td>{statusBadge(info.status)}</Table.Td>
                    <Table.Td>{info.ts ? new Date(info.ts).toLocaleString() : "-"}</Table.Td>
                    <Table.Td>
                      <Code block fz="xs">
                        {JSON.stringify(info.extra ?? {}, null, 2)}
                      </Code>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Paper>
      )}
      <Text ta="right" size="xs" c="dimmed" mt="xs">
  {t("page.status.autoRefresh")}
      </Text>
    </Container>
  );
}
