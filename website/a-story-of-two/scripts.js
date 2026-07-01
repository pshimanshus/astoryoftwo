const flowNodes = Array.from(document.querySelectorAll("[data-flow-step]"));
const activeLabel = document.querySelector("[data-flow-current]");
const board = document.querySelector("[data-flow-board]");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let activeIndex = 0;
let rotationTimer;

function setActiveFlow(index) {
  if (!flowNodes.length || !activeLabel) return;

  activeIndex = (index + flowNodes.length) % flowNodes.length;

  flowNodes.forEach((node, nodeIndex) => {
    const isActive = nodeIndex === activeIndex;
    node.classList.toggle("is-active", isActive);
    node.setAttribute("aria-pressed", String(isActive));
  });

  activeLabel.textContent = flowNodes[activeIndex].dataset.flowStep;
}

function startRotation() {
  if (prefersReducedMotion || rotationTimer || !flowNodes.length) return;

  rotationTimer = window.setInterval(() => {
    setActiveFlow(activeIndex + 1);
  }, 2600);
}

function stopRotation() {
  window.clearInterval(rotationTimer);
  rotationTimer = undefined;
}

flowNodes.forEach((node, index) => {
  node.setAttribute("aria-pressed", String(index === 0));

  node.addEventListener("click", () => {
    stopRotation();
    setActiveFlow(index);
    startRotation();
  });
});

if (board) {
  board.addEventListener("mouseenter", stopRotation);
  board.addEventListener("mouseleave", startRotation);
}

setActiveFlow(0);
startRotation();

window.addEventListener("load", () => {
  if (window.instgrm?.Embeds?.process) {
    window.instgrm.Embeds.process();
  }
});
