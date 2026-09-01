const BUDGET_LABELS = {
  USD: { budget: "$30–$70/day", moderate: "$80–$150/day", luxury: "$200+/day", flexible: "Optimize for experience" },
  EUR: { budget: "€30–€65/day", moderate: "€75–€140/day", luxury: "€190+/day", flexible: "Optimize for experience" },
  GBP: { budget: "£25–£55/day", moderate: "£65–£120/day", luxury: "£170+/day", flexible: "Optimize for experience" },
  INR: { budget: "₹2,000–5,000/day", moderate: "₹6,000–12,000/day", luxury: "₹15,000+/day", flexible: "Optimize for experience" },
  AED: { budget: "AED 110–260/day", moderate: "AED 300–550/day", luxury: "AED 750+/day", flexible: "Optimize for experience" },
  JPY: { budget: "¥4,500–10,000/day", moderate: "¥12,000–22,000/day", luxury: "¥30,000+/day", flexible: "Optimize for experience" },
  AUD: { budget: "A$45–100/day", moderate: "A$120–220/day", luxury: "A$300+/day", flexible: "Optimize for experience" },
};

const SELFIE_MOOD_MAP = {
  happy: "happy",
  sad: "sad",
  frustrated: "frustrated",
  anxious: "anxious",
  calm: "peaceful",
  tired: "burnt-out",
};

const POSITIVE = ["celebrate", "joy", "excited", "happy", "love", "adventure", "fun"];
const NEGATIVE = ["reset", "escape", "burnt", "stress", "sad", "anxious", "lonely", "heal", "recover"];
const NEUTRAL = ["explore", "learn", "culture", "food", "nature"];

const form = document.getElementById("inspire-form");
const moodInput = document.getElementById("mood");
const moodPicker = document.getElementById("mood-picker");
const submitBtn = document.getElementById("submit-btn");
const currencySelect = document.getElementById("currency");
const budgetSelect = document.getElementById("budget");
const budgetHint = document.getElementById("budget-hint");
const intentInput = document.getElementById("intent");
const sentimentHint = document.getElementById("sentiment-hint");
const facialHint = document.getElementById("facial_hint");
const selfieInput = document.getElementById("selfie-input");
const selfieStatus = document.getElementById("selfie-status");

const inputSection = document.getElementById("input-section");
const loadingSection = document.getElementById("loading-section");
const resultsSection = document.getElementById("results-section");
const errorSection = document.getElementById("error-section");

const profileCard = document.getElementById("profile-card");
const contextCard = document.getElementById("context-card");
const conceptsGrid = document.getElementById("concepts-grid");
const boardCard = document.getElementById("board-card");
const reasoningCard = document.getElementById("reasoning-card");
const sourceBadge = document.getElementById("source-badge");
const errorMessage = document.getElementById("error-message");

let loadingInterval = null;
let emotionSource = "manual";

function updateBudgetHint() {
  const currency = currencySelect.value;
  const tier = budgetSelect.value;
  budgetHint.textContent = `≈ ${BUDGET_LABELS[currency][tier]}`;
}

function inferTextSentiment(text) {
  const lower = (text || "").toLowerCase();
  if (!lower.trim()) return null;
  if (POSITIVE.some((w) => lower.includes(w))) return "positive / celebratory";
  if (NEGATIVE.some((w) => lower.includes(w))) return "seeking relief / restoration";
  if (NEUTRAL.some((w) => lower.includes(w))) return "curious / exploratory";
  return "neutral";
}

function selectMood(value) {
  moodPicker.querySelectorAll(".mood-chip").forEach((c) => {
    c.classList.toggle("selected", c.dataset.value === value);
  });
  moodInput.value = value;
}

moodPicker.addEventListener("click", (e) => {
  const chip = e.target.closest(".mood-chip");
  if (!chip) return;
  selectMood(chip.dataset.value);
  if (emotionSource === "selfie") return;
  emotionSource = "manual";
});

currencySelect.addEventListener("change", updateBudgetHint);
budgetSelect.addEventListener("change", updateBudgetHint);
updateBudgetHint();

intentInput.addEventListener("input", () => {
  const sentiment = inferTextSentiment(intentInput.value);
  sentimentHint.textContent = sentiment
    ? `Detected text sentiment: ${sentiment}`
    : "Text sentiment will be inferred from your intent.";
  if (sentiment && emotionSource === "manual") emotionSource = "text_sentiment";
});

facialHint.addEventListener("change", () => {
  const hint = facialHint.value;
  if (!hint) return;
  emotionSource = "selfie";
  const mapped = SELFIE_MOOD_MAP[hint];
  if (mapped) selectMood(mapped);
  selfieStatus.textContent = `Expression hint: ${hint} → mood ${mapped || hint}`;
});

