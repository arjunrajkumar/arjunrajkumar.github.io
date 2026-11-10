(async function () {
  const chart = document.querySelector("#proof-of-work");
  const days = document.querySelector("#proof-days");
  const details = document.querySelector("#proof-details");
  const range = document.querySelector("#proof-range");
  const previous = document.querySelector("#proof-previous");
  const next = document.querySelector("#proof-next");
  if (!chart) return;

  const history = document.querySelector("#proof-history");
  if (!history) throw new Error("Could not find the learning notes");
  const notes = JSON.parse(history.textContent);

  const indiaDate = new Intl.DateTimeFormat("sv-SE", { timeZone: "Asia/Kolkata" });
  const format = (options) => new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", ...options });
  const dayLabel = format({ day: "numeric", month: "short" });
  const fullDate = format({ dateStyle: "full" });
  const monthLabel = format({ month: "short", year: "numeric" });
  const initialToday = indiaDate.format(new Date());
  const firstRecordedDay = notes.map((note) => note.date).sort()[0] || initialToday;
  const firstMonth = firstRecordedDay.slice(0, 7);
  let selectedMonth = initialToday.slice(0, 7);
  let renderedMonth;
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

  function adjacentMonth(offset) {
    const month = new Date(selectedMonth + "-01T00:00:00Z");
    month.setUTCMonth(month.getUTCMonth() + offset);
    return month;
  }

  function changeMonth(offset) {
    const month = adjacentMonth(offset).toISOString().slice(0, 7);
    const currentMonth = indiaDate.format(new Date()).slice(0, 7);
    if (month < firstMonth || month > currentMonth) return;
    const focused = document.activeElement;
    selectedMonth = month;
    renderDays();
    if (focused === previous && previous.hidden) next.focus();
    if (focused === next && next.hidden) previous.focus();
  }

  function renderDays() {
    const today = indiaDate.format(new Date());
    const currentMonth = today.slice(0, 7);
    // Follow the new month only when the reader was viewing the current month.
    if (lastDay && selectedMonth === renderedMonth && selectedMonth === lastDay.slice(0, 7)) {
      selectedMonth = currentMonth;
    }
    if (today === lastDay && selectedMonth === renderedMonth) return;
    lastDay = today;
    renderedMonth = selectedMonth;
    closeDetails();
    days.replaceChildren();
    const start = new Date(selectedMonth + "-01T00:00:00Z");
    const end = new Date(start);
    end.setUTCMonth(end.getUTCMonth() + 1, 0);
    const dayCount = end.getUTCDate();
    days.style.setProperty("--proof-day-count", dayCount);
    range.textContent = monthLabel.format(start);
    chart.setAttribute("aria-label", "Bitcoin learning notes for " + range.textContent);
    previous.hidden = selectedMonth <= firstMonth;
    next.hidden = selectedMonth >= currentMonth;
    previous.setAttribute("aria-label", "Show " + monthLabel.format(adjacentMonth(-1)));
    next.setAttribute("aria-label", "Show " + monthLabel.format(adjacentMonth(1)));

    for (let offset = 0; offset < dayCount; offset++) {
      const day = new Date(start);
      day.setUTCDate(start.getUTCDate() + offset);
      const key = day.toISOString().slice(0, 10);
      const entries = notes.filter((note) => note.date === key);
      const label = fullDate.format(day);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "proof-day";
      button.dataset.date = key;
      if (offset % 7 === 0) button.dataset.weekStart = "";
      if (entries.length) button.dataset.written = "";
      else if (key >= firstRecordedDay && key <= today) button.dataset.missing = "";
      button.setAttribute("aria-label", label + (entries.length ? ", written work" : ", no written work"));
      button.setAttribute("aria-controls", details.id);
      button.setAttribute("aria-expanded", "false");
      const track = document.createElement("span");
      track.className = "proof-track";
      track.setAttribute("aria-hidden", "true");
      button.append(track);
      if ((offset % 7 === 0 && offset < dayCount - 3) || offset === dayCount - 1) {
        const tick = document.createElement("span");
        tick.className = "proof-date";
        tick.setAttribute("aria-hidden", "true");
        tick.textContent = dayLabel.format(day);
        button.append(tick);
      }

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
      days.append(button);
    }
    chart.hidden = false;
  }

  previous.addEventListener("click", () => changeMonth(-1));
  next.addEventListener("click", () => changeMonth(1));

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
  document.addEventListener("visibilitychange", renderDays);
  renderDays();
  window.setInterval(renderDays, 60000);
})().catch(console.error);
