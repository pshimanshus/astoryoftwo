(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var nav = document.getElementById("site-nav");
  var navToggle = document.getElementById("nav-toggle");
  var navLinks = document.getElementById("nav-links");
  var parallaxItems = Array.prototype.slice.call(document.querySelectorAll("[data-parallax]"));
  var revealItems = Array.prototype.slice.call(document.querySelectorAll(".paper-chapter, .story-stack"));

  function setNavState() {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 18);
  }

  function setPaperMotion() {
    if (reduceMotion) return;

    var viewportCenter = window.innerHeight / 2;
    parallaxItems.forEach(function (item) {
      var speed = Number(item.getAttribute("data-parallax") || 0);
      var rect = item.getBoundingClientRect();
      var itemCenter = rect.top + rect.height / 2;
      var progress = (itemCenter - viewportCenter) / window.innerHeight;
      var y = Math.max(-42, Math.min(42, progress * speed));
      item.style.setProperty("--parallax-y", y.toFixed(2) + "px");
    });
  }

  function onScroll() {
    setNavState();
    setPaperMotion();
  }

  function revealVisibleItems() {
    revealItems.forEach(function (item) {
      var rect = item.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.95 && rect.bottom > 0) {
        item.classList.add("is-visible");
      }
    });
  }

  function getHashTarget(hash) {
    if (!hash || hash === "#") return null;
    try {
      return document.getElementById(decodeURIComponent(hash.slice(1)));
    } catch (error) {
      return null;
    }
  }

  function alignHashTarget(behavior) {
    var target = getHashTarget(window.location.hash);
    if (!target) return;
    target.classList.add("is-visible");
    target.scrollIntoView({ block: "start", behavior: behavior || "auto" });
    window.setTimeout(function () {
      revealVisibleItems();
      setNavState();
      setPaperMotion();
    }, 80);
  }

  function bindChapterLinks() {
    var links = Array.prototype.slice.call(document.querySelectorAll('a[href^="#"]'));
    links.forEach(function (link) {
      link.addEventListener("click", function (event) {
        var target = getHashTarget(link.getAttribute("href"));
        if (!target) return;
        event.preventDefault();
        target.classList.add("is-visible");
        target.scrollIntoView({ block: "start", behavior: reduceMotion ? "auto" : "smooth" });
        history.pushState(null, "", link.getAttribute("href"));
        window.setTimeout(function () {
          revealVisibleItems();
          setNavState();
          setPaperMotion();
        }, reduceMotion ? 0 : 420);
      });
    });
  }

  setNavState();
  setPaperMotion();
  alignHashTarget("auto");
  bindChapterLinks();
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", setPaperMotion);

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      var isOpen = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", isOpen ? "false" : "true");
      navLinks.classList.toggle("is-open", !isOpen);
    });

    navLinks.addEventListener("click", function (event) {
      if (event.target && event.target.tagName === "A") {
        navToggle.setAttribute("aria-expanded", "false");
        navLinks.classList.remove("is-open");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        navToggle.setAttribute("aria-expanded", "false");
        navLinks.classList.remove("is-open");
      }
    });
  }

  if ("IntersectionObserver" in window && !reduceMotion) {
    revealItems.forEach(function (item) {
      item.classList.add("is-revealing");
    });

    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.18, rootMargin: "0px 0px -10% 0px" });

    revealItems.forEach(function (item) {
      revealObserver.observe(item);
    });

    revealVisibleItems();
    window.addEventListener("load", revealVisibleItems);
    window.addEventListener("hashchange", function () {
      alignHashTarget("auto");
    });
    window.setTimeout(revealVisibleItems, 320);
  }

  var storyStage = document.getElementById("story-stage");
  var storyCards = Array.prototype.slice.call(document.querySelectorAll(".story-card"));
  var storyPrev = document.getElementById("story-prev");
  var storyNext = document.getElementById("story-next");
  var storyStatus = document.getElementById("story-status");
  var storyIndex = 0;
  var pointerStartX = null;

  function renderStoryStack() {
    storyCards.forEach(function (card, index) {
      card.classList.remove("is-active", "is-next", "is-back");
      if (index === storyIndex) {
        card.classList.add("is-active");
      } else if (index === (storyIndex + 1) % storyCards.length) {
        card.classList.add("is-next");
      } else {
        card.classList.add("is-back");
      }
    });

    if (storyStatus) {
      storyStatus.textContent = (storyIndex + 1) + " / " + storyCards.length;
    }
  }

  function moveStory(delta) {
    if (!storyCards.length) return;
    storyIndex = (storyIndex + delta + storyCards.length) % storyCards.length;
    renderStoryStack();
  }

  if (storyCards.length) {
    renderStoryStack();

    if (storyPrev) {
      storyPrev.addEventListener("click", function () { moveStory(-1); });
    }

    if (storyNext) {
      storyNext.addEventListener("click", function () { moveStory(1); });
    }

    if (storyStage) {
      storyStage.addEventListener("pointerdown", function (event) {
        pointerStartX = event.clientX;
        storyStage.setPointerCapture(event.pointerId);
      });

      storyStage.addEventListener("pointerup", function (event) {
        if (pointerStartX === null) return;
        var delta = event.clientX - pointerStartX;
        if (Math.abs(delta) > 44) {
          moveStory(delta < 0 ? 1 : -1);
        }
        pointerStartX = null;
      });

      storyStage.addEventListener("pointercancel", function () {
        pointerStartX = null;
      });

      storyStage.addEventListener("keydown", function (event) {
        if (event.key === "ArrowLeft") moveStory(-1);
        if (event.key === "ArrowRight") moveStory(1);
      });
    }

    if (!reduceMotion) {
      window.setInterval(function () {
        var rect = storyStage ? storyStage.getBoundingClientRect() : { top: 0, bottom: 0 };
        var visible = rect.top < window.innerHeight && rect.bottom > 0;
        if (visible && document.visibilityState === "visible") {
          moveStory(1);
        }
      }, 5200);
    }
  }
})();