selfieInput.addEventListener("change", () => {
  if (!selfieInput.files?.length) return;
  // Demo simulation: rotate through expression hints based on file name length
  const name = selfieInput.files[0].name || "";
  const hints = Object.keys(SELFIE_MOOD_MAP);
  const pick = hints[name.length % hints.length];
  facialHint.value = pick;
  emotionSource = "selfie";
  selectMood(SELFIE_MOOD_MAP[pick]);
  selfieStatus.textContent = `Selfie loaded (${selfieInput.files[0].name}). Simulated expression: ${pick}.`;
});

document.getElementById("voice_hint").addEventListener("change", (e) => {
  if (e.target.value) emotionSource = "voice";
});

document.getElementById("back-btn").addEventListener("click", resetForm);
document.getElementById("retry-btn").addEventListener("click", resetForm);

function optional(id) {
  const v = document.getElementById(id)?.value?.trim();
  return v || null;
}

function buildPayload() {
  const textSentiment = inferTextSentiment(intentInput.value);
  const facial = facialHint.value || null;
  const voice = optional("voice_hint");

  let source = emotionSource;
  if (facial) source = "selfie";
  else if (voice) source = "voice";
  else if (textSentiment) source = "text_sentiment";

  return {
    mood: moodInput.value,
    intent: intentInput.value.trim(),
    budget: budgetSelect.value,
    currency: currencySelect.value,
    travel_style: document.getElementById("travel_style").value,
    context: optional("context"),
    profile: {
      home_base: optional("home_base"),
      traveler_type: optional("traveler_type"),
      languages: null,
      companions: optional("companions"),
    },
    preferences: {
      interests: optional("interests"),
      pace: optional("pace"),
      climate: optional("climate"),
      social_context: optional("social_context"),
    },
    policy: {
      visa_constraints: optional("visa_constraints"),
      corporate_policy: optional("corporate_policy"),
      accessibility: optional("accessibility"),
      max_flight_hours: optional("max_flight_hours"),
    },
    emotion_signals: {
      source,
      facial_hint: facial,
      voice_hint: voice,
      text_sentiment: textSentiment,
      confidence: facial || voice ? 0.65 : textSentiment ? 0.55 : 0.9,
    },
  };
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!moodInput.value) {
    alert("Please select how you're feeling (or upload a selfie / set an expression hint).");
    return;
  }

  const payload = buildPayload();
  showLoading();

  try {
    const response = await fetch("/api/inspire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    renderResults(data);
    showSection("results");
  } catch (err) {
    errorMessage.textContent = err.message;
    showSection("error");
  } finally {
    stopLoadingAnimation();
  }
});

function showLoading() {
  showSection("loading");
  submitBtn.disabled = true;
  submitBtn.querySelector(".btn-text").classList.add("hidden");
  submitBtn.querySelector(".btn-loader").classList.remove("hidden");

  const steps = ["step-1", "step-2", "step-3"];
  let current = 0;
  loadingInterval = setInterval(() => {
    steps.forEach((id, i) => {
      document.getElementById(id).classList.toggle("active", i === current);
    });
    current = (current + 1) % steps.length;
  }, 2000);
}

function stopLoadingAnimation() {
  if (loadingInterval) clearInterval(loadingInterval);
  submitBtn.disabled = false;
  submitBtn.querySelector(".btn-text").classList.remove("hidden");
  submitBtn.querySelector(".btn-loader").classList.add("hidden");
}

function showSection(name) {
  inputSection.classList.toggle("hidden", name !== "input");
  loadingSection.classList.toggle("hidden", name !== "loading");
  resultsSection.classList.toggle("hidden", name !== "results");
  errorSection.classList.toggle("hidden", name !== "error");
}

function resetForm() {
  showSection("input");
  form.reset();
  moodPicker.querySelectorAll(".mood-chip").forEach((c) => c.classList.remove("selected"));
  moodInput.value = "";
  emotionSource = "manual";
  selfieStatus.textContent = "Upload a selfie — we'll map expression → mood (simulated for demo).";
  updateBudgetHint();
}

