# Purpose: Installer for sin-doc-coauthoring
# Docs: install.sh.doc.md
#!/usr/bin/env bash
set -euo pipefail

echo "╔══════════════════════════════════════════════════╗"
echo "║  SIN-Code Doc Coauthoring Skill — Installer     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Install: brew install python"
    exit 1
fi
echo "✅ python3 found: $(python3 --version)"

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi
echo "✅ venv ready: .venv"

# Install
echo "📦 Installing package..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null
pip install -e ".[dev,pdf]"

# Verify
echo "✅ Verifying install..."
python3 -c "import sin_doc_coauthoring; print(f'  sin-doc-coauthoring {sin_doc_coauthoring.__version__}')"
sin-doc --version

# Optional: copy bash scripts to ~/.local/bin
if [ -d "$HOME/.local/bin" ]; then
    echo "📂 Installing bash scripts to ~/.local/bin/ ..."
    cp scripts/*.sh "$HOME/.local/bin/"
    chmod +x "$HOME/.local/bin/"doc-*.sh
    echo "  ✅ Installed: doc-start.sh, doc-outline.sh, doc-draft.sh,"
    echo "              doc-review.sh, doc-render.sh, doc-export.sh"
fi

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅  Installation complete!                       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Quick start:"
echo "  sin-doc start --type README --title \"My Project\""
echo "  sin-doc outline --session <id>"
echo "  sin-doc draft --session <id> --section \"Installation\""
echo "  sin-doc review --session <id>"
echo "  sin-doc export --session <id> --destination ./README.md"
echo ""
echo "MCP server:"
echo "  python3 -m sin_doc_coauthoring.mcp_server"
echo ""
echo "Or add to opencode.json:"
echo "  \"mcp\": { \"sin-doc-coauthoring\": {"
echo "    \"type\": \"stdio\","
echo "    \"command\": \"python3\","
echo "    \"args\": [\"-m\", \"sin_doc_coauthoring.mcp_server\"]"
echo "  }}"
