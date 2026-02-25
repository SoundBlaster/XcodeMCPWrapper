/* XcodeMCPWrapper Dashboard - Frontend Logic */

(function () {
    "use strict";

    // --- State ---
    let ws = null;
    let charts = {};
    let auditPage = 0;
    const auditPageSize = 50;
    let auditFilter = "";
    var auditExpandedRows = Object.create(null);
    var latencyExpandedRows = Object.create(null);
    var latestAuditRefreshRequest = 0;
    var lastSeenTotalRequests = null;

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

    const TOOL_BASE_COLORS = [
        "#32BB88", "#C4D4EB", "#F8FFF1", "#C4E894", "#105F1B",
        "#AD32BA", "#EBC3C9", "#F2F5FF", "#95AEE8", "#2F105E",
    ];
    const TOOL_COLOR_MAP_STORAGE_KEY = "xcode_mcp_tool_colors_v2";
    const MEDIUM_WIDTH_BREAKPOINT = 1280;
    var toolColorMap = loadToolColorMap();

    function safeGetLocalStorageItem(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (_err) {
            return null;
        }
    }

    function safeSetLocalStorageItem(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (_err) {
            // Ignore storage failures (private mode, disabled storage, quota)
        }
    }

    function loadToolColorMap() {
        var raw = safeGetLocalStorageItem(TOOL_COLOR_MAP_STORAGE_KEY);
        if (!raw) return Object.create(null);
        try {
            var parsed = JSON.parse(raw);
            if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
                return Object.create(null);
            }
            var sanitized = Object.create(null);
            Object.keys(parsed).forEach(function (toolName) {
                var color = parsed[toolName];
                if (typeof color === "string" && color.length > 0) {
                    sanitized[toolName] = color;
                }
            });
            return sanitized;
        } catch (_err) {
            return Object.create(null);
        }
    }

    function persistToolColorMap() {
        safeSetLocalStorageItem(TOOL_COLOR_MAP_STORAGE_KEY, JSON.stringify(toolColorMap));
    }

    function hashString(input) {
        var hash = 0;
        for (var i = 0; i < input.length; i += 1) {
            hash = (hash * 31 + input.charCodeAt(i)) >>> 0;
        }
        return hash;
    }

    function hueDistance(a, b) {
        var diff = Math.abs(a - b) % 360;
        return diff > 180 ? 360 - diff : diff;
    }

    function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

    function hexToRgb(hex) {
        var value = String(hex || "").trim();
        if (!/^#[0-9a-fA-F]{6}$/.test(value)) return null;
        return {
            r: parseInt(value.slice(1, 3), 16),
            g: parseInt(value.slice(3, 5), 16),
            b: parseInt(value.slice(5, 7), 16),
        };
    }

    function rgbToHsl(rgb) {
        var r = rgb.r / 255;
        var g = rgb.g / 255;
        var b = rgb.b / 255;
        var max = Math.max(r, g, b);
        var min = Math.min(r, g, b);
        var h = 0;
        var s = 0;
        var l = (max + min) / 2;
        var d = max - min;

        if (d !== 0) {
            s = d / (1 - Math.abs((2 * l) - 1));
            if (max === r) h = ((g - b) / d) % 6;
            else if (max === g) h = ((b - r) / d) + 2;
            else h = ((r - g) / d) + 4;
            h *= 60;
            if (h < 0) h += 360;
        }

        return {
            h: Math.round(h),
            s: Math.round(s * 100),
            l: Math.round(l * 100),
        };
    }

    function parseColorToHsl(color) {
        var value = String(color || "").trim();
        var hslMatch = /^hsl\((\d{1,3}),\s*(\d{1,3})%?,\s*(\d{1,3})%?\)$/i.exec(value);
        if (hslMatch) {
            return {
                h: ((parseInt(hslMatch[1], 10) % 360) + 360) % 360,
                s: clamp(parseInt(hslMatch[2], 10), 0, 100),
                l: clamp(parseInt(hslMatch[3], 10), 0, 100),
            };
        }
        var rgb = hexToRgb(value);
        if (!rgb) return null;
        return rgbToHsl(rgb);
    }

    function extractHue(color) {
        var parsed = parseColorToHsl(color);
        return parsed ? parsed.h : null;
    }

    function buildCandidateColor(seed, attempt) {
        var baseColor = TOOL_BASE_COLORS[seed % TOOL_BASE_COLORS.length];
        var baseHsl = parseColorToHsl(baseColor);
        if (!baseHsl) return baseColor;

        var hueSteps = [0, 18, -18, 36, -36];
        var satSteps = [0, 6, -6, 12, -12];
        var lightSteps = [0, 7, -7, 12, -12];
        var stepIndex = Math.floor(attempt / TOOL_BASE_COLORS.length);

        var hue = (baseHsl.h + hueSteps[stepIndex % hueSteps.length] + 360) % 360;
        var sat = clamp(baseHsl.s + satSteps[stepIndex % satSteps.length], 35, 88);
        var light = clamp(baseHsl.l + lightSteps[stepIndex % lightSteps.length], 28, 86);
        return "hsl(" + hue + ", " + sat + "%, " + light + "%)";
    }

    function getUsedHues() {
        var used = [];
        Object.keys(toolColorMap).forEach(function (name) {
            var hue = extractHue(toolColorMap[name]);
            if (hue !== null) used.push(hue);
        });
        return used;
    }

    function chooseDistinctColor(toolName) {
        var seed = hashString(toolName) % TOOL_BASE_COLORS.length;
        var usedHues = getUsedHues();
        var maxAttempts = TOOL_BASE_COLORS.length * 5;
        for (var attempt = 0; attempt < maxAttempts; attempt += 1) {
            var candidate = buildCandidateColor(seed, attempt);
            var candidateHue = extractHue(candidate);
            if (candidateHue === null) return candidate;
            var tooClose = usedHues.some(function (h) {
                return hueDistance(candidateHue, h) < 16;
            });
            if (!tooClose) return candidate;
        }
        return buildCandidateColor(seed, 0);
    }

    function getStableColorForTool(toolName) {
        var key = typeof toolName === "string" && toolName.length > 0 ? toolName : "(unknown)";
        if (toolColorMap[key]) return toolColorMap[key];
        var color = chooseDistinctColor(key);
        toolColorMap[key] = color;
        persistToolColorMap();
        return color;
    }

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
            data: { labels: [], datasets: [{ label: "Calls", data: [], backgroundColor: TOOL_BASE_COLORS }] },
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
            data: { labels: [], datasets: [{ data: [], backgroundColor: TOOL_BASE_COLORS }] },
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

        updateDoughnutLegendLayout();
    }

    function shouldUseBottomLegend() {
        return window.innerWidth <= MEDIUM_WIDTH_BREAKPOINT;
    }

    function updateDoughnutLegendLayout() {
        var legendPosition = shouldUseBottomLegend() ? "bottom" : "right";
        ["toolPie", "errorBreakdown"].forEach(function (chartName) {
            var chart = charts[chartName];
            if (!chart || !chart.options || !chart.options.plugins || !chart.options.plugins.legend) {
                return;
            }
            if (chart.options.plugins.legend.position !== legendPosition) {
                chart.options.plugins.legend.position = legendPosition;
                chart.update("none");
            }
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
            var escapedCount = escapeHtml(String(count));
            var escapedLastSeen = escapeHtml(String(lastSeen));
            return "<div class='client-widget-card'>"
                + "<div class='client-widget-title'>" + escapeHtml(name) + " " + escapeHtml(version) + "</div>"
                + "<div class='client-widget-meta'>Initialize calls: " + escapedCount + "</div>"
                + "<div class='client-widget-meta'>Last seen: " + escapedLastSeen + "</div>"
                + "</div>";
        }).join("");
    }

    function updateToolCharts(toolCounts) {
        var tools = Object.keys(toolCounts).sort();
        var counts = tools.map(function (t) { return toolCounts[t]; });
        var toolColors = tools.map(function (tool) {
            return getStableColorForTool(tool);
        });

        charts.toolBar.data.labels = tools;
        charts.toolBar.data.datasets[0].data = counts;
        charts.toolBar.data.datasets[0].backgroundColor = toolColors;
        charts.toolBar.update("none");

        charts.toolPie.data.labels = tools;
        charts.toolPie.data.datasets[0].data = counts;
        charts.toolPie.data.datasets[0].backgroundColor = toolColors;
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

    function updateTimeline(timeseries) {
        var requestPoints = Array.isArray(timeseries && timeseries.requests)
            ? timeseries.requests
            : [];
        var errorPoints = Array.isArray(timeseries && timeseries.errors)
            ? timeseries.errors
            : [];

        var reqMap = {};
        requestPoints.forEach(function (point) {
            var label = Math.round(point.t);
            reqMap[label] = point.v;
        });

        var errMap = {};
        errorPoints.forEach(function (point) {
            var label = Math.round(point.t);
            errMap[label] = point.v;
        });

        // Union all labels from backend-provided buckets.
        var labelSet = {};
        requestPoints.forEach(function (point) { labelSet[Math.round(point.t)] = true; });
        errorPoints.forEach(function (point) { labelSet[Math.round(point.t)] = true; });
        var labels = Object.keys(labelSet).map(Number).sort(function (a, b) { return b - a; });

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

    function collectExpandedLatencyRows(tbody) {
        var expanded = Object.create(null);
        if (!tbody) {
            return expanded;
        }
        var openButtons = tbody.querySelectorAll(".param-toggle-btn[aria-expanded='true']");
        for (var i = 0; i < openButtons.length; i++) {
            var tool = openButtons[i].getAttribute("data-tool");
            if (tool) {
                expanded[tool] = true;
            }
        }
        return expanded;
    }

    function updateLatencyTable(toolLatency) {
        var tbody = el("latency-table").querySelector("tbody");
        var expandedRows = collectExpandedLatencyRows(tbody);
        Object.keys(latencyExpandedRows).forEach(function (tool) {
            expandedRows[tool] = true;
        });
        var nextExpandedRows = Object.create(null);
        tbody.innerHTML = "";
        var tools = Object.keys(toolLatency).sort();
        if (tools.length === 0) {
            latencyExpandedRows = Object.create(null);
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

            if (expandedRows[tool]) {
                detailTr.style.display = "";
                var toggleBtn = tr.querySelector(".param-toggle-btn");
                if (toggleBtn) {
                    toggleBtn.innerHTML = "&#x25BC;";
                    toggleBtn.setAttribute("aria-expanded", "true");
                }
                fetchParamPatterns(tool, "patterns-" + rowId);
                nextExpandedRows[tool] = true;
            }
        });
        latencyExpandedRows = nextExpandedRows;
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

        // Refresh audit rows when request volume changes so new calls appear quickly.
        var totalRequests = data && data.summary ? data.summary.total_requests : null;
        if (typeof totalRequests === "number" && totalRequests !== lastSeenTotalRequests) {
            lastSeenTotalRequests = totalRequests;
            loadAuditLogs();
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

    function getAuditRowKey(entry) {
        return [
            String(entry.request_id || "-"),
            String(entry.timestamp_iso || "-"),
            String(entry.tool || "-"),
            String(entry.direction || "-"),
            String(entry.error || "-"),
        ].join("|");
    }

    function collectExpandedAuditRows(tbody) {
        var expanded = Object.create(null);
        if (!tbody) {
            return expanded;
        }

        var openRows = tbody.querySelectorAll("tr.audit-row.detail-row-open");
        for (var i = 0; i < openRows.length; i++) {
            var rowKey = openRows[i].getAttribute("data-audit-row-key");
            if (rowKey) {
                expanded[rowKey] = true;
            }
        }

        return expanded;
    }

    function toggleDetailRow(tr, requestId, rowKey, persistState) {
        var shouldPersist = persistState !== false;
        var existing = tr.nextElementSibling;
        if (existing && existing.classList && existing.classList.contains("detail-row")) {
            existing.parentNode.removeChild(existing);
            tr.classList.remove("detail-row-open");
            if (shouldPersist && rowKey) {
                delete auditExpandedRows[rowKey];
            }
            return;
        }

        tr.classList.add("detail-row-open");
        if (shouldPersist && rowKey) {
            auditExpandedRows[rowKey] = true;
        }
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
        url += "&_ts=" + Date.now();
        var refreshRequestId = ++latestAuditRefreshRequest;

        fetch(url, { cache: "no-store" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (refreshRequestId !== latestAuditRefreshRequest) {
                    return;
                }
                var tbody = el("audit-table").querySelector("tbody");
                var expandedRows = collectExpandedAuditRows(tbody);
                for (var key in auditExpandedRows) {
                    if (Object.prototype.hasOwnProperty.call(auditExpandedRows, key)) {
                        expandedRows[key] = true;
                    }
                }
                tbody.innerHTML = "";
                var nextExpandedRows = Object.create(null);

                if (!data.entries.length) {
                    tbody.innerHTML = "<tr><td colspan='6' style='text-align:center;color:#8b949e'>No audit entries</td></tr>";
                } else {
                    data.entries.forEach(function (e) {
                        var rowKey = getAuditRowKey(e);
                        var tr = document.createElement("tr");
                        tr.className = "audit-row";
                        tr.setAttribute("data-audit-row-key", rowKey);
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
                            toggleDetailRow(tr, requestId, rowKey);
                        });
                        tbody.appendChild(tr);
                        if (expandedRows[rowKey]) {
                            toggleDetailRow(tr, requestId, rowKey, false);
                            nextExpandedRows[rowKey] = true;
                        }
                    });
                }
                auditExpandedRows = nextExpandedRows;

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
                auditExpandedRows = Object.create(null);
                loadAuditLogs();
            }
        });

        el("btn-audit-next").addEventListener("click", function () {
            auditPage++;
            auditExpandedRows = Object.create(null);
            loadAuditLogs();
        });

        el("audit-filter").addEventListener("input", function () {
            auditFilter = this.value.trim();
            auditPage = 0;
            auditExpandedRows = Object.create(null);
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
                delete latencyExpandedRows[toolName];
            } else {
                detailRow.style.display = "";
                btn.innerHTML = "&#x25BC;";
                btn.setAttribute("aria-expanded", "true");
                latencyExpandedRows[toolName] = true;
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
        window.addEventListener("resize", updateDoughnutLegendLayout);
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
