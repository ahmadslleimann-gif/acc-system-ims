import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

interface Supplier { id: number; name: string; code: string; }
interface Link {
  id: number;
  supplier: number;
  supplier_name: string;
  supplier_code: string;
  supplier_item_code: string;
  cost: string;
  last_purchase_price: string;
  is_preferred: boolean;
}

/** Manage which suppliers sell a product (with each supplier's cost) + print the list. */
export default function ProductSuppliersPanel({
  product,
  productName,
  suppliers,
  onClose,
}: {
  product: number;
  productName: string;
  suppliers: Supplier[];
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const key = ["inventory/product-suppliers/", product];

  const { data, isLoading } = useQuery({
    queryKey: key,
    queryFn: async () => (await api.get(`/inventory/product-suppliers/?product=${product}&page_size=200`)).data,
  });
  const links: Link[] = data?.results || data || [];

  const [supplier, setSupplier] = useState("");
  const [cost, setCost] = useState("");
  const [itemCode, setItemCode] = useState("");

  const add = useMutation({
    mutationFn: async () =>
      (await api.post("/inventory/product-suppliers/", {
        product,
        supplier: Number(supplier),
        cost: cost || "0",
        supplier_item_code: itemCode,
      })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key });
      setSupplier(""); setCost(""); setItemCode("");
    },
  });

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/inventory/product-suppliers/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  });

  async function printPdf() {
    const res = await api.get(`/inventory/products/${product}/suppliers-pdf/`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data as Blob);
    window.open(url, "_blank");
  }

  return (
    <div className="card p-4 space-y-3 border-brand-200">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-700">{t("supplier")}s — {productName}</h3>
        <div className="flex gap-2">
          <button className="btn-ghost text-xs" onClick={printPdf}>🖨 PDF</button>
          <button className="btn-ghost text-xs" onClick={onClose}>✕</button>
        </div>
      </div>

      <form
        className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end"
        onSubmit={(e) => { e.preventDefault(); add.mutate(); }}
      >
        <select className="input" value={supplier} onChange={(e) => setSupplier(e.target.value)} required>
          <option value="">{t("supplier")}…</option>
          {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <input className="input" type="number" step="0.01" placeholder="Cost" value={cost} onChange={(e) => setCost(e.target.value)} />
        <input className="input" placeholder="Supplier item code" value={itemCode} onChange={(e) => setItemCode(e.target.value)} />
        <button className="btn-primary text-sm" disabled={add.isPending || !supplier}>+ {t("addLine")}</button>
      </form>

      {isLoading ? (
        <div className="text-slate-400 text-sm">Loading…</div>
      ) : links.length === 0 ? (
        <div className="text-slate-400 text-sm">No suppliers linked yet.</div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-500 border-b">
              <th className="text-start py-1">{t("supplier")}</th>
              <th className="text-start">Item code</th>
              <th className="text-end">Cost</th>
              <th className="text-end">Last buy</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {links.map((l) => (
              <tr key={l.id} className="border-b border-slate-100">
                <td className="py-1">{l.supplier_name} <span className="text-slate-400">({l.supplier_code})</span></td>
                <td>{l.supplier_item_code || "—"}</td>
                <td className="text-end">{Number(l.cost).toLocaleString()}</td>
                <td className="text-end">{Number(l.last_purchase_price).toLocaleString()}</td>
                <td className="text-end">
                  <button className="text-red-500 text-xs" onClick={() => remove.mutate(l.id)}>✕</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
