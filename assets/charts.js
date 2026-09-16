const F1_RED = "#e10600";
const TEXT = "#a7a7b0";
const GRID = "rgba(255,255,255,0.07)";
const F1_WHITE = "#e8e8ec";
const F1_SILVER = "#8c8c96";
const F1_GOLD = "#ffb800";
const F1_TEAL = "#00d2be";
const F1_BLUE = "#3671c6";
const LINE_COLORS = [F1_BLUE, "#6cd3bf", F1_RED, "#ff8700", "#ff87bc", "#358c75"]; // RBR, MER, FER, MCL, ALP, AMR

Chart.defaults.font.family = '"Titillium Web", "Helvetica Neue", Arial, sans-serif';
Chart.defaults.font.size = 12;
Chart.defaults.color = TEXT;
Chart.defaults.borderColor = GRID;

let CHART_DATA = null;
const activeCharts = {};

function baseOptions(extra) {
  return Object.assign(
    {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { grid: { color: GRID } },
        y: { grid: { color: GRID } },
      },
    },
    extra || {}
  );
}

function avgFinishOptions() {
  return baseOptions({
    scales: {
      x: { grid: { color: GRID } },
      y: { beginAtZero: true, title: { display: true, text: "Avg finishing position (lower is better)" }, grid: { color: GRID } },
    },
  });
}

function makeOrUpdate(id, config) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  if (activeCharts[id]) {
    activeCharts[id].destroy();
  }
  activeCharts[id] = new Chart(canvas.getContext("2d"), config);
}

function seasonKey(season) {
  return season === "all" ? "all" : String(season);
}

function renderAll(season) {
  const k = seasonKey(season);
  const d = CHART_DATA;

  makeOrUpdate("chart-01", {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Driver result",
          data: d.grid_vs_final[k],
          backgroundColor: "rgba(225,6,0,0.45)",
          pointRadius: 3,
        },
      ],
    },
    options: baseOptions({
      scales: {
        x: { title: { display: true, text: "Starting grid position" }, grid: { color: GRID } },
        y: { title: { display: true, text: "Final race position" }, reverse: true, grid: { color: GRID } },
      },
    }),
  });

  const z = d.avg_position_by_grid_zone[k];
  makeOrUpdate("chart-02", {
    type: "bar",
    data: { labels: z.labels, datasets: [{ label: "Avg final position", data: z.values, backgroundColor: F1_WHITE }] },
    options: avgFinishOptions(),
  });

  const c3 = d.avg_points_by_constructor[k];
  makeOrUpdate("chart-03", {
    type: "bar",
    data: { labels: c3.labels, datasets: [{ label: "Avg points per race", data: c3.values, backgroundColor: F1_RED }] },
    options: baseOptions({ indexAxis: "y" }),
  });

  const c4 = d.avg_position_by_pitstops[k];
  makeOrUpdate("chart-04", {
    type: "bar",
    data: { labels: c4.labels, datasets: [{ label: "Avg final position", data: c4.values, backgroundColor: F1_BLUE }] },
    options: avgFinishOptions(),
  });

  const c5 = d.pitstop_count_distribution[k];
  makeOrUpdate("chart-05", {
    type: "bar",
    data: { labels: c5.labels, datasets: [{ label: "Driver-races", data: c5.values, backgroundColor: F1_SILVER }] },
    options: baseOptions(),
  });

  const c6 = d.pitstop_duration_histogram[k];
  makeOrUpdate("chart-06", {
    type: "bar",
    data: { labels: c6.labels, datasets: [{ label: "Driver-races", data: c6.values, backgroundColor: F1_TEAL }] },
    options: baseOptions(),
  });

  const c7 = d.first_pitstop_vs_position[k];
  makeOrUpdate("chart-07", {
    type: "scatter",
    data: {
      datasets: [
        { label: "Scored points", data: c7.scored, backgroundColor: "rgba(0,210,190,0.6)", pointRadius: 3 },
        { label: "No points", data: c7.not_scored, backgroundColor: "rgba(140,140,150,0.4)", pointRadius: 3 },
      ],
    },
    options: baseOptions({
      plugins: { legend: { display: true, position: "top", labels: {} } },
      scales: {
        x: { title: { display: true, text: "Lap of first pit stop" }, grid: { color: GRID } },
        y: { title: { display: true, text: "Final position" }, reverse: true, grid: { color: GRID } },
      },
    }),
  });

  if (!activeCharts["chart-08"]) {
    const c8 = d.season_points_top_constructors;
    makeOrUpdate("chart-08", {
      type: "line",
      data: {
        labels: c8.labels,
        datasets: c8.datasets.map((ds, i) => ({
          label: ds.label,
          data: ds.data,
          borderColor: LINE_COLORS[i % LINE_COLORS.length],
          backgroundColor: LINE_COLORS[i % LINE_COLORS.length],
          fill: false,
          tension: 0,
          pointRadius: 4,
        })),
      },
      options: baseOptions({ plugins: { legend: { display: true, position: "bottom", labels: { boxWidth: 12 } } } }),
    });
  }

  const c9 = d.dnf_rate_by_constructor[k];
  makeOrUpdate("chart-09", {
    type: "bar",
    data: { labels: c9.labels, datasets: [{ label: "DNF rate (%)", data: c9.values, backgroundColor: F1_RED }] },
    options: baseOptions({ indexAxis: "y" }),
  });

  makeOrUpdate("chart-10", {
    type: "scatter",
    data: {
      datasets: [
        { label: "Driver", data: d.quali_vs_grid[k], backgroundColor: "rgba(54,113,198,0.55)", pointRadius: 3 },
      ],
    },
    options: baseOptions({
      scales: {
        x: { title: { display: true, text: "Qualifying position" }, grid: { color: GRID } },
        y: { title: { display: true, text: "Actual starting grid" }, grid: { color: GRID } },
      },
    }),
  });

  if (!activeCharts["chart-11"]) {
    const c11 = d.dnf_rate_by_temperature;
    makeOrUpdate("chart-11", {
      type: "bar",
      data: { labels: c11.labels, datasets: [{ label: "DNF rate (%)", data: c11.values, backgroundColor: F1_GOLD }] },
      options: baseOptions(),
    });
  }

  if (!activeCharts["chart-12"]) {
    const c12 = d.position_by_tyre_compounds;
    makeOrUpdate("chart-12", {
      type: "bar",
      data: { labels: c12.labels, datasets: [{ label: "Avg final position", data: c12.values, backgroundColor: F1_WHITE }] },
      options: avgFinishOptions(),
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // wait for the font or canvas text falls back to Arial
  Promise.all([fetch("data/chart_data.json").then((r) => r.json()), document.fonts.ready])
    .then(([data]) => data)
    .then((data) => {
      CHART_DATA = data;
      renderAll("all");
      const select = document.getElementById("season-filter");
      if (select) {
        select.addEventListener("change", (e) => renderAll(e.target.value));
      }
    })
    .catch((err) => {
      console.error("Failed to load chart data", err);
    });
});
