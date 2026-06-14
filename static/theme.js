// Theme toggle: switches between dark (default) and light.
// Nothing is stored — no cookies, no localStorage. The choice applies only to the
// current page and resets to the dark default on navigation.
(function () {
  "use strict";
  var btn = document.querySelector(".theme-toggle");
  if (!btn) return;
  var root = document.documentElement;
  var state = "dark";

  function apply(t) {
    state = t;
    if (t === "light") root.setAttribute("data-theme", "light");
    else root.removeAttribute("data-theme");
    btn.textContent = t;
  }

  apply("dark");
  btn.addEventListener("click", function () {
    apply(state === "dark" ? "light" : "dark");
  });
})();
