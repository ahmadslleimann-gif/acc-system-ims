import { useTranslation } from "react-i18next";
import { useList } from "../api/hooks";
import DataTable from "../components/DataTable";

interface CashAccount {
  id: number;
  name: string;
  kind: string;
  gl_code: string;
  balance: string;
}

export default function CashBanks() {
  const { t } = useTranslation();
  const { data, isLoading } = useList<CashAccount>("cashbanks/accounts/", { page_size: 100 });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">{t("cashBanks")}</h1>
      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "name", label: "Account" },
          { key: "kind", label: "Type" },
          { key: "gl_code", label: "GL Code", render: (r) => <span className="font-mono">{r.gl_code}</span> },
          { key: "balance", label: "Balance", render: (r) => Number(r.balance).toLocaleString() },
        ]}
      />
    </div>
  );
}
