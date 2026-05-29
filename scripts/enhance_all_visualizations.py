#!/usr/bin/env python3
"""
Enhance all 207 HTML visualization files with richer content and interactivity.
"""

import os
import re
import json
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

# Content mapping for each file (file number -> {title, subtitle, content, back_link, features})
CONTENT_MAP = {
    # Foundation concepts (0-20)
    "104": {"title": "Programming Paradigms", "subtitle": "Imperative, Functional, OOP, Declarative",
            "back_link": "../data/00-foundations/index.md",
            "content": ["Imperative: Step-by-step instructions", "Functional: Pure functions, immutability",
                       "OOP: Objects, inheritance, polymorphism", "Declarative: What, not how (SQL, React)"],
            "info": "4 major paradigms for solving problems"},
    "105": {"title": "Algorithms & Complexity", "subtitle": "Big O Notation Analysis",
            "back_link": "../data/00-foundations/index.md",
            "content": ["O(1): Constant time", "O(log n): Binary search", "O(n): Linear scan",
                       "O(n²): Nested loops", "O(2ⁿ): Exponential growth"],
            "info": "Analyze algorithm efficiency"},
    "106": {"title": "Data Structures", "subtitle": "Core Collection Types",
            "back_link": "../data/00-foundations/index.md",
            "content": ["Array: Fixed/Dynamic sequences", "Linked List: Nodes with pointers",
                       "Stack: LIFO operations", "Queue: FIFO operations", "Tree: Hierarchical"],
            "info": "Organize and access data efficiently"},
    "107": {"title": "Problem Solving", "subtitle": "Algorithmic Approaches",
            "back_link": "../data/00-foundations/index.md",
            "content": ["Brute Force: Try all solutions", "Divide & Conquer: Break into subproblems",
                       "Dynamic Programming: Optimize overlapping subproblems", "Greedy: Local optimal choice"],
            "info": "Strategic approaches to problem-solving"},

    # AI/ML (20-40)
    "117": {"title": "Machine Learning Basics", "subtitle": "Supervised vs Unsupervised Learning",
            "back_link": "../data/01-ai-ml/index.md",
            "content": ["Supervised: Labeled training data", "Unsupervised: Find patterns in data",
                       "Reinforcement: Learn from rewards", "Semi-supervised: Mix of labeled/unlabeled"],
            "info": "Fundamentals of ML approaches"},
    "120": {"title": "Neural Networks", "subtitle": "Artificial Neural Systems",
            "back_link": "../data/01-ai-ml/index.md",
            "content": ["Input Layer: Feature vectors", "Hidden Layers: Learn representations",
                       "Output Layer: Predictions", "Backpropagation: Weight adjustment"],
            "info": "Mimic biological neural systems"},
    "121": {"title": "Deep Learning", "subtitle": "Multi-layer Neural Networks",
            "back_link": "../data/01-ai-ml/index.md",
            "content": ["Convolutional (CNN): Image processing", "Recurrent (RNN): Sequential data",
                       "Transformer: Attention mechanism", "Autoencoders: Dimensionality reduction"],
            "info": "Advanced neural network architectures"},

    # Data Engineering (40-60)
    "130": {"title": "Data Pipelines", "subtitle": "ETL & ELT Workflows",
            "back_link": "../data/02-data-engineering/index.md",
            "content": ["Extract: Collect from sources", "Transform: Clean and normalize",
                       "Load: Store in data warehouse", "Monitor: Track quality and performance"],
            "info": "Automated data movement and processing"},
    "136": {"title": "Stream Processing", "subtitle": "Real-time Data Handling",
            "back_link": "../data/02-data-engineering/index.md",
            "content": ["Event Streams: Continuous data flow", "Windowing: Time-based aggregation",
                       "Stateful Processing: Context tracking", "Exactly-once Semantics: Reliability"],
            "info": "Process unbounded data streams"},

    # Backend (60-80)
    "143": {"title": "API Design", "subtitle": "Building Service Interfaces",
            "back_link": "../data/03-backend/index.md",
            "content": ["REST: Representational state transfer", "GraphQL: Query language for APIs",
                       "gRPC: High-performance RPC", "Versioning: Backward compatibility"],
            "info": "Design robust and scalable APIs"},
    "144": {"title": "REST Services", "subtitle": "HTTP Resource APIs",
            "back_link": "../data/03-backend/index.md",
            "content": ["GET: Retrieve resources", "POST: Create new resources",
                       "PUT: Full update", "DELETE: Remove resources", "PATCH: Partial update"],
            "info": "HTTP-based architectural style"},

    # Frontend (80-100)
    "156": {"title": "State Management", "subtitle": "Data Flow in Applications",
            "back_link": "../data/04-frontend/index.md",
            "content": ["Local State: Component-level", "Global State: App-wide data",
                       "Redux: Centralized store", "Context API: React built-in solution"],
            "info": "Manage application data efficiently"},
    "158": {"title": "React Hooks", "subtitle": "Functional Component Logic",
            "back_link": "../data/04-frontend/index.md",
            "content": ["useState: State management", "useEffect: Side effects", "useContext: Access context",
                       "useReducer: Complex state logic", "Custom Hooks: Reuse logic"],
            "info": "Modern React composition patterns"},

    # Additional topics (100+)
    "170": {"title": "Testing Fundamentals", "subtitle": "Quality Assurance Strategies",
            "back_link": "../data/19-testing/index.md",
            "content": ["Unit: Test single functions", "Integration: Test component interactions",
                       "E2E: Test full user flows", "Performance: Load and stress testing"],
            "info": "Ensure code quality and reliability"},
    "180": {"title": "DevOps & Automation", "subtitle": "Continuous Integration/Deployment",
            "back_link": "../data/09-devops/index.md",
            "content": ["CI: Automated testing on commit", "CD: Automated deployment",
                       "Infrastructure as Code: Versioned infra", "Monitoring: System observability"],
            "info": "Automate development workflows"},
    "190": {"title": "Cloud Architecture", "subtitle": "Distributed System Design",
            "back_link": "../data/05-cloud/index.md",
            "content": ["Microservices: Decoupled services", "Serverless: Event-driven compute",
                       "Containers: Portable deployment", "Orchestration: Kubernetes"],
            "info": "Design cloud-native applications"},
}

