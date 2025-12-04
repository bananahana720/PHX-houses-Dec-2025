"""HTML/CSS templates for deal sheet generation.

Contains:
- COMMON_CSS: Shared styles across all templates
- DEAL_SHEET_CSS: Styles specific to individual property sheets
- INDEX_CSS: Styles specific to master list page
- DEAL_SHEET_TEMPLATE: Individual property deal sheet HTML
- INDEX_TEMPLATE: Master list index page HTML

All templates use Jinja2 syntax for dynamic content rendering.
"""

# =============================================================================
# COMMON CSS - Shared across all templates
# =============================================================================
COMMON_CSS = """
/* Reset and Mobile-First Base */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    font-size: 16px;
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}

/* Typography - Mobile-First */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #1a1a1a;
    min-width: 320px;
    overflow-x: hidden;
}

/* Touch-Friendly Base Styles */
a, button, .clickable {
    min-height: 44px;
    min-width: 44px;
}

/* Prevent text overflow */
p, h1, h2, h3, h4, h5, h6, span, div {
    word-wrap: break-word;
    overflow-wrap: break-word;
}

/* Tier Badges */
.tier-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.tier-unicorn {
    background: linear-gradient(135deg, #a855f7, #ec4899);
    color: white;
}

.tier-contender {
    background: #3b82f6;
    color: white;
}

.tier-pass {
    background: #6b7280;
    color: white;
}

/* Status Colors */
.status-green { background: #22c55e; color: white; }
.status-red { background: #ef4444; color: white; }
.status-yellow { background: #f59e0b; color: white; }

/* Confidence Badges */
.confidence-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-left: 6px;
    vertical-align: middle;
}

.confidence-green {
    background: #dcfce7;
    color: #166534;
}

.confidence-yellow {
    background: #fef9c3;
    color: #854d0e;
}

.confidence-red {
    background: #fee2e2;
    color: #991b1b;
}

/* Header Styles */
.header {
    border-bottom: 3px solid #2563eb;
    padding-bottom: 15px;
    margin-bottom: 20px;
}

.header h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 10px;
    color: #1e40af;
}
"""

