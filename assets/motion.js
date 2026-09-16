/* Background speed lines and the car that runs across the hero, using anime.js. */

const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.addEventListener("DOMContentLoaded", () => {
  if (REDUCED_MOTION || typeof anime === "undefined") return;

  const layer = document.querySelector(".speed-lines");
  const LINES = 18;
  for (let i = 0; i < LINES; i++) {
    const line = document.createElement("i");
    if (i % 4 === 0) line.className = "red";
    line.style.top = `${anime.random(2, 98)}%`;
    line.style.width = `${anime.random(120, 360)}px`;
    line.style.opacity = (anime.random(15, 45) / 100).toFixed(2);
    layer.appendChild(line);
  }

  anime({
    targets: ".speed-lines i",
    translateX: [() => -400, () => window.innerWidth + 400],
    duration: () => anime.random(1400, 3200),
    delay: () => anime.random(0, 4000),
    easing: "linear",
    loop: true,
  });

  const road = document.querySelector(".hero-road");
  const car = document.querySelector(".hero-car");
  if (!road || !car) return;

  function lap() {
    anime({
      targets: car,
      translateX: [-140, road.clientWidth + 20],
      duration: 1500,
      easing: "easeInOutQuad",
      complete: () => setTimeout(lap, 2500),
    });
  }
  setTimeout(lap, 600);
});
