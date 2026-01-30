import React from "react";

type Props = {
  label: string;
  value: string | number;
  hint?: string;
  accent?: "amber" | "cyan" | "rose";
};

const KPIBox: React.FC<Props> = ({ label, value, hint, accent = "amber" }) => {
  return (
    <div className={`kpi-box kpi-${accent}`}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      {hint && <span className="kpi-hint">{hint}</span>}
    </div>
  );
};

export default KPIBox;