# =============================================================================
# DEAL SHEET CSS - Styles specific to individual property sheets
# =============================================================================
DEAL_SHEET_CSS = """
/* Deal Sheet Body */
body {
    background: #ffffff;
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

@media print {
    body { padding: 0; }
    .no-print { display: none; }
}

/* Deal Sheet Header */
.header h1 { font-size: 28px; }

.header-meta {
    display: flex;
    gap: 30px;
    align-items: center;
    flex-wrap: wrap;
    font-size: 18px;
}

.header-meta .price {
    font-size: 24px;
    font-weight: 700;
    color: #059669;
}

.header-meta .score {
    font-size: 20px;
    font-weight: 600;
}

/* Deal Sheet Tier Badge Override */
.tier-badge {
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
}

/* Sections */
.section {
    margin-bottom: 25px;
    page-break-inside: avoid;
}

.section h2 {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 12px;
    color: #1e40af;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 6px;
}

/* Kill Switch Table */
.kill-switch-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.kill-switch-table th {
    background: #f3f4f6;
    padding: 10px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #d1d5db;
    font-size: 14px;
}

.kill-switch-table td {
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 14px;
}

.kill-switch-table tr:last-child td { border-bottom: none; }

/* Status Indicators */
.status-indicator {
    display: inline-block;
    width: 80px;
    padding: 4px 0;
    text-align: center;
    border-radius: 4px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Verdict Badges */
.verdict-badge-container { margin-bottom: 15px; }

.verdict-badge {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.verdict-pass { background: #28a745; color: white; }
.verdict-warning { background: #ffc107; color: #212529; }
.verdict-fail { background: #dc3545; color: white; }

.severity-info {
    display: inline-block;
    margin-left: 15px;
    font-size: 14px;
    color: #6b7280;
}

/* Kill Switch Markers */
.hard-marker { color: #dc3545; font-weight: 700; font-size: 12px; }
.soft-marker { color: #6b7280; font-size: 12px; }
.severity-points { font-weight: 700; color: #dc3545; font-size: 12px; margin-left: 8px; }

/* Severity Breakdown */
.severity-breakdown {
    background: #f8f9fa;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px;
    margin-top: 15px;
    font-size: 13px;
}

.severity-breakdown .score-line { font-weight: 600; margin-bottom: 5px; }
.severity-breakdown .threshold-line { color: #6b7280; }

/* Scorecard */
.scorecard {
    background: #f9fafb;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
}

.score-row {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    gap: 15px;
}

.score-row:last-child {
    margin-bottom: 0;
    padding-top: 12px;
    border-top: 2px solid #d1d5db;
    font-weight: 700;
}

.score-label { min-width: 100px; font-weight: 600; font-size: 14px; }
.score-value { min-width: 80px; font-weight: 700; color: #1e40af; font-size: 14px; }

.score-bar-container {
    flex: 1;
    height: 24px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
}

.score-bar {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #2563eb);
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 8px;
}

.score-bar-percentage { color: white; font-size: 11px; font-weight: 700; }

/* Metrics Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
}

.metric {
    background: #f9fafb;
    padding: 12px;
    border-radius: 6px;
    border-left: 4px solid #3b82f6;
}

.metric-label {
    font-size: 12px;
    color: #6b7280;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.metric-value { font-size: 18px; font-weight: 700; color: #1e40af; }
.metric-note { font-size: 11px; color: #6b7280; margin-top: 2px; }

/* Assessment Notes */
.assessment-notes {
    margin-top: 15px;
    padding: 12px;
    background: #f8fafc;
    border-left: 3px solid #3b82f6;
    font-size: 13px;
    line-height: 1.5;
    color: #475569;
}

/* Features */
.features { display: flex; gap: 20px; flex-wrap: wrap; }
.feature-column { flex: 1; min-width: 250px; }
.feature-column h3 { font-size: 14px; font-weight: 700; margin-bottom: 8px; color: #059669; }
.feature-column.missing h3 { color: #dc2626; }
.feature-column ul { list-style: none; padding-left: 0; }
.feature-column li { padding: 4px 0; padding-left: 20px; position: relative; font-size: 14px; }
.feature-column li:before { content: "\\2713"; position: absolute; left: 0; color: #059669; font-weight: 700; }
.feature-column.missing li:before { content: "\\2717"; color: #dc2626; }

/* Back Link */
.back-link {
    display: inline-block;
    margin-bottom: 15px;
    color: #2563eb;
    text-decoration: none;
    font-weight: 600;
    padding: 8px 16px;
    border: 2px solid #2563eb;
    border-radius: 6px;
    transition: all 0.2s;
}

.back-link:hover { background: #2563eb; color: white; }

/* Failure Notice */
.failure-notice {
    background: #fef2f2;
    border: 2px solid #ef4444;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
}

.failure-notice h3 { color: #dc2626; font-size: 16px; margin-bottom: 8px; font-weight: 700; }
.failure-notice ul { margin-left: 20px; color: #7f1d1d; }

/* Cost Warning */
.cost-warning {
    background-color: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 8px;
    padding: 12px 15px;
    margin: 15px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.cost-warning .warning-badge {
    background-color: #ffc107;
    color: #000;
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.cost-warning .warning-text { font-weight: 600; font-size: 15px; color: #856404; }
.cost-warning .warning-note { font-size: 13px; color: #856404; opacity: 0.9; }

/* Location Risk Styling */
.metric-value.flood-minimal { color: #059669; }
.metric-value.flood-moderate { color: #f59e0b; }
.metric-value.flood-high { color: #dc2626; }
.metric-value.crime-safe { color: #059669; }
.metric-value.crime-average { color: #3b82f6; }
.metric-value.crime-dangerous { color: #dc2626; }

/* Noise Level Styling */
.metric-value.noise-quiet { color: #059669; }
.metric-value.noise-moderate { color: #f59e0b; }
.metric-value.noise-loud { color: #dc2626; }

/* =============================================================================
   MOBILE RESPONSIVE BREAKPOINTS
   ============================================================================= */

/* Small Mobile (320px - 374px) */
@media (max-width: 374px) {
    body { padding: 10px; font-size: 14px; }
    .header h1 { font-size: 20px; }
    .header-meta { flex-direction: column; gap: 10px; align-items: flex-start; }
    .header-meta .price { font-size: 20px; }
    .header-meta .score { font-size: 16px; }
    .metrics-grid { grid-template-columns: 1fr; gap: 10px; }
    .score-row { flex-direction: column; gap: 8px; }
    .score-label { min-width: auto; }
    .score-value { min-width: auto; }
    .kill-switch-table { font-size: 12px; }
    .kill-switch-table th, .kill-switch-table td { padding: 6px 4px; }
    .features { flex-direction: column; }
    .feature-column { min-width: 100%; }
}

/* Standard Mobile (375px - 767px) */
@media (min-width: 375px) and (max-width: 767px) {
    body { padding: 15px; }
    .header h1 { font-size: 22px; }
    .header-meta { flex-direction: column; gap: 12px; align-items: flex-start; }
    .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .score-row { flex-wrap: wrap; }
    .features { flex-direction: column; }
    .feature-column { min-width: 100%; }
}

/* Tablet (768px - 1023px) */
@media (min-width: 768px) and (max-width: 1023px) {
    body { padding: 20px; }
    .header h1 { font-size: 26px; }
    .metrics-grid { grid-template-columns: repeat(3, 1fr); }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
    body { padding: 20px; max-width: 1200px; margin: 0 auto; }
    .header h1 { font-size: 28px; }
    .metrics-grid { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
}

/* =============================================================================
   IMAGE GALLERY STYLES
   ============================================================================= */

.image-gallery {
    margin-top: 15px;
}

.image-gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
}

@media (min-width: 768px) {
    .image-gallery-grid {
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
    }
}

.image-gallery-item {
    position: relative;
    aspect-ratio: 4/3;
    overflow: hidden;
    border-radius: 8px;
    background: #f3f4f6;
}

.image-gallery-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.image-gallery-item:hover img {
    transform: scale(1.05);
}

.image-gallery-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 30px;
    background: #f9fafb;
    border: 2px dashed #d1d5db;
    border-radius: 8px;
    color: #6b7280;
    text-align: center;
}

.image-gallery-placeholder svg {
    width: 48px;
    height: 48px;
    margin-bottom: 10px;
    opacity: 0.5;
}

/* =============================================================================
   TOUR CHECKLIST STYLES
   ============================================================================= */

.tour-checklist {
    margin-top: 15px;
}

.checklist-items {
    list-style: none;
    padding: 0;
}

.checklist-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    margin-bottom: 8px;
    background: #f9fafb;
    border-radius: 6px;
    border-left: 4px solid #3b82f6;
    min-height: 44px;
}

.checklist-item.warning {
    border-left-color: #f59e0b;
    background: #fffbeb;
}

.checklist-item.fail {
    border-left-color: #ef4444;
    background: #fef2f2;
}

.checklist-checkbox {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    border: 2px solid #d1d5db;
    border-radius: 4px;
    margin-top: 2px;
}

.checklist-content {
    flex: 1;
}

.checklist-title {
    font-weight: 600;
    font-size: 14px;
    color: #1f2937;
    margin-bottom: 4px;
}

.checklist-detail {
    font-size: 13px;
    color: #6b7280;
}

.checklist-priority {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 8px;
}

.priority-high {
    background: #fef2f2;
    color: #dc2626;
}

.priority-medium {
    background: #fffbeb;
    color: #d97706;
}

.priority-low {
    background: #f0f9ff;
    color: #2563eb;
}

/* =============================================================================
   PRINT STYLES
   ============================================================================= */

@media print {
    body {
        padding: 0;
        font-size: 12px;
        color: #000;
        background: #fff;
    }

    .no-print { display: none !important; }

    .header { page-break-after: avoid; }
    .section { page-break-inside: avoid; }

    .tier-badge, .verdict-badge, .status-indicator {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    .image-gallery-grid {
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
    }

    .checklist-checkbox {
        border: 1px solid #000;
    }

    .checklist-item {
        padding: 8px;
        margin-bottom: 4px;
    }

    a { color: #000; text-decoration: none; }

    .back-link { display: none; }
}
"""

