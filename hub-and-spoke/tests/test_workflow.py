import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import initial, advance
from workflow import build_graph
from test_system import FakeModel, BAD, GOOD


class GraphWorkflowTests(unittest.TestCase):
    def test_framework_runs_and_records_real_node_paths(self):
        model = FakeModel()
        state = initial("hub", "Implement a basic email validation function.")
        original = copy.deepcopy(state)
        state = advance(state, model)
        self.assertEqual(original["phase"], "ready")
        self.assertEqual(state["engine"], "LangGraph")
        self.assertEqual(state["graph_steps"][-1]["nodes"], ["coordinator", "planner", "finish"])
        self.assertEqual(model.calls[0][0], "planner")
        state = advance(state, model)
        before = len(model.calls)
        state = advance(state, model)
        self.assertEqual(len(model.calls), before)
        self.assertEqual(state["graph_steps"][-1]["nodes"], ["coordinator", "qa", "governance", "gate_fail", "finish"])
        self.assertEqual(state["phase"], "blocked")

    def test_seed_code_is_not_claimed_as_model_generation(self):
        model = FakeModel()
        state = initial("hub", "Implement a basic email validation function.", GOOD)
        for _ in range(3):
            state = advance(state, model)
        self.assertEqual([role for role, _ in model.calls], ["planner"])
        self.assertEqual(state["phase"], "review")
        self.assertIn("gate_pass", state["graph_steps"][-1]["nodes"])
        self.assertEqual(advance(state, model, True)["phase"], "accepted")

    def test_failed_function_cannot_pass_just_because_ast_passes(self):
        model = FakeModel()
        state = initial("hub", "Implement a basic email validation function.", "def validate_email(email):\n return True")
        for _ in range(3):
            state = advance(state, model)
        self.assertTrue(state["governance"]["pass"])
        self.assertFalse(state["qa"]["pass"])
        self.assertEqual(state["phase"], "blocked")
        with self.assertRaises(ValueError):
            advance({**state, "phase": "review"}, model, True)

    def test_persistent_violation_stops_after_three_repairs(self):
        class Stubborn(FakeModel):
            def call(self, role, instruction, payload):
                data, meta = super().call(role, instruction, payload)
                return ({"code": BAD} if role == "developer" else data), meta
        model = Stubborn()
        state = initial("hub", "Implement a basic email validation function.", BAD)
        for _ in range(3):
            state = advance(state, model)
        for i in range(3):
            state = advance(state, model)
            self.assertIsNone(state["qa"])
            state = advance(state, model)
            self.assertEqual(state["phase"], "blocked")
        count = len(model.calls)
        state = advance(state, model)
        self.assertEqual(state["status"], "exhausted")
        self.assertEqual(len(model.calls), count)
        with self.assertRaises(ValueError):
            advance(state, model)

    def test_actual_graph_topology_exposes_conditional_gate(self):
        graph = build_graph(None).get_graph()
        edges = {(edge.source, edge.target) for edge in graph.edges}
        self.assertIn(("coordinator", "planner"), edges)
        self.assertIn(("governance", "gate_pass"), edges)
        self.assertIn(("governance", "gate_fail"), edges)
        self.assertNotIn(("developer", "accept"), edges)


if __name__ == "__main__":
    unittest.main()
