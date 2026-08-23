/* A Story of Two — interactions: reveals, nav, carousel, count-up, reel sort, room nav */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- scroll reveals ---------- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.16, rootMargin: "0px 0px -8% 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* ---------- nav: solidify on scroll ---------- */
  var nav = document.getElementById("nav");
  var onScroll = function () {
    if (window.scrollY > 40) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  };
  if (nav) { onScroll(); window.addEventListener("scroll", onScroll, { passive: true }); }

  /* ---------- mobile menu ---------- */
  var navToggle = document.getElementById("navtoggle");
  var navLinks = document.getElementById("navlinks");
  if (navToggle && navLinks) {
    var setMenu = function (open) {
      navLinks.classList.toggle("open", open);
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };
    navToggle.addEventListener("click", function () {
      setMenu(navToggle.getAttribute("aria-expanded") !== "true");
    });
    navLinks.addEventListener("click", function (e) {
      if (e.target.tagName === "A") setMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setMenu(false);
    });
  }

  /* ---------- carousel ---------- */
  var track = document.getElementById("track");
  if (track) {
    var slides = track.children.length;
    var idx = 0;
    var dotsWrap = document.getElementById("dots");
    var prev = document.getElementById("prev");
    var next = document.getElementById("next");

    for (var i = 0; i < slides; i++) {
      var dot = document.createElement("button");
      dot.setAttribute("aria-label", "Go to slide " + (i + 1));
      (function (n) { dot.addEventListener("click", function () { go(n); }); })(i);
      dotsWrap.appendChild(dot);
    }
    var dots = dotsWrap.children;

    function render() {
      track.style.transform = "translateX(" + (-idx * 100) + "%)";
      for (var j = 0; j < dots.length; j++) {
        dots[j].setAttribute("aria-current", j === idx ? "true" : "false");
      }
    }
    function go(n) { idx = (n + slides) % slides; render(); }
    prev.addEventListener("click", function () { go(idx - 1); });
    next.addEventListener("click", function () { go(idx + 1); });
    render();

    var carousel = document.getElementById("carousel");
    carousel.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") go(idx - 1);
      if (e.key === "ArrowRight") go(idx + 1);
    });

    var startX = null;
    carousel.addEventListener("touchstart", function (e) { startX = e.touches[0].clientX; }, { passive: true });
    carousel.addEventListener("touchend", function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 44) go(idx + (dx < 0 ? 1 : -1));
      startX = null;
    });
  }

  /* ---------- count-up stats ---------- */
  var statNums = Array.prototype.slice.call(document.querySelectorAll("[data-count]"));
  function animateCount(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    var decimals = (target % 1 !== 0) ? 1 : 0;
    if (reduceMotion) { el.textContent = target.toFixed(decimals); return; }
    var dur = 1400, start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = target.toFixed(decimals);
    }
    requestAnimationFrame(step);
  }
  if ("IntersectionObserver" in window && statNums.length) {
    var sio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { animateCount(e.target); sio.unobserve(e.target); }
      });
    }, { threshold: 0.6 });
    statNums.forEach(function (el) { sio.observe(el); });
  } else {
    statNums.forEach(function (el) { el.textContent = el.getAttribute("data-count"); });
  }

  /* ---------- reel wall sorting ---------- */
  var grid = document.getElementById("rgrid");
  var sortbar = document.querySelector(".sortbar");
  if (grid && sortbar) {
    var cards = Array.prototype.slice.call(grid.children);
    var keyOf = function (el, k) {
      if (k === "ts") return Date.parse(el.getAttribute("data-ts")) || 0;
      return parseInt(el.getAttribute("data-" + k), 10) || 0;
    };
    sortbar.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-sort]");
      if (!btn) return;
      var k = btn.getAttribute("data-sort");
      Array.prototype.forEach.call(sortbar.querySelectorAll("button"), function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      cards.sort(function (a, b) { return keyOf(b, k) - keyOf(a, k); });
      cards.forEach(function (c) { grid.appendChild(c); });
    });
  }

  /* ---------- move through the world: prev/next room band ---------- */
  var order = ["index.html", "reels.html", "stories.html", "memory.html", "studio.html", "brands.html"];
  var labels = { "index.html": "The World", "reels.html": "The Reels", "stories.html": "The Stories", "memory.html": "The Memory", "studio.html": "The Studio", "brands.html": "For Brands" };
  var path = (location.pathname.split("/").pop() || "index.html");
  var footerEl = document.querySelector(".footer");
  var pos = order.indexOf(path);
  if (pos > 0 && footerEl) {
    var prevRoom = order[(pos - 1 + order.length) % order.length];
    var nextRoom = order[(pos + 1) % order.length];
    var band = document.createElement("nav");
    band.className = "roomnav";
    band.setAttribute("aria-label", "Move through the world");
    band.innerHTML =
      '<a href="' + prevRoom + '"><span class="roomnav__dir">← back a room</span><span class="roomnav__name">' + labels[prevRoom] + "</span></a>" +
      '<a href="' + nextRoom + '"><span class="roomnav__dir">next room →</span><span class="roomnav__name">' + labels[nextRoom] + "</span></a>";
    footerEl.parentNode.insertBefore(band, footerEl);
  }
})();
