import React, { useState } from "react";
import MetricFilterBar from "./components/MetricFilterBar";
import KPIBox from "./components/KPIBox";
import AnomalyChart from "./components/AnomalyChart";
import AnomalyAlertFeed from "./components/AnomalyAlertFeed";
import MetricDetailPanel from "./components/MetricDetailPanel";
import { useOperationalStream } from "./hooks/useOperationalStream";
import AuthPanel from "./components/AuthPanel";
import { useAuth } from "./hooks/useAuth";

const App: React.FC = () => {
  const [source, setSource] = useState("finance");
  const [metric, setMetric] = useState("daily_expense");
  const auth = useAuth();
  const { metrics, alerts, kpis, connected } = useOperationalStream(metric, source, auth.token);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Operational Anomaly Radar</p>
          <h1>Radar operacional com IA em tempo real</h1>
        </div>
        <div className="header-actions">
          <MetricFilterBar
            source={source}
            metric={metric}
            onChangeSource={setSource}
            onChangeMetric={setMetric}
          />
          <AuthPanel
            isAuthenticated={auth.isAuthenticated}
            loading={auth.loading}
            error={auth.error}
            onLogin={auth.login}
            onLogout={auth.logout}
          />
        </div>
      </header>

      <section className="kpi-row">
        <KPIBox label="Anomalias 24h" value={kpis.anomalies24h} hint="últimas 24 horas" accent="rose" />
        <KPIBox label="Setor crítico" value={kpis.topSource} hint="maior incidência" accent="amber" />
        <KPIBox label="Tempo médio" value={kpis.meanDetection} hint="até detecção" accent="cyan" />
        <KPIBox label="Qualidade do stream" value={connected ? "live" : "simulado"} hint="websocket" accent="amber" />
      </section>

      <section className="main-grid">
        <div className="left-column">
          <AnomalyChart data={metrics} title="Comportamento da métrica" />
          <MetricDetailPanel metric={metric} source={source} connected={connected} />
        </div>
        <div className="right-column">
          <AnomalyAlertFeed alerts={alerts} />
        </div>
      </section>
    </div>
  );
};

export default App;
