/**
 * Enterprise RAG Intelligence Platform - Application UI & State Controller
 */

// Application State
const state = {
  users: [],
  activeUserKey: "admin",
  activeUser: null,
  documents: [],
  analytics: null,
  selectedFile: null
};

// DOM Elements
const elements = {
  // Navigation & Tabs
  tabButtons: document.querySelectorAll(".tab-btn"),
  tabPanes: document.querySelectorAll(".tab-pane"),
  
  // RBAC & Identity
  userSelect: document.getElementById("user-select"),
  userRoleBadge: document.getElementById("user-role-badge"),
  userClearanceBadge: document.getElementById("user-clearance-badge"),
  activeUserSummary: document.getElementById("active-user-summary"),
  
  // Search & Query
  queryInput: document.getElementById("query-input"),
  deptFilter: document.getElementById("dept-filter"),
  searchBtn: document.getElementById("search-btn"),
  promptChips: document.querySelectorAll(".prompt-chip"),
  
  // Response UI
  responseContainer: document.getElementById("response-container"),
  answerText: document.getElementById("answer-text"),
  groundingScoreNum: document.getElementById("grounding-score-num"),
  groundingMeterFill: document.getElementById("grounding-meter-fill"),
  groundingVerdictPill: document.getElementById("grounding-verdict-pill"),
  groundingReasoning: document.getElementById("grounding-reasoning"),
  
  // Latency
  latencyTotal: document.getElementById("latency-total"),
  latencyRetrieval: document.getElementById("latency-retrieval"),
  latencyRerank: document.getElementById("latency-rerank"),
  latencyLlm: document.getElementById("latency-llm"),
  
  // Citations & Debug
  citationsGrid: document.getElementById("citations-grid"),
  debugDrawer: document.getElementById("debug-drawer"),
  debugDrawerHeader: document.getElementById("debug-drawer-header"),
  debugTableBody: document.getElementById("debug-table-body"),
  
  // Documents
  docsTableBody: document.getElementById("docs-table-body"),
  statTotalDocs: document.getElementById("stat-total-docs"),
  statTotalChunks: document.getElementById("stat-total-chunks"),
  statTopDept: document.getElementById("stat-top-dept"),
  
  // Ingest
  dropzone: document.getElementById("dropzone"),
  pdfFileInput: document.getElementById("pdf-file-input"),
  selectedFileName: document.getElementById("selected-file-name"),
  ingestDept: document.getElementById("ingest-dept"),
  ingestClearance: document.getElementById("ingest-clearance"),
  ingestCategory: document.getElementById("ingest-category"),
  ingestBtn: document.getElementById("ingest-btn"),
  
  // Modals
  chunksModal: document.getElementById("chunks-modal"),
  chunksModalTitle: document.getElementById("chunks-modal-title"),
  chunksModalBody: document.getElementById("chunks-modal-body"),
  chunksModalClose: document.getElementById("chunks-modal-close"),
  
  // Toasts
  toastContainer: document.getElementById("toast-container")
};

// ==========================================
// Initialization
// ==========================================
async function initApp() {
  setupEventListeners();
  await loadUsers();
  await loadDocuments();
  await loadAnalytics();
}

// ==========================================
// Event Listeners
// ==========================================
function setupEventListeners() {
  // Tab Switching
  elements.tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // User Switcher
  elements.userSelect.addEventListener("change", (e) => {
    setActiveUser(e.target.value);
  });

  // Query Submission
  elements.searchBtn.addEventListener("click", handleSearch);
  elements.queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  });

  // Quick Prompt Chips
  elements.promptChips.forEach(chip => {
    chip.addEventListener("click", () => {
      elements.queryInput.value = chip.getAttribute("data-prompt") || chip.textContent.trim();
      handleSearch();
    });
  });

  // Debug Drawer Toggle
  if (elements.debugDrawerHeader) {
    elements.debugDrawerHeader.addEventListener("click", () => {
      elements.debugDrawer.classList.toggle("open");
    });
  }

  // Chunks Modal Close
  if (elements.chunksModalClose) {
    elements.chunksModalClose.addEventListener("click", () => {
      elements.chunksModal.classList.remove("active");
    });
  }

  // Dropzone and File Selection
  setupDropzone();

  // Ingest Form Submit
  if (elements.ingestBtn) {
    elements.ingestBtn.addEventListener("click", handleIngest);
  }
}

