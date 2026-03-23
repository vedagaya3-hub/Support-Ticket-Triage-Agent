from dotenv import load_dotenv
load_dotenv()

import os
from langsmith import Client
from langsmith.evaluation import evaluate
from agent import build_graph, process_ticket
from dataset import ALL_TICKETS
from evaluators import ALL_EVALUATORS

# ─────────────────────────────────────────────
# 1. INITIALIZE
# ─────────────────────────────────────────────
client = Client()

DATASET_NAME = "TicketSupportAgent-Dataset"

# ─────────────────────────────────────────────
# 2. CREATE DATASET IN LANGSMITH
# ─────────────────────────────────────────────
def create_langsmith_dataset():
    """Upload tickets to LangSmith as a dataset."""
    existing = [d for d in client.list_datasets()
                if d.name == DATASET_NAME]
    if existing:
        print(f"✅ Dataset '{DATASET_NAME}' already exists — skipping creation")
        return existing[0]

    print(f"Creating dataset '{DATASET_NAME}' in LangSmith...")
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Support ticket triage evaluation dataset — 16 tickets covering human and CloudWatch sources including edge cases"
    )

    for ticket in ALL_TICKETS:
        client.create_example(
            inputs={"ticket": ticket["input"]},
            outputs={
                "expected": ticket["expected"],
                "id": ticket["id"]
            },
            dataset_id=dataset.id
        )
        print(f"  Added: {ticket['id']}")

    print(f"✅ Dataset created with {len(ALL_TICKETS)} examples\n")
    return dataset


# ─────────────────────────────────────────────
# 3. AGENT WRAPPERS — one per experiment
# ─────────────────────────────────────────────
def make_agent_runner(use_improved: bool):
    """
    Factory function — returns a run_agent function
    that uses either the baseline or improved prompt.
    Building the graph here ensures each experiment
    uses its own fresh graph with the correct prompt.
    """
    os.environ["USE_IMPROVED_PROMPT"] = "true" if use_improved else "false"
    graph = build_graph()

    def run_agent(inputs: dict) -> dict:
        ticket = inputs["ticket"]
        result = process_ticket(graph, ticket)
        return {
            "urgency": result.get("urgency", ""),
            "ticket_type": result.get("ticket_type", ""),
            "route_to": result.get("route_to", ""),
            "should_escalate": result.get("should_escalate", False),
            "drafted_response": result.get("drafted_response", ""),
            "has_pii": result.get("has_pii", False),
            "ticket_source": result.get("ticket_source", ""),
            "confidence": result.get("confidence", 0.0),
            "sentiment": result.get("sentiment", "")
        }

    return run_agent


# ─────────────────────────────────────────────
# 4. PRINT SUMMARY
# ─────────────────────────────────────────────
def print_summary(results, label: str):
    """Print evaluation results summary."""
    print("\n" + "=" * 60)
    print(f"RESULTS: {label}")
    print("=" * 60)

    scores = {
        "urgency_accuracy": [],
        "escalation_accuracy": [],
        "response_quality": []
    }

    for result in results._results:
        for eval_result in result.get("evaluation_results", {}).get("results", []):
            key = eval_result.key
            score = eval_result.score
            if key in scores and score is not None:
                scores[key].append(score)

    for metric, values in scores.items():
        if values:
            avg = sum(values) / len(values)
            filled = int(avg * 20)
            bar = "█" * filled + "░" * (20 - filled)
            print(f"{metric:<25} {bar} {avg:.0%}")
        else:
            print(f"{metric:<25} no scores recorded")

    print("\n✅ Full results in LangSmith UI")
    print("   https://smith.langchain.com")
    print("=" * 60)


# ─────────────────────────────────────────────
# 5. RUN EXPERIMENTS
# ─────────────────────────────────────────────
def run_baseline():
    """Run baseline experiment — original weak prompt."""
    print("\nRunning BASELINE experiment...")
    print("Prompt: original — vague urgency rules")
    print("-" * 50)

    agent = make_agent_runner(use_improved=False)

    return evaluate(
        agent,
        data=DATASET_NAME,
        evaluators=ALL_EVALUATORS,
        experiment_prefix="triage-agent-baseline",
        metadata={
            "agent_version": "1.0",
            "model": "gpt-3.5-turbo",
            "prompt": "baseline — vague urgency rules"
        },
        max_concurrency=2
    )


def run_improved():
    """Run improved experiment — stronger prompt with downgrade rules."""
    print("\nRunning IMPROVED experiment...")
    print("Prompt: improved — explicit downgrade rules added")
    print("-" * 50)

    agent = make_agent_runner(use_improved=True)

    return evaluate(
        agent,
        data=DATASET_NAME,
        evaluators=ALL_EVALUATORS,
        experiment_prefix="triage-agent-improved",
        metadata={
            "agent_version": "2.0",
            "model": "gpt-3.5-turbo",
            "prompt": "improved — added explicit downgrade rules for Medium and Low"
        },
        max_concurrency=2
    )


# ─────────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SUPPORT TICKET TRIAGE — LANGSMITH EVALUATION")
    print("=" * 60 + "\n")

    # Step 1: Create dataset
    create_langsmith_dataset()

    # Step 2: Run baseline
    baseline_results = run_baseline()
    print_summary(baseline_results, "BASELINE — original prompt")

    # Step 3: Run improved
    improved_results = run_improved()
    print_summary(improved_results, "IMPROVED — downgrade rules added")

    print("\nDone! Compare experiments in LangSmith:")
    print("https://smith.langchain.com")
