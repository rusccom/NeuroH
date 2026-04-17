export function createCharts(root) {
  if (window.echarts?.init) {
    const chart = window.echarts.init(root);
    chart.setOption(baseOption([]));
    return {
      update(history) {
        chart.setOption(baseOption(history));
      },
    };
  }
  return {
    update(history) {
      root.textContent = JSON.stringify(history.at(-1) ?? {}, null, 2);
    },
  };
}

function baseOption(history) {
  const labels = history.map((_, index) => index);
  return {
    backgroundColor: "transparent",
    textStyle: { color: "#edf3f8" },
    legend: { textStyle: { color: "#edf3f8" } },
    tooltip: {},
    xAxis: { type: "category", data: labels },
    yAxis: { type: "value" },
    series: [
      line("energy_deficit", history, "#5ce1a5"),
      line("water_deficit", history, "#ff7b54"),
      line("uncertainty", history, "#ffb84d"),
      line("selected_confidence", history, "#8cc8ff"),
    ],
  };
}

function line(key, history, color) {
  return {
    type: "line",
    smooth: true,
    name: key,
    showSymbol: false,
    lineStyle: { width: 2, color },
    data: history.map((item) => item[key] ?? 0),
  };
}
