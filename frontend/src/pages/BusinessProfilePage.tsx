import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { businessApi, statusApi } from "@/api/endpoints";
import { queryClient } from "@/lib/queryClient";
import type { ApiError } from "@/lib/api";
import type { BusinessProfile, StatusResult } from "@/types/api";
import {
  decisionMeta,
  formatDate,
  formatDateTime,
  statusMeta,
  titleCase,
} from "@/lib/format";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, StatusBadge } from "@/components/ui/Badge";
import { Table, Td, Th, Tr } from "@/components/ui/Table";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { CopyButton } from "@/components/ui/CopyButton";
import { useToast } from "@/components/Toast";
import { useAuth } from "@/context/AuthContext";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { AuditFeed } from "@/components/AuditFeed";

export function BusinessProfilePage() {
  const { ubid = "" } = useParams();
  const navigate = useNavigate();
  const { notify } = useToast();
  const { can } = useAuth();
  const [statusResult, setStatusResult] = useState<StatusResult | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["business", ubid],
    queryFn: () => businessApi.profile(ubid),
  });

  useDocumentTitle(data?.business_name ?? "Business");

  const recompute = useMutation({
    mutationFn: () => statusApi.recompute(ubid),
    onSuccess: (res) => {
      setStatusResult(res);
      notify("success", `Status recomputed: ${titleCase(res.status)}`);
      queryClient.invalidateQueries({ queryKey: ["business", ubid] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) =>
      notify("error", (e as unknown as ApiError)?.message ?? "Recompute failed"),
  });

  if (isError) {
    const status = (error as unknown as ApiError)?.status;
    return (
      <Card>
        {status === 404 ? (
          <EmptyState
            title="Business not found"
            description={`No business matches "${ubid}".`}
            action={
              <Link to="/businesses">
                <Button variant="secondary" size="sm">
                  Back to search
                </Button>
              </Link>
            }
          />
        ) : (
          <ErrorState
            message={(error as unknown as ApiError)?.message}
            onRetry={() => refetch()}
          />
        )}
      </Card>
    );
  }

  return (
    <div>
      <div className="mb-5">
        <button
          onClick={() => navigate(-1)}
          className="mb-3 inline-flex items-center gap-1.5 text-[13px] text-ink-muted hover:text-ink"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </button>

        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2.5">
              {isLoading ? (
                <Skeleton className="h-7 w-64" />
              ) : (
                <h1 className="text-xl font-semibold text-ink">
                  {data?.business_name}
                </h1>
              )}
              {data && <StatusBadge status={data.status} />}
            </div>
            <div className="mt-1 flex items-center gap-1 font-mono text-[13px] text-ink-muted">
              {isLoading ? <Skeleton className="h-4 w-28" /> : data?.ubid}
              {data && <CopyButton value={data.ubid} label="UBID" />}
            </div>
          </div>

          {can("reviewer") && (
            <Button
              variant="secondary"
              size="sm"
              loading={recompute.isPending}
              onClick={() => recompute.mutate()}
              disabled={isLoading}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Recompute status
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          <IdentitySection data={data} loading={isLoading} />
          <LinkedRecordsSection data={data} loading={isLoading} />
          <TimelineSection data={data} loading={isLoading} />
        </div>

        <div className="space-y-3">
          <StatusSection
            data={data}
            loading={isLoading}
            result={statusResult}
          />
          <EvidenceSection data={data} loading={isLoading} />
          {data && (
            <Card>
              <CardHeader title="Audit trail" description="Actions on this business" />
              <CardBody>
                <AuditFeed
                  params={{ entity_type: "business_entity", entity_id: data.id }}
                  limit={6}
                  emptyLabel="No recorded actions for this business."
                />
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */

function Field({ label, value, mono }: { label: string; value?: string | null; mono?: boolean }) {
  return (
    <div>
      <dt className="text-[12px] text-ink-muted">{label}</dt>
      <dd className={mono ? "mt-0.5 font-mono text-[13px] text-ink" : "mt-0.5 text-sm text-ink"}>
        {value || <span className="text-ink-subtle">—</span>}
      </dd>
    </div>
  );
}

function IdentitySection({ data, loading }: { data?: BusinessProfile; loading: boolean }) {
  return (
    <Card>
      <CardHeader title="Identity" description="Canonical record for this business" />
      <CardBody>
        {loading ? (
          <Skeleton className="h-20 w-full" />
        ) : (
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
            <Field label="PAN" value={data?.pan} mono />
            <Field label="GSTIN" value={data?.gstin} mono />
            <Field label="PIN code" value={data?.pin_code} mono />
            <Field label="District" value={data?.district} />
            <Field label="Sector" value={data?.sector} />
            <Field
              label="Lifecycle status"
              value={data ? statusMeta(data.status).label : undefined}
            />
            <div className="col-span-2 sm:col-span-3">
              <Field label="Registered address" value={data?.address} />
            </div>
            <Field
              label="Linked records"
              value={data ? String(data.linked_records_count) : undefined}
            />
          </dl>
        )}
      </CardBody>
    </Card>
  );
}

function LinkedRecordsSection({ data, loading }: { data?: BusinessProfile; loading: boolean }) {
  return (
    <Card>
      <CardHeader
        title="Linked source records"
        description="Departmental records resolved to this identity"
      />
      {loading ? (
        <CardBody>
          <Skeleton className="h-24 w-full" />
        </CardBody>
      ) : !data || data.linked_records.length === 0 ? (
        <EmptyState title="No linked records" />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Source system</Th>
              <Th>Record name</Th>
              <Th className="w-24">Confidence</Th>
              <Th className="w-36">Link</Th>
            </tr>
          </thead>
          <tbody>
            {data.linked_records.map((r) => {
              const dec = decisionMeta(r.decision);
              return (
                <Tr key={r.link_id}>
                  <Td>
                    <div className="text-ink">{r.source_system ?? "—"}</div>
                    <div className="text-[12px] text-ink-subtle">
                      {r.department ?? ""}
                    </div>
                  </Td>
                  <Td>
                    <div>
                      <span className="text-ink">{r.extracted_name ?? "—"}</span>
                      {r.external_id && (
                        <span className="ml-1.5 font-mono text-[11px] text-ink-subtle">
                          #{r.external_id}
                        </span>
                      )}
                    </div>
                    {(r.extracted_address || r.extracted_pin) && (
                      <div className="text-[12px] text-ink-subtle">
                        {[r.extracted_address, r.extracted_pin]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    )}
                  </Td>
                  <Td className="tabular-nums text-ink-muted">
                    {r.confidence != null ? `${Math.round(r.confidence * 100)}%` : "—"}
                  </Td>
                  <Td>
                    <Badge tone={dec.tone}>{dec.label}</Badge>
                  </Td>
                </Tr>
              );
            })}
          </tbody>
        </Table>
      )}
    </Card>
  );
}

function TimelineSection({ data, loading }: { data?: BusinessProfile; loading: boolean }) {
  return (
    <Card>
      <CardHeader
        title="Activity timeline"
        description="Operational signals across departments"
      />
      <CardBody>
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : !data || data.timeline.length === 0 ? (
          <EmptyState title="No activity recorded" />
        ) : (
          <ol className="relative space-y-3 border-l border-line pl-4">
            {data.timeline.map((e, i) => {
              const positive = (e.score ?? 0) >= 0;
              return (
                <li key={i} className="relative">
                  <span
                    className="absolute -left-[21px] top-1 h-2 w-2 rounded-full ring-2 ring-surface"
                    style={{ background: positive ? "#15803d" : "#b91c1c" }}
                    aria-hidden
                  />
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-[13px] font-medium text-ink">
                      {titleCase(e.event)}
                    </span>
                    <span className="text-[12px] text-ink-subtle">
                      {formatDate(e.date)}
                    </span>
                  </div>
                  {e.score != null && (
                    <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-surface-muted">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(Math.abs(e.score) * 100, 100)}%`,
                          background: positive ? "#15803d" : "#b91c1c",
                        }}
                      />
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        )}
      </CardBody>
    </Card>
  );
}

function StatusSection({
  data,
  loading,
  result,
}: {
  data?: BusinessProfile;
  loading: boolean;
  result: StatusResult | null;
}) {
  return (
    <Card>
      <CardHeader title="Status inference" description="Explainable lifecycle state" />
      <CardBody>
        {loading ? (
          <Skeleton className="h-24 w-full" />
        ) : (
          <>
            <div className="flex items-center gap-2">
              {data && <StatusBadge status={data.status} />}
              {data?.status_history.length ? (
                <span className="text-[12px] text-ink-subtle">
                  updated {formatDate(data.status_history.at(-1)?.date)}
                </span>
              ) : null}
            </div>

            {result && (
              <div className="mt-3 rounded-md border border-line bg-surface-muted p-3">
                <div className="text-[12px] font-medium text-ink-muted">
                  Why — confidence {result.confidence.toFixed(2)}
                </div>
                <ul className="mt-1.5 space-y-1 text-[12px] text-ink-muted">
                  {result.reasons.slice(0, 6).map((r, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-ink-subtle">·</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data && data.status_history.length > 1 && (
              <div className="mt-3">
                <div className="mb-1.5 text-[12px] text-ink-muted">History</div>
                <ul className="space-y-1">
                  {data.status_history
                    .slice()
                    .reverse()
                    .slice(0, 5)
                    .map((h, i) => (
                      <li
                        key={i}
                        className="flex items-center justify-between text-[12px]"
                      >
                        <span className="text-ink">{statusMeta(h.status).label}</span>
                        <span className="text-ink-subtle">
                          {h.confidence != null && `${h.confidence.toFixed(2)} · `}
                          {formatDateTime(h.date)}
                        </span>
                      </li>
                    ))}
                </ul>
              </div>
            )}

            {!result && (
              <p className="mt-3 text-[12px] text-ink-subtle">
                Use “Recompute status” to see the full reasoning.
              </p>
            )}
          </>
        )}
      </CardBody>
    </Card>
  );
}

function EvidenceSection({ data, loading }: { data?: BusinessProfile; loading: boolean }) {
  return (
    <Card>
      <CardHeader title="Matching evidence" description="Signals behind the identity" />
      <CardBody>
        {loading ? (
          <Skeleton className="h-20 w-full" />
        ) : !data || data.matching_evidence.length === 0 ? (
          <p className="text-[13px] text-ink-subtle">
            No matching signals recorded.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.matching_evidence.map((e, i) => (
              <li key={i} className="flex items-start justify-between gap-3 text-[13px]">
                <span className="text-ink-muted">{e.signal}</span>
                <span className="text-right font-medium text-ink">{e.value}</span>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
