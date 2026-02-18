/* XcodeMCPWrapper Dashboard - Frontend Logic */

(function () {
    "use strict";

    // --- State ---
    let ws = null;
    let charts = {};
    let auditPage = 0;
    const auditPageSize = 50;
    let auditFilter = "";

    // --- Theme ---
    var THEME_COLORS = {
        dark:  { label: "#8b949e", border: "#30363d", grid: "#21262d" },
        light: { label: "#636e7b", border: "#d0d7de", grid: "#e8ecf0" },
    };

    function applyChartTheme(isDark) {
        var t = isDark ? THEME_COLORS.dark : THEME_COLORS.light;
        Chart.defaults.color = t.label;
        Chart.defaults.borderColor = t.border;
        Object.values(charts).forEach(function (chart) {
            if (!chart || !chart.options) return;
            var scales = chart.options.scales || {};
            Object.values(scales).forEach(function (scale) {
                if (scale && scale.grid) scale.grid.color = t.grid;
            });
            chart.update("none");
        });
    }

    function initTheme() {
        var saved = localStorage.getItem("theme") || "dark";
        var isDark = saved !== "light";
        document.documentElement.dataset.theme = isDark ? "dark" : "light";
        applyChartTheme(isDark);
        var btn = el("btn-theme-toggle");
        if (btn) btn.textContent = isDark ? "Light Mode" : "Dark Mode";
    }

    function setupThemeToggle() {
        var btn = el("btn-theme-toggle");
        if (!btn) return;
        btn.addEventListener("click", function () {
            var isDark = document.documentElement.dataset.theme !== "light";
            var next = isDark ? "light" : "dark";
            document.documentElement.dataset.theme = next;
            localStorage.setItem("theme", next);
            applyChartTheme(next === "dark");
            btn.textContent = next === "dark" ? "Light Mode" : "Dark Mode";
        });
    }

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

        // Error breakdown doughnut chart
        charts.errorBreakdown = new Chart(el("chart-error-breakdown"), {
            type: "doughnut",
            data: {
                labels: ["Protocol", "Tool", "Timeout", "Unknown"],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ["#e53935", "#f57c00", "#f9a825", "#757575"],
                }],
            },
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
        var clients = Array.isArray(summary.clients) ? summary.clients.slice() : [];
        if (!clients.length && summary.client_name && summary.client_name !== "unknown") {
            clients = [{
                name: summary.client_name,
                version: summary.client_version || "unknown",
                initialize_count: 1,
            }];
        }
        renderClientWidgets(clients);
    }

    function formatRelativeAge(epochSeconds) {
        if (typeof epochSeconds !== "number" || !isFinite(epochSeconds)) return "unknown";
        var age = Math.max(0, Math.round((Date.now() / 1000) - epochSeconds));
        if (age < 60) return age + "s ago";
        if (age < 3600) return Math.floor(age / 60) + "m ago";
        return Math.floor(age / 3600) + "h ago";
    }

    function renderClientWidgets(clients) {
        var container = el("client-widgets-grid");
        if (!container) return;
        if (!clients || !clients.length) {
            container.innerHTML = '<p class="clients-empty">No clients detected yet.</p>';
            return;
        }

        container.innerHTML = clients.map(function (client) {
            var name = client.name || "unknown";
            var version = client.version || "unknown";
            var count = client.initialize_count || 0;
            var lastSeen = formatRelativeAge(client.last_seen);
            return "<div class='client-widget-card'>"
                + "<div class='client-widget-title'>" + escapeHtml(name) + " " + escapeHtml(version) + "</div>"
                + "<div class='client-widget-meta'>Initialize calls: " + count + "</div>"
                + "<div class='client-widget-meta'>Last seen: " + escapeHtml(lastSeen) + "</div>"
                + "</div>";
        }).join("");
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

    function categorizeError(code) {
        if (code === null || code === undefined) return "unknown";
        if (code >= -32699 && code <= -32600) return "protocol";
        if (code === -32001) return "timeout";
        if (code >= 1) return "tool";
        return "unknown";
    }

    function updateErrorBreakdownChart(errorCountsByCode) {
        var counts = { protocol: 0, tool: 0, timeout: 0, unknown: 0 };
        var total = 0;
        Object.keys(errorCountsByCode || {}).forEach(function (codeStr) {
            var code = parseInt(codeStr, 10);
            var cat = categorizeError(code);
            counts[cat] += errorCountsByCode[codeStr];
            total += errorCountsByCode[codeStr];
        });

        var emptyEl = el("error-breakdown-empty");
        if (total === 0) {
            el("chart-error-breakdown").style.display = "none";
            if (emptyEl) emptyEl.style.display = "block";
        } else {
            el("chart-error-breakdown").style.display = "";
            if (emptyEl) emptyEl.style.display = "none";
            charts.errorBreakdown.data.datasets[0].data = [
                counts.protocol, counts.tool, counts.timeout, counts.unknown,
            ];
            charts.errorBreakdown.update("none");
        }
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
        tbody.innerHTML = "";
        var tools = Object.keys(toolLatency).sort();
        if (tools.length === 0) {
            tbody.innerHTML = "<tr><td colspan='8' style='text-align:center;color:#8b949e'>No latency data</td></tr>";
            return;
        }
        tools.forEach(function (tool) {
            var s = toolLatency[tool];
            var rowId = "param-row-" + tool.replace(/[^a-zA-Z0-9]/g, "_");
            var tr = document.createElement("tr");
            tr.innerHTML = "<td>"
                + "<button class='param-toggle-btn' data-tool='" + tool + "' "
                + "data-target='" + rowId + "' title='Show parameter patterns' "
                + "aria-expanded='false'>&#x25B6;</button> " + tool
                + "</td>"
                + "<td>" + s.count + "</td>"
                + "<td>" + s.avg_ms.toFixed(1) + "</td>"
                + "<td>" + s.p50_ms.toFixed(1) + "</td>"
                + "<td>" + s.p95_ms.toFixed(1) + "</td>"
                + "<td>" + s.p99_ms.toFixed(1) + "</td>"
                + "<td>" + s.min_ms.toFixed(1) + "</td>"
                + "<td>" + s.max_ms.toFixed(1) + "</td>";
            tbody.appendChild(tr);

            var detailTr = document.createElement("tr");
            detailTr.id = rowId;
            detailTr.className = "param-detail-row";
            detailTr.style.display = "none";
            detailTr.innerHTML = "<td colspan='8'><div class='param-patterns-container' id='patterns-" + rowId + "'>"
                + "<em style='color:#8b949e'>Loading\u2026</em></div></td>";
            tbody.appendChild(detailTr);
        });
    }

    function fetchParamPatterns(toolName, containerId) {
        fetch("/api/analytics/param-patterns?tool=" + encodeURIComponent(toolName) + "&top_n=10")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var container = document.getElementById(containerId);
                if (!container) return;
                if (!data.patterns || data.patterns.length === 0) {
                    container.innerHTML = "<em style='color:#8b949e'>No parameter patterns captured. Enable <code>capture_params</code> in config.</em>";
                    return;
                }
                var html = "<table class='param-patterns-table'><thead><tr><th>Parameter Keys</th><th>Count</th></tr></thead><tbody>";
                data.patterns.forEach(function (p) {
                    html += "<tr><td><code>" + p.keys.join(", ") + "</code></td><td>" + p.count + "</td></tr>";
                });
                html += "</tbody></table>";
                container.innerHTML = html;
            })
            .catch(function () {
                var container = document.getElementById(containerId);
                if (container) container.innerHTML = "<em style='color:#f85149'>Failed to load patterns.</em>";
            });
    }

    function handleMetricsUpdate(data) {
        updateKPIs(data.summary);
        updateToolCharts(data.summary.tool_counts);
        updateErrorBreakdownChart(data.summary.error_counts_by_code || {});
        updateLatencyTable(data.summary.tool_latency);
        updateTimeline(data.timeseries);
        updateLatencyChart(data.timeseries);
        if (data.sessions !== undefined) {
            renderTimeline(data.sessions);
        }
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
                        var errSeverityClass = "";
                        if (e.error) {
                            var errCat = categorizeError(e.error_code != null ? e.error_code : null);
                            errSeverityClass = ' class="error-' + errCat + '"';
                        }
                        tr.innerHTML = "<td>" + escapeHtml(e.timestamp_iso || "") + "</td>"
                            + "<td>" + escapeHtml(e.tool || "") + "</td>"
                            + "<td>" + escapeHtml(e.direction || "") + "</td>"
                            + "<td>" + escapeHtml(requestId || "-") + "</td>"
                            + "<td>" + (e.latency_ms != null ? e.latency_ms.toFixed(1) : "-") + "</td>"
                            + "<td" + errSeverityClass + ">" + escapeHtml(e.error || "-") + "</td>";
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

            var gapInput = document.getElementById("session-gap-input");
            var gap = gapInput ? parseInt(gapInput.value, 10) || 300 : 300;
            Promise.all([
                fetch("/api/metrics").then(function (r) { return r.json(); }),
                fetch("/api/metrics/timeseries?seconds=300").then(function (r) { return r.json(); }),
                fetch("/api/sessions?gap_seconds=" + gap).then(function (r) { return r.json(); }),
            ])
                .then(function (results) {
                    handleMetricsUpdate({
                        summary: results[0],
                        timeseries: results[1],
                        sessions: results[2].sessions || [],
                    });
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

        el("latency-table").addEventListener("click", function (e) {
            var btn = e.target.closest(".param-toggle-btn");
            if (!btn) return;
            var targetId = btn.getAttribute("data-target");
            var toolName = btn.getAttribute("data-tool");
            var detailRow = document.getElementById(targetId);
            if (!detailRow) return;
            var isOpen = detailRow.style.display !== "none";
            if (isOpen) {
                detailRow.style.display = "none";
                btn.innerHTML = "&#x25B6;";
                btn.setAttribute("aria-expanded", "false");
            } else {
                detailRow.style.display = "";
                btn.innerHTML = "&#x25BC;";
                btn.setAttribute("aria-expanded", "true");
                fetchParamPatterns(toolName, "patterns-" + targetId);
            }
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

    // --- Keyboard Shortcuts ---
    function initKeyboardShortcuts() {
        var overlay = document.getElementById("shortcut-help-overlay");
        var btnClose = document.getElementById("btn-close-shortcuts");

        function isInputFocused() {
            var tag = document.activeElement && document.activeElement.tagName;
            return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
        }

        function scrollToSection(id) {
            var el = document.getElementById(id);
            if (el) { el.scrollIntoView({ behavior: "smooth", block: "start" }); }
        }

        function toggleOverlay() {
            if (!overlay) return;
            overlay.classList.toggle("hidden");
        }

        function showOverlay() {
            if (!overlay) return;
            overlay.classList.remove("hidden");
        }

        function hideOverlay() {
            if (!overlay) return;
            overlay.classList.add("hidden");
        }

        document.addEventListener("keydown", function (e) {
            // Never fire when typing in inputs
            if (isInputFocused()) return;

            switch (e.key) {
                case "?":
                    e.preventDefault();
                    toggleOverlay();
                    break;
                case "1":
                    e.preventDefault();
                    scrollToSection("section-charts-1");
                    break;
                case "2":
                    e.preventDefault();
                    scrollToSection("section-charts-2");
                    break;
                case "3":
                    e.preventDefault();
                    scrollToSection("section-charts-3");
                    break;
                case "4":
                    e.preventDefault();
                    scrollToSection("section-latency-table");
                    break;
                case "a":
                    e.preventDefault();
                    scrollToSection("section-audit-log");
                    break;
                case "r":
                    e.preventDefault();
                    if (confirm("Reset all metrics?")) {
                        fetch("/api/metrics/reset", { method: "POST" })
                            .then(function () { loadAuditLogs(); })
                            .catch(function () {});
                    }
                    break;
                case "e":
                    e.preventDefault();
                    window.location.href = "/api/audit/export/json";
                    break;
                case "Escape":
                    hideOverlay();
                    break;
            }
        });

        if (btnClose) {
            btnClose.addEventListener("click", hideOverlay);
        }

        // Close overlay when clicking backdrop (outside modal)
        if (overlay) {
            overlay.addEventListener("click", function (e) {
                if (e.target === overlay) { hideOverlay(); }
            });
        }
    }

    // --- Init ---
    function init() {
        initCharts();
        initTheme();
        setupThemeToggle();
        setupEventHandlers();
        initKeyboardShortcuts();
        connectWebSocket();
        startPolling();
        loadAuditLogs();
        loadSessions();
        // Refresh audit logs periodically; sessions are pushed via WebSocket
        setInterval(loadAuditLogs, 5000);

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
