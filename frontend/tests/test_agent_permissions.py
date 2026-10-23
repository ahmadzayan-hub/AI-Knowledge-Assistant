"""Offline regression tests. Run: python -m unittest discover -s frontend/tests -v"""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import server


OWUI = "http://127.0.0.1:8080"
OLLAMA = "http://127.0.0.1:11434"
HISTORY = [{"role": "user", "content": "Use only my selected library."}]
KB_CACHE = [
    {"id": "other", "files": [
        {"id": "other-file", "meta": {"name": "shared.txt"}},
        {"id": "private-file", "meta": {"name": "other-only.txt"}},
    ]},
    {"id": "selected", "files": [
        {"id": "selected-file", "meta": {"name": "shared.txt"}},
    ]},
]


def tool_call(name, **arguments):
    return {"function": {"name": name, "arguments": arguments}}


def model_response(*calls):
    return {"message": {"role": "assistant", "tool_calls": list(calls),
                        "content": "" if calls else "Finished."}}


class OfflineTestCase(unittest.TestCase):
    def setUp(self):
        # No provider, local service, search engine or socket is contacted.
        self.network = self.enterContext(patch(
            "urllib.request.urlopen", side_effect=AssertionError("Network forbidden in unit tests")
        ))

    def tearDown(self):
        # Helpers catch exceptions, so assert no attempted I/O as well.
        self.network.assert_not_called()


class AgentPermissionsTests(OfflineTestCase):
    def run_calls(self, calls, *, allow_web=False, kb_ids=None, post_responses=None, get_responses=None):
        post = self.enterContext(patch.object(
            agent, "_post_json", side_effect=post_responses or [model_response(*calls), model_response()]
        ))
        get = self.enterContext(patch.object(
            agent, "_get_json", side_effect=get_responses or [KB_CACHE]
        ))
        on_step = Mock()
        result = agent.run_agent(
            model="test-model", history=HISTORY, kb_ids=["selected"] if kb_ids is None else kb_ids,
            allow_web=allow_web, owui_base=OWUI, ollama_base=OLLAMA,
            auth_headers={"X-Test-Header": "synthetic"}, on_step=on_step,
        )
        return result, post, get, on_step

    def test_disabled_web_request_never_invokes_handler_and_reports_denial(self):
        with patch.object(agent, "tool_web_search") as web:
            result, post, _, on_step = self.run_calls([tool_call("web_search", query="sample")])
        web.assert_not_called()
        step = result["steps"][0]
        self.assertTrue(step["blocked"])
        self.assertFalse(step["network"])
        self.assertIn("disabled for this run", step["result"])
        on_step.assert_any_call(step)
        sent = post.call_args_list[1].args[1]
        self.assertIn({"role": "tool", "tool_name": "web_search", "content": step["result"]}, sent["messages"])
        self.assertNotIn("web_search", [t["function"]["name"] for t in sent["tools"]])
        self.assertEqual(result["answer"], "Finished.")

    def test_enabled_web_request_calls_stub_exactly_once(self):
        with patch.object(agent, "tool_web_search", return_value="Synthetic result") as web:
            result, post, _, _ = self.run_calls([tool_call("web_search", query="sample")], allow_web=True)
        web.assert_called_once_with({"query": "sample"})
        self.assertEqual(result["steps"][0]["result"], "Synthetic result")
        self.assertTrue(result["steps"][0]["network"])
        self.assertFalse(result["steps"][0]["blocked"])
        self.assertIn("web_search", [t["function"]["name"] for t in post.call_args.args[1]["tools"]])

    def test_truthy_non_booleans_do_not_grant_direct_call_permission(self):
        for value in ("false", "true", 1, -1, [True], {"enabled": True}, None):
            with self.subTest(value=value), patch.object(agent, "tool_web_search") as web:
                result, _, _, _ = self.run_calls([tool_call("web_search", query="sample")], allow_web=value)
                web.assert_not_called()
                self.assertTrue(result["steps"][0]["blocked"])

    def test_schema_requires_explicit_boolean_true(self):
        for value in (False, None, "false", "true", 0, 1, [], [True], {}):
            with self.subTest(value=value):
                self.assertNotIn("web_search", [t["function"]["name"] for t in agent.build_tools_schema(value)])
        self.assertIn("web_search", [t["function"]["name"] for t in agent.build_tools_schema(True)])

    def test_web_permission_does_not_leak_to_next_run(self):
        with patch.object(agent, "tool_web_search", return_value="Synthetic result") as web:
            self.run_calls([tool_call("web_search", query="sample")], allow_web=True)
            result, _, _, _ = self.run_calls([tool_call("web_search", query="sample")], allow_web=False)
        web.assert_called_once_with({"query": "sample"})
        self.assertTrue(result["steps"][0]["blocked"])

    def test_repeated_disabled_calls_remain_blocked_until_step_limit(self):
        response = model_response(tool_call("web_search", query="sample"))
        with patch.object(agent, "tool_web_search") as web:
            result, post, _, _ = self.run_calls([], post_responses=[response] * agent.MAX_STEPS)
        web.assert_not_called()
        self.assertTrue(result["truncated"])
        self.assertEqual(post.call_count, agent.MAX_STEPS)
        self.assertTrue(all(s["blocked"] for s in result["steps"][:-1]))

    def test_unknown_tool_denied_even_when_web_enabled(self):
        with patch.object(agent, "tool_web_search") as web:
            result, _, _, _ = self.run_calls([tool_call("unregistered_tool")], allow_web=True)
        web.assert_not_called()
        self.assertIn("unknown tool", result["steps"][0]["result"])
        self.assertTrue(result["steps"][0]["blocked"])
        self.assertFalse(result["steps"][0]["network"])

    def test_allowed_local_tool_still_runs_after_denied_call(self):
        result, _, _, _ = self.run_calls([
            tool_call("web_search", query="sample"), tool_call("calculate", expression="6 * 7")
        ])
        self.assertTrue(result["steps"][0]["blocked"])
        self.assertEqual(result["steps"][1]["result"], "42")
        self.assertFalse(result["steps"][1]["blocked"])

    def test_search_uses_selected_kb_not_model_supplied_scope(self):
        requested = tool_call("search_knowledge_base", query="sample", kb_ids=["other"],
                              collection_names=["other"], k=100)
        responses = [model_response(requested),
                     {"documents": [["Synthetic passage"]], "metadatas": [[{"name": "shared.txt"}]]},
                     model_response()]
        result, post, _, _ = self.run_calls([], post_responses=responses)
        self.assertEqual(post.call_args_list[1], call(
            OWUI + "/api/v1/retrieval/query/collection",
            {"collection_names": ["selected"], "query": "sample", "k": 5},
            headers={"X-Test-Header": "synthetic"},
        ))
        self.assertIn("Synthetic passage", result["steps"][0]["result"])
        system = post.call_args_list[0].args[1]["messages"][0]["content"]
        self.assertIn("shared.txt", system)
        self.assertNotIn("other-only.txt", system)

    def test_search_with_no_selection_does_not_query_collection(self):
        result, post, _, _ = self.run_calls([tool_call("search_knowledge_base", query="sample")], kb_ids=[])
        self.assertEqual(post.call_count, 2)
        self.assertTrue(all(c.args[0] == OLLAMA + "/api/chat" for c in post.call_args_list))
        self.assertIn("No knowledge base is selected", result["steps"][0]["result"])

    def test_read_document_cannot_expand_selected_scope(self):
        calls = [tool_call("read_document", filename="other-only.txt", kb_ids=["other"]),
                 tool_call("read_document", filename="shared.txt", kb_ids=["other"])]
        result, _, get, _ = self.run_calls(calls, get_responses=[KB_CACHE, {"content": "Selected content"}])
        self.assertIn("No file matching", result["steps"][0]["result"])
        self.assertIn("Selected content", result["steps"][1]["result"])
        self.assertEqual(get.call_args_list, [
            call(OWUI + "/api/v1/knowledge/", headers={"X-Test-Header": "synthetic"}),
            call(OWUI + "/api/v1/files/selected-file/data/content", headers={"X-Test-Header": "synthetic"}),
        ])


