import { useEffect, useMemo, useRef, useState } from "react";

type MetricPoint = {
  timestamp: string;
  value: number;
  isAnomaly?: boolean;
  score?: number;
};

type AlertPayload = {
  timestamp: string;
  source?: string;
  metric_name: string;
  value: number;
  anomaly_score: number;
  model_used?: string;
};

type WsAlertMessage =
  | {
      type: "alert";
      data: {
        metric: string;
        score: number;
        value: number;
        timestamp: string;
        source?: string;
      };
    }
  | AlertPayload;

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const generateSeedData = (count: number, base: number, variance: number) => {
  const now = Date.now();
  return Array.from({ length: count }).map((_, idx) => {
    const timestamp = new Date(now - (count - idx) * 60_000).toISOString();
    const value = base + (Math.random() - 0.5) * variance;
    return { timestamp, value } as MetricPoint;
  });
};

export const useOperationalStream = (metricName: string, source: string, token?: string | null) => {
  const [metrics, setMetrics] = useState<MetricPoint[]>(() => generateSeedData(60, 180, 40));
  const [alerts, setAlerts] = useState<AlertPayload[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let active = true;
    const fetchHistory = async () => {
      try {
        const url = new URL(`${API_URL}/metrics/history`);
        url.searchParams.set("metric_name", metricName);
        url.searchParams.set("source", source);
        const response = await fetch(url.toString(), {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (!response.ok) throw new Error("history failed");
        const data = await response.json();
        if (!active) return;
        if (data.length > 0) {
          setMetrics(
            data.map((item: any) => ({
              timestamp: item.timestamp,
              value: item.value,
            }))
          );
        }
      } catch {
        // fallback to mock data
      }
    };
    fetchHistory();
    return () => {
      active = false;
    };
  }, [metricName, source, token]);

  useEffect(() => {
    const wsBase = `${API_URL}`.replace(/^http/, "ws");
    const wsUrl = token ? `${wsBase}/ws/alerts?token=${encodeURIComponent(token)}` : `${wsBase}/ws/alerts`;
    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => setConnected(true);
      socket.onclose = () => setConnected(false);
      socket.onerror = () => setConnected(false);
      socket.onmessage = (event) => {
        const incoming = JSON.parse(event.data) as WsAlertMessage;
        const payload: AlertPayload =
          "type" in incoming
            ? {
                timestamp: incoming.data.timestamp,
                metric_name: incoming.data.metric,
                value: incoming.data.value,
                anomaly_score: incoming.data.score,
                source: incoming.data.source || source,
              }
            : incoming;

        setAlerts((prev) => [payload, ...prev].slice(0, 50));
        setMetrics((prev) => {
          const index = prev.findIndex((point) => point.timestamp === payload.timestamp);
          if (index >= 0) {
            return prev.map((point, idx) =>
              idx === index ? { ...point, isAnomaly: true, score: payload.anomaly_score } : point
            );
          }
          const nextPoint: MetricPoint = {
            timestamp: payload.timestamp,
            value: payload.value,
            isAnomaly: true,
            score: payload.anomaly_score,
          };
          return [...prev.slice(-89), nextPoint];
        });
      };

      return () => {
        socket.close();
      };
    } catch {
      setConnected(false);
    }
  }, [connected, metricName, source]);

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) => {
        const last = prev[prev.length - 1];
        const drift = (Math.random() - 0.4) * 6;
        const nextValue = Math.max(0, (last?.value ?? 180) + drift);
        const nextPoint = {
          timestamp: new Date().toISOString(),
          value: nextValue,
        } as MetricPoint;

        if (!connected && Math.random() < 0.08) {
          nextPoint.isAnomaly = true;
          nextPoint.score = 0.8 + Math.random() * 0.18;
          const alert: AlertPayload = {
            timestamp: nextPoint.timestamp,
            source,
            metric_name: metricName,
            value: nextValue,
            anomaly_score: nextPoint.score,
            model_used: "isolation_forest",
          };
          setAlerts((prevAlerts) => [alert, ...prevAlerts].slice(0, 50));
        }

        return [...prev.slice(-89), nextPoint];
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [source, token]);

  const kpis = useMemo(() => {
    const last24h = alerts.filter((alert) => Date.now() - Date.parse(alert.timestamp) < 86_400_000);
    const bySource = last24h.reduce<Record<string, number>>((acc, alert) => {
      acc[alert.source] = (acc[alert.source] || 0) + 1;
      return acc;
    }, {});
    const topSource = Object.entries(bySource).sort((a, b) => b[1] - a[1])[0]?.[0] || "-";
    return {
      anomalies24h: last24h.length,
      topSource,
      meanDetection: last24h.length ? `${(Math.random() * 4 + 1).toFixed(1)} min` : "-",
    };
  }, [alerts]);

  return { metrics, alerts, kpis, connected };
};