# =============================================================================
# INDEX CSS - Styles specific to master list page
# =============================================================================
INDEX_CSS = """
/* Index Body */
body {
    background: #f3f4f6;
    padding: 20px;
}

/* Container */
.container {
    max-width: 1400px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Index Header */
.header {
    padding-bottom: 20px;
    margin-bottom: 30px;
}

.header h1 { font-size: 32px; }
.header p { font-size: 16px; color: #6b7280; }

/* Stats Cards */
.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
}

.stat-card h3 {
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
    opacity: 0.9;
}

.stat-card .value { font-size: 32px; font-weight: 700; }

/* Properties Table */
.properties-table {
    width: 100%;
    border-collapse: collapse;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.properties-table thead { background: #f3f4f6; }

.properties-table th {
    padding: 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #d1d5db;
    font-size: 14px;
    color: #374151;
}

.properties-table td {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 14px;
}

.properties-table tbody tr:hover { background: #f9fafb; }
.properties-table tbody tr.failed { background: #fef2f2; }
.properties-table tbody tr.failed:hover { background: #fee2e2; }

/* Rank Badge */
.rank-badge {
    display: inline-block;
    width: 40px;
    height: 40px;
    line-height: 40px;
    text-align: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: white;
    font-weight: 700;
    font-size: 16px;
}

.rank-badge.top3 { background: linear-gradient(135deg, #10b981, #059669); }

/* Status Badge */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
}

.status-pass { background: #dcfce7; color: #166534; }
.status-fail { background: #fee2e2; color: #991b1b; }

/* Links */
.address-link {
    color: #2563eb;
    text-decoration: none;
    font-weight: 600;
}

.address-link:hover { text-decoration: underline; }

/* Score */
.score { font-weight: 700; color: #1e40af; font-size: 16px; }

/* Loading State */
.loading {
    text-align: center;
    padding: 60px 20px;
    font-size: 1.2em;
    color: #2563eb;
}

.loading::after {
    content: '';
    animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
    0%, 20% { content: ''; }
    40% { content: '.'; }
    60% { content: '..'; }
    80%, 100% { content: '...'; }
}

/* Error State */
.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.error strong { display: block; margin-bottom: 10px; }
.error em { font-size: 0.9em; opacity: 0.8; }
"""

