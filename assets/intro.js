// Cinematic title sequence. Plays once per browser session, then hands the
// screen to the hero. Skippable, and skipped outright for reduced motion.
document.addEventListener("DOMContentLoaded", () => {
  const intro = document.getElementById("intro");
  if (!intro) return;

  const word = document.getElementById("intro-word");
  const sub = document.getElementById("intro-sub");
  const mark = intro.querySelector(".intro-mark");
  const sweep = intro.querySelector(".intro-sweep");
  const skip = document.getElementById("intro-skip");

  const finish = () => {
    intro.hidden = true;
    document.body.classList.remove("intro-playing");
    document.dispatchEvent(new CustomEvent("introdone"));
  };

  const seen = sessionStorage.getItem("introSeen") === "1";
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const skipped = new URLSearchParams(location.search).has("nointro");
  if (seen || still || skipped || !window.anime) {
    finish();
    return;
  }

  // Backstop: if frames never arrive (headless capture, a throttled
  // background tab), the overlay still gets out of the way.
  const bail = setTimeout(finish, 9000);
  document.addEventListener("introdone", () => clearTimeout(bail), { once: true });

  sessionStorage.setItem("introSeen", "1");
  intro.hidden = false;
  document.body.classList.add("intro-playing");

  // One span per character so they can land independently.
  word.textContent = "";
  [...word.dataset.text].forEach((c) => {
    const span = document.createElement("span");
    span.className = c === " " ? "ch sp" : "ch";
    span.textContent = c === " " ? "" : c;
    word.appendChild(span);
  });

  const ring = mark.querySelector(".im-ring");
  const apex = mark.querySelector(".im-apex");
  [ring, apex].forEach((p) => {
    const len = p.getTotalLength();
    p.style.strokeDasharray = len;
    p.style.strokeDashoffset = len;
  });

  const tl = anime.timeline({ easing: "easeOutExpo", complete: finish });

  tl.add({
    targets: sweep,
    width: [0, () => Math.min(innerWidth * 0.82, 900)],
    duration: 620,
    easing: "easeOutQuart",
  })
    .add({
      targets: mark,
      opacity: [0, 1],
      scale: [0.72, 1],
      duration: 520,
    }, "-=380")
    .add({
      targets: [ring, apex],
      strokeDashoffset: [anime.setDashoffset, 0],
      duration: 760,
      easing: "easeInOutSine",
    }, "-=440")
    .add({
      targets: ".intro-word .ch",
      opacity: [0, 1],
      translateY: [42, 0],
      rotateX: [-70, 0],
      scale: [1.22, 1],
      duration: 620,
      delay: anime.stagger(34),
    }, "-=520")
    .add({
      targets: sweep,
      width: 0,
      opacity: [1, 0],
      duration: 480,
      easing: "easeInQuart",
    }, "-=420")
    .add({
      targets: sub,
      opacity: [0, 1],
      letterSpacing: ["1.1em", ".58em"],
      duration: 760,
    }, "-=460")
    // Hold on the finished lockup, then punch out toward the hero.
    .add({
      targets: ".intro-stage",
      scale: [1, 1.14],
      opacity: [1, 0],
      duration: 620,
      delay: 520,
      easing: "easeInCubic",
    })
    .add({
      targets: intro,
      opacity: [1, 0],
      duration: 420,
      easing: "linear",
    }, "-=300");

  skip.addEventListener("click", () => {
    tl.pause();
    anime({
      targets: intro,
      opacity: 0,
      duration: 260,
      easing: "linear",
      complete: finish,
    });
  });
});
