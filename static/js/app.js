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

selfieInput.addEventListener("change", async () => {
  if (!selfieInput.files?.length) return;
  const file = selfieInput.files[0];
  selfieStatus.textContent = "Detecting face expression…";
  emotionSource = "selfie";

  try {
    const result = await detectSelfieExpression(file);
    applyFacialExpression(result.expression, result.confidence, result.notes, result.source);
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    selfieStatus.textContent = `Could not read expression (${msg}). Choose one from the dropdown.`;
    facialHint.focus();
  }
});

function applyFacialExpression(expression, confidence, notes, source) {
  const key = String(expression || "").toLowerCase();
  if (!SELFIE_MOOD_MAP[key]) {
    throw new Error(`Unexpected expression: ${key || "unknown"}`);
  }
  facialHint.value = key;
  selectMood(SELFIE_MOOD_MAP[key]);
  const pct = Math.round((Number(confidence) || 0) * 100);
  const via = source ? ` via ${source}` : "";
  const note = notes ? ` — ${notes}` : "";
  selfieStatus.textContent = `Detected: ${key} (${pct}%${via})${note}. Mood → ${SELFIE_MOOD_MAP[key]}.`;
}

const FACE_EXPR_MAP = {
  happy: "happy",
  sad: "sad",
  angry: "frustrated",
  fearful: "anxious",
  disgusted: "frustrated",
  surprised: "anxious",
  neutral: "calm",
};

let faceApiReady = null;

async function ensureFaceApi() {
  if (faceApiReady) return faceApiReady;
  faceApiReady = (async () => {
    if (typeof faceapi === "undefined") {
      throw new Error("face-api failed to load — hard refresh the page");
    }
    const modelUrl = "/static/vendor/face-api/model";
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(modelUrl),
      faceapi.nets.faceExpressionNet.loadFromUri(modelUrl),
    ]);
  })();
  try {
    await faceApiReady;
  } catch (e) {
    faceApiReady = null;
    throw e;
  }
  return faceApiReady;
}

/** On-device expression detection (works even if Quasar vision API is down). */
async function detectExpressionLocal(file) {
  await ensureFaceApi();
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement("canvas");
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bitmap, 0, 0);
  bitmap.close?.();

  const detection = await faceapi
    .detectSingleFace(canvas, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.3 }))
    .withFaceExpressions();

  if (!detection || !detection.expressions) {
    throw new Error("No face found — try a clearer front-facing selfie");
  }

  const ranked = Object.entries(detection.expressions).sort((a, b) => b[1] - a[1]);
  const [label, score] = ranked[0];
  const expression = FACE_EXPR_MAP[label] || "calm";
  // If "tired" isn't in face-api, map low-energy neutral+sad mix
  let finalExpr = expression;
  if (label === "neutral" && (detection.expressions.sad || 0) > 0.2) {
    finalExpr = "tired";
  }
  return {
    expression: finalExpr,
    confidence: score,
    notes: `face-api top=${label}`,
    source: "on-device",
  };
}

async function detectExpressionRemote(file) {
  const { base64, mimeType } = await fileToResizedBase64(file, 512);
  const res = await fetch("/api/analyze-selfie", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_base64: base64, mime_type: mimeType }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return {
    expression: String(data.expression || "").toLowerCase(),
    confidence: data.confidence,
    notes: data.notes,
    source: data.provider || "quasar",
  };
}

async function detectSelfieExpression(file) {
  // Prefer on-device first (reliable offline / without Docker restart)
  try {
    return await detectExpressionLocal(file);
  } catch (localErr) {
    try {
      return await detectExpressionRemote(file);
    } catch (remoteErr) {
      throw new Error(localErr.message || remoteErr.message);
    }
  }
}

