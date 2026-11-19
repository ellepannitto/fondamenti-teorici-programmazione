const slides = Array.from(document.querySelectorAll(".slide"));
const counter = document.getElementById("counter");
const progress = document.getElementById("progress");
const announcer = document.getElementById("slide-announcer");
let current = 0;

function slideLabel(slide, index) {
  const heading = slide.querySelector("h1, h2, h3");
  const title = heading ? heading.textContent.trim() : "";
  const position = `Diapositiva ${index + 1} di ${slides.length}`;
  return title ? `${position}: ${title}` : position;
}

function updateSlide(index, options) {
  const opts = options || {};
  current = Math.max(0, Math.min(index, slides.length - 1));
  slides.forEach((slide, i) => slide.classList.toggle("active", i === current));
  counter.textContent = `${current + 1} / ${slides.length}`;
  progress.style.width = `${((current + 1) / slides.length) * 100}%`;

  const activeSlide = slides[current];
  const label = slideLabel(activeSlide, current);
  activeSlide.setAttribute("aria-label", label);
  announcer.textContent = label;

  if (opts.moveFocus) {
    activeSlide.focus({ preventScroll: true });
  }

  const anchor = activeSlide.querySelector("[id]");
  if (anchor) {
    history.replaceState(null, "", `#${anchor.id}`);
  }
}

document.getElementById("prev").addEventListener("click", () => updateSlide(current - 1, { moveFocus: true }));
document.getElementById("next").addEventListener("click", () => updateSlide(current + 1, { moveFocus: true }));

document.addEventListener("keydown", (event) => {
  if (["ArrowRight", "PageDown", " "].includes(event.key)) {
    event.preventDefault();
    updateSlide(current + 1, { moveFocus: true });
  }
  if (["ArrowLeft", "PageUp"].includes(event.key)) {
    event.preventDefault();
    updateSlide(current - 1, { moveFocus: true });
  }
  if (event.key === "Home") updateSlide(0, { moveFocus: true });
  if (event.key === "End") updateSlide(slides.length - 1, { moveFocus: true });
});

function slideFromHash() {
  const id = decodeURIComponent(location.hash.slice(1));
  const target = id ? document.getElementById(id) : null;
  const slide = target ? target.closest(".slide") : null;
  const index = slide ? slides.indexOf(slide) : -1;
  return index;
}

window.addEventListener("hashchange", () => {
  const index = slideFromHash();
  if (index >= 0 && index !== current) updateSlide(index, { moveFocus: true });
});

const startIndex = slideFromHash();
updateSlide(startIndex >= 0 ? startIndex : 0);
