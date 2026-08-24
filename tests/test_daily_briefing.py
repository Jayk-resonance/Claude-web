import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daily_briefing"))

import run
from gmail_sender import build_mime_message
from send_email import build_email


def sample_data():
    first_article = {
        "title": "Battery <script>alert(1)</script>",
        "url": "https://example.com/article-0?a=1&b=2",
        "publishedAt": "2026-08-24T08:00:00+09:00",
        "category": "EV 배터리 기술/산업",
        "summary": "첫 줄\n둘째 줄",
        "impact_score": 8,
    }
    articles = [first_article]
    for index in range(1, 8):
        articles.append(
            {
                "title": f"Battery article {index}",
                "url": f"https://example.com/article-{index}",
                "publishedAt": "2026-08-24T08:00:00+09:00",
                "category": "EV 배터리 기술/산업",
                "summary": "요약",
                "impact_score": 7,
            }
        )
    return {
        "date_str": "2026-08-24",
        "articles": articles,
        "insight": (
            "## 배경\n**확인된 사실** <img src=x onerror=alert(1)>\n"
            "## 핵심 내용\n핵심\n"
            "## 산업 영향\n영향\n"
            "## SK온 관점에서의 시사점\n시사점"
        ),
    }


class DailyBriefingTests(unittest.TestCase):
    def test_renderer_escapes_external_html(self):
        data = sample_data()
        email = build_email(
            data["articles"], data["insight"], data["articles"][0], data["date_str"]
        )
        self.assertIn("&lt;script&gt;", email["htmlBody"])
        self.assertIn("&lt;img", email["htmlBody"])
        self.assertIn("<strong>확인된 사실</strong>", email["htmlBody"])
        self.assertNotIn("<script>", email["htmlBody"])
        self.assertIn("Battery <script>alert(1)</script>", email["textBody"])

    def test_mime_message_is_multipart_alternative(self):
        data = sample_data()
        email = build_email(
            data["articles"], data["insight"], data["articles"][0], data["date_str"]
        )
        message = build_mime_message(
            email["to"], email["subject"], email["textBody"], email["htmlBody"]
        )
        self.assertEqual("multipart/alternative", message.get_content_type())
        self.assertEqual(
            ["text/plain", "text/html"],
            [part.get_content_type() for part in message.get_payload()],
        )

    def test_main_renders_only_to_approved_recipient(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            input_path.write_text(json.dumps(sample_data(), ensure_ascii=False), encoding="utf-8")

            run.main([
                "--input", str(input_path),
                "--output", str(output_path),
                "--to", "jupiter@sk.com",
            ])

            email = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(["jupiter@sk.com"], email["to"])

    def test_rejects_unapproved_recipient(self):
        with self.assertRaisesRegex(ValueError, "허용된 수신자"):
            run.main(["--input", "unused.json", "--to", "someone@example.com"])

    def test_rejects_unsafe_url(self):
        data = sample_data()
        data["articles"][0]["url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "http/https"):
            run.validate_input(data)

    def test_rejects_blocklisted_source(self):
        data = sample_data()
        data["articles"][0]["url"] = "https://evcube.net/article"
        with self.assertRaisesRegex(ValueError, "차단된 출처"):
            run.validate_input(data)

    def test_rejects_fewer_than_eight_articles(self):
        data = sample_data()
        data["articles"] = data["articles"][:7]
        with self.assertRaisesRegex(ValueError, "8건 이상"):
            run.validate_input(data)


if __name__ == "__main__":
    unittest.main()
