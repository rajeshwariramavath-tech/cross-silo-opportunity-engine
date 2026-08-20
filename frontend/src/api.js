const API_BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (networkErr) {
    throw new Error(`Could not reach the API at ${API_BASE} - is uvicorn running? (${networkErr.message})`);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body);
    } catch {
      // response body wasn't JSON - keep statusText
    }
    throw new Error(`${response.status} ${detail}`);
  }

  return response.json();
}

function windowQuery(limit, offset) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (offset) params.set("offset", String(offset));
  return params.toString();
}

export const api = {
  salesRecords: (limit, offset = 0) => request(`/sales-records?${windowQuery(limit, offset)}`),
  debtRecords: (limit, offset = 0) => request(`/debt-records?${windowQuery(limit, offset)}`),
  ingest: (limit, offset = 0) => request(`/ingest?${windowQuery(limit, offset)}`, { method: "POST" }),
  resolveEntities: () => request("/resolve-entities", { method: "POST" }),
  detectOpportunities: () => request("/detect-opportunities", { method: "POST" }),
  opportunitiesForRole: (role) => request(`/opportunities?role=${encodeURIComponent(role)}`),
};
