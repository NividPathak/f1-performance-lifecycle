document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("nav.tabs button");
  const panels = document.querySelectorAll(".tab-panel");

  function activate(tabId) {
    buttons.forEach((b) => b.classList.toggle("active", b.dataset.tab === tabId));
    panels.forEach((p) => p.classList.toggle("active", p.id === tabId));
    history.replaceState(null, "", "#" + tabId);
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => activate(btn.dataset.tab));
  });

  const initial = window.location.hash.replace("#", "") || "introduction";
  if (document.getElementById(initial)) {
    activate(initial);
  } else {
    activate("introduction");
  }
});
