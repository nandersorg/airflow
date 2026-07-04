import os
import sys
import unittest
from unittest.mock import patch

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.sentiment import analyze_sentiment, get_rss_url


class FakeResponse:
    def __init__(self, payload, status_raises: Exception | None = None):
        self._payload = payload
        self._status_raises = status_raises

    def raise_for_status(self):
        if self._status_raises:
            raise self._status_raises
        return None

    def json(self):
        return self._payload


class SentimentTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_analyze_sentiment_returns_positive_label(self):
        with patch(
            "src.sentiment.requests.post",
            return_value=FakeResponse({"message": {"content": "POSITIVE"}}),
        ):
            self.assertEqual(analyze_sentiment("Titel"), "POSITIVE")

    @patch.dict(
        os.environ,
        {
            "OLLAMA_MAX_RETRIES": "2",
            "OLLAMA_RETRY_BACKOFF_SECONDS": "0.01",
        },
        clear=True,
    )
    def test_retries_after_transient_connection_error(self):
        side_effects = [
            requests.ConnectionError("connection dropped"),
            FakeResponse({"message": {"content": "NEUTRAL"}}),
        ]

        with patch("src.sentiment.requests.post", side_effect=side_effects):
            with patch("src.sentiment.time.sleep") as sleep_mock:
                self.assertEqual(analyze_sentiment("Titel"), "NEUTRAL")
                sleep_mock.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "OLLAMA_MAX_RETRIES": "2",
            "OLLAMA_RETRY_BACKOFF_SECONDS": "0.01",
        },
        clear=True,
    )
    def test_returns_none_after_retry_exhaustion(self):
        with patch(
            "src.sentiment.requests.post",
            side_effect=requests.ConnectionError("still down"),
        ):
            with patch("src.sentiment.time.sleep"):
                self.assertIsNone(analyze_sentiment("Titel"))

    @patch.dict(os.environ, {}, clear=True)
    def test_supports_legacy_response_field(self):
        with patch(
            "src.sentiment.requests.post",
            return_value=FakeResponse({"response": "NEGATIVE"}),
        ):
            self.assertEqual(analyze_sentiment("Titel"), "NEGATIVE")

    def test_get_rss_url_falls_back_to_voorpagina(self):
        self.assertEqual(
            get_rss_url("ONBEKEND"),
            "https://feeds.nos.nl/nosnieuwsalgemeen",
        )


if __name__ == "__main__":
    unittest.main()
