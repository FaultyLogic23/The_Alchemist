/* Drag and zoom for graph boxes */

document.querySelectorAll(".graph-box").forEach(box => {
  const img = box.querySelector("img");
  let down = false, startX, startY, left, top;
  let scale = 1;

  /* Drag Part */
  box.addEventListener("mousedown", e => {
    down = true; box.classList.add("dragging");
    startX = e.pageX; startY = e.pageY;
    left = box.scrollLeft; top = box.scrollTop;
    e.preventDefault();
  });
  window.addEventListener("mouseup", () => { down = false; box.classList.remove("dragging"); });
  window.addEventListener("mousemove", e => {
    if (!down) return;
    box.scrollLeft = left - (e.pageX - startX);
    box.scrollTop  = top  - (e.pageY - startY);
  });

  /* Zoom part */
  const zoom = f => {
    scale = Math.min(4, Math.max(0.2, scale * f));
    img.style.width = (img.naturalWidth || 2000) * scale + "px";
  };
  const controls = box.previousElementSibling;
  if (controls && controls.classList.contains("zoom-controls")) {
    controls.querySelector(".zoom-in").onclick  = () => zoom(1.25);
    controls.querySelector(".zoom-out").onclick = () => zoom(0.8);
    controls.querySelector(".zoom-reset").onclick = () => { scale = 1; zoom(1); };
  }
  box.addEventListener("wheel", e => {
    if (e.ctrlKey) { e.preventDefault(); zoom(e.deltaY < 0 ? 1.1 : 0.9); }
  }, { passive: false });
});