// ==========================================
// Tabs & Navigation
// ==========================================
function switchTab(tabId) {
  elements.tabButtons.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  elements.tabPanes.forEach(pane => {
    pane.classList.toggle("active", pane.id === `tab-${tabId}`);
  });

  if (tabId === "documents") {
    loadDocuments();
  } else if (tabId === "overview") {
    loadAnalytics();
  }
}

// ==========================================
// RBAC & Identity Management
// ==========================================
async function loadUsers() {
  try {
    const users = await EnterpriseAPI.getUsers();
    state.users = users;
    
    elements.userSelect.innerHTML = "";
    users.forEach(u => {
      const opt = document.createElement("option");
      opt.value = u.key;
      opt.textContent = `${u.name} [${u.max_clearance.toUpperCase()}]`;
      elements.userSelect.appendChild(opt);
    });

    elements.userSelect.value = state.activeUserKey;
    setActiveUser(state.activeUserKey);
  } catch (err) {
    showToast("Failed to load users: " + err.message, "error");
  }
}

function setActiveUser(userKey) {
  state.activeUserKey = userKey;
  state.activeUser = state.users.find(u => u.key === userKey) || state.users[0];
  
  if (state.activeUser) {
    const clearance = state.activeUser.max_clearance.toLowerCase();
    
    elements.userClearanceBadge.className = `clearance-pill clearance-${clearance}`;
    elements.userClearanceBadge.textContent = clearance.toUpperCase();
    
    if (elements.userRoleBadge) {
      elements.userRoleBadge.textContent = `${state.activeUser.role.toUpperCase()} (${state.activeUser.department.toUpperCase()})`;
    }
    
    showToast(`Switched active profile to ${state.activeUser.name}`, "info");
  }
}

// ==========================================
// Search & RAG Execution
// ==========================================
async function handleSearch() {
  const query = elements.queryInput.value.trim();
  if (!query) {
    showToast("Please enter a question to ask the intelligence platform.", "info");
    return;
  }

  setSearchLoading(true);
  try {
    const deptFilter = elements.deptFilter.value;
    const payload = {
      query: query,
      user_id: state.activeUserKey,
      department_filter: deptFilter === "all" ? null : deptFilter,
      include_debug_chunks: true
    };

    const response = await EnterpriseAPI.query(payload);
    renderQueryResult(response);
  } catch (err) {
    showToast(`Query execution failed: ${err.message}`, "error");
  } finally {
    setSearchLoading(false);
  }
}

function setSearchLoading(isLoading) {
  elements.searchBtn.disabled = isLoading;
  if (isLoading) {
    elements.searchBtn.innerHTML = `<span class="spinner"></span> Analyzing...`;
  } else {
    elements.searchBtn.innerHTML = `<span>Submit Query</span> ➔`;
  }
}

