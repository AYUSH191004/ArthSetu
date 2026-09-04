import { useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, RefreshCw, Upload } from "lucide-react";
import { ingestApi } from "@/api/endpoints";
import { queryClient } from "@/lib/queryClient";
import type { ApiError } from "@/lib/api";
import type { IngestionReport, ProcessPendingResult } from "@/types/api";
import { formatNumber } from "@/lib/format";
import { useToast } from "@/components/Toast";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Field";
import { Table, Td, Th } from "@/components/ui/Table";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/States";

function TallyRow({ tally }: { tally: { auto_link: number; review: number; new_entity: number; failed: number } }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge tone="brand">{formatNumber(tally.auto_link)} auto-linked</Badge>
      <Badge tone="warn">{formatNumber(tally.review)} to review</Badge>
      <Badge tone="neutral">{formatNumber(tally.new_entity)} new identities</Badge>
      {tally.failed > 0 && (
        <Badge tone="danger">{formatNumber(tally.failed)} failed</Badge>
      )}
    </div>
  );
}

export function IngestionPage() {
  useDocumentTitle("Data Ingestion");
  const { notify } = useToast();
  const fileInput = useRef<HTMLInputElement>(null);

  const [system, setSystem] = useState("");
  const [runMatching, setRunMatching] = useState(true);
  const [report, setReport] = useState<IngestionReport | null>(null);
  const [pendingResult, setPendingResult] = useState<ProcessPendingResult | null>(null);

  const systems = useQuery({
    queryKey: ["source-systems"],
    queryFn: ingestApi.sourceSystems,
  });
  const pending = useQuery({
    queryKey: ["ingest-pending"],
    queryFn: ingestApi.pending,
  });

  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ["source-systems"] });
    queryClient.invalidateQueries({ queryKey: ["ingest-pending"] });
    queryClient.invalidateQueries({ queryKey: ["reviews"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const upload = useMutation({
    mutationFn: () => {
      const file = fileInput.current?.files?.[0];
      if (!file) throw Object.assign(new Error("Choose a CSV file first"), { status: 400 });
      if (!system) throw Object.assign(new Error("Pick a source system"), { status: 400 });
      return ingestApi.uploadCsv(file, system, runMatching);
    },
    onSuccess: (r) => {
      setReport(r);
      notify("success", `${r.created} record${r.created === 1 ? "" : "s"} imported`);
      if (fileInput.current) fileInput.current.value = "";
      refreshAll();
    },
    onError: (e) =>
      notify("error", (e as unknown as ApiError)?.message ?? "Import failed"),
  });

  const processPending = useMutation({
    mutationFn: ingestApi.processPending,
    onSuccess: (r) => {
      setPendingResult(r);
      notify("success", `Processed ${r.processed} pending record${r.processed === 1 ? "" : "s"}`);
      refreshAll();
    },
    onError: (e) =>
      notify("error", (e as unknown as ApiError)?.message ?? "Processing failed"),
  });

  const systemOptions = [
    { value: "", label: "Select a source system…" },
    ...(systems.data ?? []).map((s) => ({
      value: s.code,
      label: `${s.name} (${s.department})`,
    })),
  ];

  return (
    <div className="space-y-3">
      <PageHeader
        title="Data Ingestion"
        description="Import departmental records and resolve them to business identities."
      />

      {/* Pending */}
      <Card>
        <CardHeader
          title="Unresolved records"
          description="Records not yet linked or in the review queue"
        />
        <CardBody className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-2xl font-semibold tabular-nums text-ink">
            {pending.isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              formatNumber(pending.data ?? 0)
            )}
          </div>
          <Button
            variant="secondary"
            size="sm"
            loading={processPending.isPending}
            disabled={!pending.data}
            onClick={() => processPending.mutate()}
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Run matching on pending
          </Button>
        </CardBody>
        {pendingResult && (
          <div className="border-t border-line px-4 py-3">
            <TallyRow tally={pendingResult} />
          </div>
        )}
      </Card>

      {/* CSV import */}
      <Card>
        <CardHeader
          title="Import CSV"
          description="One department's export. Headers are matched loosely (name / firm_name / trade_name, pan, gstin, address, pin…)."
          action={
            <Button
              variant="ghost"
              size="sm"
              onClick={() => ingestApi.downloadTemplate()}
            >
              <Download className="h-3.5 w-3.5" />
              Template
            </Button>
          }
        />
        <CardBody className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                Source system
              </label>
              <Select
                options={systemOptions}
                value={system}
                onChange={(e) => setSystem(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                CSV file
              </label>
              <input
                ref={fileInput}
                type="file"
                accept=".csv,text/csv"
                className="block w-full text-[13px] text-ink-muted file:mr-3 file:cursor-pointer file:rounded-md file:border-0 file:bg-brand-soft file:px-3 file:py-1.5 file:text-[13px] file:font-medium file:text-brand hover:file:bg-brand-soft/70"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-[13px] text-ink-muted">
            <input
              type="checkbox"
              checked={runMatching}
              onChange={(e) => setRunMatching(e.target.checked)}
              className="h-3.5 w-3.5 rounded border-line text-brand focus:ring-brand"
            />
            Resolve imported records through the matching engine now
          </label>

          <Button loading={upload.isPending} onClick={() => upload.mutate()}>
            <Upload className="h-3.5 w-3.5" />
            Import
          </Button>

          {report && (
            <div className="rounded-md border border-line bg-surface-muted p-3">
              <div className="flex flex-wrap gap-x-5 gap-y-1 text-[13px]">
                <span className="text-ink-muted">
                  Rows read <b className="text-ink">{formatNumber(report.rows_read)}</b>
                </span>
                <span className="text-ink-muted">
                  Created <b className="text-ok">{formatNumber(report.created)}</b>
                </span>
                <span className="text-ink-muted">
                  Duplicates skipped{" "}
                  <b className="text-ink">{formatNumber(report.skipped_duplicates)}</b>
                </span>
                {report.errors.length > 0 && (
                  <span className="text-ink-muted">
                    Errors <b className="text-danger">{report.errors.length}</b>
                  </span>
                )}
              </div>
              {report.matching && (
                <div className="mt-2">
                  <TallyRow tally={report.matching} />
                </div>
              )}
              {report.errors.length > 0 && (
                <ul className="mt-2 space-y-0.5 text-[12px] text-danger">
                  {report.errors.slice(0, 10).map((e, i) => (
                    <li key={i}>
                      Row {e.row}: {e.error}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Source systems */}
      <Card>
        <CardHeader title="Source systems" description="Connected departmental registries" />
        {systems.isLoading ? (
          <CardBody>
            <Skeleton className="h-24 w-full" />
          </CardBody>
        ) : systems.isError ? (
          <ErrorState onRetry={() => systems.refetch()} />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Code</Th>
                <Th>Registry</Th>
                <Th>Department</Th>
                <Th className="text-right">Records</Th>
              </tr>
            </thead>
            <tbody>
              {systems.data?.map((s) => (
                <tr key={s.code}>
                  <Td className="font-mono text-[12px]">{s.code}</Td>
                  <Td>{s.name}</Td>
                  <Td className="text-ink-muted">{s.department}</Td>
                  <Td className="text-right tabular-nums">
                    {formatNumber(s.record_count)}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </div>
  );
}
