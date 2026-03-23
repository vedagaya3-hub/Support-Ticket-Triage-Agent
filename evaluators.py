from dotenv import load_dotenv
load_dotenv()

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


def evaluate_urgency(run, example):
    """
    Metric 1: Did the agent classify urgency correctly?
    Exact match — returns 1.0 (correct) or 0.0 (wrong).
    """
    predicted = (run.outputs or {}).get("urgency", "").strip().lower()
    expected = example.outputs["expected"]["urgency"].strip().lower()
    correct = predicted == expected

    return {
        "key": "urgency_accuracy",
        "score": 1.0 if correct else 0.0,
        "comment": f"Predicted: '{predicted}' | Expected: '{expected}'"
    }


def evaluate_escalation(run, example):
    """
    Metric 2: Did the agent correctly decide whether to escalate?
    Binary — returns 1.0 (correct) or 0.0 (wrong).
    """
    predicted = bool((run.outputs or {}).get("should_escalate", False))
    expected = bool(example.outputs["expected"]["should_escalate"])
    correct = predicted == expected

    return {
        "key": "escalation_accuracy",
        "score": 1.0 if correct else 0.0,
        "comment": f"Predicted escalate={predicted} | Expected escalate={expected}"
    }


def evaluate_response_quality(run, example):
    """
    Metric 3: LLM-as-judge — does the response cover expected topics?
    Returns 0.0 to 1.0 based on content quality.
    """
    drafted_response = (run.outputs or {}).get("drafted_response", "")
    expected_topics = example.outputs["expected"].get("response_should_include", [])

    if not drafted_response:
        return {"key": "response_quality", "score": 0.0,
                "comment": "No response drafted"}

    if not expected_topics:
        return {"key": "response_quality", "score": 1.0,
                "comment": "No expected topics to check"}

    prompt = f"""You are evaluating a customer support response.

The response SHOULD address these topics: {expected_topics}

Response to evaluate:
{drafted_response}

Score from 0 to 10:
- 9-10: Addresses all expected topics clearly and helpfully
- 7-8: Addresses most topics, minor gaps
- 5-6: Addresses some topics but missing key information
- 3-4: Barely touches the expected topics
- 0-2: Completely misses what was needed

Return ONLY valid JSON, no other text:
{{"score": 7, "reason": "one sentence explanation"}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content.strip())
        return {
            "key": "response_quality",
            "score": round(parsed["score"] / 10.0, 2),
            "comment": parsed.get("reason", "")
        }
    except Exception as e:
        return {
            "key": "response_quality",
            "score": 0.5,
            "comment": f"Evaluator error: {str(e)}"
        }


# The 3 evaluators used in LangSmith evaluation
ALL_EVALUATORS = [
    evaluate_urgency,
    evaluate_escalation,
    evaluate_response_quality,
]
