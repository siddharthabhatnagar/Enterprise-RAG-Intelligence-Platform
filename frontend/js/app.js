/**
 * Enterprise RAG Intelligence Platform - Application UI & State Controller
 * Minimalist, high-precision dark technical design
 */

// Application State
const state = {
  users: [],
  activeUserKey: "admin",
  activeUser: null,
  documents: [],
  analytics: null,
  selectedFile: null,
  currentView: "search",
  lastRawAnswer: ""
};

// View Names Mapping
const VIEW_TITLES = {
  search: "Query Studio",
  documents: "Document Vault",
  ingest: "Ingest Portal",
  overview: "Security & RBAC Matrix"
};

// DOM Elements
const elements = {
  // Navigation & Views
  navItems: document.querySelectorAll(".nav-item"),
  viewPanes: document.querySelectorAll(".view-pane"),
  currentViewTitle: document.getElementById("current-view-title"),
  sidebarDocCount: document.getElementById("sidebar-doc-count"),
  
  // RBAC & Identity
  userSelect: document.getElementById("user-select"),
  userRoleBadge: document.getElementById("user-role-badge"),
  userClearanceBadge: document.getElementById("user-clearance-badge"),
  
  // Search & Query
  queryInput: document.getElementById("query-input"),
  deptFilter: document.getElementById("dept-filter"),
  searchBtn: document.getElementById("search-btn"),
  promptTags: document.querySelectorAll(".prompt-tag"),
  
  // Response UI
  responseContainer: document.getElementById("response-container"),
  answerText: document.getElementById("answer-text"),
  btnCopyAnswer: document.getElementById("btn-copy-answer"),
  groundingScoreNum: document.getElementById("grounding-score-num"),
  groundingMeterFill: document.getElementById("grounding-meter-fill"),
  groundingVerdictPill: document.getElementById("grounding-verdict-pill"),
  groundingReasoning: document.getElementById("grounding-reasoning"),
  
  // Latency Telemetry
  latencyTotal: document.getElementById("latency-total"),
  latencyRetrieval: document.getElementById("latency-retrieval"),
  latencyRerank: document.getElementById("latency-rerank"),
  latencyLlm: document.getElementById("latency-llm"),
  
  // Citations & Debug
  citationsGrid: document.getElementById("citations-grid"),
  debugDrawer: document.getElementById("debug-drawer"),
  debugDrawerHeader: document.getElementById("debug-drawer-header"),
  debugTableBody: document.getElementById("debug-table-body"),
  
  // Documents Vault
  docsTableBody: document.getElementById("docs-table-body"),
  statTotalDocs: document.getElementById("stat-total-docs"),
  statTotalChunks: document.getElementById("stat-total-chunks"),
  statTopDept: document.getElementById("stat-top-dept"),
  
  // Ingest Portal
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
  
  // Toast
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
  // Sidebar Navigation
  elements.navItems.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Global Keyboard Shortcuts (Ctrl+K or Cmd+K to focus search)
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      switchTab("search");
      if (elements.queryInput) {
        elements.queryInput.focus();
        elements.queryInput.select();
      }
    }
  });

  // User Switcher
  if (elements.userSelect) {
    elements.userSelect.addEventListener("change", (e) => {
      setActiveUser(e.target.value);
    });
  }

  // Query Submission
  if (elements.searchBtn) {
    elements.searchBtn.addEventListener("click", handleSearch);
  }
  if (elements.queryInput) {
    elements.queryInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSearch();
      }
    });
  }

  // Quick Prompt Chips
  elements.promptTags.forEach(tag => {
    tag.addEventListener("click", () => {
      if (elements.queryInput) {
        elements.queryInput.value = tag.getAttribute("data-prompt") || tag.textContent.trim();
        handleSearch();
      }
    });
  });

  // Copy Answer Button
  if (elements.btnCopyAnswer) {
    elements.btnCopyAnswer.addEventListener("click", () => {
      if (state.lastRawAnswer) {
        navigator.clipboard.writeText(state.lastRawAnswer).then(() => {
          showToast("Answer copied to clipboard", "success");
        }).catch(() => {
          showToast("Failed to copy to clipboard", "error");
        });
      }
    });
  }

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

  // Click outside modal to close
  if (elements.chunksModal) {
    elements.chunksModal.addEventListener("click", (e) => {
      if (e.target === elements.chunksModal) {
        elements.chunksModal.classList.remove("active");
      }
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
// Tabs & Workspace Navigation
// ==========================================
function switchTab(tabId) {
  state.currentView = tabId;
  
  elements.navItems.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  elements.viewPanes.forEach(pane => {
    pane.classList.toggle("active", pane.id === `tab-${tabId}`);
  });

  if (elements.currentViewTitle) {
    elements.currentViewTitle.textContent = VIEW_TITLES[tabId] || "Workspace";
  }

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
    
    if (elements.userSelect) {
      elements.userSelect.innerHTML = "";
      users.forEach(u => {
        const opt = document.createElement("option");
        opt.value = u.key;
        opt.textContent = `${u.name} [${u.max_clearance.toUpperCase()}]`;
        elements.userSelect.appendChild(opt);
      });

      elements.userSelect.value = state.activeUserKey;
    }
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
    
    if (elements.userClearanceBadge) {
      elements.userClearanceBadge.className = `clearance-badge clearance-${clearance}`;
      elements.userClearanceBadge.textContent = clearance.toUpperCase();
    }
    
    if (elements.userRoleBadge) {
      elements.userRoleBadge.textContent = `${state.activeUser.role.toUpperCase()} · ${state.activeUser.department.toUpperCase()}`;
    }
    
    showToast(`Identity active: ${state.activeUser.name}`, "info");
  }
}

// ==========================================
// Search & RAG Execution
// ==========================================
async function handleSearch() {
  const query = elements.queryInput.value.trim();
  if (!query) {
    showToast("Enter an enterprise inquiry to evaluate.", "info");
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
    state.lastRawAnswer = response.answer;
    renderQueryResult(response);
  } catch (err) {
    showToast(`Inquiry execution failed: ${err.message}`, "error");
  } finally {
    setSearchLoading(false);
  }
}

function setSearchLoading(isLoading) {
  if (!elements.searchBtn) return;
  elements.searchBtn.disabled = isLoading;
  if (isLoading) {
    elements.searchBtn.innerHTML = `<span class="spinner-minimal"></span> Evaluating...`;
  } else {
    elements.searchBtn.innerHTML = `<span>Run Query</span> <span style="font-family: var(--font-mono); opacity: 0.8; font-size: 0.72rem;">↵</span>`;
  }
}

function renderQueryResult(res) {
  elements.responseContainer.classList.add("active");

  // 1. Answer text (formatted)
  elements.answerText.innerHTML = formatMarkdown(res.answer);

  // 2. Grounding & Faithfulness Gauge
  const score = res.grounding.score;
  elements.groundingScoreNum.textContent = `${score}%`;
  elements.groundingMeterFill.style.width = `${score}%`;

  if (score >= 80) {
    elements.groundingMeterFill.style.background = "var(--status-emerald)";
    elements.groundingVerdictPill.className = "clearance-badge clearance-public";
    elements.groundingVerdictPill.textContent = "VERIFIED GROUNDED";
  } else if (score >= 50) {
    elements.groundingMeterFill.style.background = "var(--status-amber)";
    elements.groundingVerdictPill.className = "clearance-badge clearance-confidential";
    elements.groundingVerdictPill.textContent = "MODERATE CITATION";
  } else {
    elements.groundingMeterFill.style.background = "var(--status-rose)";
    elements.groundingVerdictPill.className = "clearance-badge clearance-restricted";
    elements.groundingVerdictPill.textContent = "LOW GROUNDING RISK";
  }

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

  // Smooth scroll
  elements.responseContainer.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderCitations(citations) {
  elements.citationsGrid.innerHTML = "";
  if (!citations || citations.length === 0) {
    elements.citationsGrid.innerHTML = `
      <div style="color: var(--text-dim); font-size: 0.78rem; grid-column: 1 / -1; padding: 0.5rem 0;">
        No candidate citations cleared for active security tier.
      </div>
    `;
    return;
  }

  citations.forEach(c => {
    const card = document.createElement("div");
    card.className = "citation-box";

    const scorePct = Math.round((c.relevance_score || 0.8) * 100);
    const clearance = (c.access_level || "internal").toLowerCase();

    card.innerHTML = `
      <div class="citation-box-header">
        <span class="citation-doc-title" title="${escapeHtml(c.document_name)}">📄 ${escapeHtml(c.document_name)}</span>
        <span class="citation-page-num">p. ${c.page_number}</span>
      </div>
      <div class="citation-quote">"${escapeHtml(c.excerpt)}"</div>
      <div class="citation-box-footer">
        <span class="clearance-badge clearance-${clearance}">${clearance.toUpperCase()}</span>
        <span>Relevance: <strong>${scorePct}%</strong></span>
      </div>
    `;
    
    // Clicking a citation triggers document chunk view
    card.style.cursor = "pointer";
    card.title = "Click to inspect document chunks";
    card.addEventListener("click", () => {
      // Find matching document by name
      const matchedDoc = state.documents.find(d => d.filename === c.document_name);
      if (matchedDoc) {
        inspectDocumentChunks(matchedDoc.document_id, matchedDoc.filename);
      }
    });

    elements.citationsGrid.appendChild(card);
  });
}

function renderDebugChunks(chunks) {
  elements.debugTableBody.innerHTML = "";
  if (!chunks || chunks.length === 0) {
    elements.debugTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim);">No candidate chunks available.</td></tr>`;
    return;
  }

  chunks.forEach((chunk, i) => {
    const tr = document.createElement("tr");
    const clearance = (chunk.access_level || "internal").toLowerCase();
    
    tr.innerHTML = `
      <td>#${i + 1}</td>
      <td><strong>${escapeHtml(chunk.document_name)}</strong></td>
      <td>p.${chunk.page_number}</td>
      <td><span class="clearance-badge clearance-${clearance}">${clearance.toUpperCase()}</span></td>
      <td>${chunk.vector_score ? (chunk.vector_score * 100).toFixed(1) + "%" : "—"}</td>
      <td><strong style="color: var(--text-pure);">${chunk.rerank_score ? (chunk.rerank_score * 100).toFixed(1) + "%" : "—"}</strong></td>
      <td style="max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-dim);">
        ${escapeHtml(chunk.content)}
      </td>
    `;
    elements.debugTableBody.appendChild(tr);
  });
}

// ==========================================
// Document Vault Management
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
  if (elements.sidebarDocCount) elements.sidebarDocCount.textContent = totalDocs;
  
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
    elements.docsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No documents indexed in vault.</td></tr>`;
    return;
  }

  docs.forEach(d => {
    const tr = document.createElement("tr");
    const clearance = (d.access_level || "internal").toLowerCase();
    const sizeKb = (d.file_size_bytes / 1024).toFixed(1);

    tr.innerHTML = `
      <td><strong>${escapeHtml(d.filename)}</strong></td>
      <td><span style="color: var(--text-secondary); text-transform: capitalize;">${escapeHtml(d.department)}</span></td>
      <td><span class="clearance-badge clearance-${clearance}">${clearance.toUpperCase()}</span></td>
      <td>${d.total_pages}</td>
      <td><strong>${d.total_chunks}</strong></td>
      <td style="font-family: var(--font-mono); font-size: 0.74rem;">${sizeKb} KB</td>
      <td>
        <button class="btn-vault-action" onclick="inspectDocumentChunks('${d.document_id}', '${escapeHtml(d.filename)}')">Inspect</button>
        <button class="btn-vault-action btn-vault-danger" onclick="deleteDocument('${d.document_id}', '${escapeHtml(d.filename)}')">Delete</button>
      </td>
    `;
    elements.docsTableBody.appendChild(tr);
  });
}

window.inspectDocumentChunks = async function(docId, filename) {
  try {
    elements.chunksModalTitle.textContent = `Inspect Chunks: ${filename}`;
    elements.chunksModalBody.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-muted);"><span class="spinner-minimal"></span> Loading chunks...</div>`;
    elements.chunksModal.classList.add("active");

    const chunks = await EnterpriseAPI.getDocumentChunks(docId);
    if (!chunks || chunks.length === 0) {
      elements.chunksModalBody.innerHTML = `<p style="color: var(--text-muted);">No chunks found.</p>`;
      return;
    }

    let html = `<div style="display: flex; flex-direction: column; gap: 0.75rem;">`;
    chunks.forEach((chunk, i) => {
      html += `
        <div style="background: var(--surface-2); border: 1px solid var(--border-default); border-radius: var(--radius-sm); padding: 0.85rem 1rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted);">
            <span>CHUNK #${i + 1} (${chunk.chunk_id})</span>
            <span style="background: var(--surface-3); padding: 1px 4px; border-radius: 2px;">p. ${chunk.page_number}</span>
          </div>
          <div style="font-size: 0.82rem; line-height: 1.6; color: var(--text-primary); white-space: pre-wrap;">${escapeHtml(chunk.content)}</div>
        </div>
      `;
    });
    html += `</div>`;
    elements.chunksModalBody.innerHTML = html;
  } catch (err) {
    elements.chunksModalBody.innerHTML = `<p style="color: var(--status-rose);">Failed to load chunks: ${err.message}</p>`;
  }
};

