"""HawkPhish - Template Engine"""
import re
import html as html_module
from typing import Dict
from datetime import datetime


class TemplateEngine:
    DEFAULT_VARIABLES = {
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "position": "Employee",
        "domain": "example.com",
        "date": "January 01, 2024",
        "link": "http://localhost:8000/track/abc123",
        "tracking_id": "abc123",
    }

    def render(self, subject: str, html_body: str, text_body: str, variables: dict,
               disclaimer: bool = False, scenario_name: str = "Custom", severity: str = "N/A") -> dict:
        merged = {**self.DEFAULT_VARIABLES, **variables}

        rendered_subject = self._replace_vars(subject, merged)
        rendered_html = self._replace_vars(html_body, merged)
        rendered_text = self._replace_vars(text_body, merged)

        # Auto-generate text from HTML if not provided
        if not rendered_text.strip() and rendered_html.strip():
            rendered_text = self._strip_html(rendered_html)

        # Add disclaimer if enabled
        if disclaimer:
            rendered_html += self._disclaimer_html(scenario_name, severity)
            rendered_text += self._disclaimer_text(scenario_name, severity)

        return {
            "subject": rendered_subject,
            "html_body": rendered_html,
            "text_body": rendered_text,
        }

    def _replace_vars(self, text: str, variables: dict) -> str:
        if not text:
            return ""
        for key, value in variables.items():
            text = text.replace(f"##{key}##", str(value))
        return text

    def _strip_html(self, html_body: str) -> str:
        text = re.sub(r"<\s*br\s*/?>", "\n", html_body, flags=re.IGNORECASE)
        text = re.sub(r"<\s*/p\s*>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return html_module.unescape(text)

    def _disclaimer_text(self, scenario_name: str, severity: str) -> str:
        return (
            f"\n{'─' * 64}\n"
            "This email was sent using HawkPhish for authorized security testing.\n"
            "If you received this unexpectedly, contact your IT security team.\n\n"
            f"Test Details:\n"
            f"  Scenario : {scenario_name}\n"
            f"  Severity : {severity}\n"
            f"  Timestamp: {datetime.utcnow().isoformat()}\n\n"
            f"HawkPhish v1.2.0 — Advanced Phishing Simulation Platform\n"
            f"{'─' * 64}"
        )

    def _disclaimer_html(self, scenario_name: str, severity: str) -> str:
        return (
            "<hr style='margin:18px 0; border:0; border-top:1px solid #e5e7eb;'>"
            "<p style='font-size:12px; color:#6b7280; line-height:1.6;'>"
            "This email was sent using <strong>HawkPhish</strong> for authorized security testing.<br>"
            "If you received this unexpectedly, contact your IT security team.<br><br>"
            f"Scenario: {html_module.escape(scenario_name)}<br>"
            f"Severity: {html_module.escape(severity)}<br>"
            f"Timestamp: {datetime.utcnow().isoformat()}<br><br>"
            "HawkPhish v1.2.0 — Advanced Phishing Simulation Platform"
            "</p>"
        )

    def extract_variables(self, text: str) -> list:
        return list(set(re.findall(r'##(\w+)##', text or "")))

    def preview(self, subject: str, html_body: str, text_body: str) -> dict:
        return self.render(subject, html_body, text_body, self.DEFAULT_VARIABLES)
