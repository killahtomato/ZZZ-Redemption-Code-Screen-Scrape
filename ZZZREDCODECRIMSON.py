# ZZZ redemption codes for funzies
import sys
import re
from playwright.sync_api import sync_playwright
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextBrowser
)
from PyQt5.QtGui import QFont, QGuiApplication

# ---------- SOURCE ----------
SOURCE = "https://www.crimsonwitch.com/codes/Zenless_Zone_Zero"

CODE_PATTERN = re.compile(r"\b[A-Z0-9]{5,20}\b")

HARD_EXCLUDES = {
    "CODES","REDEEM","REDEMPTION","HOYOVERSE","HOYOLAB",
    "POLYCHROME","UPDATED","VERSION","EVENT","STREAM","LOGIN"
}

REWARD_WORDS = {"POLY", "POLYCHROME", "DENNY", "DENNIES", "LOG", "MODULE", "REWARD"}

# ---------- CRIMSONWITCH PARSER ----------
def extract_crimsonwitch(url):
    active = []
    expired = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        headers = page.query_selector_all("h2, h3")

        for header in headers:
            title = header.inner_text().lower()

            is_expired_section = "expired" in title
            is_active_section = (
                "new codes" in title or "active codes" in title
            )

            if not (is_active_section or is_expired_section):
                continue

            section_text = ""
            sibling = header.evaluate_handle("el => el.nextElementSibling")

            while sibling:
                try:
                    tag_name = sibling.evaluate("el => el.tagName.toLowerCase()")
                except:
                    break

                if tag_name in ["h2", "h3"]:
                    break

                try:
                    section_text += sibling.inner_text() + "\n"
                except:
                    pass

                sibling = sibling.evaluate_handle("el => el.nextElementSibling")

            lines = section_text.split("\n")

            for line in lines:
                clean_line = line.strip().upper()

                if not clean_line:
                    continue

                # ❌ Skip reward lines
                if any(word in clean_line for word in REWARD_WORDS):
                    continue

                # ❌ Skip lines with spaces (likely descriptions)
                if " " in clean_line:
                    continue

                # ✅ Only accept full-line codes
                if CODE_PATTERN.fullmatch(clean_line):
                    token = clean_line

                    if token in HARD_EXCLUDES:
                        continue

                    if is_expired_section:
                        expired.append((token, [url]))
                    else:
                        active.append((token, [url]))

        browser.close()

    # Remove duplicates
    active = list({c[0]: c for c in active}.values())
    expired = list({c[0]: c for c in expired}.values())

    return active, expired

# ---------- SCRAPER ----------
def scrape_all():
    active, expired = extract_crimsonwitch(SOURCE)
    return active, [], expired  # keeping UI structure intact

# ---------- UI ----------
class ZZZWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍅 Tomato Code Harvester")
        self.setGeometry(100,100,880,680)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget { background-color: #1c1b1a; color: #f5e6d3; }
            QPushButton {
                background-color: #ff6b4a;
                color: black;
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #ff8a65; }
        """)

        self.status = QLabel("😊 Ready to hunt some codes!")
        layout.addWidget(self.status)

        self.fetch_btn = QPushButton("🔎 Find Codes")
        self.fetch_btn.clicked.connect(self.fetch_codes)
        layout.addWidget(self.fetch_btn)

        self.text = QTextBrowser()
        self.text.setFont(QFont("Consolas", 10))
        self.text.setOpenExternalLinks(False)
        layout.addWidget(self.text)

        self.text.anchorClicked.connect(self.copy_code)

    def copy_code(self, url):
        code = url.toString()
        QGuiApplication.clipboard().setText(code)
        self.status.setText(f"📋 Copied {code}!")

    def add_section(self, title, color):
        self.text.insertHtml(f"<h3 style='color:{color}'>{title}</h3><hr>")

    def add_code(self, code, sources, color):
        html = f"<b style='color:{color}'>{code}</b> <a href='{code}'>📋</a><br>"
        for s in sources:
            html += f"<span style='color:#aaa'>↳ {s}</span><br>"
        html += "<br>"
        self.text.insertHtml(html)

    def fetch_codes(self):
        self.status.setText("🔎 Hunting codes from CrimsonWitch...")
        QApplication.processEvents()

        active, others, expired = scrape_all()

        self.text.clear()

        self.add_section("🟢 Live Codes", "#7CFC9F")
        for c in active:
            self.add_code(*c, "#7CFC9F")

        self.add_section("🟡 Possibly Working", "#FFD166")
        for c in others:
            self.add_code(*c, "#FFD166")

        self.add_section("🔴 Expired", "#FF6B6B")
        for c in expired:
            self.add_code(*c, "#FF6B6B")

        self.status.setText(
            f"🎉 Done! {len(active)} live, {len(expired)} expired."
        )

# ---------- RUN ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ZZZWindow()
    win.show()
    sys.exit(app.exec_())
