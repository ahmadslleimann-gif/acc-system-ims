import { useTranslation } from "react-i18next";
import { useList } from "../api/hooks";
import DataTable from "../components/DataTable";

interface Account {
  id: number;
  code: string;
  name_en: string;
  name_ar: string;
  type: string;
  normal_balance: string;
  is_postable: boolean;
  is_active: boolean;
}

export default function ChartOfAccounts() {
  const { t } = useTranslation();
  const { data, isLoading } = useList<Account>("coa/accounts/", { ordering: "code", page_size: 200 });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">{t("chartOfAccounts")}</h1>
      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "code", label: "Code", render: (r) => <span className="font-mono">{r.code}</span> },
          { key: "name_en", label: "Name" },
          { key: "name_ar", label: "الاسم" },
          { key: "type", label: "Type" },
          { key: "normal_balance", label: "Normal" },
          {
            key: "is_postable",
            label: "Postable",
            render: (r) => (r.is_postable ? "✓" : "—"),
          },
          {
            key: "is_active",
            label: "Status",
            render: (r) => (
              <span className={r.is_active ? "text-brand-700" : "text-slate-400"}>
                {r.is_active ? "Active" : "Inactive"}
              </span>
            ),
          },
        ]}
      />
    </div>
  );
}
