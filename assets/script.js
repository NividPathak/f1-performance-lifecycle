document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("nav.tabs button");
  const panels = document.querySelectorAll(".tab-panel");

  function activate(tabId) {
    buttons.forEach((b) => b.classList.toggle("active", b.dataset.tab === tabId));
    panels.forEach((p) => p.classList.toggle("active", p.id === tabId));
    history.replaceState(null, "", "#" + tabId);
    document.dispatchEvent(new CustomEvent("tabchange", { detail: tabId }));
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      activate(btn.dataset.tab);
      window.scrollTo({ top: 0 });
    });
  });

  const initial = window.location.hash.replace("#", "");
  activate(document.getElementById(initial) ? initial : "introduction");
  // The hash matches a section id, so the browser would jump past the header on load.
  window.addEventListener("load", () => window.scrollTo(0, 0));

  const log = document.getElementById("cleaning-log-content");
  fetch("data/cleaning_log.txt")
    .then((r) => r.text())
    .then((t) => { log.textContent = t; })
    .catch(() => { log.textContent = "See data/cleaning_log.txt in the repo."; });
});
