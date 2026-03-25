# Support-Ticket-Triage-Agent
Support Ticket Triage Agent — LangGraph + LangSmith Evaluation

---

## What I Built
A LangGraph-based agent that triages customer support tickets and CloudWatch auto-generated alerts — evaluated with LangSmith.

## Agent Design — 6 Nodes
- Node 0: Detect source (human vs CloudWatch auto-generated)
- Node 1: Extract ticket info (LLM for human, regex for CloudWatch)
- Node 2: Classify urgency, type, sentiment
- Node 3a: Handle PII — security warning path
- Node 3b: Request clarification — vague ticket path
- Node 3c: Route and respond — normal path

## Evaluation Results
| Metric | Baseline | Improved |
|---|---|---|
| urgency_accuracy | 31% | 44% |
| escalation_accuracy | 81% | 88% |
| response_quality | 74% | 75% |

## Files
- `agent.py` — LangGraph agent
- `dataset.py` — 16 test support tickets
- `evaluators.py` — 3 LangSmith scoring functions
- `evaluate.py` — SDK evaluation script
- `observation_log.md` — friction log and product feedback

## Setup
> pip install langgraph langchain langchain-openai langsmith python-dotenv
# Add OPENAI_API_KEY and LANGCHAIN_API_KEY to .env file
> python evaluate.py
