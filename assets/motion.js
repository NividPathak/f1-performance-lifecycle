document.addEventListener("DOMContentLoaded", () => {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches || !window.anime) return;

  const bg = document.querySelector(".speed-lines");
  for (let i = 0; i < 18; i++) {
    const line = document.createElement("i");
    if (i % 4 === 0) line.className = "red";
    line.style.top = anime.random(2, 98) + "%";
    line.style.width = anime.random(120, 360) + "px";
    line.style.opacity = anime.random(15, 45) / 100;
    bg.appendChild(line);
  }

  anime({
    targets: ".speed-lines i",
    translateX: [-400, () => innerWidth + 400],
    duration: () => anime.random(1400, 3200),
    delay: () => anime.random(0, 4000),
    easing: "linear",
    loop: true,
  });

  // Blocks fade up the first time they scroll into view.
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add("in");
      io.unobserve(e.target);
    });
  }, { rootMargin: "-8% 0px -4%" });

  const watch = () => document.querySelectorAll(".tab-panel.active .block:not(.in)")
    .forEach((b) => { b.classList.add("reveal"); io.observe(b); });
  watch();
  document.addEventListener("tabchange", watch);

  // Hero counters run once, when the intro is out of the way.
  const countUp = () => document.querySelectorAll(".hero-stats dd").forEach((el) => {
    const end = parseFloat(el.dataset.count);
    const decimals = (el.dataset.count.split(".")[1] || "").length;
    anime({
      targets: { v: 0 },
      v: end,
      duration: 1600,
      delay: 260,
      easing: "easeOutExpo",
      update(a) {
        const v = a.animatables[0].target.v;
        el.textContent = decimals
          ? v.toFixed(decimals)
          : Math.round(v).toLocaleString("en-US");
      },
    });
  });

  anime({
    targets: ".hero-copy > *",
    opacity: [0, 1],
    translateY: [28, 0],
    duration: 900,
    delay: anime.stagger(110, { start: 120 }),
    easing: "easeOutExpo",
  });

  if (document.getElementById("intro")?.hidden !== false) countUp();
  else document.addEventListener("introdone", countUp, { once: true });

  const header = document.querySelector(".site-header");
  const car = document.querySelector(".header-car");
  const drive = () => anime({
    targets: car,
    translateX: [-80, header.clientWidth + 20],
    duration: 1600,
    easing: "easeInOutQuad",
    complete: () => setTimeout(drive, 4000),
  });
  setTimeout(drive, 800);
});
