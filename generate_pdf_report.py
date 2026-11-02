"""
Generates an academic-grade, publication-ready PDF for CineMatch Project Report.
Uses Python Markdown with PyMdown Extensions, KaTeX, and Headless Chrome.
Author: Sahil (Reg: 2427010355)
"""
import os
import re
import subprocess
import markdown
import pypdf

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(PROJECT_DIR, 'PROJECT_REPORT.md')
HTML_PATH = os.path.join(PROJECT_DIR, 'PROJECT_REPORT.html')
PDF_PATH = os.path.join(PROJECT_DIR, 'PROJECT_REPORT_Sahil_2427010355.pdf')
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

with open(MD_PATH, 'r', encoding='utf-8') as f:
    raw_md = f.read()

# Strip out the initial raw markdown title block since the formal cover page covers it
cleaned_md = re.sub(
    r'^# CineMatch: Hybrid AI-Powered Movie Recommender & Discovery Platform.*?(?=## 1\. Executive Summary)',
    '',
    raw_md,
    flags=re.DOTALL
)

# Convert Markdown to HTML using tables, fenced_code, and arithmatex for KaTeX math protection
html_content = markdown.markdown(
    cleaned_md,
    extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'attr_list',
        'def_list',
        'pymdownx.arithmatex'
    ],
    extension_configs={
        'pymdownx.arithmatex': {
            'generic': True
        }
    }
)

# Custom Print & Typography CSS designed for dense, balanced page filling
PAGE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

@page {
    size: A4;
    margin: 16mm 14mm 16mm 14mm;
    @top-right {
        content: "CineMatch — Project Report | Sahil (2427010355)";
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 7.5pt;
        color: #64748B;
        font-weight: 500;
    }
    @bottom-left {
        content: "Department of Computer Science & Engineering";
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 7.5pt;
        color: #94A3B8;
    }
    @bottom-right {
        content: "Page " counter(page);
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 8pt;
        color: #475569;
        font-weight: 600;
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #0F172A;
    background: #FFFFFF;
    font-size: 9.25pt;
    line-height: 1.50;
    margin: 0;
    padding: 0;
}

/* Headings */
h1 {
    font-size: 15pt;
    font-weight: 800;
    color: #0F172A;
    margin-top: 1.2rem;
    margin-bottom: 0.5rem;
    border-bottom: 1.5px solid #4F46E5;
    padding-bottom: 0.25rem;
    break-after: avoid;
    page-break-after: avoid;
}

h2 {
    font-size: 12pt;
    font-weight: 750;
    color: #1E293B;
    margin-top: 1.0rem;
    margin-bottom: 0.4rem;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 0.2rem;
    break-after: avoid;
    page-break-after: avoid;
}

h3 {
    font-size: 10.2pt;
    font-weight: 700;
    color: #334155;
    margin-top: 0.8rem;
    margin-bottom: 0.3rem;
    break-after: avoid;
    page-break-after: avoid;
}

h4 {
    font-size: 9.5pt;
    font-weight: 700;
    color: #475569;
    margin-top: 0.6rem;
    margin-bottom: 0.25rem;
    break-after: avoid;
    page-break-after: avoid;
}

p {
    margin-top: 0;
    margin-bottom: 0.6rem;
    text-align: justify;
    text-justify: inter-word;
    orphans: 3;
    widows: 3;
}

ul, ol {
    margin-top: 0;
    margin-bottom: 0.6rem;
    padding-left: 1.4rem;
    orphans: 3;
    widows: 3;
}

li {
    margin-bottom: 0.25rem;
    text-align: justify;
}

/* Cover Page Styles */
.cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 88vh;
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}

.cover-badge {
    display: inline-block;
    background: #EEF2FF;
    color: #4338CA;
    font-weight: 700;
    font-size: 8.5pt;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 0.35rem 1.2rem;
    border-radius: 999px;
    border: 1px solid #C7D2FE;
    margin-bottom: 1.2rem;
}

.cover-title {
    font-size: 26pt;
    font-weight: 900;
    line-height: 1.15;
    color: #0F172A;
    margin: 0 0 0.5rem;
    letter-spacing: -0.5px;
}

.cover-tagline {
    font-size: 14pt;
    font-weight: 750;
    color: #4F46E5;
    margin-bottom: 0.5rem;
    letter-spacing: -0.3px;
}

.cover-subtitle {
    font-size: 10.5pt;
    color: #475569;
    font-weight: 500;
    max-width: 580px;
    margin: 0 auto 2rem;
    line-height: 1.45;
}

.cover-card {
    background: #F8FAFC;
    border: 1.5px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    width: 100%;
    max-width: 520px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
    margin-bottom: 1.8rem;
    text-align: left;
}

.cover-card table {
    width: 100%;
    border-collapse: collapse;
    margin: 0;
}

.cover-card td {
    padding: 0.45rem 0.4rem;
    border-bottom: 1px solid #EDF2F7;
    font-size: 9.5pt;
}

.cover-card tr:last-child td {
    border-bottom: none;
}

.cover-card td:first-child {
    font-weight: 700;
    color: #475569;
    width: 40%;
}

.cover-card td:last-child {
    color: #0F172A;
    font-weight: 600;
}

.cover-footer {
    font-size: 8.5pt;
    color: #64748B;
    margin-top: 1rem;
    line-height: 1.5;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.6rem 0 0.8rem;
    font-size: 8.5pt;
    break-inside: auto;
}

