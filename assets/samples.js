document.addEventListener("DOMContentLoaded", () => {
  const cell = (t, v) => `<${t}>${v}</${t}>`;
  const render = (table, d) => {
    table.innerHTML =
      "<thead><tr>" + d.columns.map((c) => cell("th", c)).join("") + "</tr></thead>" +
      "<tbody>" + d.rows.map((r) => "<tr>" + r.map((v) => cell("td", v)).join("") + "</tr>").join("") + "</tbody>";
  };

  fetch("data/sample_tables.json")
    .then((r) => r.json())
    .then((d) => {
      render(document.getElementById("sample-raw"), d.raw);
      render(document.getElementById("sample-cleaned"), d.cleaned);
    })
    .catch((err) => console.error("Failed to load sample tables", err));
});
