import React from "react";

const sources = ["finance", "logistics", "production", "it"];
const metrics = ["daily_expense", "delivery_time", "output_rate", "latency_ms"];

type Props = {
  source: string;
  metric: string;
  onChangeSource: (value: string) => void;
  onChangeMetric: (value: string) => void;
};

const MetricFilterBar: React.FC<Props> = ({ source, metric, onChangeSource, onChangeMetric }) => {
  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label>Setor</label>
        <select value={source} onChange={(e) => onChangeSource(e.target.value)}>
          {sources.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>
      <div className="filter-group">
        <label>Métrica</label>
        <select value={metric} onChange={(e) => onChangeMetric(e.target.value)}>
          {metrics.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>
      <div className="filter-group">
        <label>Janela</label>
        <button className="ghost">Últimas 2h</button>
      </div>
    </div>
  );
};

export default MetricFilterBar;