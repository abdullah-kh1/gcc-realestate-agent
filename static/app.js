(() => {
  const STORAGE_KEY = "horizon.activeConversation";
  const TYPING_DELAY_MS = 700;
  const STARTERS = [
    "I'm looking for an apartment in Dubai",
    "أبي شقة في دبي",
    "What are the DLD fees in Dubai?",
    "هل يقدر الأجنبي يتملك في السعودية؟",
  ];
  const STATUS_LABELS = { new: "New", active: "In progress", qualified: "Qualified", booked: "Booked" };
  const FACTS = [
    ["market", "Market"],
    ["purpose", "Purpose"],
    ["budget", "Budget"],
    ["timeline", "Timeline"],
    ["name", "Name"],
  ];

  const el = (id) => document.getElementById(id);
  const refs = {
    app: el("app"),
    list: el("conversationList"),
    newChat: el("newChat"),
    menuBtn: el("menuBtn"),
    infoBtn: el("infoBtn"),
    scrim: el("scrim"),
    title: el("chatTitle"),
    subtitle: el("chatSubtitle"),
    messages: el("messages"),
    chips: el("chips"),
    composer: el("composer"),
    input: el("input"),
    sendBtn: el("sendBtn"),
    profileCount: el("profileCount"),
    progressBar: el("progressBar"),
    facts: el("facts"),
    meetingPill: el("meetingPill"),
    meetingText: el("meetingText"),
    bookingCount: el("bookingCount"),
    bookings: el("bookings"),
    toast: el("toast"),
  };

  const store = { conversations: [], activeId: null, view: null, sending: false, toastTimer: null };

  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };

  const request = async (path, options = {}) => {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    return response.json();
  };

  const remember = (id) => {
    try {
      if (id) localStorage.setItem(STORAGE_KEY, id);
      else localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      return;
    }
  };

  const recall = () => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return null;
    }
  };

  const showToast = (message) => {
    refs.toast.textContent = message;
    refs.toast.classList.add("show");
    clearTimeout(store.toastTimer);
    store.toastTimer = setTimeout(() => refs.toast.classList.remove("show"), 3200);
  };

  const closeDrawers = () => refs.app.classList.remove("show-sidebar", "show-insights");

  const formatClock = (iso) => {
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const formatListTime = (iso) => {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    const today = new Date();
    if (date.toDateString() === today.toDateString()) return formatClock(iso);
    return date.toLocaleDateString([], { day: "numeric", month: "short" });
  };

  const renderConversationList = () => {
    refs.list.replaceChildren();
    if (!store.conversations.length) {
      refs.list.appendChild(node("li", "empty-list", "No conversations yet."));
      return;
    }
    store.conversations.forEach((conversation) => {
      const item = node("li");
      const button = node("div", "conversation-item");
      button.setAttribute("role", "button");
      button.tabIndex = 0;
      if (conversation.id === store.activeId) button.classList.add("active");

      const top = node("div", "conversation-top");
      top.append(node("span", "conversation-name", conversation.title), node("span", "conversation-time", formatListTime(conversation.updated_at)));
      const badge = node("span", `badge ${conversation.status}`, STATUS_LABELS[conversation.status] || "New");
      const remove = node("button", "delete-btn", "×");
      remove.type = "button";
      remove.setAttribute("aria-label", "Delete conversation");
      remove.addEventListener("click", (event) => {
        event.stopPropagation();
        removeConversation(conversation.id);
      });

      button.append(top, node("span", "conversation-preview", conversation.preview), badge, remove);
      button.addEventListener("click", () => openConversation(conversation.id));
      button.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openConversation(conversation.id);
        }
      });
      item.appendChild(button);
      refs.list.appendChild(item);
    });
  };

  const buildMessage = (message) => {
    const wrapper = node("div", `message ${message.role}`);
    const bubble = node("div", "bubble", message.content);
    bubble.dir = "auto";
    wrapper.append(bubble, node("span", "stamp", formatClock(message.at)));
    return wrapper;
  };

  const buildTyping = () => {
    const wrapper = node("div", "message assistant typing");
    const bubble = node("div", "bubble");
    bubble.append(node("span", "dot"), node("span", "dot"), node("span", "dot"));
    wrapper.appendChild(bubble);
    return wrapper;
  };

  const renderMessages = (messages, typing) => {
    refs.messages.replaceChildren();
    if (!messages.length && !typing) {
      const welcome = node("div", "welcome");
      welcome.append(node("h2", "", "Start a conversation"), node("p", "", "Write in English or Arabic. The consultant replies in your language."));
      refs.messages.appendChild(welcome);
      return;
    }
    messages.forEach((message) => refs.messages.appendChild(buildMessage(message)));
    if (typing) refs.messages.appendChild(buildTyping());
    refs.messages.scrollTop = refs.messages.scrollHeight;
  };

  const renderChips = (view) => {
    refs.chips.replaceChildren();
    if (!view || store.sending) return;
    if (view.awaiting === "slot_choice" && view.slots.length) {
      view.slots.forEach((slot) => {
        const chip = node("button", "chip slot", slot.label);
        chip.type = "button";
        chip.dir = "auto";
        chip.addEventListener("click", () => sendMessage(String(slot.index)));
        refs.chips.appendChild(chip);
      });
      return;
    }
    if (!view.messages.length) {
      STARTERS.forEach((text) => {
        const chip = node("button", "chip", text);
        chip.type = "button";
        chip.dir = "auto";
        chip.addEventListener("click", () => sendMessage(text));
        refs.chips.appendChild(chip);
      });
    }
  };

  const renderInsights = (view) => {
    const profile = view.profile;
    refs.profileCount.textContent = `${profile.completed} of 4`;
    refs.progressBar.style.width = `${(profile.completed / 4) * 100}%`;
    refs.facts.replaceChildren();
    FACTS.forEach(([key, label]) => {
      const row = node("div", "fact");
      const value = node("dd", profile[key] ? "" : "empty", profile[key] || "Pending");
      row.append(node("dt", "", label), value);
      refs.facts.appendChild(row);
    });

    const booking = view.booking;
    refs.meetingPill.className = "pill";
    if (booking.status === "BOOKED") {
      refs.meetingPill.textContent = "Booked";
      refs.meetingPill.classList.add("good");
      refs.meetingText.replaceChildren(node("strong", "", booking.label), document.createTextNode(`Reference ${booking.reference}`));
    } else if (booking.status === "SLOTS_OFFERED") {
      refs.meetingPill.textContent = "Awaiting choice";
      refs.meetingPill.classList.add("pending");
      refs.meetingText.textContent = "Time slots were offered. Waiting for the lead to pick one.";
    } else {
      refs.meetingPill.textContent = "Not scheduled";
      refs.meetingText.textContent = "A call is arranged once the lead is qualified.";
    }
  };

  const renderBookings = (bookings) => {
    refs.bookingCount.textContent = String(bookings.length);
    refs.bookings.replaceChildren();
    if (!bookings.length) {
      refs.bookings.appendChild(node("li", "bookings-empty", "No calls booked yet."));
      return;
    }
    bookings.forEach((booking) => {
      const item = node("li", "booking");
      item.append(node("strong", "", booking.label), node("span", "", `${booking.name} · ${booking.reference}`));
      refs.bookings.appendChild(item);
    });
  };

  const renderView = (view, typing = false, pending = null) => {
    store.view = view;
    refs.title.textContent = view.title;
    refs.subtitle.textContent = view.profile.qualified ? "Qualified lead" : "Property consultant desk";
    const messages = pending ? [...view.messages, pending] : view.messages;
    renderMessages(messages, typing);
    renderChips(view);
    renderInsights(view);
  };

  const refreshSidebar = async () => {
    const [conversations, bookings] = await Promise.all([request("/api/conversations"), request("/api/bookings")]);
    store.conversations = conversations.conversations;
    renderConversationList();
    renderBookings(bookings.bookings);
  };

  const openConversation = async (id) => {
    try {
      const view = await request(`/api/conversations/${encodeURIComponent(id)}`);
      store.activeId = id;
      remember(id);
      renderView(view);
      renderConversationList();
      closeDrawers();
      refs.input.focus();
    } catch (error) {
      showToast("Could not open that conversation.");
    }
  };

  const createConversation = async () => {
    try {
      const view = await request("/api/conversations", { method: "POST", body: "{}" });
      store.activeId = view.id;
      remember(view.id);
      renderView(view);
      await refreshSidebar();
      closeDrawers();
      refs.input.focus();
    } catch (error) {
      showToast("Could not start a new conversation.");
    }
  };

  const removeConversation = async (id) => {
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await request(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
      await refreshSidebar();
      if (id === store.activeId) {
        if (store.conversations.length) await openConversation(store.conversations[0].id);
        else await createConversation();
      }
    } catch (error) {
      showToast("Could not delete that conversation.");
    }
  };

  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || store.sending || !store.activeId || !store.view) return;
    store.sending = true;
    refs.sendBtn.disabled = true;
    refs.input.value = "";
    autoResize();
    renderChips(store.view);
    const pending = { role: "user", content: trimmed, at: new Date().toISOString() };
    renderView(store.view, true, pending);
    try {
      const [view] = await Promise.all([
        request(`/api/conversations/${encodeURIComponent(store.activeId)}/messages`, {
          method: "POST",
          body: JSON.stringify({ text: trimmed }),
        }),
        new Promise((resolve) => setTimeout(resolve, TYPING_DELAY_MS)),
      ]);
      store.sending = false;
      renderView(view);
      await refreshSidebar();
    } catch (error) {
      store.sending = false;
      renderView(store.view);
      refs.input.value = trimmed;
      autoResize();
      showToast("Message failed to send. Please try again.");
    } finally {
      store.sending = false;
      refs.sendBtn.disabled = false;
      if (store.view) renderChips(store.view);
      refs.input.focus();
    }
  };

  const autoResize = () => {
    refs.input.style.height = "auto";
    refs.input.style.height = `${Math.min(refs.input.scrollHeight, 140)}px`;
  };

  refs.composer.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(refs.input.value);
  });

  refs.input.addEventListener("input", autoResize);
  refs.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      sendMessage(refs.input.value);
    }
  });

  refs.newChat.addEventListener("click", createConversation);
  refs.menuBtn.addEventListener("click", () => {
    refs.app.classList.remove("show-insights");
    refs.app.classList.toggle("show-sidebar");
  });
  refs.infoBtn.addEventListener("click", () => {
    refs.app.classList.remove("show-sidebar");
    refs.app.classList.toggle("show-insights");
  });
  refs.scrim.addEventListener("click", closeDrawers);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeDrawers();
  });

  const start = async () => {
    try {
      await refreshSidebar();
      const saved = recall();
      const known = store.conversations.find((conversation) => conversation.id === saved);
      if (known) await openConversation(known.id);
      else if (store.conversations.length) await openConversation(store.conversations[0].id);
      else await createConversation();
    } catch (error) {
      showToast("Could not reach the server.");
    }
  };

  start();
})();