# =============================================================================
# DEAL SHEET TEMPLATE - Individual property deal sheet HTML
# =============================================================================
DEAL_SHEET_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deal Sheet: {{{{ property.full_address }}}}</title>
    <style>{COMMON_CSS}{DEAL_SHEET_CSS}</style>
</head>
<body>
    <a href="index.html" class="back-link no-print">\\u2190 Back to All Properties</a>

    {{% if property.kill_switch_passed != 'PASS' %}}
    <div class="failure-notice">
        <h3>\\u26a0\\ufe0f KILL SWITCH FAILURES</h3>
        <ul>
        {{% for failure in property.kill_switch_failures.split(';') if failure.strip() %}}
            <li>{{{{ failure.strip() }}}}</li>
        {{% endfor %}}
        </ul>
    </div>
    {{% endif %}}

    {{% if monthly_cost and monthly_cost > 4000 %}}
    <div class="cost-warning">
        <span class="warning-badge">BUDGET WARNING</span>
        <span class="warning-text">Estimated Monthly Cost: ${{{{ "{{:,.0f}}".format(monthly_cost) }}}}</span>
        <span class="warning-note">(Exceeds $4,000 threshold)</span>
    </div>
    {{% endif %}}

    <div class="header">
        <h1>{{{{ property.full_address }}}}</h1>
        <div class="header-meta">
            <span class="price">${{{{ "{{:,.0f}}".format(property['price']) }}}}</span>
            <span class="score">{{{{ property['total_score'] }}}}/605 pts</span>
            <span class="tier-badge tier-{{{{ property['tier'].lower() }}}}">{{{{ property['tier'] }}}}</span>
            <span style="color: #6b7280;">Rank #{{{{ int(property['rank']) }}}}</span>
        </div>
    </div>

    <div class="section">
        <h2>Kill Switch Status</h2>

        <!-- Verdict Badge -->
        <div class="verdict-badge-container">
            {{% if ks_verdict == 'PASS' %}}
            <span class="verdict-badge verdict-pass">PASS</span>
            {{% elif ks_verdict == 'WARNING' %}}
            <span class="verdict-badge verdict-warning">WARNING</span>
            <span class="severity-info">Severity: {{{{ "%.1f"|format(ks_severity) }}}}/{{{{ "%.1f"|format(severity_fail_threshold) }}}}</span>
            {{% else %}}
            <span class="verdict-badge verdict-fail">{{% if ks_has_hard_failure %}}HARD FAIL{{% else %}}FAIL{{% endif %}}</span>
            {{% if not ks_has_hard_failure %}}
            <span class="severity-info">Severity: {{{{ "%.1f"|format(ks_severity) }}}}/{{{{ "%.1f"|format(severity_fail_threshold) }}}}</span>
            {{% endif %}}
            {{% endif %}}
        </div>

        <table class="kill-switch-table">
            <thead>
                <tr>
                    <th>Criterion</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
            {{% for name, status in kill_switches.items() %}}
                <tr>
                    <td><strong>{{{{ name }}}}</strong></td>
                    <td>
                        {{% if status.is_hard %}}
                        <span class="hard-marker">[H]</span>
                        {{% else %}}
                        <span class="soft-marker">[S]</span>
                        {{% endif %}}
                    </td>
                    <td>
                        <span class="status-indicator status-{{{{ status.color }}}}">
                            {{{{ status.label }}}}
                        </span>
                    </td>
                    <td>
                        {{{{ status.description }}}}
                        {{% if status.severity_weight > 0 %}}
                        <span class="severity-points">+{{{{ "%.1f"|format(status.severity_weight) }}}} pts</span>
                        {{% endif %}}
                    </td>
                </tr>
            {{% endfor %}}
            </tbody>
        </table>

        <!-- Severity Breakdown Footer -->
        {{% if ks_severity > 0 or ks_verdict != 'PASS' %}}
        <div class="severity-breakdown">
            <div class="score-line">
                Severity Score: {{{{ "%.1f"|format(ks_severity) }}}}/{{{{ "%.1f"|format(severity_fail_threshold) }}}}
                {{% if ks_severity > 0 %}}
                ({{% for name, status in kill_switches.items() if status.severity_weight > 0 %}}{{{{ name }}}}{{% if not loop.last %}}, {{% endif %}}{{% endfor %}})
                {{% endif %}}
            </div>
            <div class="threshold-line">
                Thresholds: FAIL >= {{{{ "%.1f"|format(severity_fail_threshold) }}}} | WARNING >= {{{{ "%.1f"|format(severity_warning_threshold) }}}}
            </div>
        </div>
        {{% endif %}}
    </div>

    <div class="section">
        <h2>Scorecard</h2>
        <div class="scorecard">
            <div class="score-row">
                <div class="score-label">Location:</div>
                <div class="score-value">{{{{ "{{:.1f}}".format(property.score_location) }}}}/250</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{{{ (property.score_location / 250 * 100)|round(1) }}}}%">
                        <span class="score-bar-percentage">{{{{ (property.score_location / 250 * 100)|round(0)|int }}}}%</span>
                    </div>
                </div>
            </div>
            <div class="score-row">
                <div class="score-label">Systems:</div>
                <div class="score-value">{{{{ "{{:.1f}}".format(property.score_lot_systems) }}}}/175</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{{{ (property.score_lot_systems / 175 * 100)|round(1) }}}}%">
                        <span class="score-bar-percentage">{{{{ (property.score_lot_systems / 175 * 100)|round(0)|int }}}}%</span>
                    </div>
                </div>
            </div>
            <div class="score-row">
                <div class="score-label">Interior:</div>
                <div class="score-value">{{{{ "{{:.1f}}".format(property.score_interior) }}}}/180</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{{{ (property.score_interior / 180 * 100)|round(1) }}}}%">
                        <span class="score-bar-percentage">{{{{ (property.score_interior / 180 * 100)|round(0)|int }}}}%</span>
                    </div>
                </div>
            </div>
            <div class="score-row">
                <div class="score-label">TOTAL:</div>
                <div class="score-value">{{{{ property.total_score }}}}/605</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{{{ (property.total_score / 605 * 100)|round(1) }}}}%">
                        <span class="score-bar-percentage">{{{{ (property.total_score / 605 * 100)|round(0)|int }}}}%</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Interior Assessment (Section C: 180 pts)</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Kitchen</div>
                <div class="metric-value">{{{{ property.kitchen_layout_score or 'N/A' }}}}/10</div>
                <div class="metric-note">(40 pts max)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Master Suite</div>
                <div class="metric-value">{{{{ property.master_suite_score or 'N/A' }}}}/10</div>
                <div class="metric-note">(35 pts max)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Natural Light</div>
                <div class="metric-value">{{{{ property.natural_light_score or 'N/A' }}}}/10</div>
                <div class="metric-note">(30 pts max)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Ceilings</div>
                <div class="metric-value">{{{{ property.high_ceilings_score or 'N/A' }}}}/10</div>
                <div class="metric-note">(25 pts max)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Fireplace</div>
                <div class="metric-value">{{% if property.fireplace_present %}}Yes{{% else %}}No{{% endif %}}</div>
                <div class="metric-note">(20 pts max)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Laundry</div>
                <div class="metric-value">{{{{ property.laundry_area_score or 'N/A' }}}}/10</div>
                <div class="metric-note">(20 pts max)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Aesthetics</div>
                <div class="metric-value">{{{{ property.aesthetics_score or 'N/A' }}}}/10</div>
                <div class="metric-note">(10 pts max)</div>
            </div>
        </div>
        {{% if property.interior_assessment_notes %}}
        <div class="assessment-notes">
            <strong>Assessment Notes:</strong> {{{{ property.interior_assessment_notes }}}}
        </div>
        {{% endif %}}
    </div>

    <div class="section">
        <h2>Exterior Assessment</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Roof Condition</div>
                <div class="metric-value">{{{{ property.roof_visual_condition or 'N/A' }}}}</div>
                <div class="metric-note">Est. Age: {{{{ property.roof_age_visual_estimate or property.roof_age or 'Unknown' }}}} yrs</div>
            </div>
            <div class="metric">
                <div class="metric-label">HVAC</div>
                <div class="metric-value">{{{{ property.hvac_brand or 'Unknown' }}}}</div>
                <div class="metric-note">Est. Age: {{{{ property.hvac_age_visual_estimate or property.hvac_age or 'Unknown' }}}} yrs | {{{{ property.hvac_refrigerant or 'N/A' }}}}</div>
            </div>
            {{% if property.has_pool %}}
            <div class="metric">
                <div class="metric-label">Pool Equipment</div>
                <div class="metric-value">{{{{ property.pool_system_type or 'Unknown' }}}}</div>
                <div class="metric-note">Est. Age: {{{{ property.pool_equipment_age_visual or property.pool_equipment_age or 'Unknown' }}}} yrs</div>
            </div>
            {{% endif %}}
            <div class="metric">
                <div class="metric-label">Covered Patio</div>
                <div class="metric-value">{{{{ 'Yes' if property.backyard_covered_patio else 'No' }}}}</div>
                <div class="metric-note">Score: {{{{ property.backyard_patio_score or 'N/A' }}}}/10</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Market Position</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Days on Market</div>
                <div class="metric-value">{{{{ property.days_on_market or 'N/A' }}}}</div>
                <div class="metric-note">{{% if property.days_on_market %}}{{% if property.days_on_market < 30 %}}Hot market{{% elif property.days_on_market > 90 %}}Buyer leverage{{% else %}}Normal{{% endif %}}{{% endif %}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Price Reduced</div>
                <div class="metric-value">{{{{ 'Yes' if property.price_reduced else 'No' }}}}</div>
                <div class="metric-note">{{% if property.price_reduced_pct %}}{{{{ property.price_reduced_pct }}}}% off{{% endif %}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Air Quality</div>
                <div class="metric-value">{{{{ property.air_quality_aqi or 'N/A' }}}}</div>
                <div class="metric-note">{{{{ property.air_quality_category or 'Unknown' }}}}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Location Risk Assessment</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Flood Zone</div>
                <div class="metric-value">{{{{ property.flood_zone or 'Unknown' }}}}</div>
                <div class="metric-note">Insurance: {{{{ property.flood_insurance_required or 'Unknown' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Safety Score</div>
                <div class="metric-value">
                    {{{{ property.safety_neighborhood_score or 'N/A' }}}}/100
                    {{{{ confidence_badges.safety_neighborhood_score|safe }}}}
                </div>
                <div class="metric-note">Higher = Safer</div>
            </div>
            <div class="metric">
                <div class="metric-label">Violent Crime Index</div>
                <div class="metric-value">{{{{ property.violent_crime_index or 'N/A' }}}}/100</div>
                <div class="metric-note">Higher = Safer</div>
            </div>
            <div class="metric">
                <div class="metric-label">Property Crime Index</div>
                <div class="metric-value">{{{{ property.property_crime_index or 'N/A' }}}}/100</div>
                <div class="metric-note">Higher = Safer</div>
            </div>
            <div class="metric">
                <div class="metric-label">Crime Risk Level</div>
                <div class="metric-value">{{{{ property.crime_risk_level or 'Unknown' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Zoning</div>
                <div class="metric-value">{{{{ property.zoning_code or 'Unknown' }}}}</div>
                <div class="metric-note">{{{{ property.zoning_description or '' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Noise Level</div>
                <div class="metric-value">{{{{ property.noise_score or 'N/A' }}}}/100</div>
                <div class="metric-note">{{{{ property.noise_label or 'Unknown' }}}} (100=Quietest)</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Walkability & Transit</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Walk Score</div>
                <div class="metric-value">{{{{ property.walk_score or 'N/A' }}}}/100</div>
                <div class="metric-note">{{{{ property.walk_score_description or '' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Transit Score</div>
                <div class="metric-value">{{{{ property.transit_score or 'N/A' }}}}/100</div>
                <div class="metric-note">{{{{ property.transit_score_description or '' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Bike Score</div>
                <div class="metric-value">{{{{ property.bike_score or 'N/A' }}}}/100</div>
                <div class="metric-note">{{{{ property.bike_score_description or '' }}}}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Neighborhood Demographics</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Census Tract</div>
                <div class="metric-value">{{{{ property.census_tract or 'Unknown' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Median Household Income</div>
                <div class="metric-value">${{{{ "{{:,}}".format(int(property.median_household_income)) if property.median_household_income else 'N/A' }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Median Home Value</div>
                <div class="metric-value">${{{{ "{{:,}}".format(int(property.median_home_value)) if property.median_home_value else 'N/A' }}}}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Key Metrics</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Price/Sqft</div>
                <div class="metric-value">${{{{ "{{:.2f}}".format(property.price_per_sqft) }}}}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Living Area</div>
                <div class="metric-value">{{{{ "{{:,}}".format(int(property.sqft)) }}}} sqft</div>
            </div>
            <div class="metric">
                <div class="metric-label">Lot Size</div>
                <div class="metric-value">
                    {{{{ "{{:,}}".format(int(property.lot_sqft)) if property.lot_sqft else 'N/A' }}}} sqft
                    {{{{ confidence_badges.lot_sqft|safe }}}}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Year Built</div>
                <div class="metric-value">
                    {{{{ int(property.year_built) if property.year_built else 'N/A' }}}}
                    {{{{ confidence_badges.year_built|safe }}}}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Garage Spaces</div>
                <div class="metric-value">
                    {{{{ int(property.garage_spaces) if property.garage_spaces else 'N/A' }}}}
                    {{{{ confidence_badges.garage_spaces|safe }}}}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">HOA Fee</div>
                <div class="metric-value">
                    ${{{{ "{{:,}}".format(int(property.hoa_fee)) if property.hoa_fee else '0' }}}}/mo
                    {{{{ confidence_badges.hoa_fee|safe }}}}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Commute Time</div>
                <div class="metric-value">{{{{ int(property.commute_minutes) }}}} min</div>
            </div>
            <div class="metric">
                <div class="metric-label">School Rating</div>
                <div class="metric-value">
                    {{{{ property.school_rating }}}}/10
                    {{{{ confidence_badges.school_rating|safe }}}}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Sun Orientation</div>
                <div class="metric-value">
                    {{{{ property.orientation or 'N/A' }}}}
                    {{{{ confidence_badges.orientation|safe }}}}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Property Tax</div>
                <div class="metric-value">${{{{ "{{:,}}".format(int(property.tax_annual)) }}}}/yr</div>
            </div>
            <div class="metric">
                <div class="metric-label">Grocery Distance</div>
                <div class="metric-value">{{{{ property.distance_to_grocery_miles }}}} mi</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Feature Highlights</h2>
        <div class="features">
            <div class="feature-column">
                <h3>PRESENT</h3>
                <ul>
                {{% for feature in features.present %}}
                    <li>{{{{ feature }}}}</li>
                {{% endfor %}}
                </ul>
            </div>
            <div class="feature-column missing">
                <h3>MISSING/UNKNOWN</h3>
                <ul>
                {{% for feature in features.missing %}}
                    <li>{{{{ feature }}}}</li>
                {{% endfor %}}
                </ul>
            </div>
        </div>
    </div>

    <!-- Image Gallery Section -->
    <div class="section">
        <h2>Property Images</h2>
        <div class="image-gallery">
            {{% if property_images and property_images|length > 0 %}}
            <div class="image-gallery-grid">
                {{% for image in property_images %}}
                <div class="image-gallery-item">
                    <img src="{{{{ image.path }}}}" alt="Property image {{{{ loop.index }}}}" loading="lazy">
                </div>
                {{% endfor %}}
            </div>
            {{% else %}}
            <div class="image-gallery-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span>No property images available</span>
                <span style="font-size: 12px; margin-top: 5px;">Images will appear after Phase 1 extraction</span>
            </div>
            {{% endif %}}
        </div>
    </div>

    <!-- Tour Checklist Section -->
    <div class="section">
        <h2>Tour Checklist</h2>
        <div class="tour-checklist">
            {{% if tour_checklist and tour_checklist|length > 0 %}}
            <ul class="checklist-items">
                {{% for item in tour_checklist %}}
                <li class="checklist-item {{{{ item.severity }}}}">
                    <div class="checklist-checkbox"></div>
                    <div class="checklist-content">
                        <div class="checklist-title">
                            {{{{ item.title }}}}
                            {{% if item.priority %}}
                            <span class="checklist-priority priority-{{{{ item.priority }}}}">{{{{ item.priority }}}}</span>
                            {{% endif %}}
                        </div>
                        {{% if item.detail %}}
                        <div class="checklist-detail">{{{{ item.detail }}}}</div>
                        {{% endif %}}
                    </div>
                </li>
                {{% endfor %}}
            </ul>
            {{% else %}}
            <div class="image-gallery-placeholder">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>No special inspection items</span>
                <span style="font-size: 12px; margin-top: 5px;">All kill-switch criteria passed - standard inspection recommended</span>
            </div>
            {{% endif %}}
        </div>
    </div>
</body>
</html>
"""

# =============================================================================
# INDEX TEMPLATE - Master list index page HTML
# =============================================================================
INDEX_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phoenix Home Deal Sheets - Master List</title>
    <style>{COMMON_CSS}{INDEX_CSS}</style>
</head>
<body>
    <div class="container">
        <!-- Loading State -->
        <div id="loading" class="loading">Loading property data</div>

        <!-- Error State -->
        <div id="error" class="error" style="display: none;"></div>

        <!-- Content (hidden until data loads) -->
        <div id="content" style="display: none;">
            <div class="header">
                <h1>Phoenix Home Deal Sheets</h1>
                <p>Automated property analysis with traffic light kill-switch indicators</p>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <h3>Total Properties</h3>
                    <div class="value" id="stat-total">-</div>
                </div>
                <div class="stat-card">
                    <h3>Passed Filters</h3>
                    <div class="value" id="stat-passed">-</div>
                </div>
                <div class="stat-card">
                    <h3>Failed Filters</h3>
                    <div class="value" id="stat-failed">-</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Score (Passed)</h3>
                    <div class="value" id="stat-avg">-</div>
                </div>
            </div>

            <table class="properties-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Address</th>
                        <th>City</th>
                        <th>Price</th>
                        <th>Score</th>
                        <th>Tier</th>
                        <th>Status</th>
                        <th>Deal Sheet</th>
                    </tr>
                </thead>
                <tbody id="properties-body">
                    <!-- Populated by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Format currency
        function formatCurrency(value) {{
            return '$' + value.toLocaleString('en-US', {{
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }});
        }}

        // Capitalize first letter
        function capitalize(str) {{
            return str.charAt(0).toUpperCase() + str.slice(1);
        }}

        // Get tier badge HTML
        function getTierBadge(tier) {{
            const tierLower = tier.toLowerCase();
            return '<span class="tier-badge tier-' + tierLower + '">' + capitalize(tierLower) + '</span>';
        }}

        // Get status badge HTML
        function getStatusBadge(status) {{
            const statusLower = status.toLowerCase();
            const cssClass = statusLower === 'pass' ? 'status-pass' : 'status-fail';
            return '<span class="status-badge ' + cssClass + '">' + status + '</span>';
        }}

        // Load and display data
        async function loadData() {{
            try {{
                const response = await fetch('./data.json');
                if (!response.ok) {{
                    throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                }}

                const data = await response.json();

                // Update stats
                document.getElementById('stat-total').textContent = data.metadata.total_properties;
                document.getElementById('stat-passed').textContent = data.metadata.passed_properties;
                document.getElementById('stat-failed').textContent = data.metadata.failed_properties;
                document.getElementById('stat-avg').textContent = data.metadata.avg_score_passed.toFixed(1);

                // Build table rows
                const tbody = document.getElementById('properties-body');
                let html = '';

                if (data.properties.length === 0) {{
                    html = '<tr><td colspan="8" style="text-align: center; padding: 40px;">No properties found</td></tr>';
                }} else {{
                    data.properties.forEach(function(prop) {{
                        const rowClass = prop.status !== 'PASS' ? 'failed' : '';
                        const rankClass = prop.rank <= 3 ? 'top3' : '';

                        html += '<tr class="' + rowClass + '">';
                        html += '<td><span class="rank-badge ' + rankClass + '">' + prop.rank + '</span></td>';
                        html += '<td>' + prop.address + '</td>';
                        html += '<td>' + prop.city + '</td>';
                        html += '<td>' + formatCurrency(prop.price) + '</td>';
                        html += '<td class="score">' + prop.total_score.toFixed(1) + '</td>';
                        html += '<td>' + getTierBadge(prop.tier) + '</td>';
                        html += '<td>' + getStatusBadge(prop.status) + '</td>';
                        html += '<td><a href="' + prop.filename + '" class="address-link">View Details \\u2192</a></td>';
                        html += '</tr>';
                    }});
                }}

                tbody.innerHTML = html;

                // Hide loading, show content
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'block';

            }} catch (error) {{
                console.error('Error loading data:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').innerHTML =
                    '<strong>Error loading property data</strong>' +
                    error.message + '<br><br>' +
                    '<em>Note: If opening this file directly (file:// protocol), ' +
                    'the browser may block loading data.json for security reasons. ' +
                    'Try using a local web server: python -m http.server 8000</em>';
            }}
        }}

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
"""
