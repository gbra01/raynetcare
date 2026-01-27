function getOutbox() {
  return JSON.parse(localStorage.getItem("raynetcare_outbox_notes") || "[]");
}
function setOutbox(items) {
  localStorage.setItem("raynetcare_outbox_notes", JSON.stringify(items));
}

function isForcedOffline() {
  return localStorage.getItem("raynetcare_force_offline") === "1";
}
function setForcedOffline(on) {
  localStorage.setItem("raynetcare_force_offline", on ? "1" : "0");
}
function isActuallyOnline() {
  return navigator.onLine && !isForcedOffline();
}
function addToOutbox(note) {
  const items = getOutbox();
  items.push(note);
  setOutbox(items);
}
function outboxCount() {
  return getOutbox().length;
}
function uid() {
  return "offline-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
}
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function syncNotes() {
  const items = getOutbox();
  if (items.length === 0) {
    alert("No offline notes to sync.");
    return;
  }
  fetch("/sync/push-notes/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ notes: items })
  })
    .then(r => r.json())
    .then(result => {
      if (result.errors && result.errors.length) {
        alert("Some notes failed to sync. Please try again.");
        return;
      }
      localStorage.removeItem("raynetcare_outbox_notes");
      alert(`✅ Synced ${result.saved} note(s).`);
      location.reload();
    })
    .catch(() => alert("Could not sync. Are you online?"));
}