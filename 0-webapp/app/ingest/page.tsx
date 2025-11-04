"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "react-i18next";
import {
  Container,
  Tabs,
  Stack,
  Text,
  Title,
  TextInput,
  Button,
  Group,
  FileInput,
  Alert,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

// New ingest page: first tab = URL ingestion form, second tab (disabled) = future file upload
export default function IngestPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [active, setActive] = useState<string | null>("url");

  // URL form state
  const [sourceUrl, setSourceUrl] = useState("");
  const [urlTouched, setUrlTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Placeholder upload state (disabled tab)
  const [file, setFile] = useState<File | null>(null);

  const urlError = (() => {
    if (!urlTouched) return null;
    if (!sourceUrl.trim()) return t("page.ingest.validation.required");
    try {
      const u = new URL(sourceUrl.trim());
      if (!u.protocol.startsWith("http")) return t("page.ingest.validation.httpOnly");
      return null;
    } catch {
      return t("page.ingest.validation.invalidUrl");
    }
  })();

  async function submitUrl(e: React.FormEvent) {
    e.preventDefault();
    setUrlTouched(true);
    if (urlError) return;
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("sourceUrl", sourceUrl.trim());
      // Updated to new ingest API endpoint
      const resp = await fetch("/api/ingest", { method: "POST", body: fd });
      if (!resp.ok) throw new Error(await resp.text());
      const data = (await resp.json()) as { doc_id: string };
      router.push(`/status/${encodeURIComponent(data.doc_id)}`);
    } catch (err) {
      notifications.show({
        color: "red",
        title: t("page.ingest.errorTitle", "Ingest failed"),
        message: (err as Error).message || t("page.ingest.errorMessage", "An unexpected error occurred"),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Container size="sm" py="lg">
      <Stack gap="md">
        <Title order={2}>{t("page.ingest.title", t("page.upload.title"))}</Title>
        <Text c="dimmed" size="sm">
          {t("page.ingest.instructions", t("page.upload.instructions"))} {t("page.ingest.urlOnlyHint", "Provide an HTTP(S) URL to ingest; file upload is temporarily disabled.")}
        </Text>
        <Tabs value={active} onChange={setActive} keepMounted={false}>
          <Tabs.List>
            <Tabs.Tab value="url">{t("page.ingest.tabs.url", "URL")}</Tabs.Tab>
            <Tabs.Tab value="file" disabled>{t("page.ingest.tabs.file", t("page.upload.navLabel"))}</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="url" pt="md">
            <form onSubmit={submitUrl} noValidate>
              <Stack gap="sm">
                <TextInput
                  label={t("page.ingest.urlLabel", t("page.upload.urlLabel"))}
                  placeholder={t("page.ingest.urlPlaceholder", t("page.upload.urlPlaceholder"))}
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.currentTarget.value)}
                  onBlur={() => setUrlTouched(true)}
                  error={urlError}
                  required
                />
                <Group gap="sm">
                  <Button type="submit" loading={submitting} disabled={!!urlError || !sourceUrl.trim()}>
                    {submitting ? t("page.ingest.submitting", t("page.upload.uploading")) : t("page.ingest.ingest", t("page.upload.upload"))}
                  </Button>
                  <Button variant="default" type="button" disabled={submitting} onClick={() => { setSourceUrl(""); setUrlTouched(false); }}>
                    {t("page.ingest.reset", t("page.upload.reset"))}
                  </Button>
                </Group>
                <Text size="xs" c="dimmed">
                  {t("page.ingest.info", t("page.upload.info"))}
                </Text>
              </Stack>
            </form>
          </Tabs.Panel>

          <Tabs.Panel value="file" pt="md">
            <Alert color="gray" variant="light" title={t("page.ingest.disabledTitle", "Coming soon")}> 
              {t("page.ingest.disabledDescription", "File upload has been temporarily disabled in favor of URL ingestion.")}
            </Alert>
            <FileInput
              label={t("page.upload.fileLabel") + " (disabled)"}
              value={file}
              onChange={setFile}
              disabled
              clearable
            />
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}