function renderQueryResult(res) {
  elements.responseContainer.classList.add("active");

  // 1. Answer text (formatted)
  elements.answerText.innerHTML = formatMarkdown(res.answer);

  // 2. Grounding & Hallucination Gauge
  const score = res.grounding.score;
  elements.groundingScoreNum.textContent = `${score}%`;
  elements.groundingMeterFill.style.width = `${score}%`;

  elements.groundingMeterFill.className = "meter-fill " + (
    score >= 80 ? "meter-fill-emerald" :
    score >= 50 ? "meter-fill-amber" : "meter-fill-rose"
  );

  elements.groundingVerdictPill.textContent = `${res.grounding.verdict} FAITHFULNESS`;
  elements.groundingVerdictPill.className = "clearance-pill " + (
    score >= 80 ? "clearance-public" :
    score >= 50 ? "clearance-confidential" : "clearance-restricted"
  );
  elements.groundingReasoning.textContent = res.grounding.reasoning;

  // 3. Latency Metrics
  elements.latencyTotal.textContent = `${res.latency.total_ms} ms`;
  elements.latencyRetrieval.textContent = `${res.latency.retrieval_ms} ms`;
  elements.latencyRerank.textContent = `${res.latency.rerank_ms} ms`;
  elements.latencyLlm.textContent = `${res.latency.llm_generation_ms} ms`;

  // 4. Citations
  renderCitations(res.citations);

  // 5. Debug Drawer Chunks
  renderDebugChunks(res.debug_chunks || []);

  // Scroll to answer smoothly
  elements.responseContainer.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderCitations(citations) {
  elements.citationsGrid.innerHTML = "";
  if (!citations || citations.length === 0) {
    elements.citationsGrid.innerHTML = `
      <div style="color: var(--text-muted); font-size: 0.85rem; grid-column: 1 / -1;">
        No source citations available for this response.
      </div>
    `;
    return;
  }

  citations.forEach(c => {
    const card = document.createElement("div");
    card.className = "citation-card";

    const scorePct = Math.round((c.relevance_score || 0.8) * 100);
    const clearance = (c.access_level || "internal").toLowerCase();

    card.innerHTML = `
      <div class="citation-top">
        <span class="citation-doc-name" title="${escapeHtml(c.document_name)}">📄 ${escapeHtml(c.document_name)}</span>
        <span class="citation-page-badge">Page ${c.page_number}</span>
      </div>
      <div class="citation-excerpt">"${escapeHtml(c.excerpt)}"</div>
      <div class="citation-footer">
        <span class="clearance-pill clearance-${clearance}">${clearance.toUpperCase()}</span>
        <span>Relevance: <strong>${scorePct}%</strong></span>
      </div>
    `;
    elements.citationsGrid.appendChild(card);
  });
}

function renderDebugChunks(chunks) {
  elements.debugTableBody.innerHTML = "";
  if (!chunks || chunks.length === 0) {
    elements.debugTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-muted);">No candidate chunks available.</td></tr>`;
    return;
  }

  chunks.forEach((chunk, i) => {
    const tr = document.createElement("tr");
    const clearance = (chunk.access_level || "internal").toLowerCase();
    
    tr.innerHTML = `
      <td>#${i + 1}</td>
      <td><strong>${escapeHtml(chunk.document_name)}</strong></td>
      <td>Page ${chunk.page_number}</td>
      <td><span class="clearance-pill clearance-${clearance}">${clearance.toUpperCase()}</span></td>
      <td>${chunk.vector_score ? (chunk.vector_score * 100).toFixed(1) + "%" : "N/A"}</td>
      <td><strong style="color: #60a5fa;">${chunk.rerank_score ? (chunk.rerank_score * 100).toFixed(1) + "%" : "N/A"}</strong></td>
      <td style="max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
        ${escapeHtml(chunk.content)}
      </td>
    `;
    elements.debugTableBody.appendChild(tr);
  });
}

// ==========================================
// Documents Knowledge Base Tab
// ==========================================
async function loadDocuments() {
  try {
    const docs = await EnterpriseAPI.getDocuments();
    state.documents = docs;
    renderDocumentsTable(docs);
    updateDocumentStats(docs);
  } catch (err) {
    showToast("Failed to fetch documents: " + err.message, "error");
  }
}

