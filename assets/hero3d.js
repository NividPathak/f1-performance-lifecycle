// WebGL hero: three original-livery open-wheel cars on a night circuit.
// Everything here is generated in code, so the site ships no third-party
// models, liveries, or marks.
import * as THREE from "three";

const canvas = document.getElementById("hero-canvas");
const hero = document.getElementById("hero");
const still = matchMedia("(prefers-reduced-motion: reduce)").matches;

function init() {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05050a, 0.021);

  const camera = new THREE.PerspectiveCamera(38, 2, 0.1, 400);
  camera.position.set(2.6, 1.85, 8.4);

  buildLights(scene);
  const road = buildRoad(scene);

  // Lead car plus two chasers, each on its own line and slightly behind.
  const cars = [
    makeCar({ body: 0x101c3d, accent: 0xe10600, trim: 0xdfe6f2, number: "14" }),
    makeCar({ body: 0x191c23, accent: 0xffb020, trim: 0x8a9099, number: "7" }),
    makeCar({ body: 0xe6ecf4, accent: 0x18b8a6, trim: 0x2a3138, number: "23" }),
  ];
  // The copy sits left, so the pack runs down the right of the frame.
  const pack = new THREE.Group();
  pack.position.x = 3.1;
  scene.add(pack);

  const lanes = [
    { x: 0, z: 0, delay: 0 },
    { x: -2.6, z: -5.4, delay: 1.1 },
    { x: 1.9, z: -10.5, delay: 2.3 },
  ];
  cars.forEach((car, i) => {
    car.position.set(lanes[i].x, 0, lanes[i].z);
    pack.add(car);
  });

  const streaks = buildStreaks(scene);

  const pointer = new THREE.Vector2();
  addEventListener("pointermove", (e) => {
    pointer.x = (e.clientX / innerWidth) * 2 - 1;
    pointer.y = (e.clientY / innerHeight) * 2 - 1;
  }, { passive: true });

  let scrolled = 0;
  addEventListener("scroll", () => {
    scrolled = Math.min(scrollY / innerHeight, 1);
  }, { passive: true });

  function resize() {
    const w = hero.clientWidth;
    const h = hero.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    // Widen the framing on phones so the cars still fit.
    camera.fov = w < 700 ? 52 : 38;
    camera.updateProjectionMatrix();
  }
  resize();
  addEventListener("resize", resize);

  const clock = new THREE.Clock();
  let visible = true;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }, { threshold: 0.01 })
    .observe(hero);

  function frame(t) {
    const dt = Math.min(clock.getDelta(), 0.05);
    const time = t / 1000;

    if (!still) {
      road.tick(dt);
      streaks.tick(dt);
      cars.forEach((car, i) => {
        const lane = lanes[i];
        const ph = time + lane.delay;
        car.tick(dt, ph);
        // Cars breathe around their line: a little weave, a little squat.
        car.position.x = lane.x + Math.sin(ph * 0.55) * 0.22;
        car.position.z = lane.z + Math.sin(ph * 0.4 + i) * 0.5;
        car.position.y = Math.sin(ph * 3.1) * 0.012;
        car.rotation.z = Math.sin(ph * 0.55 + 1.2) * 0.035;
        car.rotation.y = Math.sin(ph * 0.55) * 0.05;
      });
    }

    // Cursor parallax, plus a lift and pull-back as the page scrolls away.
    const tx = 4.4 + pointer.x * 1.4;
    const ty = 1.55 - pointer.y * 0.4 + scrolled * 2.4;
    camera.position.x += (tx - camera.position.x) * 0.04;
    camera.position.y += (ty - camera.position.y) * 0.04;
    camera.position.z = 8.6 + scrolled * 3.2;
    camera.lookAt(2.9, 0.58 + scrolled * 0.4, -1.8);

    renderer.render(scene, camera);
  }

  const loop = (t) => {
    if (visible && !document.hidden) frame(t);
    requestAnimationFrame(loop);
  };

  const start = () => {
    resize();
    if (still) {
      frame(0);
      return;
    }
    requestAnimationFrame(loop);
  };

  // Wait for the title sequence so the first frame lands on a warm GPU.
  if (document.getElementById("intro")?.hidden !== false) start();
  else document.addEventListener("introdone", start, { once: true });
}

