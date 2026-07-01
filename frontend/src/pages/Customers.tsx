import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useList, useCreate } from "../api/hooks";
import DataTable from "../components/DataTable";
import SearchBar from "../components/SearchBar";
import { useAuth } from "../auth/AuthContext";

interface Customer {
  id: number;
  code: string;
  name: string;
  phone: string;
  email: string;
  balance: string;
  is_active: boolean;
}

export default function Customers() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const canAdd = isAdmin || can("customers.add_customer");
  const [search, setSearch] = useState("");
  const [active, setActive] = useState("");
  const params: Record<string, unknown> = { page_size: 100 };
  if (search) params.search = search;
  if (active) params.is_active = active;
  const { data, isLoading } = useList<Customer>("customers/", params);
  const create = useCreate<Customer>("customers/");
  const [form, setForm] = useState({ code: "", name: "", phone: "", email: "" });
  const [open, setOpen] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await create.mutateAsync(form);
    setForm({ code: "", name: "", phone: "", email: "" });
    setOpen(false);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">{t("customers")}</h1>
        {canAdd && (
          <button className="btn-primary" onClick={() => setOpen((o) => !o)}>
            + {t("newRecord")}
          </button>
        )}
      </div>

      {open && (
        <form onSubmit={submit} className="card p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <input className="input" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input className="input" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="input" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <button className="btn-primary col-span-2 md:col-span-1" disabled={create.isPending}>
            {t("save")}
          </button>
        </form>
      )}

      <SearchBar
        onSearch={setSearch}
        placeholder={`${t("search")} (code, name, phone…)`}
        filters={[
          {
            value: active,
            onChange: setActive,
            options: [
              { label: t("all"), value: "" },
              { label: t("active"), value: "true" },
              { label: t("inactive"), value: "false" },
            ],
          },
        ]}
      />

      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "name", label: "Name" },
          { key: "phone", label: "Phone" },
          { key: "email", label: "Email" },
          { key: "balance", label: "Balance", render: (r) => <span className="font-medium">{Number(r.balance).toLocaleString()}</span> },
        ]}
      />
    </div>
  );
}
