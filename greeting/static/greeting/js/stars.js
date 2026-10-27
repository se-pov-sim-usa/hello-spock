// Warp-speed starfield. Renders a single static frame when reduced motion is requested.
(() => {
  const canvas = document.getElementById("starfield");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const STAR_COUNT = 420;
  const SPEED = 0.0016;
  let width = 0;
  let height = 0;
  let stars = [];

  const spawn = (star = {}) => {
    star.x = (Math.random() - 0.5) * 2;
    star.y = (Math.random() - 0.5) * 2;
    star.z = Math.random() * 0.9 + 0.1;
    star.hue = Math.random() < 0.15 ? 30 : Math.random() < 0.3 ? 265 : 220;
    return star;
  };

  const resize = () => {
    const dpr = window.devicePixelRatio || 1;
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  const draw = () => {
    ctx.clearRect(0, 0, width, height);
    const cx = width / 2;
    const cy = height / 2;
    const scale = Math.max(width, height) / 2;

    for (const star of stars) {
      if (!reducedMotion) {
        star.z -= SPEED;
        if (star.z <= 0.02) spawn(star).z = 1;
      }
      const px = cx + (star.x / star.z) * scale;
      const py = cy + (star.y / star.z) * scale;
      if (px < 0 || px > width || py < 0 || py > height) {
        if (!reducedMotion) spawn(star).z = 1;
        continue;
      }
      const depth = 1 - star.z;
      ctx.beginPath();
      ctx.fillStyle = `hsla(${star.hue}, 90%, 85%, ${0.25 + depth * 0.75})`;
      ctx.arc(px, py, 0.3 + depth * 1.8, 0, Math.PI * 2);
      ctx.fill();
    }

    if (!reducedMotion) requestAnimationFrame(draw);
  };

  resize();
  stars = Array.from({ length: STAR_COUNT }, () => spawn());
  window.addEventListener("resize", () => {
    resize();
    if (reducedMotion) draw();
  });
  draw();
})();
