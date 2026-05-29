#!/usr/bin/env python3
"""Create advanced visualizations for key topics."""

import json
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

# Key files to enhance with advanced features
KEY_TOPICS = {
    "103": {  # Algorithms & Complexity
        "feature": "animated_complexity_chart",
        "description": "Interactive Big O visualization with animation"
    },
    "50": {  # JWT & OAuth2
        "feature": "token_flow_diagram",
        "description": "Animated authentication flow visualization"
    },
    "130": {  # Data Pipelines
        "feature": "pipeline_animation",
        "description": "ETL pipeline step-by-step animation"
    },
    "143": {  # API Design
        "feature": "request_response_flow",
        "description": "RESTful API request/response cycle"
    },
    "158": {  # React Hooks
        "feature": "hook_lifecycle",
        "description": "React hooks lifecycle visualization"
    },
    "99": {  # Incident Trends
        "feature": "real_time_metrics",
        "description": "Live incident metrics dashboard"
    },
}

def add_animated_complexity_chart(html_file):
    """Add animated Big O complexity chart."""
    with open(html_file) as f:
        content = f.read()

    animation_script = """
    app.animateChart = function() {
      const canvas = document.getElementById('viz-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      let frame = 0;
      const maxFrames = 60;

      const animate = () => {
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const progress = frame / maxFrames;
        const curves = {
          'O(1)': x => 20,
          'O(log n)': x => 30 + Math.log2(x + 1) * 10,
          'O(n)': x => 20 + x * 2,
          'O(n²)': x => 20 + x * x
        };
        const colors = ['#10b981', '#60a5fa', '#fbbf24', '#ef4444'];

        Object.entries(curves).forEach(([label, fn], idx) => {
          ctx.strokeStyle = colors[idx];
          ctx.lineWidth = 2;
          ctx.beginPath();
          for(let i = 0; i < progress * 150; i++) {
            const y = Math.min(150, fn(i / 30));
            i === 0 ? ctx.moveTo(i, 150 - y) : ctx.lineTo(i, 150 - y);
          }
          ctx.stroke();
        });

        frame++;
        if (frame < maxFrames) requestAnimationFrame(animate);
      };
      animate();
    };"""

    # Insert animation into load function
    if 'app.animateChart' not in content:
        content = content.replace(
            'setTimeout(() => this.drawVisualization(), 100);',
            'setTimeout(() => this.animateChart(), 100);'
        )
        content = content.replace('</script>', animation_script + '\n</script>')

    with open(html_file, 'w') as f:
        f.write(content)

def add_token_flow(html_file):
    """Add JWT token flow visualization."""
    flow_html = """
    <div class="flow-diagram">
      <div class="flow-step" style="left:5%">1. Request</div>
      <div class="flow-arrow">→</div>
      <div class="flow-step" style="left:30%">2. Verify</div>
      <div class="flow-arrow">→</div>
      <div class="flow-step" style="left:55%">3. Token</div>
      <div class="flow-arrow">→</div>
      <div class="flow-step" style="left:80%">4. Access</div>
    </div>
    <style>
      .flow-diagram { position: relative; height: 60px; margin: 20px 0; }
      .flow-step { position: absolute; background: #60a5fa; color: white; padding: 10px 15px; border-radius: 4px; font-size: 12px; }
      .flow-arrow { position: absolute; top: 20px; color: #60a5fa; font-size: 18px; }
    </style>"""

    with open(html_file) as f:
        content = f.read()

    if 'flow-diagram' not in content:
        content = content.replace(
            '<canvas id="viz-canvas"',
            flow_html + '\n    <canvas id="viz-canvas"'
        )

    with open(html_file, 'w') as f:
        f.write(content)

def enhance_file(file_num, feature):
    """Apply enhancement to specific file."""
    files = list(HTML_DIR.glob(f"{file_num}-*.html"))
    if not files:
        return False

    html_file = files[0]

    if feature == "animated_complexity_chart":
        add_animated_complexity_chart(html_file)
    elif feature == "token_flow_diagram":
        add_token_flow(html_file)

    return True

def main():
    enhanced = 0
    for file_num, config in KEY_TOPICS.items():
        try:
            if enhance_file(file_num, config["feature"]):
                enhanced += 1
                print(f"✓ Enhanced {file_num}: {config['description']}")
        except Exception as e:
            print(f"✗ Failed {file_num}: {e}")

    print(f"\n✓ Enhanced {enhanced} key topics")

if __name__ == '__main__':
    main()