window.deleteDocument = async function(docId, filename) {
  if (!confirm(`Confirm deletion of '${filename}' from vector vault?`)) {
    return;
  }

  try {
    await EnterpriseAPI.deleteDocument(docId);
    showToast(`Deleted '${filename}'`, "success");
    await loadDocuments();
    await loadAnalytics();
  } catch (err) {
    showToast(`Deletion failed: ${err.message}`, "error");
  }
};

// ==========================================
// Ingestion Portal & File Dropzone
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
    showToast("Supported format: PDF only", "error");
    return;
  }
  state.selectedFile = file;
  elements.selectedFileName.textContent = `File selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  elements.selectedFileName.style.display = "block";
}

async function handleIngest() {
  if (!state.selectedFile) {
    showToast("Select a PDF document prior to ingestion.", "info");
    return;
  }

  elements.ingestBtn.disabled = true;
  elements.ingestBtn.innerHTML = `<span class="spinner-minimal"></span> Parsing & Indexing...`;

  try {
    const formData = new FormData();
    formData.append("file", state.selectedFile);
    formData.append("department", elements.ingestDept.value);
    formData.append("access_level", elements.ingestClearance.value);
    formData.append("category", elements.ingestCategory.value.trim() || "Standard");

    const result = await EnterpriseAPI.uploadPDF(formData);
    showToast(`Ingested ${result.total_chunks} chunks from '${result.filename}'`, "success");

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
    elements.ingestBtn.innerHTML = `<span>Start Ingestion & Indexing</span>`;
  }
}

// ==========================================
// Analytics & System Telemetry
// ==========================================
async function loadAnalytics() {
  try {
    const analytics = await EnterpriseAPI.getAnalytics();
    state.analytics = analytics;

    const groqStatusBadge = document.getElementById("groq-status-badge");
    const nvidiaStatusBadge = document.getElementById("nvidia-status-badge");

    if (groqStatusBadge) {
      const active = analytics.model_config.is_groq_active;
      const modelName = analytics.model_config.groq_model.split("/").pop();
      groqStatusBadge.innerHTML = `<span class="telemetry-dot" style="background: ${active ? 'var(--status-emerald)' : 'var(--status-amber)'}"></span> ${modelName}`;
    }

    if (nvidiaStatusBadge) {
      const active = analytics.model_config.is_nvidia_active;
      const modelName = analytics.model_config.nvidia_embed_model.split("/").pop();
      nvidiaStatusBadge.innerHTML = `<span class="telemetry-dot" style="background: ${active ? 'var(--status-emerald)' : 'var(--status-blue)'}"></span> ${active ? modelName : 'BGE Fallback'}`;
    }
  } catch (err) {
    console.warn("Analytics telemetry error:", err);
  }
}

// ==========================================
// Formatting & Utilities
// ==========================================
function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Code block
  html = html.replace(/```([\s\S]*?)```/g, '<pre style="background: var(--surface-2); border: 1px solid var(--border-default); padding: 0.75rem 1rem; border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 0.8em; margin: 0.75rem 0; overflow-x: auto;"><code>$1</code></pre>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Citations [Doc: ..., Page: ...]
  html = html.replace(/\[Doc:\s*([^,]+),\s*Page:\s*(\d+)\]/g, '<span class="inline-citation-pill">📄 $1:p$2</span>');
  // Markdown Alert boxes
  html = html.replace(/&gt; \[!NOTE\]\s*([\s\S]*?)(?=\n\n|$)/g, '<div style="background: var(--surface-2); border-left: 2px solid var(--border-highlight); padding: 0.65rem 0.85rem; border-radius: var(--radius-xs); font-size: 0.82rem; margin: 0.75rem 0; color: var(--text-secondary);">$1</div>');

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
  toast.className = `toast-pill toast-${type}`;
  toast.innerHTML = `
    <span style="font-size: 0.75rem;">${type === 'success' ? '✓' : type === 'error' ? '!' : 'ℹ'}</span>
    <span>${escapeHtml(message)}</span>
  `;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(6px)";
    toast.style.transition = "all 0.15s ease";
    setTimeout(() => toast.remove(), 180);
  }, 3200);
}

// Start Application on DOM ready
document.addEventListener("DOMContentLoaded", initApp);
