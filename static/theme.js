// Theme toggle: switches between dark (default) and light, and remembers the
// choice in localStorage so it persists across pages and visits.
//
// The saved theme is applied before first paint by a small inline script in the
// document head (no flash of the wrong colors). This file only syncs the button
// label and writes the choice when the user clicks.
(function () {
  "use strict";
  var btn = document.querySelector(".theme-toggle");
  if (!btn) return;
  var root = document.documentElement;

  function current() {
    return root.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function apply(theme, persist) {
    if (theme === "light") root.setAttribute("data-theme", "light");
    else root.removeAttribute("data-theme");
    btn.textContent = theme;
    if (persist) {
      try { localStorage.setItem("theme", theme); } catch (e) {}
    }
  }

  // Match the label to whatever the head script already applied.
  apply(current(), false);

  btn.addEventListener("click", function () {
    apply(current() === "dark" ? "light" : "dark", true);
  });
})();
