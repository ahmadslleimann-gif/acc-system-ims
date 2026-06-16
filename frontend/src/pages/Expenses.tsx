import { useTranslation } from "react-i18next";
import { useList, useAction } from "../api/hooks";
import DataTable from "../components/DataTable";

interface Expense {
  id: number;
  doc_no: string;
  description: string;
  category_name: string;
  date: string;
  total: string;
  status: string;
}

const flow: Record<string, { action: string; label: string }[]> = {
  DRAFT: [{ action: "submit", label: "Submit" }],
  PENDING: [
    { action: "approve", label: "Approve" },
    { action: "reject", label: "Reject" },
  ],
  APPROVED: [{ action: "post_expense", label: "Post" }],
};

export default function Expenses() {
  const { t } = useTranslation();
  const { data, isLoading } = useList<Expense>("expenses/", { page_size: 100 });
  const action = useAction("expenses/");

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">{t("expenses")}</h1>
      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "doc_no", label: "No." },
          { key: "description", label: "Description" },
          { key: "category_name", label: "Category" },
          { key: "date", label: "Date" },
          { key: "total", label: "Total", render: (r) => Number(r.total).toLocaleString() },
          { key: "status", label: "Status" },
          {
            key: "actions",
            label: "",
            render: (r) => (
              <div className="flex gap-2">
                {(flow[r.status] || []).map((f) => (
                  <button key={f.action} className="btn-ghost text-xs" onClick={() => action.mutate({ id: r.id, action: f.action })}>
                    {f.label}
                  </button>
                ))}
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
