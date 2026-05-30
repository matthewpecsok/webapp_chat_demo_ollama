import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .views import PRODUCTS


class StorefrontTests(TestCase):
    def test_index_lists_seed_products(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        for product in PRODUCTS:
            self.assertContains(response, product["title"])
            self.assertContains(response, product["price"])

    def test_chat_requires_message(self):
        response = self.client.post(
            reverse("chat"),
            data=json.dumps({"message": ""}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Message is required.")

    @override_settings(
        OLLAMA_BASE_URL="http://ollama.test",
        OLLAMA_MODEL="test-model",
        OLLAMA_TIMEOUT=5,
    )
    @patch("storefront.views.urlopen")
    def test_chat_calls_ollama_api_with_product_catalog(self, mock_urlopen):
        ollama_response = mock_urlopen.return_value.__enter__.return_value
        ollama_response.read.return_value = json.dumps(
            {"message": {"content": "Try the Harbor Quilted Crop Jacket for $118."}}
        ).encode("utf-8")

        response = self.client.post(
            reverse("chat"),
            data=json.dumps({"message": "I need a light jacket."}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["reply"],
            "Try the Harbor Quilted Crop Jacket for $118.",
        )

        request = mock_urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "http://ollama.test/api/chat")
        self.assertEqual(body["model"], "test-model")
        self.assertFalse(body["stream"])
        self.assertIn(PRODUCTS[0]["title"], body["messages"][0]["content"])
        self.assertIn(PRODUCTS[0]["price"], body["messages"][0]["content"])
        self.assertIn(PRODUCTS[0]["description"], body["messages"][0]["content"])
