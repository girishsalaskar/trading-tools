  Trading Tools body { font-family: Arial, sans-serif; margin: 2em; } h1 { color: #2c3e50; } .tool-list { margin-bottom: 2em; } .tool-item { margin-bottom: 1em; } .readme { background: #f9f9f9; border: 1px solid #ddd; padding: 1em; margin-top: 0.5em; } a { color: #2980b9; text-decoration: none; } a:hover { text-decoration: underline; }

# Trading Tools

## Available Tools

[chartink-backtest](../chartink-backtest/chartink-backtest.py)  
[Show README](#)

_Guidance: Click 'Show README' to view guidance for chartink-backtest._

© 2025 Trading Tools

// Utility to convert markdown to HTML (basic) function markdownToHtml(md) { // Simple replacements for headings, bold, italics, code, lists return md .replace(/^# (.\*$)/gim, '<h2>$1</h2>') .replace(/^## (.\*$)/gim, '<h3>$1</h3>') .replace(/^### (.\*$)/gim, '<h4>$1</h4>') .replace(/\\\*\\\*(.\*?)\\\*\\\*/gim, '<b>$1</b>') .replace(/\\\*(.\*?)\\\*/gim, '<i>$1</i>') .replace(/\`(\[^\`\]+)\`/gim, '<code>$1</code>') .replace(/^\\s\*\[-\*\] (.\*$)/gim, '<li>$1</li>') .replace(/\\n\\n/gim, '<br><br>'); } // Handle README link clicks const readmeLinks = document.querySelectorAll('.readme-link'); readmeLinks.forEach(link => { link.addEventListener('click', function(e) { e.preventDefault(); const readmePath = this.getAttribute('data-readme'); const readmeDiv = this.parentElement.querySelector('.readme'); fetch(readmePath) .then(response => response.text()) .then(md => { readmeDiv.innerHTML = markdownToHtml(md); }) .catch(() => { readmeDiv.innerHTML = '<em>Could not load README.md</em>'; }); }); });