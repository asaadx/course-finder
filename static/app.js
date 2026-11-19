// Course Finder front end. Plain JS, no dependencies.
// All API data is rendered with textContent / createElement, never innerHTML.
(function () {
  "use strict";

  var DEBOUNCE_MS = 250;

  var els = {
    form: document.getElementById("search-form"),
    input: document.getElementById("search-input"),
    results: document.getElementById("results"),
    resultsStatus: document.getElementById("results-status"),
    enrolledList: document.getElementById("enrolled-list"),
    enrolledStatus: document.getElementById("enrolled-status"),
  };

  // Course ids the learner is enrolled in (from the sidebar data and enroll calls).
  var enrolledIds = new Set();
  var searchController = null;
  var debounceTimer = null;

  // ---------- helpers ----------

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function setStatus(node, message, isError) {
    node.textContent = message || "";
    node.classList.toggle("error", Boolean(isError));
  }

  // fetch JSON; throws an Error with .status and the API's {"error"} message on non-2xx.
  function fetchJSON(url, options) {
    return fetch(url, options).then(function (res) {
      return res
        .json()
        .catch(function () { return null; })
        .then(function (body) {
          if (!res.ok) {
            var msg = body && typeof body.error === "string" ? body.error : "Request failed (" + res.status + ")";
            var err = new Error(msg);
            err.status = res.status;
            throw err;
          }
          return body;
        });
    });
  }

  // ---------- sidebar ----------

  function renderEnrollments(enrollments) {
    els.enrolledList.replaceChildren();
    enrollments.forEach(function (enrollment) {
      addEnrolledCourse(enrollment.course);
    });
    updateEnrolledEmptyState();
  }

  function addEnrolledCourse(course) {
    if (!course) return;
    enrolledIds.add(course.id);
    var li = el("li");
    li.dataset.courseId = String(course.id);
    li.append(el("span", "code", course.code), el("span", "title", course.title));
    els.enrolledList.append(li);
    updateEnrolledEmptyState();
  }

  function updateEnrolledEmptyState() {
    if (els.enrolledList.children.length === 0) {
      setStatus(els.enrolledStatus, "You are not enrolled in any courses yet.");
    } else {
      setStatus(els.enrolledStatus, "");
    }
  }

  function loadEnrollments() {
    return fetchJSON("/api/enrollments")
      .then(function (data) {
        renderEnrollments(Array.isArray(data) ? data : []);
      })
      .catch(function () {
        setStatus(els.enrolledStatus, "Could not load your enrollments. Check your connection.", true);
      });
  }

  // ---------- results ----------

  function isEnrolled(course) {
    return Boolean(course.enrolled) || enrolledIds.has(course.id);
  }

  function renderEnrolledBadge(action) {
    action.replaceChildren(el("span", "badge", "Enrolled"));
  }

  function renderResultAction(action, course) {
    if (isEnrolled(course)) {
      renderEnrolledBadge(action);
      return;
    }
    var btn = el("button", "btn", "Enroll");
    btn.type = "button";
    btn.setAttribute("aria-label", "Enroll in " + course.code + " " + course.title);
    action.replaceChildren(btn);
  }

  function renderResult(course) {
    var li = el("li", "result");
    li.dataset.courseId = String(course.id);

    var body = el("div", "result-body");
    body.append(el("span", "code", course.code), el("h3", null, course.title), el("p", null, course.description));

    var action = el("div", "result-action");
    renderResultAction(action, course);

    li.append(body, action);
    return li;
  }

  function renderResults(courses) {
    els.results.replaceChildren();
    if (courses.length === 0) {
      setStatus(els.resultsStatus, "No courses found.");
      return;
    }
    setStatus(els.resultsStatus, courses.length + (courses.length === 1 ? " course" : " courses"));
    var frag = document.createDocumentFragment();
    courses.forEach(function (course) { frag.append(renderResult(course)); });
    els.results.append(frag);
  }

  // ---------- search ----------

  function search(query) {
    if (searchController) searchController.abort();
    var controller = new AbortController();
    searchController = controller;

    setStatus(els.resultsStatus, "Searching...");
    return fetchJSON("/api/courses?q=" + encodeURIComponent(query), { signal: controller.signal })
      .then(function (data) {
        if (controller !== searchController) return; // stale
        renderResults(Array.isArray(data) ? data : []);
      })
      .catch(function (err) {
        if (err.name === "AbortError" || controller !== searchController) return;
        els.results.replaceChildren();
        setStatus(els.resultsStatus, "Could not load courses. Check your connection and try again.", true);
      });
  }

  function onSearchInput() {
    clearTimeout(debounceTimer);
    var query = els.input.value.trim();
    debounceTimer = setTimeout(function () { search(query); }, DEBOUNCE_MS);
  }

  // ---------- enroll ----------

  function showInlineError(action, message) {
    var existing = action.querySelector(".inline-error");
    if (existing) existing.remove();
    var msg = el("p", "inline-error", message);
    msg.setAttribute("role", "alert");
    action.append(msg);
  }

  function markEnrolledInResults(courseId) {
    var item = els.results.querySelector('li[data-course-id="' + String(Number(courseId)) + '"]');
    if (item) renderEnrolledBadge(item.querySelector(".result-action"));
  }

  function enroll(courseId, btn) {
    var action = btn.parentElement;
    btn.disabled = true;
    btn.textContent = "Enrolling...";
    var oldError = action.querySelector(".inline-error");
    if (oldError) oldError.remove();

    return fetchJSON("/api/enrollments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ course_id: courseId }),
    })
      .then(function (enrollment) {
        if (enrollment && enrollment.course) {
          if (!enrolledIds.has(courseId)) addEnrolledCourse(enrollment.course);
        } else {
          loadEnrollments(); // unexpected body: resync the sidebar from the server
        }
        enrolledIds.add(courseId);
        markEnrolledInResults(courseId);
      })
      .catch(function (err) {
        if (err.status === 409) {
          // Already enrolled on the server: reflect that, and resync the sidebar.
          enrolledIds.add(courseId);
          markEnrolledInResults(courseId);
          var item = els.results.querySelector('li[data-course-id="' + courseId + '"] .result-action');
          if (item) showInlineError(item, err.message);
          loadEnrollments();
          return;
        }
        btn.disabled = false;
        btn.textContent = "Enroll";
        var message = err.status ? err.message : "Network error. Please try again.";
        showInlineError(action, message);
      });
  }

  function onResultsClick(e) {
    var btn = e.target.closest("button.btn");
    if (!btn || btn.disabled || !els.results.contains(btn)) return;
    var item = btn.closest("li.result");
    var courseId = Number(item && item.dataset.courseId);
    if (!Number.isInteger(courseId)) return;
    enroll(courseId, btn);
  }

  // ---------- init ----------

  function init() {
    els.input.addEventListener("input", onSearchInput);
    els.results.addEventListener("click", onResultsClick);
    els.form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearTimeout(debounceTimer);
      search(els.input.value.trim());
    });

    // Load enrollments first so enrolledIds is populated before results render.
    loadEnrollments().then(function () { return search(""); });
  }

  init();
})();
