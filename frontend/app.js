const API_BASE = "http://127.0.0.1:8000";

const form = document.querySelector("#transactionForm");
const output = document.querySelector("#output");
const rankingBody = document.querySelector("#ranking");
const summaryList = document.querySelector("#summary");
const requestIdInput = document.querySelector("#requestId");
const summaryUserIdInput = document.querySelector("#summaryUserId");

function setOutput(value) {
  output.textContent = JSON.stringify(value, null, 2);
}

function randomRequestId() {
  return `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json();
  if (!response.ok) {
    throw body;
  }
  return body;
}

function renderSummary(summary) {
  const items = [
    ["User", summary.userId],
    ["Points", summary.totalPoints],
    ["Transactions", summary.transactionCount],
    ["Purchases", summary.purchaseCount],
    ["Refunds", summary.refundCount],
    ["Bonuses", summary.bonusCount],
  ];
  summaryList.innerHTML = items
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");
}

function renderRanking(rows) {
  if (rows.length === 0) {
    rankingBody.innerHTML = `<tr><td colspan="6">No transactions yet.</td></tr>`;
    return;
  }
  rankingBody.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${row.rank}</td>
          <td>${row.userId}</td>
          <td>${row.score}</td>
          <td>${row.totalPoints}</td>
          <td>${row.transactionCount}</td>
          <td>${row.abusePenalty}</td>
        </tr>
      `,
    )
    .join("");
}

async function refreshRanking() {
  const rows = await request("/ranking?limit=10");
  renderRanking(rows);
}

async function loadSummary(userId) {
  const summary = await request(`/summary/${encodeURIComponent(userId)}`);
  renderSummary(summary);
  return summary;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const payload = {
    requestId: formData.get("requestId"),
    userId: formData.get("userId"),
    amount: Number(formData.get("amount")),
    type: formData.get("type"),
  };

  try {
    const result = await request("/transaction", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setOutput(result);
    renderSummary(result.summary);
    summaryUserIdInput.value = result.summary.userId;
    requestIdInput.value = randomRequestId();
    await refreshRanking();
  } catch (error) {
    setOutput(error);
  }
});

document.querySelector("#loadSummary").addEventListener("click", async () => {
  try {
    setOutput(await loadSummary(summaryUserIdInput.value || "alice"));
  } catch (error) {
    setOutput(error);
  }
});

document.querySelector("#refreshRanking").addEventListener("click", async () => {
  try {
    const rows = await request("/ranking?limit=10");
    renderRanking(rows);
    setOutput(rows);
  } catch (error) {
    setOutput(error);
  }
});

requestIdInput.value = randomRequestId();
document.querySelector("#userId").value = "alice";
document.querySelector("#amount").value = "100";
summaryUserIdInput.value = "alice";
renderSummary({
  userId: "alice",
  totalPoints: 0,
  transactionCount: 0,
  purchaseCount: 0,
  refundCount: 0,
  bonusCount: 0,
});
refreshRanking().catch(setOutput);