/* ---------- scene pieces ---------- */

function buildLights(scene) {
  scene.add(new THREE.HemisphereLight(0x7f9dff, 0x05050a, 0.55));

  const key = new THREE.DirectionalLight(0xfff0e0, 2.1);
  key.position.set(6, 9, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 40;
  key.shadow.camera.left = -12;
  key.shadow.camera.right = 12;
  key.shadow.camera.top = 12;
  key.shadow.camera.bottom = -12;
  scene.add(key);

  // Trackside rims: warm on one side, cold on the other.
  const warm = new THREE.SpotLight(0xff5a2b, 60, 30, 0.7, 0.6, 1.6);
  warm.position.set(-9, 5.5, -6);
  scene.add(warm);

  const cold = new THREE.SpotLight(0x5fb8ff, 45, 30, 0.8, 0.6, 1.6);
  cold.position.set(9, 4.5, 3);
  scene.add(cold);

  scene.add(new THREE.AmbientLight(0x20243a, 0.8));
}

function buildRoad(scene) {
  // Asphalt drawn to a canvas so lane lines and kerbs can scroll as one.
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#15161c";
  g.fillRect(0, 0, 256, 512);

  const grain = g.createLinearGradient(0, 0, 256, 0);
  grain.addColorStop(0, "rgba(255,255,255,.05)");
  grain.addColorStop(0.5, "rgba(255,255,255,0)");
  grain.addColorStop(1, "rgba(255,255,255,.05)");
  g.fillStyle = grain;
  g.fillRect(0, 0, 256, 512);

  for (let i = 0; i < 1600; i++) {
    g.fillStyle = `rgba(255,255,255,${Math.random() * 0.05})`;
    g.fillRect(Math.random() * 256, Math.random() * 512, 2, 2);
  }

  // Dashed centre line.
  g.fillStyle = "rgba(255,255,255,.55)";
  for (let y = 0; y < 512; y += 96) g.fillRect(124, y, 6, 52);

  // Solid edge lines.
  g.fillStyle = "rgba(255,255,255,.4)";
  g.fillRect(18, 0, 4, 512);
  g.fillRect(234, 0, 4, 512);

  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1, 14);
  tex.anisotropy = 8;

  const road = new THREE.Mesh(
    new THREE.PlaneGeometry(16, 240),
    new THREE.MeshStandardMaterial({ map: tex, roughness: 0.82, metalness: 0.05 }),
  );
  road.rotation.x = -Math.PI / 2;
  road.position.z = -90;
  road.receiveShadow = true;
  scene.add(road);

  // Red-and-white kerbs down both sides.
  const kerbs = [];
  for (const side of [-8.1, 8.1]) {
    const group = new THREE.Group();
    for (let i = 0; i < 120; i++) {
      const block = new THREE.Mesh(
        new THREE.BoxGeometry(1.1, 0.06, 1.6),
        new THREE.MeshStandardMaterial({
          color: i % 2 ? 0xe10600 : 0xf2f2f2,
          roughness: 0.55,
          emissive: i % 2 ? 0x2a0400 : 0x161616,
        }),
      );
      block.position.set(side, 0.03, -i * 1.6 + 8);
      group.add(block);
    }
    scene.add(group);
    kerbs.push(group);
  }

  // Dark run-off beyond the kerbs.
  const apron = new THREE.Mesh(
    new THREE.PlaneGeometry(90, 240),
    new THREE.MeshStandardMaterial({ color: 0x0a0b12, roughness: 1 }),
  );
  apron.rotation.x = -Math.PI / 2;
  apron.position.set(0, -0.02, -90);
  scene.add(apron);

  const speed = 3.4;
  return {
    tick(dt) {
      tex.offset.y -= dt * speed * 0.42;
      kerbs.forEach((group) => {
        group.position.z += dt * speed * 4.2;
        if (group.position.z > 3.2) group.position.z = 0;
      });
    },
  };
}

