const slides = [...document.querySelectorAll(".slide")];
const progress = document.querySelector("#progress");
const timer = document.querySelector("#timer");
const demoLink = document.querySelector("#demo-link");

let current = 0;
let startedAt = null;
let elapsedBeforeStart = 0;
let timerHandle = null;

const parameters = new URLSearchParams(window.location.search);
const demoUrl = parameters.get("demo");
if (demoUrl) demoLink.href = demoUrl;

function showSlide(index) {
  current = Math.max(0, Math.min(index, slides.length - 1));
  slides.forEach((slide, slideIndex) => {
    const active = slideIndex === current;
    slide.classList.toggle("is-active", active);
    slide.setAttribute("aria-hidden", String(!active));
  });
  progress.textContent = `${current + 1} / ${slides.length}`;
  window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#${current + 1}`);
}

function renderTimer() {
  const elapsed = elapsedBeforeStart + (startedAt ? Date.now() - startedAt : 0);
  const totalSeconds = Math.floor(elapsed / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  timer.textContent = `${minutes}:${seconds}`;
  timer.classList.toggle("is-over", totalSeconds > 210);
}

function startTimer() {
  if (startedAt) {
    elapsedBeforeStart += Date.now() - startedAt;
    startedAt = null;
    clearInterval(timerHandle);
    timerHandle = null;
    timer.classList.remove("is-running");
    renderTimer();
    return;
  }
  startedAt = Date.now();
  timerHandle = window.setInterval(renderTimer, 250);
  timer.classList.add("is-running");
  renderTimer();
}

function resetTimer() {
  startedAt = null;
  elapsedBeforeStart = 0;
  clearInterval(timerHandle);
  timerHandle = null;
  timer.classList.remove("is-running", "is-over");
  renderTimer();
}

document.addEventListener("keydown", (event) => {
  if (["ArrowRight", "PageDown"].includes(event.key) || event.code === "Space") {
    event.preventDefault();
    showSlide(current + 1);
  } else if (["ArrowLeft", "PageUp"].includes(event.key)) {
    event.preventDefault();
    showSlide(current - 1);
  } else if (event.key === "Home") {
    showSlide(0);
  } else if (event.key === "End") {
    showSlide(slides.length - 1);
  } else if (event.key.toLowerCase() === "t") {
    startTimer();
  } else if (event.key.toLowerCase() === "r") {
    resetTimer();
  } else if (event.key.toLowerCase() === "n") {
    document.body.classList.toggle("notes-open");
  }
});

timer.addEventListener("click", startTimer);
const initialSlide = Number.parseInt(window.location.hash.slice(1), 10);
showSlide(Number.isFinite(initialSlide) ? initialSlide - 1 : 0);
renderTimer();

export { resetTimer, showSlide, startTimer };
