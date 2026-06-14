// Client-side search and tag filtering for the index.
// Progressive enhancement: with JS off, the full list renders normally.
(function () {
  "use strict";

  var input = document.querySelector(".search");
  var tagButtons = Array.prototype.slice.call(
    document.querySelectorAll(".filter-tags .tag")
  );
  var items = Array.prototype.slice.call(
    document.querySelectorAll(".post-item")
  );
  var noResults = document.querySelector(".no-results");
  if (!input || !items.length) return;

  var query = "";
  var activeTag = null;

  function apply() {
    var visible = 0;
    items.forEach(function (item) {
      var hay = item.getAttribute("data-search") || "";
      var tags = (item.getAttribute("data-tags") || "").split(",");
      var matchText = !query || hay.indexOf(query) !== -1;
      var matchTag = !activeTag || tags.indexOf(activeTag) !== -1;
      var show = matchText && matchTag;
      item.hidden = !show;
      if (show) visible++;
    });
    if (noResults) noResults.hidden = visible !== 0;
  }

  input.addEventListener("input", function () {
    query = input.value.trim().toLowerCase();
    apply();
  });

  tagButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tag = btn.getAttribute("data-tag");
      activeTag = activeTag === tag ? null : tag;
      tagButtons.forEach(function (b) {
        b.classList.toggle("active", b === btn && activeTag !== null);
      });
      apply();
    });
  });

  // Allow Escape to clear the search field.
  input.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      input.value = "";
      query = "";
      apply();
    }
  });
})();
