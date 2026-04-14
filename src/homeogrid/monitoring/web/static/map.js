export function renderMap(canvas, snapshot) {
  const ctx = canvas.getContext("2d");
  const cells = snapshot.belief_map.tile_ids;
  const size = cells.length;
  const cell = canvas.width / size;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      ctx.fillStyle = colorFor(cells[y][x], snapshot.belief_map.known_mask[y][x]);
      ctx.fillRect(x * cell, y * cell, cell - 1, cell - 1);
    }
  }
  drawPoints(ctx, cell, snapshot.belief_map.frontier_cells, "#ffb84d");
  drawPoints(ctx, cell, snapshot.belief_map.observed_food, "#5ce1a5");
  drawPoints(ctx, cell, snapshot.belief_map.observed_water, "#8cc8ff");
  drawPath(ctx, cell, snapshot.world.path);
  drawAgent(ctx, cell, snapshot.world.pose);
}

function colorFor(tile, known) {
  if (!known) return "#111722";
  const colors = {
    [-1]: "#1f2933",
    0: "#2b3542",
    1: "#55606e",
    2: "#2fbf71",
    3: "#45aaf2",
    4: "#7b5e57",
    5: "#f5d76e",
  };
  return colors[tile] ?? "#202833";
}

function drawPoints(ctx, cell, points, color) {
  ctx.fillStyle = color;
  points.forEach(([x, y]) => {
    ctx.beginPath();
    ctx.arc((x + 0.5) * cell, (y + 0.5) * cell, cell * 0.18, 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawPath(ctx, cell, points) {
  if (!points.length) return;
  ctx.strokeStyle = "#edf3f8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach(([x, y], index) => {
    const px = (x + 0.5) * cell;
    const py = (y + 0.5) * cell;
    if (index === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
}

function drawAgent(ctx, cell, pose) {
  const [x, y] = pose;
  ctx.fillStyle = "#ff5d73";
  ctx.beginPath();
  ctx.arc((x + 0.5) * cell, (y + 0.5) * cell, cell * 0.25, 0, Math.PI * 2);
  ctx.fill();
}
