"""Offline model readiness checks: no Ollama server or model download needed."""
import json
import urllib.error
from unittest.mock import Mock, patch

from test_agent_permissions import OfflineTestCase, HISTORY, OLLAMA, OWUI, model_response
import agent


class ModelReadinessTests(OfflineTestCase):
    def run_with_show(self, response, *, model="test-model", base=OLLAMA):
        post = self.enterContext(patch.object(
            agent, "_post_json", side_effect=[response, model_response()]
        ))
        get = self.enterContext(patch.object(agent, "_get_json", return_value=[]))
        on_step = Mock()
        result = agent.run_agent(
            model=model, history=HISTORY, kb_ids=["selected"], allow_web=False,
            owui_base=OWUI, ollama_base=base,
            auth_headers={"Authorization": "synthetic-private-token"}, on_step=on_step,
        )
        return result, post, get, on_step

    def assert_denied(self, response, text):
        result, post, get, on_step = self.run_with_show(response)
        self.assertTrue(result["error"])
        self.assertEqual(result["steps"], [
            {"type": "answer", "content": result["answer"], "error": True}
        ])
        self.assertEqual(result["answer"], result["steps"][0]["content"])
        self.assertIn(text, result["answer"])
        post.assert_called_once_with(OLLAMA + "/api/show", {"model": "test-model"},
                                     timeout=agent.TOOL_HTTP_TIMEOUT)
        get.assert_not_called()
        on_step.assert_not_called()

    def test_supporting_model_checked_before_private_library_fetch(self):
        events = []

        def post(url, payload, **kwargs):
            events.append(url)
            if url.endswith("/api/show"):
                self.assertEqual(payload, {"model": "test-model"})
                self.assertEqual(kwargs, {"timeout": agent.TOOL_HTTP_TIMEOUT})
                return {"capabilities": ["completion", "tools"]}
            self.assertIn("messages", payload)
            return model_response()

        def get(url, **kwargs):
            events.append(url)
            return []

        with patch.object(agent, "_post_json", side_effect=post), \
                patch.object(agent, "_get_json", side_effect=get):
            result = agent.run_agent(
                model="test-model", history=HISTORY, kb_ids=["selected"], allow_web=False,
                owui_base=OWUI, ollama_base=OLLAMA, auth_headers={"Authorization": "synthetic"},
            )
        self.assertEqual(result["answer"], "Finished.")
        self.assertNotIn("error", result)
        self.assertEqual(events, [OLLAMA + "/api/show", OWUI + "/api/v1/knowledge/",
                                  OLLAMA + "/api/chat"])

    def test_unsupported_models_denied(self):
        for capabilities in ([], ["completion"], ["embedding"], ["TOOLS"]):
            with self.subTest(capabilities=capabilities):
                self.assert_denied({"capabilities": capabilities}, "does not support tools")

    def test_missing_model_denied(self):
        self.assert_denied(urllib.error.HTTPError(OLLAMA + "/api/show", 404, "missing", {}, None),
                           "was not found")

    def test_other_http_errors_denied(self):
        for status in (401, 500):
            with self.subTest(status=status):
                self.assert_denied(urllib.error.HTTPError(OLLAMA + "/api/show", status, "error", {}, None),
                                   f"HTTP {status}")

    def test_missing_or_malformed_capabilities_denied(self):
        for response in ({}, {"capabilities": None}, {"capabilities": "tools"},
                         {"capabilities": {"tools": True}}, {"capabilities": ["tools", 1]}):
            with self.subTest(response=response):
                self.assert_denied(response, "capabilities are missing or malformed")

    def test_malformed_response_or_error_envelope_denied(self):
        for response in (None, [], "tools", 1, {"error": "missing"},
                         {"error": "failure", "capabilities": ["tools"]}):
            with self.subTest(response=response):
                self.assert_denied(response, "invalid or error response")

    def test_invalid_json_denied(self):
        self.assert_denied(json.JSONDecodeError("bad JSON", "<html>", 0), "invalid JSON")

    def test_unreachable_or_timed_out_denied(self):
        for error in (urllib.error.URLError("connection refused"), TimeoutError("timeout")):
            with self.subTest(error=error):
                self.assert_denied(error, "unreachable or request timed out")

    def test_remote_backed_models_denied_even_with_tools(self):
        for key in ("remote_host", "remote_model"):
            with self.subTest(key=key):
                self.assert_denied({"capabilities": ["tools"], key: "remote-value"},
                                   "locally hosted model")

    def test_invalid_model_name_denied_without_io(self):
        for model in (None, "", "  ", [], {}, 1):
            with self.subTest(model=model):
                result, post, get, on_step = self.run_with_show({}, model=model)
                self.assertTrue(result["error"])
                self.assertIn("select a model name", result["answer"])
                self.assertEqual(result["steps"][0]["type"], "answer")
                self.assertEqual(result["answer"], result["steps"][0]["content"])
                post.assert_not_called()
                get.assert_not_called()
                on_step.assert_not_called()

    def test_trailing_slash_and_empty_remote_metadata_are_supported(self):
        result, post, _, _ = self.run_with_show(
            {"capabilities": ["tools"], "remote_host": "", "remote_model": ""}, base=OLLAMA + "/"
        )
        self.assertEqual(result["answer"], "Finished.")
        self.assertEqual([c.args[0] for c in post.call_args_list],
                         [OLLAMA + "/api/show", OLLAMA + "/api/chat"])
