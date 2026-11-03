(async function () {
  const chart = document.querySelector("#proof-of-work");
  const week = document.querySelector("#proof-week");
  const details = document.querySelector("#proof-details");
  const range = document.querySelector("#proof-range");
  if (!chart) return;

  const response = await fetch("/assets/proof-of-work.json");
  if (!response.ok) throw new Error("Could not load the learning notes");
  const notes = await response.json();

  const indiaDate = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Kolkata" });
  const format = (options) => new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", ...options });
  const weekday = format({ weekday: "short" });
  const fullDate = format({ dateStyle: "full" });
  const shortDate = format({ day: "numeric", month: "short", year: "numeric" });
  let lastDay;
  let active;
  let pinned = false;

  function closeDetails() {
    active?.setAttribute("aria-expanded", "false");
    active = null;
    pinned = false;
    details.hidden = true;
  }

  function positionDetails() {
    if (!active) return;
    const middle = active.offsetLeft + active.offsetWidth / 2;
    const left = Math.min(middle - details.offsetWidth / 2, chart.clientWidth - details.offsetWidth);
    details.style.left = Math.max(0, left) + "px";
  }

  function showDay(button, label, entries) {
    active?.setAttribute("aria-expanded", "false");
    active = button;
    button.setAttribute("aria-expanded", "true");
    const title = document.createElement("strong");
    title.textContent = label;
    details.replaceChildren(title);
    if (entries.length) {
      const list = document.createElement("ul");
      for (const entry of entries) {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = entry.href;
        link.textContent = entry.topic;
        item.append(link);
        list.append(item);
      }
      details.append(list);
    } else {
      const empty = document.createElement("div");
      empty.textContent = "No written work.";
      details.append(empty);
    }
    details.hidden = false;
    positionDetails();
  }

  function renderWeek() {
    const today = indiaDate.format(new Date());
    if (today === lastDay) return;
    lastDay = today;
    closeDetails();
    week.replaceChildren();
    const end = new Date(today + "T00:00:00Z");
    const start = new Date(end);
    start.setUTCDate(end.getUTCDate() - 6);
    range.textContent = shortDate.formatRange(start, end);

    for (let offset = 0; offset < 7; offset++) {
      const day = new Date(start);
      day.setUTCDate(start.getUTCDate() + offset);
      const key = day.toISOString().slice(0, 10);
      const entries = notes.filter((note) => note.date === key);
      const label = fullDate.format(day);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "proof-day";
      button.dataset.date = key;
      if (entries.length) button.dataset.written = "";
      button.setAttribute("aria-label", label + (entries.length ? ", written work" : ", no written work"));
      button.setAttribute("aria-controls", details.id);
      button.setAttribute("aria-expanded", "false");
      const track = document.createElement("span");
      track.className = "proof-track";
      track.setAttribute("aria-hidden", "true");
      button.append(track, weekday.format(day));

      const show = () => showDay(button, label, entries);
      button.addEventListener("pointerenter", (event) => {
        if (event.pointerType === "mouse" && !pinned) show();
      });
      button.addEventListener("focus", () => { pinned = false; show(); });
      button.addEventListener("click", (event) => {
        if (pinned && active === button) return closeDetails();
        show();
        pinned = true;
        if (event.detail === 0) details.querySelector("a")?.focus();
      });
      week.append(button);
    }
    chart.hidden = false;
  }

  chart.addEventListener("pointerleave", (event) => {
    if (!pinned && event.pointerType === "mouse" && !details.contains(document.activeElement)) closeDetails();
  });
  chart.addEventListener("focusout", (event) => {
    if (event.relatedTarget && !chart.contains(event.relatedTarget)) closeDetails();
  });
  document.addEventListener("pointerdown", (event) => {
    if (!chart.contains(event.target)) closeDetails();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && active) {
      if (details.contains(document.activeElement)) active.focus();
      closeDetails();
    }
  });
  window.addEventListener("resize", positionDetails);
  document.addEventListener("visibilitychange", renderWeek);
  renderWeek();
  window.setInterval(renderWeek, 60000);
})().catch(console.error);