def get_title_from_filename(filename):
    """Extract title from filename."""
    # Remove number prefix and .html
    name = re.sub(r'^[0-9]+-', '', filename)
    name = name.replace('-viz.html', '').replace('-', ' ')
    return name.title()

def get_file_number(filename):
    """Extract number from filename."""
    match = re.match(r'(\d+)-', filename)
    return match.group(1) if match else None

def get_back_link(filename):
    """Guess back link from filename."""
    num = get_file_number(filename)
    if not num:
        return "../data/index.md"

    num_int = int(num)

    # Map ranges to topics
    if num_int < 50:
        return "../data/15-system-design/index.md"
    elif num_int < 100:
        return "../data/13-security/index.md"
    elif num_int < 150:
        return "../data/00-foundations/index.md"
    elif num_int < 200:
        return "../data/02-data-engineering/index.md"
    else:
        return "../data/19-testing/index.md"

def create_enhanced_html(filename, title, back_link):
    """Create enhanced HTML with richer interactivity."""
    num = get_file_number(filename)
    content_info = CONTENT_MAP.get(num, {})

    subtitle = content_info.get("subtitle", f"Interactive Learning")
    content_items = content_info.get("content", [f"Concept from {title}", "Learn and explore"])
    info_text = content_info.get("info", "Interactive visualization for learning")
    back_link = content_info.get("back_link", back_link)

    content_html = "".join([
        f'<div class="item"><div class="item-title">→ {item.split(":")[0]}</div>'
        f'<div class="item-desc">{item.split(":", 1)[-1].strip() if ":" in item else item}</div></div>'
        for item in content_items
    ])

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #e2e8f0;
    }}
    header {{
      background: #1e293b;
      padding: 20px;
      border-bottom: 1px solid #334155;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    h1 {{ font-size: 24px; font-weight: 600; }}
    h2 {{ font-size: 18px; margin: 20px 0 15px 0; color: #cbd5e1; }}
    .back-link {{
      color: #60a5fa;
      text-decoration: none;
      font-size: 14px;
      padding: 8px 12px;
      border: 1px solid #334155;
      border-radius: 4px;
      transition: all 0.2s;
    }}
    .back-link:hover {{ background: #334155; }}
    .container {{ display: flex; height: calc(100vh - 60px); }}
    #canvas {{
      flex: 1;
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
      overflow-y: auto;
      padding: 20px;
    }}
    .controls {{
      width: 320px;
      background: #1e293b;
      border-left: 1px solid #334155;
      padding: 20px;
      overflow-y: auto;
    }}
    .control-group {{ margin-bottom: 20px; }}
    .control-group label {{
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      color: #94a3b8;
      margin-bottom: 8px;
      font-weight: 600;
    }}
    button {{
      background: #3b82f6;
      color: white;
      border: none;
      padding: 10px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 14px;
      width: 100%;
      margin-bottom: 8px;
      transition: all 0.2s;
    }}
    button:hover {{ background: #2563eb; }}
    .status {{
      background: #334155;
      padding: 12px;
      border-radius: 6px;
      font-size: 12px;
      font-family: monospace;
      margin: 10px 0;
      border-left: 3px solid #60a5fa;
    }}
    .status > div {{ margin: 4px 0; }}
    .info-text {{
      font-size: 12px;
      color: #cbd5e1;
      line-height: 1.6;
      margin: 12px 0;
    }}
    .content-box {{
      background: #334155;
      padding: 15px;
      border-radius: 8px;
      margin: 15px 0;
    }}
    .item {{
      padding: 12px;
      background: #1e293b;
      border-left: 3px solid #60a5fa;
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.5;
      margin-bottom: 8px;
      transition: all 0.2s;
    }}
    .item:hover {{ background: #334155; border-left-color: #3b82f6; }}
    .item.active {{ border-left-color: #10b981; background: rgba(16, 185, 129, 0.1); }}
    .item-title {{ font-weight: 600; color: #e2e8f0; margin-bottom: 4px; }}
    .item-desc {{ font-size: 12px; color: #cbd5e1; }}
  </style>
</head>
<body>
  <header>
    <h1>🎨 {title}</h1>
    <a href="{back_link}" class="back-link">← Back to Notes</a>
  </header>

  <div class="container">
    <div id="canvas">
      <h2>{subtitle}</h2>
      <div id="content-main" class="content-box">
        <div style="color:#94a3b8;text-align:center;padding:40px;">Click "Load" to view content</div>
      </div>
    </div>

    <div class="controls">
      <div class="control-group">
        <label>Controls</label>
        <button onclick="app.load()">Load Content</button>
        <button onclick="app.nextStep()">Next Step</button>
        <button onclick="app.reset()">Reset</button>
      </div>

      <div class="status">
        <div>Status: <strong id="status">Ready</strong></div>
        <div>Progress: <strong id="progress">0%</strong></div>
      </div>

      <div class="control-group">
        <label>Info</label>
        <div class="info-text">{info_text}</div>
      </div>
    </div>
  </div>

  <script>
    const app = {{
      state: {{ loaded: false, step: 0 }},
      content: {json.dumps(content_items)},

      init() {{ this.render(); }},

      load() {{
        this.state.loaded = true;
        this.state.step = 0;
        this.render();
      }},

      nextStep() {{
        if (this.state.loaded) {{
          this.state.step = (this.state.step + 1) % this.content.length;
          this.render();
        }}
      }},

      reset() {{
        this.state = {{ loaded: false, step: 0 }};
        this.render();
      }},

      render() {{
        const container = document.getElementById('content-main');
        const status = document.getElementById('status');
        const progress = document.getElementById('progress');

        if (this.state.loaded) {{
          const items = this.content.map((item, idx) => `
            <div class="item ${{idx === this.state.step ? 'active' : ''}}">
              <div class="item-title">${{idx === this.state.step ? '→' : '•'}} ${{item.split(':')[0]}}</div>
              <div class="item-desc">${{item.split(':').length > 1 ? item.split(':')[1].trim() : item}}</div>
            </div>
          `).join('');

          container.innerHTML = `<div class="item-list">${{items}}</div>`;
          status.textContent = '✓ Active';
          progress.textContent = `${{Math.round((this.state.step + 1) / this.content.length * 100)}}%`;
        }} else {{
          container.innerHTML = '<div style="color:#94a3b8;text-align:center;padding:40px;">Click "Load" to view content</div>';
          status.textContent = 'Ready';
          progress.textContent = '0%';
        }}
      }}
    }};

    window.addEventListener('load', () => app.init());
  </script>
</body>
</html>'''
    return html

def enhance_all_files():
    """Process all HTML files and enhance them."""
    files = sorted([f for f in os.listdir(HTML_DIR) if f.endswith('.html') and not f.startswith('.')])

    processed = 0
    skipped = 0

    for filename in files:
        filepath = HTML_DIR / filename
        num = get_file_number(filename)
        title = get_title_from_filename(filename)
        back_link = get_back_link(filename)

        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Skip if already enhanced (has "nextStep" method)
            if 'nextStep' in content:
                skipped += 1
                continue

            # Generate new HTML
            new_html = create_enhanced_html(filename, title, back_link)

            # Write back
            with open(filepath, 'w') as f:
                f.write(new_html)

            processed += 1
            if processed % 10 == 0:
                print(f"Enhanced {processed} files...")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\n✓ Enhanced {processed} files, skipped {skipped} already-enhanced files")
    return processed

if __name__ == '__main__':
    enhance_all_files()
