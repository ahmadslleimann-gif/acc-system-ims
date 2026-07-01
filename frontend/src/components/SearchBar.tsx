import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

export interface FilterDef {
  value: string;
  onChange: (v: string) => void;
  options: { label: string; value: string }[];
}

/**
 * Debounced search box + optional filter dropdowns.
 * `onSearch` fires 300ms after the user stops typing.
 */
export default function SearchBar({
  onSearch,
  placeholder,
  filters = [],
}: {
  onSearch: (q: string) => void;
  placeholder?: string;
  filters?: FilterDef[];
}) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");

  useEffect(() => {
    const id = setTimeout(() => onSearch(q.trim()), 300);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <div className="relative">
        <span className="absolute inset-y-0 start-2 flex items-center text-slate-400 text-sm">🔍</span>
        <input
          className="input ps-7 w-60"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={placeholder || t("search")}
        />
      </div>
      {filters.map((f, i) => (
        <select key={i} className="input w-auto" value={f.value} onChange={(e) => f.onChange(e.target.value)}>
          {f.options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}
