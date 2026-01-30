import React from "react";

type Props = {
  metric: string;
  source: string;
  connected: boolean;
};

const MetricDetailPanel: React.FC<Props> = ({ metric, source, connected }) => {
  return (
    <div className="detail-panel">
      <div>
        <h3>Detalhes da Métrica</h3>
        <p>
          <strong>{metric}</strong> · {source}
        </p>
      </div>
      <div className="detail-grid">
        <div>
          <span>Status do Stream</span>
          <strong className={connected ? "ok" : "warn"}>{connected ? "Ativo" : "Simulado"}</strong>
        </div>
        <div>
          <span>Modelo</span>
          <strong>Isolation Forest</strong>
        </div>
        <div>
          <span>Threshold</span>
          <strong>0.85</strong>
        </div>
        <div>
          <span>Janela</span>
          <strong>50 pontos</strong>
        </div>
      </div>
    </div>
  );
};

export default MetricDetailPanel;