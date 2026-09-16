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