function renderResults(data) {
  const source = (data.source || "mock").toLowerCase();
  if (sourceBadge) {
    const labels = {
      gemini: "Source: Gemini (live AI)",
      "self-hosted": "Source: Quasar (self-hosted)",
      mock: "Source: Mock (local catalog)",
    };
    const cls = source === "self-hosted" ? "self-hosted" : source === "gemini" ? "gemini" : "mock";
    sourceBadge.className = `source-badge ${cls}`;
    sourceBadge.textContent = labels[source] || labels.mock;
  }

  const profile = data.emotional_profile;
  profileCard.innerHTML = `
    <h3>${escapeHtml(profile.travel_personality)}</h3>
    <p style="color: var(--text-muted); font-weight: 300;">${escapeHtml(profile.decision_style)}</p>
    <p style="margin-top: 0.75rem;">Primary emotion: <strong style="color: var(--accent);">${escapeHtml(profile.primary_emotion)}</strong></p>
    <div class="profile-meta">
      ${profile.priority_factors.map((f) => `<span class="tag">${escapeHtml(f)}</span>`).join("")}
    </div>
  `;

  if (data.context_summary) {
    contextCard.classList.remove("hidden");
    contextCard.innerHTML = `
      <h4 style="color: var(--teal); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem;">Context used (3 Ps + emotion)</h4>
      <p style="font-size: 0.9rem; color: var(--text-muted);">${escapeHtml(data.context_summary)}</p>
    `;
  } else {
    contextCard.classList.add("hidden");
    contextCard.innerHTML = "";
  }

  conceptsGrid.innerHTML = data.travel_concepts
    .map(
      (concept) => `
    <div class="concept-card">
      <h3>${escapeHtml(concept.title)}</h3>
      <p class="concept-tagline">${escapeHtml(concept.tagline)}</p>
      <p class="concept-hook">${escapeHtml(concept.emotional_hook)}</p>
      <div class="vibe-keywords">
        ${concept.vibe_keywords.map((k) => `<span>${escapeHtml(k)}</span>`).join("")}
      </div>
      <div class="destinations-list">
        ${concept.destinations.map(renderDestination).join("")}
      </div>
      <ul class="itinerary-list">
        ${concept.sample_itinerary.map((day) => `<li>${escapeHtml(day)}</li>`).join("")}
      </ul>
      <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 1rem;">
        <strong>Budget:</strong> ${escapeHtml(concept.budget_breakdown)} ·
        <strong>Fit:</strong> ${escapeHtml(concept.personality_fit)}
      </p>
    </div>
  `
    )
    .join("");

  const board = data.inspiration_board;
  boardCard.innerHTML = `
    <div class="board-header">
      <h3>${escapeHtml(board.board_title)}</h3>
      <p class="board-subtitle">${escapeHtml(board.subtitle)}</p>
      <p class="board-summary">${escapeHtml(board.emotional_summary)}</p>
    </div>
    <div class="clusters-grid">
      ${board.clusters.map(renderCluster).join("")}
    </div>
    <p class="board-quote">"${escapeHtml(board.quote)}"</p>
  `;

  reasoningCard.innerHTML = `
    <h4>AI Reasoning</h4>
    <p>${escapeHtml(data.agent_reasoning)}</p>
    <p class="hint" style="margin-top: 0.75rem;">
      Engine: <strong>${escapeHtml(
        source === "self-hosted" ? "Quasar (self-hosted)" : source === "gemini" ? "Gemini" : "Mock"
      )}</strong>
      ${
        source === "mock"
          ? " — live LLM unavailable. Connect Coforge VPN, then open /api/llm-ping to verify."
          : source === "self-hosted"
            ? " — answered via Coforge Quasar router."
            : " — answered by live Gemini."
      }
    </p>
    ${
      data.fallback_reason
        ? `<p class="hint" style="margin-top: 0.5rem; color: #c4a35a;">Fallback detail: ${escapeHtml(
            data.fallback_reason
          )}</p>`
        : ""
    }
  `;
}

function renderDestination(dest) {
  return `
    <div class="destination-item">
      <div class="destination-header">
        <span class="destination-name">${escapeHtml(dest.name)}, ${escapeHtml(dest.country)}</span>
        <span class="match-score">${dest.match_score}% match</span>
      </div>
      <p style="font-size: 0.9rem; color: var(--text-muted);">${escapeHtml(dest.why_it_fits)}</p>
      <div class="destination-meta">
        <span>💰 ${escapeHtml(dest.estimated_cost)}</span>
        <span>📅 ${escapeHtml(dest.suggested_duration)}</span>
        <span>🌤 ${escapeHtml(dest.best_time_to_visit)}</span>
      </div>
    </div>
  `;
}

function renderCluster(cluster) {
  const c1 = cluster.color_palette[0] || "#2D5A4A";
  const c2 = cluster.color_palette[1] || "#E8D5B7";

  return `
    <div class="cluster-card" style="--c1: ${c1}; --c2: ${c2};">
      <div class="cluster-content">
        <h4>${escapeHtml(cluster.cluster_name)}</h4>
        <p class="cluster-theme">${escapeHtml(cluster.theme)} · ${escapeHtml(cluster.mood_alignment)}</p>
        <p style="font-size: 0.8rem; font-style: italic; color: var(--text-muted); margin-bottom: 0.5rem;">
          ${escapeHtml(cluster.visual_mood)}
        </p>
        <div class="color-palette">
          ${cluster.color_palette.map((c) => `<div class="color-swatch" style="background: ${c};"></div>`).join("")}
        </div>
        <p class="cluster-destinations"><strong>Destinations:</strong> ${cluster.destinations.map(escapeHtml).join(" · ")}</p>
        <ul class="activity-list">
          ${cluster.suggested_activities.map((a) => `<li>• ${escapeHtml(a)}</li>`).join("")}
        </ul>
      </div>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}