/** Downscale selfie before upload so vision requests stay small/fast. */
function fileToResizedBase64(file, maxSide = 512) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read image file"));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("Invalid image"));
      img.onload = () => {
        const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
        const w = Math.max(1, Math.round(img.width * scale));
        const h = Math.max(1, Math.round(img.height * scale));
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          reject(new Error("Canvas unavailable"));
          return;
        }
        ctx.drawImage(img, 0, 0, w, h);
        const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
        const base64 = dataUrl.split(",")[1] || "";
        resolve({ base64, mimeType: "image/jpeg" });
      };
      img.src = String(reader.result || "");
    };
    reader.readAsDataURL(file);
  });
}

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
    // Keep loading visible until GPT-prompt photos are fetched AND decoded
    setLoadingHint("Generating realtime photos from GPT prompts…");
    await ensureRealtimeImages(data);
    await waitForDestinationImages(data);
    renderResults(data);
    showSection("results");
  } catch (err) {
    errorMessage.textContent = err.message;
    showSection("error");
  } finally {
    stopLoadingAnimation();
  }
});

function setLoadingHint(text) {
  const step3 = document.getElementById("step-3");
  if (step3) {
    step3.textContent = text;
    ["step-1", "step-2", "step-3"].forEach((id) => {
      document.getElementById(id)?.classList.toggle("active", id === "step-3");
    });
  }
}

function hashStr(text) {
  let h = 0;
  const s = String(text || "");
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

function isUsablePhoto(src) {
  if (!src) return false;
  if (String(src).startsWith("data:image/svg")) return false;
  return true;
}

function gptRealtimeImageUrl(prompt, index) {
  const p = encodeURIComponent(String(prompt || "").slice(0, 300));
  const seed = (hashStr(prompt) + index * 997) % 1000000;
  return `https://image.pollinations.ai/prompt/${p}?width=800&height=600&nologo=true&enhance=true&seed=${seed}&model=flux`;
}

function loadImage(src, timeoutMs = 90000) {
  return new Promise((resolve) => {
    const img = new Image();
    const timer = setTimeout(() => resolve(false), timeoutMs);
    img.onload = () => {
      clearTimeout(timer);
      resolve(true);
    };
    img.onerror = () => {
      clearTimeout(timer);
      resolve(false);
    };
    img.src = src;
  });
}

async function fetchPromptPhotoBlobUrl(prompt, index, name, country) {
  try {
    const res = await fetch("/api/place-photo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, i: index, name: name || "", country: country || "" }),
    });
    if (!res.ok) return null;
    const blob = await res.blob();
    if (!blob || blob.size < 800) return null;
    if ((blob.type || "").includes("svg")) return null;
    const url = URL.createObjectURL(blob);
    if (!(await loadImage(url))) {
      URL.revokeObjectURL(url);
      return null;
    }
    return url;
  } catch (_) {
    return null;
  }
}

function normalizeImagePrompts(dest) {
  const name = dest.name || "destination";
  const country = dest.country || "";
  const raw = Array.isArray(dest.image_prompts) ? dest.image_prompts : [];
  const prompts = [];
  const seen = new Set();
  for (const p of raw) {
    const t = String(p || "").trim();
    if (!t) continue;
    const key = t.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    prompts.push(t);
    if (prompts.length === 3) break;
  }
  const defaults = [
    `${name}, ${country} landmark view`,
    `${name}, ${country} street atmosphere`,
    `${name}, ${country} scenic viewpoint`,
  ];
  for (const d of defaults) {
    if (prompts.length >= 3) break;
    if (!seen.has(d.toLowerCase())) prompts.push(d);
  }
  return prompts.slice(0, 3);
}

/** Fetch 3 realtime photos per destination from GPT prompts; do not reveal UI until done. */
async function ensureRealtimeImages(data) {
  const dests = [];
  for (const concept of data.travel_concepts || []) {
    for (const dest of concept.destinations || []) dests.push(dest);
  }

  // Limit concurrency so Quasar/image API is not flooded
  const queue = [];
  for (const dest of dests) {
    queue.push(
      (async () => {
        const prompts = normalizeImagePrompts(dest);
        const existing = Array.isArray(dest.images) ? dest.images : [];
        const resolved = [];

        for (let i = 0; i < 3; i++) {
          const prompt = prompts[i];
          if (isUsablePhoto(existing[i]) && (await loadImage(existing[i]))) {
            resolved[i] = existing[i];
            continue;
          }

          const blobUrl = await fetchPromptPhotoBlobUrl(prompt, i, dest.name, dest.country);
          if (blobUrl) {
            resolved[i] = blobUrl;
            continue;
          }

          const direct = gptRealtimeImageUrl(prompt, i);
          if (await loadImage(direct)) {
            resolved[i] = direct;
            continue;
          }

          // Last resort: still attach something so layout is complete
          resolved[i] = existing[i] || direct;
        }

        dest.images = resolved;
      })()
    );
  }

  await Promise.all(queue);
}

