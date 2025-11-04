"use client";

import React, { useEffect, useState } from "react";
import { Table } from '@mantine/core';
import { useTranslation } from "react-i18next";

export default function ProcessedDocumentsPage() {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDocs() {
      try {
        const res = await fetch("/api/processed-documents");
        if (!res.ok) throw new Error(`Error fetching documents: ${res.statusText}`);
        const data = await res.json();
        setDocuments(data.documents || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    fetchDocs();
  }, []);

  if (loading) return <main style={{ padding: 32 }}>{t("page.processedDocuments.loading")}</main>;
  if (error) return <main style={{ padding: 32, color: 'red' }}>{t("page.processedDocuments.error")}: {error}</main>;

  return (
    <main style={{ padding: 32 }}>
  <h1>{t("page.processedDocuments.title")}</h1>
      <Table striped highlightOnHover withTableBorder withColumnBorders mt={24}>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{t("page.processedDocuments.id")}</Table.Th>
            <Table.Th>{t("page.processedDocuments.name")}</Table.Th>
            <Table.Th>{t("page.processedDocuments.status")}</Table.Th>
            <Table.Th>{t("page.processedDocuments.uploadedAt")}</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {documents.map((doc) => (
            <Table.Tr key={doc._id}>
              <Table.Td>{doc._id}</Table.Td>
              <Table.Td>{doc.name || doc.url || t("page.processedDocuments.noName")}</Table.Td>
              <Table.Td>{doc.status || t("page.processedDocuments.noStatus")}</Table.Td>
              <Table.Td>{doc.uploadedAt ? new Date(doc.uploadedAt).toLocaleString() : t("page.processedDocuments.noDate")}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </main>
  );
}
