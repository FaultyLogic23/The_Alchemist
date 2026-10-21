/* Drag for graphs boxes */

document.querySelectorAll(".graph-box").forEach(box => {
  let down = false, startX, startY, left, top;
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
});