function waitForDestinationImages(data) {
  const urls = [];
  for (const concept of data.travel_concepts || []) {
    for (const dest of concept.destinations || []) {
      for (const src of dest.images || []) {
        if (src) urls.push(src);
      }
    }
  }
  if (!urls.length) return Promise.resolve();
  return Promise.all(urls.map((src) => loadImage(src)));
}

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
  selfieStatus.textContent = "Upload a selfie — on-device face AI reads your expression and maps it to mood.";
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
        ${concept.destinations.map((d) => renderDestination(d)).join("")}
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

  wireGalleries();

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
  const name = dest.name || "";
  const country = dest.country || "";
  const prompts = normalizeImagePrompts(dest);
  const urls = Array.isArray(dest.images) ? dest.images.filter(Boolean).slice(0, 3) : [];

  const thumbs = [0, 1, 2]
    .map((i) => {
      const src = urls[i];
      if (!src) return "";
      const caption = String(prompts[i] || "")
        .replace(/^photorealistic travel photo of\s*/i, "")
        .slice(0, 72);
      return `
      <button type="button" class="gallery-thumb"
        data-full="${escapeAttr(src)}"
        data-title="${escapeAttr(name)} · photo ${i + 1}"
        aria-label="View photo ${i + 1}">
        <img class="place-photo" src="${escapeAttr(src)}" alt="${escapeHtml(name)} ${i + 1}"
             loading="eager" decoding="async" />
        <span class="photo-caption">${escapeHtml(caption || `Photo ${i + 1}`)}</span>
      </button>`;
    })
    .filter(Boolean)
    .join("");

  return `
    <div class="destination-item">
      <div class="destination-header">
        <span class="destination-name">${escapeHtml(name)}, ${escapeHtml(country)}</span>
        <span class="match-score">${dest.match_score}% match</span>
      </div>
      <p style="font-size: 0.9rem; color: var(--text-muted);">${escapeHtml(dest.why_it_fits)}</p>
      <div class="destination-meta">
        <span>💰 ${escapeHtml(dest.estimated_cost)}</span>
        <span>📅 ${escapeHtml(dest.suggested_duration)}</span>
        <span>🌤 ${escapeHtml(dest.best_time_to_visit)}</span>
      </div>
      <div class="place-gallery" data-name="${escapeAttr(name)}" data-country="${escapeAttr(country)}">
        <p class="gallery-label">Photos · ${escapeHtml(name)}</p>
        <div class="gallery-grid">${thumbs}</div>
        <p class="gallery-credit">Realtime images from Quasar GPT scene prompts · tap to enlarge</p>
      </div>
    </div>
  `;
}

function escapeAttr(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function wireGalleries() {
  document.querySelectorAll(".place-gallery .gallery-thumb").forEach((btn) => {
    btn.addEventListener("click", () => {
      const img = btn.querySelector("img");
      openLightbox(img?.currentSrc || img?.src || btn.dataset.full, btn.dataset.title);
    });
  });
}

function openLightbox(url, title) {
  let overlay = document.getElementById("image-lightbox");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "image-lightbox";
    overlay.className = "lightbox hidden";
    overlay.innerHTML = `
      <button type="button" class="lightbox-close" aria-label="Close">×</button>
      <img class="lightbox-img" alt="" />
      <p class="lightbox-caption"></p>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay || e.target.classList.contains("lightbox-close")) {
        overlay.classList.add("hidden");
      }
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") overlay.classList.add("hidden");
    });
  }
  overlay.querySelector(".lightbox-img").src = url;
  overlay.querySelector(".lightbox-img").alt = title || "";
  overlay.querySelector(".lightbox-caption").textContent = title || "";
  overlay.classList.remove("hidden");
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
