import React from "react";

type Alert = {
  timestamp: string;
  source?: string;
  metric_name: string;
  value: number;
  anomaly_score: number;
  model_used?: string;
};

type Props = {
  alerts: Alert[];
};

const AnomalyAlertFeed: React.FC<Props> = ({ alerts }) => {
  return (
    <div className="alert-feed">
      <div className="feed-header">
        <h3>Alertas Recentes</h3>
        <span className="badge">real-time</span>
      </div>
      <div className="feed-list">
        {alerts.length === 0 && <p className="feed-empty">Nenhum alerta crítico nas últimas horas.</p>}
        {alerts.map((alert, index) => (
          <div key={`${alert.timestamp}-${index}`} className="alert-item">
            <div>
              <strong>{alert.metric_name}</strong>
              <span>{alert.source || "stream"}</span>
            </div>
            <div>
              <span className="score">{alert.anomaly_score.toFixed(2)}</span>
              <span className="value">{alert.value.toFixed(2)}</span>
            </div>
            <small>{new Date(alert.timestamp).toLocaleTimeString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AnomalyAlertFeed;
