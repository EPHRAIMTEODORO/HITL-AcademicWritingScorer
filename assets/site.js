/* Progressive enhancements only: all reference content is in index.html. */
"use strict";

const menuButton = document.getElementById("menu-toggle");
const sidebar = document.getElementById("sidebar");
function closeMenu() {
  sidebar.classList.remove("open");
  menuButton.setAttribute("aria-expanded", "false");
}
menuButton.addEventListener("click", () => {
  const open = sidebar.classList.toggle("open");
  menuButton.setAttribute("aria-expanded", String(open));
});
document.addEventListener("click", (event) => {
  if (!sidebar.contains(event.target) && !menuButton.contains(event.target)) closeMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && sidebar.classList.contains("open")) {
    closeMenu();
    menuButton.focus();
  }
});
sidebar.querySelectorAll("nav a").forEach((link) => link.addEventListener("click", () => {
  closeMenu();
  // Avoid leaving keyboard focus inside a hidden mobile menu.
  if (window.matchMedia("(max-width: 960px)").matches) {
    const target = document.querySelector(link.hash);
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  }
}));

const progress = document.getElementById("reading-progress");
const sections = [...document.querySelectorAll(".observed-section")];
const navLinks = [...sidebar.querySelectorAll("nav a")];
let scrollFrame = null;
function updateReadingPosition() {
  scrollFrame = null;
  const available = document.documentElement.scrollHeight - window.innerHeight;
  progress.style.width = `${available > 0 ? Math.min(100, Math.max(0, window.scrollY / available * 100)) : 0}%`;
  let active = sections[0];
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= 160) active = section;
  }
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 5) active = sections.at(-1);
  navLinks.forEach((link) => {
    const selected = link.hash === `#${active.id}`;
    link.classList.toggle("active", selected);
    if (selected) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}
function schedulePositionUpdate() {
  if (scrollFrame === null) scrollFrame = window.requestAnimationFrame(updateReadingPosition);
}
window.addEventListener("scroll", schedulePositionUpdate, { passive: true });
window.addEventListener("resize", schedulePositionUpdate);
updateReadingPosition();

const featureSearch = document.getElementById("feature-search");
const featureRows = [...document.querySelectorAll("[data-feature]")];
featureSearch.addEventListener("input", () => {
  const query = featureSearch.value.trim().toLowerCase();
  let count = 0;
  featureRows.forEach((row) => {
    const matches = row.textContent.toLowerCase().includes(query);
    row.hidden = !matches;
    if (matches) count++;
  });
  document.getElementById("feature-count").textContent = `${count} ${count === 1 ? "feature" : "features"}`;
  document.getElementById("feature-empty").hidden = count !== 0;
});

const promptBlocks = [...document.querySelectorAll(".prompt-block")];
const expandButton = document.getElementById("expand-prompts");
function updateExpandButton() {
  const allOpen = promptBlocks.every((block) => block.open);
  expandButton.textContent = allOpen ? "Collapse all prompts" : "Expand all prompts";
  expandButton.setAttribute("aria-expanded", String(allOpen));
  schedulePositionUpdate();
}
expandButton.addEventListener("click", () => {
  const expand = !promptBlocks.every((block) => block.open);
  promptBlocks.forEach((block) => { block.open = expand; });
  updateExpandButton();
});
promptBlocks.forEach((block) => block.addEventListener("toggle", updateExpandButton));

function revealHashTarget() {
  if (!window.location.hash) return;
  const target = document.getElementById(window.location.hash.slice(1));
  if (!target) return;
  const detail = target.closest("details");
  if (detail) detail.open = true;
}
window.addEventListener("hashchange", revealHashTarget);
revealHashTarget();

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try { await navigator.clipboard.writeText(text); return; } catch { /* Try local fallback. */ }
  }
  const field = document.createElement("textarea");
  field.value = text;
  field.style.cssText = "position:fixed;left:-9999px;top:0";
  field.setAttribute("readonly", "");
  document.body.append(field);
  field.select();
  const copied = document.execCommand("copy");
  field.remove();
  if (!copied) throw new Error("Clipboard unavailable");
}
document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const target = document.getElementById(button.dataset.copy);
    try {
      await copyText(target.textContent);
      button.textContent = "Copied";
      document.getElementById("copy-status").textContent = "Prompt text copied to clipboard.";
      setTimeout(() => { button.textContent = "Copy text"; }, 1800);
    } catch {
      button.textContent = "Select text";
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(target);
      selection.removeAllRanges();
      selection.addRange(range);
      document.getElementById("copy-status").textContent = "Clipboard unavailable. Text selected; use your browser's Copy command.";
    }
    button.focus({ preventScroll: true });
  });
});

let detailsBeforePrint = null;
window.addEventListener("beforeprint", () => {
  detailsBeforePrint = [...document.querySelectorAll("details")].map((detail) => [detail, detail.open]);
  detailsBeforePrint.forEach(([detail]) => { detail.open = true; });
});
window.addEventListener("afterprint", () => {
  if (detailsBeforePrint) detailsBeforePrint.forEach(([detail, open]) => { detail.open = open; });
  detailsBeforePrint = null;
});
document.getElementById("print-guide").addEventListener("click", () => window.print());
