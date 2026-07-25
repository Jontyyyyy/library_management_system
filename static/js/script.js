document.addEventListener("DOMContentLoaded", function () {
  // Mobile sidebar toggle
  var toggle = document.getElementById("navToggle");
  var sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  // Confirm before any destructive action (delete book / delete member)
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // Auto-fade flash messages after a few seconds
  document.querySelectorAll(".flash").forEach(function (el, i) {
    setTimeout(function () {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(function () { el.style.display = "none"; }, 400);
    }, 5000 + i * 300);
  });
});
