/* XcodeMCPWrapper Dashboard - Frontend Logic */

(function () {
    "use strict";

    // --- State ---
    let ws = null;
    let charts = {};
    let auditPage = 0;
    const auditPageSize = 50;
    let auditFilter = "";

    // --- Chart.js defaults ---
    Chart.defaults.color = "#8b949e";
    Chart.defaults.borderColor = "#30363d";

    const COLORS = [
        "#58a6ff", "#3fb950", "#bc8cff", "#d29922",
        "#f85149", "#79c0ff", "#56d364", "#d2a8ff",
        "#e3b341", "#ffa198",
    ];

    // --- Utility ---
    function formatUptime(seconds) {
        var h = Math.floor(seconds / 3600);
        var m = Math.floor((seconds % 3600) / 60);
        var s = Math.floor(seconds % 60);
        return h + "h " + m + "m " + s + "s";
    }

    function el(id) {
        return document.getElementById(id);
    }

    // --- Chart Initialization ---
    function initCharts() {
        // Tool usage bar chart
        charts.toolBar = new Chart(el("chart-tool-bar"), {
            type: "bar",
            data: { labels: [], datasets: [{ label: "Calls", data: [], backgroundColor: COLORS }] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: "#21262d" } },
                    x: { grid: { display: false } },
                },
            },
        });

        // Tool distribution pie chart
        charts.toolPie = new Chart(el("chart-tool-pie"), {
            type: "doughnut",
            data: { labels: [], datasets: [{ data: [], backgroundColor: COLORS }] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "right", labels: { boxWidth: 12 } } },
            },
        });

        // Request timeline
        charts.timeline = new Chart(el("chart-timeline"), {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Requests",
                        data: [],
                        borderColor: "#58a6ff",
                        backgroundColor: "rgba(88,166,255,0.1)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                    },
                    {
                        label: "Errors",
                        data: [],
                        borderColor: "#f85149",
                        backgroundColor: "rgba(248,81,73,0.1)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: "#21262d" } },
                    x: { grid: { display: false }, title: { display: true, text: "Seconds ago" } },
                },
                plugins: { legend: { labels: { boxWidth: 12 } } },
                animation: { duration: 300 },
            },
        });

        // Latency chart
        charts.latency = new Chart(el("chart-latency"), {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Latency (ms)",
                        data: [],
                        borderColor: "#bc8cff",
                        backgroundColor: "rgba(188,140,255,0.1)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: "#21262d" }, title: { display: true, text: "ms" } },
                    x: { grid: { display: false }, title: { display: true, text: "Seconds ago" } },
                },
                plugins: { legend: { display: false } },
                animation: { duration: 300 },
            },
        });
    }

    // --- Update Functions ---
    function updateKPIs(summary) {
        el("kpi-uptime").textContent = formatUptime(summary.uptime_seconds);
        el("kpi-total-requests").textContent = summary.total_requests.toLocaleString();
        el("kpi-rps").textContent = summary.rps.toFixed(2);
        el("kpi-error-rate").textContent = (summary.error_rate * 100).toFixed(2) + "%";
        el("kpi-total-errors").textContent = summary.total_errors.toLocaleString();
        el("kpi-in-flight").textContent = summary.in_flight;
    }

    function updateToolCharts(toolCounts) {
        var tools = Object.keys(toolCounts).sort();
        var counts = tools.map(function (t) { return toolCounts[t]; });

        charts.toolBar.data.labels = tools;
        charts.toolBar.data.datasets[0].data = counts;
        charts.toolBar.data.datasets[0].backgroundColor = tools.map(function (_, i) {
            return COLORS[i % COLORS.length];
        });
        charts.toolBar.update("none");

        charts.toolPie.data.labels = tools;
        charts.toolPie.data.datasets[0].data = counts;
        charts.toolPie.data.datasets[0].backgroundColor = tools.map(function (_, i) {
            return COLORS[i % COLORS.length];
        });
        charts.toolPie.update("none");
    }

    function bucketTimeseries(points, bucketSize) {
        // Bucket points into time intervals and count per bucket
        if (!points.length) return { labels: [], data: [] };
        var buckets = {};
        points.forEach(function (p) {
            var key = Math.floor(p.t / bucketSize) * bucketSize;
            buckets[key] = (buckets[key] || 0) + p.v;
        });
        var keys = Object.keys(buckets).map(Number).sort(function (a, b) { return a - b; });
        return {
            labels: keys.map(function (k) { return Math.round(k); }),
            data: keys.map(function (k) { return buckets[k]; }),
        };
    }

    function updateTimeline(timeseries) {
        var reqBuckets = bucketTimeseries(timeseries.requests, 5);
        var errBuckets = bucketTimeseries(timeseries.errors, 5);

        // Union all labels
        var labelSet = {};
        reqBuckets.labels.forEach(function (l) { labelSet[l] = true; });
        errBuckets.labels.forEach(function (l) { labelSet[l] = true; });
        var labels = Object.keys(labelSet).map(Number).sort(function (a, b) { return a - b; });

        var reqMap = {};
        reqBuckets.labels.forEach(function (l, i) { reqMap[l] = reqBuckets.data[i]; });
        var errMap = {};
        errBuckets.labels.forEach(function (l, i) { errMap[l] = errBuckets.data[i]; });

        charts.timeline.data.labels = labels;
        charts.timeline.data.datasets[0].data = labels.map(function (l) { return reqMap[l] || 0; });
        charts.timeline.data.datasets[1].data = labels.map(function (l) { return errMap[l] || 0; });
        charts.timeline.update("none");
    }

    function updateLatencyChart(timeseries) {
        var points = timeseries.latencies || [];
        charts.latency.data.labels = points.map(function (p) { return Math.round(p.t); });
        charts.latency.data.datasets[0].data = points.map(function (p) { return p.v; });
        charts.latency.update("none");
    }

    function updateLatencyTable(toolLatency) {
        var tbody = el("latency-table").querySelector("tbody");
        var rows = "";
        var tools = Object.keys(toolLatency).sort();
        tools.forEach(function (tool) {
            var s = toolLatency[tool];
            rows += "<tr>"
                + "<td>" + tool + "</td>"
                + "<td>" + s.count + "</td>"
                + "<td>" + s.avg_ms.toFixed(1) + "</td>"
                + "<td>" + s.p50_ms.toFixed(1) + "</td>"
                + "<td>" + s.p95_ms.toFixed(1) + "</td>"
                + "<td>" + s.p99_ms.toFixed(1) + "</td>"
                + "<td>" + s.min_ms.toFixed(1) + "</td>"
                + "<td>" + s.max_ms.toFixed(1) + "</td>"
                + "</tr>";
        });
        tbody.innerHTML = rows || "<tr><td colspan='8' style='text-align:center;color:#8b949e'>No latency data</td></tr>";
    }

    function handleMetricsUpdate(data) {
        updateKPIs(data.summary);
        updateToolCharts(data.summary.tool_counts);
        updateLatencyTable(data.summary.tool_latency);
        updateTimeline(data.timeseries);
        updateLatencyChart(data.timeseries);
    }

    // --- Audit Detail Panel ---
    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function toggleDetailRow(tr, requestId) {
        var existing = tr.nextSibling;
        if (existing && existing.classList && existing.classList.contains("detail-row")) {
            existing.parentNode.removeChild(existing);
            tr.classList.remove("detail-row-open");
            return;
        }

        tr.classList.add("detail-row-open");
        var detailTr = document.createElement("tr");
        detailTr.className = "detail-row";
        var td = document.createElement("td");
        td.colSpan = 6;
        td.innerHTML = "<div class='detail-panel'><span class='detail-loading'>Loading…</span></div>";
        detailTr.appendChild(td);
        tr.parentNode.insertBefore(detailTr, tr.nextSibling);

        if (!requestId || requestId === "-") {
            td.querySelector(".detail-loading").textContent = "No request ID — payload not available.";
            return;
        }

        fetch("/api/audit/" + encodeURIComponent(requestId) + "/detail")
            .then(function (r) {
                if (r.status === 404) throw new Error("not_found");
                return r.json();
            })
            .then(function (payload) {
                var reqJson = JSON.stringify(payload.request, null, 2);
                var resJson = JSON.stringify(payload.response, null, 2);
                td.innerHTML = "<div class='detail-panel'>"
                    + "<div class='detail-section'>"
                    + "<div class='detail-section-title'>Request</div>"
                    + "<pre class='detail-pre'>" + escapeHtml(reqJson) + "</pre>"
                    + "</div>"
                    + "<div class='detail-section'>"
                    + "<div class='detail-section-title'>Response</div>"
                    + "<pre class='detail-pre'>" + escapeHtml(resJson) + "</pre>"
                    + "</div>"
                    + "</div>";
            })
            .catch(function (err) {
                var msg = err && err.message === "not_found"
                    ? "Payload not captured (capture_payload disabled or entry evicted)."
                    : "Failed to load payload.";
                td.innerHTML = "<div class='detail-panel'><span class='detail-loading'>" + escapeHtml(msg) + "</span></div>";
            });
    }

    // --- Audit Log ---
    function loadAuditLogs() {
        var url = "/api/audit?limit=" + auditPageSize + "&offset=" + (auditPage * auditPageSize);
        if (auditFilter) url += "&tool=" + encodeURIComponent(auditFilter);

        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var tbody = el("audit-table").querySelector("tbody");
                tbody.innerHTML = "";

                if (!data.entries.length) {
                    tbody.innerHTML = "<tr><td colspan='6' style='text-align:center;color:#8b949e'>No audit entries</td></tr>";
                } else {
                    data.entries.forEach(function (e) {
                        var tr = document.createElement("tr");
                        tr.className = "audit-row";
                        var requestId = e.request_id || "";
                        var errClass = e.error ? ' class="error-cell"' : "";
                        tr.innerHTML = "<td>" + escapeHtml(e.timestamp_iso || "") + "</td>"
                            + "<td>" + escapeHtml(e.tool || "") + "</td>"
                            + "<td>" + escapeHtml(e.direction || "") + "</td>"
                            + "<td>" + escapeHtml(requestId || "-") + "</td>"
                            + "<td>" + (e.latency_ms != null ? e.latency_ms.toFixed(1) : "-") + "</td>"
                            + "<td" + errClass + ">" + escapeHtml(e.error || "-") + "</td>";
                        tr.addEventListener("click", function () {
                            toggleDetailRow(tr, requestId);
                        });
                        tbody.appendChild(tr);
                    });
                }

                el("audit-page-info").textContent = "Page " + (auditPage + 1);
                el("btn-audit-prev").disabled = auditPage === 0;
                el("btn-audit-next").disabled = data.entries.length < auditPageSize;
            })
            .catch(function () {});
    }

    // --- WebSocket Connection ---
    function connectWebSocket() {
        var protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        var url = protocol + "//" + window.location.host + "/ws/metrics";
        var wsToken = typeof window.__WS_AUTH_TOKEN__ === "string"
            ? window.__WS_AUTH_TOKEN__.trim()
            : "";
        if (wsToken) {
            url += "?token=" + encodeURIComponent(wsToken);
        }

        ws = new WebSocket(url);

        ws.onopen = function () {
            el("connection-status").textContent = "Connected";
            el("connection-status").className = "status-badge connected";
        };

        ws.onmessage = function (event) {
            try {
                var data = JSON.parse(event.data);
                if (data.type === "metrics_update") {
                    handleMetricsUpdate(data);
                }
            } catch (e) {
                // Ignore parse errors
            }
        };

        ws.onclose = function () {
            el("connection-status").textContent = "Disconnected";
            el("connection-status").className = "status-badge disconnected";
            // Reconnect after 3 seconds
            setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = function () {
            ws.close();
        };
    }

    // --- Fallback Polling ---
    function startPolling() {
        setInterval(function () {
            if (ws && ws.readyState === WebSocket.OPEN) return;

            Promise.all([
                fetch("/api/metrics").then(function (r) { return r.json(); }),
                fetch("/api/metrics/timeseries?seconds=300").then(function (r) { return r.json(); }),
            ])
                .then(function (results) {
                    handleMetricsUpdate({ summary: results[0], timeseries: results[1] });
                })
                .catch(function () {});
        }, 2000);
    }

    // --- Event Handlers ---
    function setupEventHandlers() {
        el("btn-reset-metrics").addEventListener("click", function () {
            if (confirm("Reset all metrics?")) {
                fetch("/api/metrics/reset", { method: "POST" })
                    .then(function () { loadAuditLogs(); })
                    .catch(function () {});
            }
        });

        el("btn-export-json").addEventListener("click", function () {
            window.location.href = "/api/audit/export/json";
        });

        el("btn-export-csv").addEventListener("click", function () {
            window.location.href = "/api/audit/export/csv";
        });

        el("btn-audit-prev").addEventListener("click", function () {
            if (auditPage > 0) {
                auditPage--;
                loadAuditLogs();
            }
        });

        el("btn-audit-next").addEventListener("click", function () {
            auditPage++;
            loadAuditLogs();
        });

        el("audit-filter").addEventListener("input", function () {
            auditFilter = this.value.trim();
            auditPage = 0;
            loadAuditLogs();
        });
    }

    // --- Session Timeline ---

    function loadSessions() {
        var gapInput = document.getElementById("session-gap-input");
        var gap = gapInput ? parseInt(gapInput.value, 10) || 300 : 300;
        fetch("/api/sessions?gap_seconds=" + gap)
            .then(function (r) { return r.json(); })
            .then(function (data) { renderTimeline(data.sessions || []); })
            .catch(function () { renderTimeline([]); });
    }

    function renderTimeline(sessions) {
        var container = document.getElementById("timeline-container");
        if (!container) return;

        if (!sessions || sessions.length === 0) {
            container.innerHTML = '<p class="timeline-empty">No sessions yet.</p>';
            return;
        }

        var html = "";
        sessions.forEach(function (session, idx) {
            var startDate = new Date(session.start * 1000).toLocaleString();
            var endDate = new Date(session.end * 1000).toLocaleString();
            var durationSec = Math.round(session.end - session.start);
            var errorBadge = session.error_count > 0
                ? '<span class="timeline-session-error-badge">' + session.error_count + ' error' + (session.error_count > 1 ? 's' : '') + '</span>'
                : "";

            html += '<div class="timeline-session" id="' + session.id + '">';
            html += '<div class="timeline-session-header">';
            html += '<span class="timeline-session-label">Session ' + (idx + 1) + '</span>';
            html += '<span class="timeline-session-meta">' + startDate + ' &mdash; ' + durationSec + 's &middot; ' + session.tool_count + ' call' + (session.tool_count !== 1 ? 's' : '') + '</span>';
            html += errorBadge;
            html += '</div>';
            html += '<div class="timeline-track">';

            session.tools.forEach(function (tool) {
                var dotClass = tool.error ? "timeline-dot error" : "timeline-dot";
                var latencyStr = tool.latency_ms != null ? tool.latency_ms + " ms" : "";
                var errorStr = tool.error ? '<span class="error-text">' + escHtml(tool.error) + '</span>' : "";
                var tsStr = tool.timestamp_iso || "";
                var reqId = tool.request_id || "";

                html += '<div class="timeline-node" onclick="openDetail(\'' + escHtml(reqId) + '\')">';
                html += '<span class="' + dotClass + '"></span>';
                html += '<div class="timeline-node-card">';
                html += '<div class="timeline-node-title">' + escHtml(tool.tool || "(unknown)") + '</div>';
                html += '<div class="timeline-node-meta">';
                if (tsStr) html += '<span>' + tsStr + '</span>';
                if (latencyStr) html += '<span class="latency">' + latencyStr + '</span>';
                if (errorStr) html += errorStr;
                html += '</div>';
                html += '</div>';
                html += '</div>';
            });

            html += '</div>';  // .timeline-track
            html += '</div>';  // .timeline-session
        });

        container.innerHTML = html;
    }

    function escHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    // --- Init ---
    function init() {
        initCharts();
        setupEventHandlers();
        connectWebSocket();
        startPolling();
        loadAuditLogs();
        loadSessions();
        // Refresh audit logs and sessions periodically
        setInterval(loadAuditLogs, 5000);
        setInterval(loadSessions, 15000);

        var btnRefreshSessions = document.getElementById("btn-refresh-sessions");
        if (btnRefreshSessions) {
            btnRefreshSessions.addEventListener("click", loadSessions);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
