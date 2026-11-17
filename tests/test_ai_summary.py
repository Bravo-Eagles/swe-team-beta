import json
import os
import unittest
from unittest.mock import patch

from src.ai_request import AIRequest
from src.ai_summary import summarize_responses


class AiSummaryTests(unittest.TestCase):
    def setUp(self):
        self.responses = [{"question": "What did you learn?", "answer": " Recursion ",
                           "name": "Private Name", "student_id": 99}]

    @patch("src.ai_summary.AIRequest")
    def test_sends_only_question_and_answer(self, factory):
        factory.return_value.send.return_value.json.return_value = {"output_text": " Summary "}
        self.assertEqual(summarize_responses(self.responses, api_key="test-key"), "Summary")
        client = factory.return_value
        payload = json.loads(client.send.call_args.args[0])
        self.assertEqual(payload, {"response_count": 1, "responses": [
            {"question": "What did you learn?", "answer": "Recursion"}]})
        self.assertIn("untrusted data", client.send.call_args.kwargs["instructions"])

    @patch("src.ai_summary.AIRequest")
    def test_no_network_for_empty_responses_or_missing_key(self, factory):
        with self.assertRaisesRegex(ValueError, "No responses"):
            summarize_responses([], api_key="key")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "AI_API_KEY"):
                summarize_responses(self.responses)
        factory.assert_not_called()

    @patch("src.ai_summary.AIRequest")
    def test_reads_nested_responses_api_output(self, factory):
        factory.return_value.send.return_value.json.return_value = {
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": "Learning themes"}]}]}
        self.assertEqual(summarize_responses(self.responses, api_key="key"), "Learning themes")

    @patch("src.ai_summary.AIRequest")
    def test_empty_output_is_not_a_success(self, factory):
        factory.return_value.send.return_value.json.return_value = {"output": []}
        with self.assertRaisesRegex(ValueError, "empty summary"):
            summarize_responses(self.responses, api_key="key")

    @patch("src.ai_summary.AIRequest")
    def test_malformed_output_is_reported_as_an_error(self, factory):
        for output in [None, [], {"output": None}, {"output": [None, {"content": None}]}]:
            factory.return_value.send.return_value.json.return_value = output
            with self.assertRaises(ValueError):
                summarize_responses(self.responses, api_key="key")

    @patch("src.ai_request.requests.post")
    @patch("src.ai_request.requests.get")
    def test_models_without_custom_metadata_are_supported(self, get, post):
        get.return_value.json.return_value = {"data": [{"id": "test-model"}]}
        client = AIRequest("key")
        client.send("answers", instructions="summarize")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["instructions"], "summarize")
        self.assertFalse(payload["store"])