class AgentRequestTests(OfflineTestCase):
    def request(self, payload):
        # Exercise the actual request handler without binding a server/socket.
        body = json.dumps(payload).encode()
        handler = object.__new__(server.Handler)
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler._json = Mock()
        with patch.object(agent, "run_agent", return_value={"answer": "Synthetic answer"}) as run:
            handler._agent_run()
        return handler._json, run

    def test_missing_allow_web_defaults_false(self):
        response, run = self.request({"model": "test-model"})
        self.assertIs(run.call_args.kwargs["allow_web"], False)
        response.assert_called_once_with(200, {"answer": "Synthetic answer"})

    def test_boolean_values_are_preserved(self):
        for value in (False, True):
            with self.subTest(value=value):
                response, run = self.request({"model": "test-model", "allowWeb": value})
                run.assert_called_once()
                self.assertIs(run.call_args.kwargs["allow_web"], value)
                self.assertEqual(response.call_args.args[0], 200)

    def test_non_boolean_allow_web_is_rejected_before_agent_runs(self):
        for value in (None, "false", "true", "", 0, 1, -1, 1.0, [], [True], {}, {"enabled": True}):
            with self.subTest(value=value):
                response, run = self.request({"model": "test-model", "allowWeb": value})
                run.assert_not_called()
                response.assert_called_once_with(400, {"error": "allowWeb must be a boolean"})

    def test_non_object_json_is_rejected_without_running_agent(self):
        for payload in (None, [], "test", 1, True):
            with self.subTest(payload=payload):
                response, run = self.request(payload)
                run.assert_not_called()
                response.assert_called_once_with(400, {"error": "JSON body must be an object"})

    def test_frontend_binding_remains_loopback(self):
        self.assertEqual(server.HOST, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
