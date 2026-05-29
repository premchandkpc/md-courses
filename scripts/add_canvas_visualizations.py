#!/usr/bin/env python3
"""Add canvas-based visualizations to HTML files."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

# Canvas visualizations per topic range
CANVAS_TEMPLATES = {
    "default": """
    <canvas id="viz-canvas" width="600" height="300"></canvas>
    <script>
      const canvas = document.getElementById('viz-canvas');
      if (canvas) {
        const ctx = canvas.getContext('2d');
        app.drawVisualization = function() {
          ctx.fillStyle = '#334155';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.fillStyle = '#60a5fa';
          ctx.font = '14px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('Topic Visualization', canvas.width/2, canvas.height/2);
        };
      }
    </script>""",

    "growth": """
    <canvas id="viz-canvas" width="600" height="250"></canvas>
    <script>
      const canvas = document.getElementById('viz-canvas');
      if (canvas) {
        const ctx = canvas.getContext('2d');
        app.drawVisualization = function() {
          ctx.fillStyle = '#1e293b';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.strokeStyle = '#60a5fa';
          ctx.lineWidth = 2;
          ctx.beginPath();
          const data = [10, 15, 22, 30, 40, 52, 65];
          const step = canvas.width / (data.length - 1);
          data.forEach((v, i) => {
            const x = i * step;
            const y = canvas.height - (v / 100) * canvas.height;
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
          });
          ctx.stroke();
        };
      }
    </script>""",

    "comparison": """
    <canvas id="viz-canvas" width="600" height="250"></canvas>
    <script>
      const canvas = document.getElementById('viz-canvas');
      if (canvas) {
        const ctx = canvas.getContext('2d');
        app.drawVisualization = function() {
          ctx.fillStyle = '#1e293b';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          const colors = ['#60a5fa', '#10b981', '#fbbf24'];
          const data = [65, 75, 55];
          const barWidth = 80;
          data.forEach((v, i) => {
            ctx.fillStyle = colors[i];
            const x = 100 + i * 140;
            const h = (v / 100) * 150;
            ctx.fillRect(x, canvas.height - h - 30, barWidth, h);
          });
        };
      }
    </script>""",
}

def add_canvas_to_file(html_file):
    """Add canvas visualization to HTML file."""
    with open(html_file) as f:
        content = f.read()

    # Skip if already has canvas
    if '<canvas' in content:
        return False

    # Get file number
    match = re.match(r'(\d+)-', html_file.name)
    if not match:
        return False

    file_num = int(match.group(1))

    # Choose template based on file number
    if file_num < 50:
        template = CANVAS_TEMPLATES["comparison"]
    elif file_num < 100:
        template = CANVAS_TEMPLATES["growth"]
    else:
        template = CANVAS_TEMPLATES["default"]

    # Insert canvas before </div> of #canvas section
    canvas_html = f"      {template}\n    </div>"
    content = re.sub(r'      </div>\s*</div>\s*<div class="controls"', canvas_html + "\n    <div class=\"controls\"", content)

    # Add drawVisualization call to load function
    if 'app.drawVisualization' in content:
        content = re.sub(
            r'this\.state\.loaded = true;',
            'this.state.loaded = true;\n        setTimeout(() => this.drawVisualization(), 100);',
            content
        )

    with open(html_file, 'w') as f:
        f.write(content)

    return True

def main():
    enhanced = 0
    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        if add_canvas_to_file(html_file):
            enhanced += 1
            if enhanced % 20 == 0:
                print(f"Added canvas to {enhanced} files...")

    print(f"\n✓ Added canvas visualizations to {enhanced} files")

if __name__ == '__main__':
    main()