function updateDocumentStats(docs) {
  const totalDocs = docs.length;
  const totalChunks = docs.reduce((acc, d) => acc + (d.total_chunks || 0), 0);
  
  if (elements.statTotalDocs) elements.statTotalDocs.textContent = totalDocs;
  if (elements.statTotalChunks) elements.statTotalChunks.textContent = totalChunks;
  
  if (elements.statTopDept) {
    const deptCount = {};
    docs.forEach(d => { deptCount[d.department] = (deptCount[d.department] || 0) + 1; });
    const top = Object.keys(deptCount).sort((a,b) => deptCount[b] - deptCount[a])[0] || "General";
    elements.statTopDept.textContent = top.toUpperCase();
  }
}

function renderDocumentsTable(docs) {
  elements.docsTableBody.innerHTML = "";
  if (!docs || docs.length === 0) {
    elements.docsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No documents indexed yet. Upload a PDF or run database seeder.</td></tr>`;
    return;
  }

  docs.forEach(d => {
    const tr = document.createElement("tr");
    const clearance = (d.access_level || "internal").toLowerCase();
    const sizeKb = (d.file_size_bytes / 1024).toFixed(1);

    tr.innerHTML = `
      <td><strong>📄 ${escapeHtml(d.filename)}</strong></td>
      <td><span style="color: var(--text-secondary); text-transform: capitalize;">${escapeHtml(d.department)}</span></td>
      <td><span class="clearance-pill clearance-${clearance}">${clearance.toUpperCase()}</span></td>
      <td>${d.total_pages} pages</td>
      <td><strong>${d.total_chunks}</strong> chunks</td>
      <td>${sizeKb} KB</td>
      <td>
        <button class="btn-sm" onclick="inspectDocumentChunks('${d.document_id}', '${escapeHtml(d.filename)}')">Inspect</button>
        <button class="btn-sm btn-danger" onclick="deleteDocument('${d.document_id}', '${escapeHtml(d.filename)}')">Delete</button>
      </td>
    `;
    elements.docsTableBody.appendChild(tr);
  });
}

window.inspectDocumentChunks = async function(docId, filename) {
  try {
    elements.chunksModalTitle.textContent = `Chunks for: ${filename}`;
    elements.chunksModalBody.innerHTML = `<div style="text-align:center; padding: 2rem;"><span class="spinner"></span> Loading chunks...</div>`;
    elements.chunksModal.classList.add("active");

    const chunks = await EnterpriseAPI.getDocumentChunks(docId);
    if (!chunks || chunks.length === 0) {
      elements.chunksModalBody.innerHTML = `<p style="color: var(--text-muted);">No chunks found.</p>`;
      return;
    }

    let html = `<div style="display: flex; flex-direction: column; gap: 1rem;">`;
    chunks.forEach((chunk, i) => {
      html += `
        <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.8rem; color: var(--text-muted);">
            <span>Chunk #${i + 1} (${chunk.chunk_id})</span>
            <span class="citation-page-badge">Page ${chunk.page_number}</span>
          </div>
          <div style="font-size: 0.88rem; line-height: 1.6; color: var(--text-primary); white-space: pre-wrap;">${escapeHtml(chunk.content)}</div>
        </div>
      `;
    });
    html += `</div>`;
    elements.chunksModalBody.innerHTML = html;
  } catch (err) {
    elements.chunksModalBody.innerHTML = `<p style="color: #f87171;">Failed to load chunks: ${err.message}</p>`;
  }
};

window.deleteDocument = async function(docId, filename) {
  if (!confirm(`Are you sure you want to delete '${filename}' from the vector knowledge base?`)) {
    return;
  }

  try {
    await EnterpriseAPI.deleteDocument(docId);
    showToast(`Deleted document '${filename}'`, "success");
    await loadDocuments();
    await loadAnalytics();
  } catch (err) {
    showToast(`Failed to delete document: ${err.message}`, "error");
  }
};

// ==========================================
// Ingest Portal & File Dropzone
// ==========================================
function setupDropzone() {
  const dropzone = elements.dropzone;
  const fileInput = elements.pdfFileInput;

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showToast("Only PDF documents are supported for ingestion.", "error");
    return;
  }
  state.selectedFile = file;
  elements.selectedFileName.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  elements.selectedFileName.style.display = "block";
}

async function handleIngest() {
  if (!state.selectedFile) {
    showToast("Please select a PDF document first.", "info");
    return;
  }

  elements.ingestBtn.disabled = true;
  elements.ingestBtn.innerHTML = `<span class="spinner"></span> Parsing, Chunking & Indexing...`;

  try {
    const formData = new FormData();
    formData.append("file", state.selectedFile);
    formData.append("department", elements.ingestDept.value);
    formData.append("access_level", elements.ingestClearance.value);
    formData.append("category", elements.ingestCategory.value.trim() || "Standard");

    const result = await EnterpriseAPI.uploadPDF(formData);
    showToast(`Success! Ingested ${result.total_chunks} chunks from '${result.filename}'`, "success");

    // Reset Form
    state.selectedFile = null;
    elements.pdfFileInput.value = "";
    elements.selectedFileName.style.display = "none";

    // Refresh Documents & Analytics
    await loadDocuments();
    await loadAnalytics();

    // Switch to Documents view
    switchTab("documents");
  } catch (err) {
    showToast(`Ingestion failed: ${err.message}`, "error");
  } finally {
    elements.ingestBtn.disabled = false;
    elements.ingestBtn.innerHTML = `Start Ingestion & Indexing ➔`;
  }
}

// ==========================================
// Analytics & System Stats
// ==========================================
async function loadAnalytics() {
  try {
    const analytics = await EnterpriseAPI.getAnalytics();
    state.analytics = analytics;

    // Update model provider badges
    const groqStatusBadge = document.getElementById("groq-status-badge");
    const nvidiaStatusBadge = document.getElementById("nvidia-status-badge");

    if (groqStatusBadge) {
      const active = analytics.model_config.is_groq_active;
      groqStatusBadge.textContent = active ? `Groq: ${analytics.model_config.groq_model}` : `Groq: Local Mode`;
      groqStatusBadge.style.borderColor = active ? "rgba(16, 185, 129, 0.4)" : "rgba(245, 158, 11, 0.4)";
    }

    if (nvidiaStatusBadge) {
      const active = analytics.model_config.is_nvidia_active;
      nvidiaStatusBadge.textContent = active ? `NVIDIA: ${analytics.model_config.nvidia_embed_model}` : `Embeddings: BGE Local`;
      nvidiaStatusBadge.style.borderColor = active ? "rgba(16, 185, 129, 0.4)" : "rgba(245, 158, 11, 0.4)";
    }
  } catch (err) {
    console.warn("Analytics fetch error:", err);
  }
}

// ==========================================
// Helper Utilities
// ==========================================
function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Code block
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Citations [Doc: ..., Page: ...]
  html = html.replace(/\[Doc:\s*([^,]+),\s*Page:\s*(\d+)\]/g, '<span class="citation-page-badge">📄 $1 (p.$2)</span>');
  // Markdown Alert boxes
  html = html.replace(/&gt; \[!NOTE\]\s*([\s\S]*?)(?=\n\n|$)/g, '<div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.75rem 0;">$1</div>');

  // Paragraphs & Lists
  const paragraphs = html.split(/\n\n+/);
  return paragraphs.map(p => {
    p = p.trim();
    if (p.startsWith("- ") || p.startsWith("* ")) {
      const items = p.split(/\n[-*]\s+/).filter(Boolean);
      return `<ul>${items.map(it => `<li>${it.replace(/^[-*]\s+/, '')}</li>`).join('')}</ul>`;
    }
    return `<p>${p.replace(/\n/g, '<br/>')}</p>`;
  }).join('');
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
    <span>${escapeHtml(message)}</span>
  `;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Start Application on Load
document.addEventListener("DOMContentLoaded", initApp);
