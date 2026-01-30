import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

export type ChartPoint = {
  timestamp: string;
  value: number;
  isAnomaly?: boolean;
  score?: number;
};

type Props = {
  data: ChartPoint[];
  title: string;
};

const AnomalyChart: React.FC<Props> = ({ data, title }) => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    if (data.length === 0) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = 280;
    const margin = { top: 24, right: 24, bottom: 32, left: 48 };

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("width", width).attr("height", height);

    const defs = svg.append("defs");
    const gradient = defs
      .append("linearGradient")
      .attr("id", "lineGradient")
      .attr("x1", "0%")
      .attr("x2", "100%")
      .attr("y1", "0%")
      .attr("y2", "0%");

    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#2be4f5");
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#ffb86b");

    const parsed = data.map((d) => ({
      date: new Date(d.timestamp),
      value: d.value,
      isAnomaly: d.isAnomaly,
      score: d.score,
    }));

    const xScale = d3
      .scaleTime()
      .domain(d3.extent(parsed, (d) => d.date) as [Date, Date])
      .range([margin.left, width - margin.right]);

    const yExtent = d3.extent(parsed, (d) => d.value) as [number, number];
    const yScale = d3
      .scaleLinear()
      .domain([Math.min(yExtent[0] * 0.95, yExtent[0] - 5), yExtent[1] * 1.05])
      .range([height - margin.bottom, margin.top]);

    const line = d3
      .line<{ date: Date; value: number }>()
      .x((d) => xScale(d.date))
      .y((d) => yScale(d.value))
      .curve(d3.curveMonotoneX);

    svg
      .append("path")
      .datum(parsed)
      .attr("class", "chart-line")
      .attr("d", line);

    const tooltip = d3.select(container).select<HTMLDivElement>(".chart-tooltip");

    const points = svg
      .append("g")
      .selectAll("circle")
      .data(parsed)
      .enter()
      .append("circle")
      .attr("cx", (d) => xScale(d.date))
      .attr("cy", (d) => yScale(d.value))
      .attr("r", (d) => (d.isAnomaly ? 6 : 3))
      .attr("class", (d) => (d.isAnomaly ? "chart-point anomaly" : "chart-point"))
      .on("mouseenter", (event, d) => {
        tooltip
          .style("opacity", 1)
          .style("transform", "translateY(0)")
          .html(
            `<strong>${d.value.toFixed(2)}</strong><div>${d.date.toLocaleTimeString()}</div>${
              d.isAnomaly ? `<span>Score: ${(d.score ?? 0).toFixed(2)}</span>` : ""
            }`
          );
        const [x, y] = d3.pointer(event, container);
        tooltip.style("left", `${x + 12}px`).style("top", `${y - 16}px`);
      })
      .on("mouseleave", () => {
        tooltip.style("opacity", 0).style("transform", "translateY(6px)");
      });

    points.append("title").text((d) => `${d.value.toFixed(2)}`);

    svg
      .append("g")
      .attr("class", "axis")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(xScale).ticks(5));

    svg
      .append("g")
      .attr("class", "axis")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(yScale).ticks(5));

    const zoomed = (event: d3.D3ZoomEvent<Element, unknown>) => {
      const newX = event.transform.rescaleX(xScale);
      svg.selectAll(".axis").remove();
      svg
        .append("g")
        .attr("class", "axis")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(newX).ticks(5));
      svg
        .append("g")
        .attr("class", "axis")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(yScale).ticks(5));
      svg.selectAll(".chart-line").attr("d", line.x((d) => newX(d.date)) as any);
      svg
        .selectAll(".chart-point")
        .attr("cx", (d: any) => newX(d.date))
        .attr("cy", (d: any) => yScale(d.value));
    };

    const zoom = d3
      .zoom()
      .scaleExtent([1, 6])
      .translateExtent([
        [margin.left, 0],
        [width - margin.right, height],
      ])
      .on("zoom", zoomed);

    svg.call(zoom as any).on("wheel.zoom", null).on("dblclick.zoom", null);
    svg.on("dblclick", (event) => zoom.scaleBy(svg.transition().duration(250), 1.4, d3.pointer(event)));
  }, [data]);

  return (
    <div className="chart-card" ref={containerRef}>
      <div className="chart-header">
        <h3>{title}</h3>
        <span className="chip">zoom</span>
      </div>
      <svg ref={svgRef}></svg>
      <div className="chart-tooltip" />
    </div>
  );
};

export default AnomalyChart;
