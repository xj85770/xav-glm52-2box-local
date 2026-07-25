(() => {
  const state = {
    models: [],
    lanes: null,
    sessionId: null,
    sessions: [],
    model: localStorage.getItem("lanes.model") || "lane/smart",
    busy: false,
  };

  const $ = (id) => document.getElementById(id);
  const chatEl = $("chat");
  const emptyEl = $("empty");
  const inputEl = $("input");
  const modelSelect = $("modelSelect");
  const lanePills = $("lanePills");
  const sessionsEl = $("sessions");

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    if (res.headers.get("content-type")?.includes("application/json")) {
      return res.json();
    }
    return res;
  }

  function setStatus(ok, text) {
    const dot = $("statusDot");
    dot.className = "dot " + (ok === true ? "ok" : ok === false ? "bad" : "");
    $("statusText").textContent = text;
  }

  function renderLanePills() {
    const lanes = ["lane/local", "lane/fast", "lane/smart", "lane/code"];
    lanePills.innerHTML = "";
    for (const id of lanes) {
      const info = state.lanes?.lanes?.[id];
      const btn = document.createElement("button");
      btn.className = "lane-pill" + (state.model === id ? " active" : "");
      btn.innerHTML = `<span>${id.replace("lane/", "")}</span><small>${
        info ? `${info.ready_count}/${info.card_count} ready` : "…"
      }</small>`;
      btn.onclick = () => {
        state.model = id;
        localStorage.setItem("lanes.model", id);
        modelSelect.value = id;
        renderLanePills();
        updateMeta();
      };
      lanePills.appendChild(btn);
    }
  }

  function renderModels() {
    const groups = {
      lane: [],
      model: [],
      other: [],
    };
    for (const m of state.models) {
      if (m.kind === "lane" || m.kind === "lane-alias" || m.id === "lanes") groups.lane.push(m);
      else if (m.kind === "model") groups.model.push(m);
      else groups.other.push(m);
    }
    const html = [];
    html.push(`<optgroup label="Lanes">`);
    for (const m of groups.lane.filter((x) => x.kind === "lane" || x.id === "lanes")) {
      const ready = m.ready === false ? " (no ready cards)" : m.ready_count != null ? ` (${m.ready_count} ready)` : "";
      html.push(`<option value="${m.id}">${m.id}${ready}</option>`);
    }
    html.push(`</optgroup>`);
    html.push(`<optgroup label="Individual APIs (ready)">`);
    for (const m of groups.model.filter((x) => x.ready)) {
      html.push(`<option value="${m.id}">${m.id} · ctx ${m.context ?? "?"} · ~${m.tps_typical ?? "?"} t/s</option>`);
    }
    html.push(`</optgroup>`);
    html.push(`<optgroup label="Individual APIs (need key)">`);
    for (const m of groups.model.filter((x) => !x.ready)) {
      html.push(`<option value="${m.id}">${m.id} · needs ${m.requires_env || "key"}</option>`);
    }
    html.push(`</optgroup>`);
    modelSelect.innerHTML = html.join("");
    if (![...modelSelect.options].some((o) => o.value === state.model)) {
      state.model = "lane/smart";
    }
    modelSelect.value = state.model;
  }

  function renderSessions() {
    sessionsEl.innerHTML = "";
    for (const s of state.sessions) {
      const b = document.createElement("button");
      b.className = "session-item" + (s.id === state.sessionId ? " active" : "");
      b.innerHTML = `<div class="t">${escapeHtml(s.title || "chat")}</div><div class="m">${escapeHtml(s.model)} · ${s.messages} msgs</div>`;
      b.onclick = () => loadSession(s.id);
      sessionsEl.appendChild(b);
    }
  }

  function updateMeta() {
    $("chatMeta").textContent = `model: ${state.model}  ·  backend: lanes2`;
    const ready = state.models.filter((m) => m.kind === "model" && m.ready).length;
    const total = state.models.filter((m) => m.kind === "model").length;
    $("readyMeta").textContent = total ? `${ready}/${total} APIs ready` : "";
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function appendMsg(role, content) {
    emptyEl.style.display = "none";
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.innerHTML = `<div class="who">${role}</div><div class="body"></div>`;
    div.querySelector(".body").textContent = content;
    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
    return div.querySelector(".body");
  }

  function clearChat() {
    [...chatEl.querySelectorAll(".msg")].forEach((n) => n.remove());
    emptyEl.style.display = "";
  }

  async function refreshHealth() {
    try {
      const h = await api("/health");
      if (h.lanes2_health?.ok) setStatus(true, `lanes2 online · ${h.lanes2}`);
      else setStatus(false, `lanes2 down · start lanes2 first`);
    } catch (e) {
      setStatus(false, String(e.message || e));
    }
  }

  async function refreshModels() {
    const [models, lanes] = await Promise.all([api("/api/models"), api("/api/lanes")]);
    state.models = models.data || [];
    state.lanes = lanes;
    renderModels();
    renderLanePills();
    updateMeta();
  }

  async function refreshSessions() {
    const data = await api("/api/sessions");
    state.sessions = data.sessions || [];
    renderSessions();
  }

  async function loadSession(id) {
    const s = await api(`/api/sessions/${id}`);
    state.sessionId = s.id;
    state.model = s.model || state.model;
    modelSelect.value = state.model;
    localStorage.setItem("lanes.model", state.model);
    $("chatTitle").textContent = s.title || "chat";
    clearChat();
    for (const m of s.messages || []) appendMsg(m.role, m.content);
    renderSessions();
    renderLanePills();
    updateMeta();
  }

  async function newChat() {
    const s = await api("/api/sessions", {
      method: "POST",
      body: JSON.stringify({ model: state.model }),
    });
    state.sessionId = s.id;
    $("chatTitle").textContent = s.title;
    clearChat();
    await refreshSessions();
  }

  async function send() {
    if (state.busy) return;
    const content = inputEl.value.trim();
    if (!content) return;
    state.busy = true;
    $("btnSend").disabled = true;
    inputEl.value = "";
    appendMsg("user", content);
    const bodyEl = appendMsg("assistant", "");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.sessionId,
          model: state.model,
          content,
          stream: true,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() || "";
        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;
          const obj = JSON.parse(line.slice(6));
          if (obj.type === "session") {
            state.sessionId = obj.session_id;
          } else if (obj.type === "token") {
            bodyEl.textContent += obj.content;
            chatEl.scrollTop = chatEl.scrollHeight;
          } else if (obj.type === "error") {
            bodyEl.textContent += `\n[error] ${obj.error}`;
          } else if (obj.type === "done") {
            await refreshSessions();
            $("chatTitle").textContent =
              state.sessions.find((s) => s.id === state.sessionId)?.title || "chat";
          }
        }
      }
    } catch (e) {
      bodyEl.textContent += `\n[error] ${e.message || e}`;
    } finally {
      state.busy = false;
      $("btnSend").disabled = false;
      inputEl.focus();
    }
  }

  modelSelect.onchange = () => {
    state.model = modelSelect.value;
    localStorage.setItem("lanes.model", state.model);
    renderLanePills();
    updateMeta();
  };
  $("btnNew").onclick = () => newChat();
  $("btnRefresh").onclick = async () => {
    await refreshHealth();
    await refreshModels();
  };
  $("btnSend").onclick = send;
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  (async () => {
    await refreshHealth();
    try {
      await refreshModels();
    } catch (e) {
      setStatus(false, `lanes2 models failed: ${e.message || e}`);
    }
    await refreshSessions();
    if (!state.sessionId) await newChat();
  })();
})();