function buildStreaks(scene) {
  const count = 220;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 26;
    positions[i * 3 + 1] = Math.random() * 7 + 0.3;
    positions[i * 3 + 2] = -Math.random() * 90;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const points = new THREE.Points(
    geo,
    new THREE.PointsMaterial({
      color: 0x9fd0ff,
      size: 0.06,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }),
  );
  scene.add(points);

  return {
    tick(dt) {
      const p = geo.attributes.position.array;
      for (let i = 0; i < count; i++) {
        p[i * 3 + 2] += dt * 34;
        if (p[i * 3 + 2] > 10) {
          p[i * 3 + 2] = -90;
          p[i * 3] = (Math.random() - 0.5) * 26;
        }
      }
      geo.attributes.position.needsUpdate = true;
    },
  };
}

/* ---------- the car ---------- */

// Half of the plan-view outline, nose to tail, mirrored to build the tub.
const TUB = [
  [0.07, 2.62], [0.11, 2.3], [0.17, 1.9], [0.23, 1.42],
  [0.32, 1.0], [0.46, 0.6], [0.6, 0.18], [0.62, -0.4],
  [0.52, -1.0], [0.4, -1.58], [0.31, -2.06], [0.22, -2.44], [0.13, -2.6],
];

function symmetricShape(half, scale = 1) {
  const shape = new THREE.Shape();
  shape.moveTo(half[0][0] * scale, half[0][1] * scale);
  half.forEach(([x, y]) => shape.lineTo(x * scale, y * scale));
  [...half].reverse().forEach(([x, y]) => shape.lineTo(-x * scale, y * scale));
  shape.closePath();
  return shape;
}

function extruded(shape, depth, bevel = 0.045) {
  const geo = new THREE.ExtrudeGeometry(shape, {
    depth,
    bevelEnabled: true,
    bevelSize: bevel,
    bevelThickness: bevel,
    bevelSegments: 3,
    curveSegments: 8,
  });
  // Shape lives in XY with depth on Z; stand it up so depth becomes height.
  geo.rotateX(-Math.PI / 2);
  return geo;
}

