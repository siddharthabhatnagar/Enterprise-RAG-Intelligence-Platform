/**
 * Enterprise RAG Intelligence Platform - API Client
 */

const API_BASE = window.location.origin;

class EnterpriseAPI {
  static async get(endpoint) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "API request failed");
      }
      return await res.json();
    } catch (err) {
      console.error(`GET ${endpoint} failed:`, err);
      throw err;
    }
  }

  static async post(endpoint, data) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "API request failed");
      }
      return await res.json();
    } catch (err) {
      console.error(`POST ${endpoint} failed:`, err);
      throw err;
    }
  }

  static async postForm(endpoint, formData) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Upload failed");
      }
      return await res.json();
    } catch (err) {
      console.error(`Upload to ${endpoint} failed:`, err);
      throw err;
    }
  }

  static async delete(endpoint) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Delete failed");
      }
      return await res.json();
    } catch (err) {
      console.error(`DELETE ${endpoint} failed:`, err);
      throw err;
    }
  }

  // Domain API Methods
  static getUsers() {
    return this.get("/api/users");
  }

  static getDocuments() {
    return this.get("/api/documents");
  }

  static getDocumentChunks(docId) {
    return this.get(`/api/documents/${docId}/chunks`);
  }

  static deleteDocument(docId) {
    return this.delete(`/api/documents/${docId}`);
  }

  static query(payload) {
    return this.post("/api/query", payload);
  }

  static uploadPDF(formData) {
    return this.postForm("/api/ingest/upload", formData);
  }

  static getAnalytics() {
    return this.get("/api/analytics/stats");
  }
}

window.EnterpriseAPI = EnterpriseAPI;
