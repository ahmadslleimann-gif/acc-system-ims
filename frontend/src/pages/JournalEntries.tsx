import { useTranslation } from "react-i18next";
import { useList, useAction } from "../api/hooks";
import DataTable from "../components/DataTable";
import { useAuth } from "../auth/AuthContext";

interface Entry {
  id: number;
  entry_no: string;
  entry_date: string;
  status: string;
  memo: string;
  total_debit: string;
  total_credit: string;
  source_type: string;
}

const statusColor: Record<string, string> = {
  DRAFT: "text-slate-500",
  POSTED: "text-brand-700",
  REVERSED: "text-red-600",
};

export default function JournalEntries() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const canManage = isAdmin || can("journal.change_journalentry");
  const { data, isLoading } = useList<Entry>("journal/entries/", { page_size: 100, ordering: "-entry_date" });
  const action = useAction("journal/entries/");

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">{t("journal")}</h1>
      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "entry_no", label: "No.", render: (r) => <span className="font-mono text-xs">{r.entry_no}</span> },
          { key: "entry_date", label: "Date" },
          { key: "memo", label: "Memo" },
          { key: "source_type", label: "Source" },
          { key: "total_debit", label: "Debit", render: (r) => Number(r.total_debit).toLocaleString() },
          { key: "status", label: "Status", render: (r) => <span className={statusColor[r.status]}>{r.status}</span> },
          {
            key: "actions",
            label: "",
            render: (r) =>
              !canManage ? null : r.status === "DRAFT" ? (
                <button className="btn-ghost text-xs" onClick={() => action.mutate({ id: r.id, action: "post_entry" })}>
                  Post
                </button>
              ) : r.status === "POSTED" ? (
                <button className="btn-ghost text-xs" onClick={() => action.mutate({ id: r.id, action: "reverse" })}>
                  Reverse
                </button>
              ) : null,
          },
        ]}
      />
    </div>
  );
}