tr {
    break-inside: avoid;
    page-break-inside: avoid;
}

th {
    background: #F1F5F9;
    color: #1E293B;
    font-weight: 700;
    text-align: left;
    padding: 0.45rem 0.6rem;
    border: 1px solid #CBD5E1;
}

td {
    padding: 0.4rem 0.6rem;
    border: 1px solid #E2E8F0;
    vertical-align: top;
}

tr:nth-child(even) td {
    background: #F8FAFC;
}

/* Code Blocks */
pre {
    background: #0F172A;
    color: #F8FAFC;
    border-radius: 6px;
    padding: 0.65rem 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.8pt;
    line-height: 1.45;
    overflow-x: auto;
    margin: 0.55rem 0;
    break-inside: avoid;
}

code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 8pt;
    background: #F1F5F9;
    color: #4338CA;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
}

pre code {
    background: transparent;
    color: inherit;
    padding: 0;
}

/* Quotes & Callouts */
blockquote {
    border-left: 3.5px solid #4F46E5;
    background: #F5F7FF;
    margin: 0.6rem 0;
    padding: 0.45rem 0.85rem;
    border-radius: 0 6px 6px 0;
    color: #334155;
    font-size: 8.75pt;
    break-inside: avoid;
}

hr {
    border: none;
    border-top: 1px solid #E2E8F0;
    margin: 1rem 0;
}

.arithmatex {
    display: inline;
}
div.arithmatex {
    display: block;
    text-align: center;
    margin: 0.5rem 0;
}
"""

FULL_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CineMatch Project Report - Sahil (2427010355)</title>

<!-- KaTeX for formula rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>

<style>
{PAGE_CSS}
</style>
</head>
<body>

<!-- Formal Cover Page -->
<div class="cover-page">
    <div class="cover-badge">Academic Project Report</div>
    <div class="cover-title">CINEMATCH</div>
    <div class="cover-tagline">Hybrid AI-Powered Movie Recommender & Discovery Platform</div>
    <div class="cover-subtitle">
        Semantic Natural Language Embeddings, Behavioral Modeling & Emotion-Aware Recommendation
    </div>

    <div class="cover-card">
        <table>
            <tr>
                <td>Candidate Name</td>
                <td><strong style="color:#4338CA; font-size: 10.5pt;">Sahil</strong></td>
            </tr>
            <tr>
                <td>Registration No.</td>
                <td><strong style="font-size: 10.5pt; color: #0F172A;">2427010355</strong></td>
            </tr>
            <tr>
                <td>Degree Program</td>
                <td>Bachelor of Technology (B.Tech / CSE)</td>
            </tr>
            <tr>
                <td>Primary Model</td>
                <td>Sentence-Transformers (<code>all-MiniLM-L6-v2</code>)</td>
            </tr>
            <tr>
                <td>Embedding Space</td>
                <td>384-Dimensional Dense Metric Space ($\mathbb{{R}}^{{384}}$)</td>
            </tr>
            <tr>
                <td>Corpus Scale</td>
                <td>13,157 Curated Motion Pictures (TMDB Dataset)</td>
            </tr>
            <tr>
                <td>Architecture</td>
                <td>Hybrid Tri-Tier (Content, History, Mood)</td>
            </tr>
            <tr>
                <td>Date of Submission</td>
                <td>November 2026</td>
            </tr>
        </table>
    </div>

    <div class="cover-footer">
        <strong>Department of Computer Science & Engineering</strong><br/>
        School of Computing & Information Technologies
    </div>
</div>

<!-- Main Body -->
<div class="report-content">
{html_content}
</div>

<script>
    document.addEventListener("DOMContentLoaded", function() {{
        renderMathInElement(document.body, {{
            delimiters: [
                {{left: "$$", right: "$$", display: true}},
                {{left: "$", right: "$", display: false}},
                {{left: "\\\\(", right: "\\\\)", display: false}},
                {{left: "\\\\[", right: "\\\\]", display: true}}
            ],
            throwOnError: false
        }});
    }});
</script>

</body>
</html>
"""

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(FULL_HTML)

print(f"Generated HTML template at: {HTML_PATH}")

print("Rendering PDF via Google Chrome Headless Engine...")
cmd = [
    CHROME_PATH,
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--virtual-time-budget=8000",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]

res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

if os.path.exists(PDF_PATH) and os.path.getsize(PDF_PATH) > 1000:
    size_mb = os.path.getsize(PDF_PATH) / 1024 / 1024
    print(f"SUCCESS: Generated PDF at {PDF_PATH} ({size_mb:.2f} MB)")
    
    # Inspect every page
    reader = pypdf.PdfReader(PDF_PATH)
    total_pages = len(reader.pages)
    print(f"\n==================================================")
    print(f"PDF PAGE DENSITY ANALYSIS ({total_pages} PAGES)")
    print(f"==================================================")
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        chars = len(text)
        words = len(text.split())
        first_line = (text.strip().splitlines()[0] if text.strip() else 'EMPTY')[:40]
        last_line = (text.strip().splitlines()[-1] if text.strip() else 'EMPTY')[:40]
        print(f"Page {i+1:02d}: {chars:4d} chars | {words:3d} words | Starts: '{first_line}' | Ends: '{last_line}'")
else:
    print(f"FAILED to generate PDF: {res.stderr}")
