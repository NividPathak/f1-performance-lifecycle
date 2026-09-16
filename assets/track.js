/* Bahrain track map on the Introduction tab. The outline comes from
   data/track_bahrain.json (see code/make_track_data.py). Plays a short
   three-lap race that walks through the steps listed next to the map:
   grid, start lights, racing, a pit stop, and the chequered flag. */

(() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const LAPS = 3;
  const LAP_SECONDS = 7;
  const PIT_CAR = 2;
  const PIT_SECONDS = 1.8;

  const CARS = [
    { color: "#e10600", pace: 1.0 },
    { color: "#00d2be", pace: 0.988 },
    { color: "#ff8700", pace: 1.012 },
    { color: "#3671c6", pace: 0.972 },
    { color: "#f4f4f4", pace: 0.962 },
  ];

  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  function el(tag, attrs, parent) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }

  function build(svg, data) {
    svg.setAttribute("viewBox", `0 0 ${data.width} ${data.height + 40}`);

    el("path", { d: data.path, fill: "none", stroke: "rgba(255,255,255,0.07)", "stroke-width": 40, "stroke-linejoin": "round" }, svg);
    el("path", { d: data.path, fill: "none", stroke: "#2c2c35", "stroke-width": 28, "stroke-linejoin": "round" }, svg);
    const outline = el("path", { d: data.path, fill: "none", stroke: "#e10600", "stroke-width": 2.5, "stroke-linejoin": "round", opacity: 0.85 }, svg);
    el("path", { d: data.path, fill: "none", stroke: "rgba(255,255,255,0.12)", "stroke-width": 1.5, "stroke-dasharray": "6 12" }, svg);

    const L = outline.getTotalLength();
    const at = (d) => {
      const dist = ((d % L) + L) % L;
      const p = outline.getPointAtLength(dist);
      const q = outline.getPointAtLength((dist + 2) % L);
      const ang = Math.atan2(q.y - p.y, q.x - p.x);
      return { x: p.x, y: p.y, ang, nx: -Math.sin(ang), ny: Math.cos(ang) };
    };

    // Start/finish line: a chequered strip across the track.
    const s = at(0);
    const line = el("g", { transform: `translate(${s.x},${s.y}) rotate(${(s.ang * 180) / Math.PI})` }, svg);
    for (let i = 0; i < 6; i++) {
      for (let j = 0; j < 2; j++) {
        el("rect", { x: -5 + j * 5, y: -15 + i * 5, width: 5, height: 5, fill: (i + j) % 2 ? "#000" : "#fff" }, line);
      }
    }
    el("text", { x: s.x, y: s.y + 52, "text-anchor": "middle", class: "track-tag", fill: "#a7a7b0" }, svg).textContent = "START / FINISH";

    // Corner numbers, pushed outward from the middle of the circuit.
    const cx = data.width / 2;
    const cy = data.height / 2;
    for (const c of data.corners) {
      const dx = c.x - cx;
      const dy = c.y - cy;
      const len = Math.hypot(dx, dy) || 1;
      el("text", {
        x: c.x + (dx / len) * 34,
        y: c.y + (dy / len) * 34 + 7,
        "text-anchor": "middle",
        class: "corner-label",
      }, svg).textContent = c.n;
    }

    const pitTag = el("text", { x: s.x - 60, y: s.y - 44, "text-anchor": "middle", class: "track-tag", fill: "#ff8700", opacity: 0 }, svg);
    pitTag.textContent = "PIT";
    const flagTag = el("text", { x: s.x, y: s.y - 40, "text-anchor": "middle", class: "track-tag", fill: "#fff", opacity: 0 }, svg);
    flagTag.textContent = "FINISH";

    const cars = CARS.map((c) => {
      const g = el("g", {}, svg);
      el("rect", { x: -16, y: -6, width: 30, height: 12, rx: 5, fill: c.color }, g);
      el("rect", { x: -18, y: -9, width: 5, height: 18, rx: 1, fill: c.color }, g);
      el("rect", { x: 12, y: -9, width: 4, height: 18, rx: 1, fill: "#ddd" }, g);
      el("rect", { x: -2, y: -3, width: 8, height: 6, rx: 3, fill: "#000" }, g);
      return Object.assign({ g }, c);
    });

    return { outline, L, at, cars, pitTag, flagTag };
  }

  document.addEventListener("DOMContentLoaded", () => {
    const svg = document.getElementById("track-svg");
    if (!svg) return;
    const steps = [...document.querySelectorAll("#race-steps li")];
    const lights = [...document.querySelectorAll(".start-lights span")];
    const replay = document.getElementById("track-replay");

    const setStep = (n) => steps.forEach((li, i) => li.classList.toggle("active", i === n));
    let visible = document.getElementById("introduction").classList.contains("active");
    document.addEventListener("tabchange", (e) => { visible = e.detail === "introduction"; });

    fetch("data/track_bahrain.json")
      .then((r) => r.json())
      .then((data) => {
        const t = build(svg, data);
        const { L, at, cars } = t;
        const gridDist = (k) => L - 34 - k * 34;
        const lateral = (k) => (k % 2 ? -7 : 7);

        function place(car, k, dist, side) {
          const p = at(dist);
          const x = p.x + p.nx * side;
          const y = p.y + p.ny * side;
          car.g.setAttribute("transform", `translate(${x},${y}) rotate(${(p.ang * 180) / Math.PI})`);
        }

        function resetGrid() {
          cars.forEach((car, k) => {
            car.dist = gridDist(k);
            car.travelled = 0;
            car.speed = 0;
            car.side = lateral(k);
            car.pitTimer = 0;
            car.pitted = false;
            car.done = false;
            place(car, k, car.dist, car.side);
          });
          lights.forEach((l) => l.classList.remove("on"));
          t.pitTag.setAttribute("opacity", 0);
          t.flagTag.setAttribute("opacity", 0);
        }

        if (REDUCED) {
          resetGrid();
          steps.forEach((li) => li.classList.add("active"));
          replay.hidden = true;
          return;
        }

        anime({
          targets: t.outline,
          strokeDashoffset: [anime.setDashOffset, 0],
          duration: 2200,
          easing: "easeInOutSine",
        });

        let run = 0;
        let racing = false;

        function frame(dt) {
          const base = L / LAP_SECONDS;
          const finishAt = (k) => (L - gridDist(k)) + LAPS * L;
          cars.forEach((car, k) => {
            if (car.pitTimer > 0) {
              car.pitTimer -= dt;
              if (car.pitTimer <= 0) t.pitTag.setAttribute("opacity", 0);
              car.side = 22;
              place(car, k, car.dist, car.side);
              return;
            }
            const pace = car.done ? 0.3 : car.pace * (1 + 0.03 * Math.sin(car.travelled / 90 + k));
            car.speed += (base * pace - car.speed) * Math.min(1, dt * 1.6);
            const before = ((car.dist % L) + L) % L;
            const step = car.speed * dt;
            car.dist += step;
            car.travelled += step;
            car.side -= car.side * Math.min(1, dt * 2);
            const after = ((car.dist % L) + L) % L;
            const crossed = after < before;

            if (k === PIT_CAR && !car.pitted && crossed && car.travelled > L * 1.2) {
              car.pitted = true;
              car.pitTimer = PIT_SECONDS;
              car.speed = 0;
              t.pitTag.setAttribute("opacity", 1);
              setStep(3);
            }
            if (!car.done && car.travelled >= finishAt(k)) car.done = true;
            place(car, k, car.dist, car.side);
          });
        }

        let last = performance.now();
        function loop(now) {
          const dt = Math.min(0.05, (now - last) / 1000);
          last = now;
          if (racing && visible && !document.hidden) frame(dt);
          requestAnimationFrame(loop);
        }
        requestAnimationFrame(loop);

        async function race() {
          const id = ++run;
          const alive = () => id === run;
          racing = false;
          resetGrid();
          setStep(0);
          await wait(2200);
          if (!alive()) return;

          setStep(1);
          const tl = anime.timeline({ easing: "easeOutQuad" });
          lights.forEach((light, i) => {
            tl.add({
              targets: light,
              scale: [0.6, 1],
              duration: 250,
              begin: () => light.classList.add("on"),
            }, i * 700);
          });
          await tl.finished;
          await wait(900);
          if (!alive()) return;
          lights.forEach((l) => l.classList.remove("on"));

          setStep(2);
          racing = true;
          let flagShown = false;
          while (alive() && !cars.every((c) => c.done)) {
            if (!flagShown && cars.some((c) => c.done)) {
              flagShown = true;
              setStep(4);
              anime({ targets: t.flagTag, opacity: [0, 1], duration: 400, easing: "linear" });
            }
            await wait(100);
          }
          if (!alive()) return;
          await wait(2500);
          if (alive()) race();
        }

        replay.addEventListener("click", race);
        race();
      })
      .catch((err) => console.error("Failed to load track", err));
  });
})();