function numberPlate(number, bg, fg) {
  const c = document.createElement("canvas");
  c.width = 128;
  c.height = 128;
  const g = c.getContext("2d");
  g.fillStyle = `#${bg.toString(16).padStart(6, "0")}`;
  g.fillRect(0, 0, 128, 128);
  g.fillStyle = `#${fg.toString(16).padStart(6, "0")}`;
  g.font = "900 88px 'Titillium Web', Arial, sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText(number, 64, 70);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeCar({ body, accent, trim, number }) {
  const car = new THREE.Group();

  const paint = new THREE.MeshStandardMaterial({
    color: body,
    roughness: 0.28,
    metalness: 0.65,
  });
  const accentMat = new THREE.MeshStandardMaterial({
    color: accent,
    roughness: 0.3,
    metalness: 0.4,
    emissive: accent,
    emissiveIntensity: 0.18,
  });
  const carbon = new THREE.MeshStandardMaterial({
    color: 0x0c0d11,
    roughness: 0.45,
    metalness: 0.5,
  });
  const trimMat = new THREE.MeshStandardMaterial({
    color: trim,
    roughness: 0.35,
    metalness: 0.5,
  });

  const add = (mesh, x, y, z) => {
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    car.add(mesh);
    return mesh;
  };

  // Tub and the engine cover that tapers back over it.
  const tub = new THREE.Mesh(extruded(symmetricShape(TUB), 0.34), paint);
  add(tub, 0, 0.26, 0);

  const cover = new THREE.Mesh(
    extruded(symmetricShape(TUB.slice(4).map(([x, y]) => [x * 0.68, y]), 1), 0.3),
    accentMat,
  );
  add(cover, 0, 0.58, 0);

  // Floor, nose cone, airbox.
  add(new THREE.Mesh(new THREE.BoxGeometry(1.34, 0.05, 5.1), carbon), 0, 0.12, 0);

  const nose = new THREE.Mesh(new THREE.CapsuleGeometry(0.12, 0.5, 4, 12), paint);
  nose.rotation.x = Math.PI / 2;
  add(nose, 0, 0.3, 2.45);

  const airbox = new THREE.Mesh(new THREE.ConeGeometry(0.2, 0.46, 4), paint);
  airbox.rotation.y = Math.PI / 4;
  add(airbox, 0, 0.92, -0.72);

  // Halo, as an arc with a centre strut.
  const halo = new THREE.Mesh(
    new THREE.TorusGeometry(0.42, 0.035, 8, 22, Math.PI),
    carbon,
  );
  halo.rotation.set(Math.PI / 2, 0, 0);
  add(halo, 0, 0.84, 0.18);
  add(new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.06, 0.22), carbon), 0, 0.84, 0.58);

  // Front wing: main plane, upper flap, endplates.
  add(new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.04, 0.5), carbon), 0, 0.12, 2.72);
  const flap = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.035, 0.3), accentMat);
  flap.rotation.x = -0.22;
  add(flap, 0, 0.23, 2.62);
  for (const side of [-0.95, 0.95]) {
    add(new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.3, 0.56), trimMat), side, 0.24, 2.7);
  }

  // Rear wing on twin pylons, plus a diffuser.
  add(new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.05, 0.42), carbon), 0, 0.96, -2.42);
  const upper = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.04, 0.3), accentMat);
  upper.rotation.x = 0.3;
  add(upper, 0, 1.12, -2.5);
  for (const side of [-0.6, 0.6]) {
    add(new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.42, 0.5), trimMat), side, 0.9, -2.45);
  }
  add(new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.5, 0.1), carbon), 0, 0.72, -2.3);
  const diffuser = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.22, 0.5), carbon);
  diffuser.rotation.x = 0.22;
  add(diffuser, 0, 0.18, -2.35);

  // Sidepod inlets.
  for (const side of [-0.62, 0.62]) {
    add(new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.24, 0.5), carbon), side, 0.36, 0.5);
  }

  // Number panels either side of the engine cover.
  const plate = numberPlate(number, body, accent);
  for (const side of [-0.43, 0.43]) {
    const panel = new THREE.Mesh(
      new THREE.PlaneGeometry(0.4, 0.4),
      new THREE.MeshBasicMaterial({ map: plate, toneMapped: false }),
    );
    panel.position.set(side, 0.62, -0.95);
    panel.rotation.y = side > 0 ? Math.PI / 2 : -Math.PI / 2;
    car.add(panel);
  }

  // Wheels: tyre, rim, and a glowing brake disc.
  const tyre = new THREE.MeshStandardMaterial({ color: 0x141418, roughness: 0.92 });
  const rim = new THREE.MeshStandardMaterial({
    color: 0xb9c0cc,
    roughness: 0.25,
    metalness: 0.95,
  });
  const brake = new THREE.MeshStandardMaterial({
    color: 0xff5a2b,
    emissive: 0xff2d00,
    emissiveIntensity: 1.4,
  });

  const wheels = [];
  for (const [x, z, r] of [[-0.95, 1.72, 0.36], [0.95, 1.72, 0.36], [-1.0, -1.72, 0.4], [1.0, -1.72, 0.4]]) {
    const w = new THREE.Group();
    const t = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.34, 26), tyre);
    t.rotation.z = Math.PI / 2;
    t.castShadow = true;
    w.add(t);

    const d = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.62, r * 0.62, 0.36, 22), rim);
    d.rotation.z = Math.PI / 2;
    w.add(d);

    const b = new THREE.Mesh(new THREE.TorusGeometry(r * 0.44, 0.03, 6, 18), brake);
    b.rotation.y = Math.PI / 2;
    w.add(b);

    w.position.set(x, r, z);
    car.add(w);
    wheels.push(w);
  }

  // A faint pool of light under the car to seat it on the asphalt.
  const glow = new THREE.Mesh(
    new THREE.PlaneGeometry(2.6, 6),
    new THREE.MeshBasicMaterial({ color: accent, transparent: true, opacity: 0.07 }),
  );
  glow.rotation.x = -Math.PI / 2;
  glow.position.y = 0.01;
  car.add(glow);

  car.tick = (dt) => {
    wheels.forEach((w) => { w.rotation.x -= dt * 26; });
  };

  return car;
}

// Started last: the builders above use module constants that are not
// initialised until this point in the file.
if (canvas && hero) init();
