import * as THREE from "./vendor/three.module.js";

export async function renderBlob(root, snapshot) {
  if (!root.__blobState) {
    try {
      root.__blobState = createScene(root);
    } catch {
      root.__blobState = { fallback: true };
    }
  }
  if (root.__blobState.fallback) {
    renderFallback(root, snapshot);
    return;
  }
  updateScene(root.__blobState, snapshot);
}

function createScene(root) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, root.clientWidth / root.clientHeight, 0.1, 100);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(root.clientWidth || 320, root.clientHeight || 320);
  renderer.setAnimationLoop(() => renderer.render(scene, camera));
  root.innerHTML = "";
  root.appendChild(renderer.domElement);
  camera.position.set(0, 0, 4.5);

  const globe = new THREE.Mesh(
    new THREE.SphereGeometry(1, 48, 48),
    new THREE.MeshStandardMaterial({
      color: "#5ce1a5",
      transparent: true,
      opacity: 0.82,
      roughness: 0.32,
      metalness: 0.08,
    }),
  );
  const halo = new THREE.Mesh(
    new THREE.SphereGeometry(1.18, 32, 32),
    new THREE.MeshBasicMaterial({
      color: "#ff5d73",
      transparent: true,
      opacity: 0.14,
      side: THREE.BackSide,
    }),
  );
  scene.add(globe);
  scene.add(halo);
  scene.add(new THREE.AmbientLight("#dcecff", 1.6));
  const light = new THREE.PointLight("#ffb84d", 6);
  light.position.set(2, 3, 5);
  scene.add(light);
  return { renderer, scene, camera, globe, halo };
}

function updateScene(state, snapshot) {
  const { blob } = snapshot;
  state.globe.scale.set(blob.scale_x, blob.scale_y, blob.scale_z);
  state.globe.rotation.y += 0.01 + blob.pulse_hz * 0.002;
  state.globe.rotation.x += 0.002 + blob.noise_amp * 0.08;
  state.halo.scale.setScalar(1 + blob.halo_level * 0.3);
  state.halo.material.opacity = 0.1 + blob.halo_level * 0.35;
  state.globe.material.color = new THREE.Color(
    blendColor(blob.stress, blob.uncertainty, blob.instability),
  );
}

function blendColor(stress, uncertainty, instability) {
  const r = 0.36 + stress * 0.54 + instability * 0.1;
  const g = 0.88 - stress * 0.45;
  const b = 0.64 + uncertainty * 0.18;
  return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
}

function renderFallback(root, snapshot) {
  root.innerHTML = "";
  const canvas = document.createElement("canvas");
  canvas.width = root.clientWidth || 320;
  canvas.height = root.clientHeight || 320;
  root.appendChild(canvas);
  const ctx = canvas.getContext("2d");
  const { blob } = snapshot;
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "rgba(92, 225, 165, 0.16)";
  ctx.beginPath();
  ctx.ellipse(cx, cy, 70 * blob.scale_x, 70 * blob.scale_y, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = blob.halo_level > 0.8 ? "#ff5d73" : "#5ce1a5";
  ctx.lineWidth = 10 * blob.halo_level;
  ctx.beginPath();
  ctx.ellipse(cx, cy, 86 * blob.scale_x, 86 * blob.scale_y, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = "#edf3f8";
  ctx.fillText(`stress ${blob.stress.toFixed(2)}`, 18, 24);
  ctx.fillText(`uncertainty ${blob.uncertainty.toFixed(2)}`, 18, 44);
  ctx.fillText(`instability ${blob.instability.toFixed(2)}`, 18, 64);
}
