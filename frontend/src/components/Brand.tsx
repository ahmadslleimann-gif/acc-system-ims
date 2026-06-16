import { useState } from "react";
import { useTranslation } from "react-i18next";

/**
 * Brand block: company logo (/logo.png) + name + tagline.
 * Falls back to an "IMS" monogram if the image is missing.
 * Logo file lives at: frontend/public/logo.png
 */
export default function Brand({
  layout = "vertical",
  variant = "light",
  showText = true,
}: {
  layout?: "vertical" | "horizontal";
  variant?: "light" | "dark";
  showText?: boolean;
}) {
  const { t } = useTranslation();
  const [imgOk, setImgOk] = useState(true);
  const titleColor = variant === "light" ? "text-white" : "text-slate-800";
  const subColor = variant === "light" ? "text-slate-300" : "text-slate-500";

  const img = imgOk ? (
    <img
      src="/logo.png"
      alt={t("brandName")}
      onError={() => setImgOk(false)}
      className="w-full h-full object-cover"
    />
  ) : (
    <div className="w-full h-full grid place-items-center bg-gradient-to-br from-slate-500 to-slate-900 text-white font-extrabold tracking-wide">
      IMS
    </div>
  );

  if (layout === "horizontal") {
    return (
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 shrink-0 rounded-xl overflow-hidden bg-white shadow-sm ring-1 ring-black/5">
          {img}
        </div>
        {showText && (
          <div className="leading-tight">
            <div className={`font-bold ${titleColor}`}>{t("brandName")}</div>
            <div className={`text-[11px] ${subColor}`}>{t("tagline")}</div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center text-center gap-2.5">
      <div className="w-full aspect-square rounded-2xl overflow-hidden bg-white shadow-sm ring-1 ring-black/5">
        {img}
      </div>
      {showText && (
        <div className="leading-tight">
          <div className={`font-bold tracking-wide ${titleColor}`}>{t("brandName")}</div>
          <div className={`text-[11px] ${subColor}`}>{t("tagline")}</div>
        </div>
      )}
    </div>
  );
}
