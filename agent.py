from dotenv import load_dotenv
load_dotenv()

import os
import json
import re
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ─────────────────────────────────────────────
# 1. STATE
# ─────────────────────────────────────────────
class TicketState(TypedDict):
    raw_ticket: dict
    ticket_source: str
    subject: str
    description: str
    customer_tier: str
    product: str
    extracted_metrics: dict
    urgency: str
    ticket_type: str
    sentiment: str
    has_pii: bool
    has_enough_info: bool
    clarifying_questions: str
    route_to: str
    should_escalate: bool
    drafted_response: str
    confidence: float
    _known_issue: Optional[dict]


# ─────────────────────────────────────────────
# 2. KNOWN ISSUES
# ─────────────────────────────────────────────
KNOWN_ISSUES = [
    {
        "pattern": ["traces", "docker", "ecs", "not showing", "not appearing"],
        "issue": "LangSmith tracing not working in ECS/Docker",
        "solution": "This is a known networking issue. Ensure your ECS task has outbound internet access via NAT Gateway, and verify LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY are set as environment variables in your task definition — not just in your .env file.",
        "docs_link": "https://docs.smith.langchain.com/self_hosting/configuration"
    },
    {
        "pattern": ["recursion", "maximum recursion", "langgraph", "upgrade"],
        "issue": "RecursionError after upgrading langchain-core to 0.3.x",
        "solution": "This is a known breaking change in langchain-core 0.3.0. Roll back to 0.1.52 immediately using: pip install langchain-core==0.1.52. A fix is in progress.",
        "docs_link": "https://github.com/langchain-ai/langchain/releases"
    },
    {
        "pattern": ["evaluation", "scores", "returning 0", "all zero"],
        "issue": "LangSmith evaluator returning 0 scores",
        "solution": "Your evaluator function must return a dict with key and score fields. Ensure your LLM-as-judge prompt instructs the model to return a parseable numeric score, and handle JSON parsing errors explicitly.",
        "docs_link": "https://docs.smith.langchain.com/evaluation"
    }
]

def check_known_issues(text: str) -> Optional[dict]:
    """Check if ticket matches a known issue pattern."""
    text_lower = text.lower()
    for issue in KNOWN_ISSUES:
        matches = sum(1 for p in issue["pattern"] if p in text_lower)
        if matches >= 2:
            return issue
    return None


# ─────────────────────────────────────────────
# 3. PII DETECTION
# ─────────────────────────────────────────────
PII_PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',                   # OpenAI API key
    r'postgresql://[^\s]+:[^\s]+@',            # PostgreSQL connection string
    r'mysql://[^\s]+:[^\s]+@',                 # MySQL connection string
    r'AKIA[0-9A-Z]{16}',                       # AWS access key
    r'-----BEGIN RSA PRIVATE KEY-----',        # Private key
    r'(?:password|passwd|pwd)\s*[:=]\s*\S+',  # Password patterns
]

def detect_pii(text: str) -> bool:
    """Detect if ticket contains sensitive credentials or PII."""
    for pattern in PII_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ─────────────────────────────────────────────
# 4. LLM
# ─────────────────────────────────────────────
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)


# ─────────────────────────────────────────────
# 5. NODES
# ─────────────────────────────────────────────

def detect_source(state: TicketState) -> dict:
    """Node 0: Detect whether ticket is human or CloudWatch generated."""
    ticket = state["raw_ticket"]
    subject = ticket.get("subject", "")
    body = ticket.get("body", "")

    is_cloudwatch = any([
        "[AUTO]" in subject,
        "ALARM:" in subject,
        "=== CLOUDWATCH ALERT ===" in body,
        "AlarmName" in body,
        "Threshold Crossed" in body,
        ticket.get("source") == "cloudwatch"
    ])

    return {"ticket_source": "cloudwatch" if is_cloudwatch else "human"}


def extract_ticket_info(state: TicketState) -> dict:
    """Node 1: Extract key information from the ticket."""
    ticket = state["raw_ticket"]

    # ── CloudWatch path ──
    if state["ticket_source"] == "cloudwatch":
        body = ticket.get("body", "")

        alarm_name = re.search(r'Alarm Name:\s*(.+)', body)
        metric = re.search(r'Metric:\s*(.+)', body)
        namespace = re.search(r'Namespace:\s*(.+)', body)
        reason = re.search(r'Reason:\s*(.+)', body)
        region = re.search(r'Region:\s*(.+)', body)

        metrics = {}
        context_match = re.search(
            r'=== ADDITIONAL CONTEXT ===(.*?)(===|$)',
            body, re.DOTALL
        )
        if context_match:
            context_text = context_match.group(1)
            for line in context_text.strip().split('\n'):
                if ':' in line:
                    key, _, value = line.partition(':')
                    metrics[key.strip()] = value.strip()

        return {
            "subject": ticket.get("subject", ""),
            "description": body,
            "customer_tier": ticket.get("customer_tier", "Unknown"),
            "product": ticket.get("product", "AWS/Infrastructure"),
            "extracted_metrics": {
                "alarm_name": alarm_name.group(1).strip() if alarm_name else "",
                "metric": metric.group(1).strip() if metric else "",
                "namespace": namespace.group(1).strip() if namespace else "",
                "reason": reason.group(1).strip() if reason else "",
                "region": region.group(1).strip() if region else "",
                **metrics
            }
        }

    # ── Human path ──
    else:
        prompt = f"""Extract key information from this support ticket.

Ticket Subject: {ticket.get('subject', '')}
Ticket Body: {ticket.get('body', '')}
Customer Tier: {ticket.get('customer_tier', 'Unknown')}
Product: {ticket.get('product', 'Unknown')}

Return ONLY a JSON object with these exact fields:
{{
  "subject": "the subject line",
  "description": "a clean 1-2 sentence summary of the issue",
  "customer_tier": "the customer tier",
  "product": "LangChain / LangGraph / LangSmith / Unknown",
  "key_error": "the specific error or problem if mentioned",
  "user_impact": "how many users or what business impact if mentioned"
}}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            extracted = json.loads(content.strip())
        except json.JSONDecodeError:
            extracted = {
                "subject": ticket.get("subject", ""),
                "description": ticket.get("body", "")[:200],
                "customer_tier": ticket.get("customer_tier", "Unknown"),
                "product": ticket.get("product", "Unknown"),
            }

        return {
            "subject": extracted.get("subject", ""),
            "description": extracted.get("description", ""),
            "customer_tier": extracted.get("customer_tier", "Unknown"),
            "product": extracted.get("product", "Unknown"),
            "extracted_metrics": {}
        }


def classify_ticket(state: TicketState) -> dict:
    """Node 2: Classify urgency, type, sentiment. Check PII and known issues."""

    # Read prompt version flag — must be inside function to update between runs
    use_improved = os.getenv("USE_IMPROVED_PROMPT", "false").lower() == "true"

    full_text = f"{state['subject']} {state['description']}"

    has_pii = detect_pii(state["raw_ticket"].get("body", ""))
    known_issue = check_known_issues(full_text)

    # ── CloudWatch path ──
    if state["ticket_source"] == "cloudwatch":
        metrics = state.get("extracted_metrics", {})
        prompt = f"""You are an SRE classifying a CloudWatch alarm ticket.

Alarm Details:
- Alarm: {metrics.get('alarm_name', 'Unknown')}
- Metric: {metrics.get('metric', 'Unknown')}
- Namespace: {metrics.get('namespace', 'Unknown')}
- Reason: {metrics.get('reason', 'Unknown')}
- Additional metrics: {json.dumps({k:v for k,v in metrics.items() if k not in ['alarm_name','metric','namespace','reason','region']})}
- Customer tier: {state['customer_tier']}

Classify this alarm:
- urgency: Critical / High / Medium / Low
- ticket_type: Infrastructure Alert / Performance Degradation / Capacity Issue / Security Alert / Configuration Issue
- sentiment: system

Return ONLY valid JSON:
{{"urgency": "...", "ticket_type": "...", "sentiment": "system", "confidence": 0.0}}"""

    # ── Human path ──
    else:
        if use_improved:
            urgency_rules = """
URGENCY — choose exactly one, be conservative:
* Critical = production completely down OR revenue actively being lost OR
  50000+ users cannot use the product at all OR customer explicitly
  threatening to cancel contract TODAY OR error rate above 20%

* High = major feature broken for Enterprise customer OR
  security/compliance/PII issue OR 200+ users affected OR
  infinite loop blocking production for enterprise OR
  certificate expiring within 24 hours with auto-renewal failed

* Medium = partial or intermittent issue, NOT blocking all work:
  Intermittent errors, traces not appearing, state not persisting,
  billing questions, single endpoint errors, evaluation issues

* Low = no production impact:
  How-to questions, feature requests, vague tickets, documentation

CRITICAL DOWNGRADE RULES — apply these first:
- How-to question = always Low
- Feature request = always Low
- Billing question = always Medium (not Low, not High)
- Intermittent errors = always Medium maximum
- Traces not showing = always Medium
- Evaluation scores issue = always Medium
- State not persisting but app runs = always Medium
- Free tier customer = reduce urgency by one level
- Vague ticket with no error details = always Low"""
        else:
            urgency_rules = "- urgency: Critical (production down, revenue loss) / High (major feature broken) / Medium (partial issue) / Low (question, feature request)"

        prompt = f"""You are classifying a customer support ticket.

Subject: {state['subject']}
Description: {state['description']}
Customer Tier: {state['customer_tier']}
Product: {state['product']}

{urgency_rules}

TICKET TYPE — choose exactly one:
* Production Bug = something that worked before is now broken in production
* Integration Issue = third-party or API connection problem
* How-To Question = customer asking how to use the product
* Feature Request = customer asking for new functionality
* Billing Issue = payment, invoice, subscription question
* Security Issue = PII, credentials, compliance, data privacy
* Escalation = customer expressing anger, threatening churn, repeated failures
* Unclear = not enough information to classify

SENTIMENT — choose exactly one:
* angry = threatening, cancelling, extremely frustrated
* frustrated = clearly unhappy but not threatening
* calm = neutral or professional tone

MANDATORY RULES:
- Enterprise customer + production down = always Critical
- Mentions cancelling contract OR losing money = always Critical
- Vague ticket with no technical details = always Unclear type

Return ONLY valid JSON:
{{"urgency": "...", "ticket_type": "...", "sentiment": "...", "confidence": 0.0}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        classification = json.loads(content.strip())
    except json.JSONDecodeError:
        classification = {
            "urgency": "Medium",
            "ticket_type": "Unclear",
            "sentiment": "calm",
            "confidence": 0.5
        }

    # Sentiment override
    if classification.get("sentiment") == "angry":
        if classification["urgency"] in ["Low", "Medium"]:
            classification["urgency"] = "High"

    return {
        "urgency": classification.get("urgency", "Medium"),
        "ticket_type": classification.get("ticket_type", "Unclear"),
        "sentiment": classification.get("sentiment", "calm"),
        "confidence": float(classification.get("confidence", 0.5)),
        "has_pii": has_pii,
        "has_enough_info": classification.get("ticket_type") != "Unclear",
        "_known_issue": known_issue
    }


def handle_pii(state: TicketState) -> dict:
    """Node 3a: PII detected — warn customer immediately."""
    return {
        "route_to": "Security Queue",
        "should_escalate": True,
        "drafted_response": """Hi,

Thank you for reaching out. Before we address your technical question, we noticed your ticket may contain sensitive credentials such as API keys, passwords, or connection strings.

IMMEDIATE ACTION REQUIRED:
1. Rotate your API key immediately
2. Change your database password immediately
3. Check your access logs for any unauthorized usage in the last 24 hours

We have flagged this ticket for our security team. Once you have rotated your credentials, please reply and we will help you with your original technical issue.

For future reference, never share API keys or passwords in support tickets.

LangChain Security Team"""
    }


def request_clarification(state: TicketState) -> dict:
    """Node 3b: Vague ticket — ask clarifying questions."""
    prompt = f"""A customer submitted a vague support ticket.

Subject: {state['subject']}
Description: {state['description']}
Product: {state['product']}

Generate 3 specific clarifying questions to get the information needed.
Be friendly and concise.

Return ONLY valid JSON:
{{"questions": ["question 1", "question 2", "question 3"]}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content.strip())
        questions = parsed.get("questions", [])
    except json.JSONDecodeError:
        questions = [
            "Which product are you using — LangChain, LangGraph, or LangSmith?",
            "What is the exact error message you are seeing?",
            "What were you trying to do when the issue occurred?"
        ]

    formatted_questions = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

    return {
        "route_to": "Needs More Info",
        "should_escalate": False,
        "has_enough_info": False,
        "clarifying_questions": formatted_questions,
        "drafted_response": f"""Hi,

Thank you for reaching out to LangChain Support!

To help you effectively, could you please provide a bit more information?

{formatted_questions}

Once we have these details we will be able to assist you right away.

Best regards,
LangChain Support"""
    }


def route_and_respond(state: TicketState) -> dict:
    """Node 3c: Route ticket and draft response."""

    # Known issue fast path
    known_issue = state.get("_known_issue")
    if known_issue:
        return {
            "route_to": "Known Issue — Auto-resolved",
            "should_escalate": False,
            "drafted_response": f"""Hi,

Thank you for contacting LangChain Support.

We recognize this as a known issue: {known_issue['issue']}

Solution:
{known_issue['solution']}

Documentation: {known_issue['docs_link']}

Please try this solution and let us know if it resolves your issue.

Best regards,
LangChain Support"""
        }

    # Routing map
    routing_map = {
# ── Human ticket routing ──
        ("Critical", "Production Bug"):      ("Engineering — P0 Response", True),
        ("Critical", "Escalation"):          ("Senior Engineer + Account Manager", True),
        ("High", "Production Bug"):          ("Senior Engineer", True),
        ("High", "Security Issue"):          ("Enterprise Sales / Legal", True),
        ("High", "Escalation"):              ("Senior Engineer + Account Manager", True),
        ("Medium", "Integration Issue"):     ("Standard Support", False),
        ("Medium", "How-To Question"):       ("Standard Support", False),
        ("Medium", "Billing Issue"):         ("Billing Team", False),
        ("Low", "Feature Request"):          ("Product Team", False),
        ("Low", "How-To Question"):          ("Documentation / Community", False),

        # ── CloudWatch ticket routing ──
        ("Critical", "Infrastructure Alert"):    ("On-Call SRE — Immediate Page", True),
        ("Critical", "Performance Degradation"): ("On-Call SRE — Immediate Page", True),
        ("High", "Infrastructure Alert"):        ("On-Call SRE", True),
        ("High", "Performance Degradation"):     ("SRE Team", True),
        ("High", "Capacity Issue"):              ("SRE Team", True),
        ("Medium", "Infrastructure Alert"):      ("SRE Queue", False),
        ("Medium", "Capacity Issue"):            ("SRE Queue", False),
        ("Low", "Infrastructure Alert"):         ("Monitoring Queue", False),
    }

    route_key = (state["urgency"], state["ticket_type"])
    route_to, should_escalate = routing_map.get(route_key, ("Standard Support", False))

    # Enterprise always escalates for High+
    if state["customer_tier"] == "Enterprise" and state["urgency"] in ["Critical", "High"]:
        should_escalate = True

    # Draft response
    if state["ticket_source"] == "cloudwatch":
        metrics = state.get("extracted_metrics", {})
        prompt = f"""You are a senior SRE drafting an incident response for a CloudWatch alarm.

Alarm: {metrics.get('alarm_name', 'Unknown')}
Metric: {metrics.get('metric', 'Unknown')}
Reason: {metrics.get('reason', 'Unknown')}
Additional context: {json.dumps({k:v for k,v in metrics.items() if k not in ['alarm_name','metric','namespace','reason','region']})}
Severity: {state['urgency']}

Write a concise incident response with:
1. Immediate triage steps (2-3 specific actions)
2. Likely root cause
3. Escalation recommendation

Be direct and technical."""

    else:
        tone_map = {
            "angry": "Start with a sincere apology. Acknowledge their frustration explicitly before any technical content.",
            "frustrated": "Start by acknowledging their experience. Show urgency.",
            "calm": "Be professional, friendly, and direct.",
            "system": "Be technical and concise."
        }
        tone = tone_map.get(state.get("sentiment", "calm"), "Be professional and helpful.")

        prompt = f"""You are a Senior Technical Support Engineer at LangChain.
Draft a response to this support ticket.

Subject: {state['subject']}
Issue: {state['description']}
Customer Tier: {state['customer_tier']}
Product: {state['product']}
Urgency: {state['urgency']}
Type: {state['ticket_type']}

Tone: {tone}

Guidelines:
- Be specific and technical
- For Critical/High: acknowledge immediately and give a concrete next step
- Keep it under 200 words
- End with: LangChain Support Team"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "route_to": route_to,
        "should_escalate": should_escalate,
        "drafted_response": response.content
    }


# ─────────────────────────────────────────────
# 6. ROUTING FUNCTION
# ─────────────────────────────────────────────

def route_after_classification(state: TicketState) -> Literal["handle_pii", "request_clarification", "route_and_respond"]:
    """Decide which path to take after classification."""
    if state.get("has_pii"):
        return "handle_pii"
    if not state.get("has_enough_info"):
        return "request_clarification"
    return "route_and_respond"


# ─────────────────────────────────────────────
# 7. BUILD THE GRAPH
# ─────────────────────────────────────────────

def build_graph():
    graph = StateGraph(TicketState)

    graph.add_node("detect_source", detect_source)
    graph.add_node("extract_ticket_info", extract_ticket_info)
    graph.add_node("classify_ticket", classify_ticket)
    graph.add_node("handle_pii", handle_pii)
    graph.add_node("request_clarification", request_clarification)
    graph.add_node("route_and_respond", route_and_respond)

    graph.set_entry_point("detect_source")

    graph.add_edge("detect_source", "extract_ticket_info")
    graph.add_edge("extract_ticket_info", "classify_ticket")

    graph.add_conditional_edges(
        "classify_ticket",
        route_after_classification,
        {
            "handle_pii": "handle_pii",
            "request_clarification": "request_clarification",
            "route_and_respond": "route_and_respond"
        }
    )

    graph.add_edge("handle_pii", END)
    graph.add_edge("request_clarification", END)
    graph.add_edge("route_and_respond", END)

    return graph.compile()


# ─────────────────────────────────────────────
# 8. PROCESS A TICKET
# ─────────────────────────────────────────────

def process_ticket(graph, ticket: dict) -> dict:
    """Process a single support ticket through the agent."""
    initial_state: TicketState = {
        "raw_ticket": ticket,
        "ticket_source": "",
        "subject": "",
        "description": "",
        "customer_tier": ticket.get("customer_tier", "Unknown"),
        "product": ticket.get("product", "Unknown"),
        "extracted_metrics": {},
        "urgency": "",
        "ticket_type": "",
        "sentiment": "",
        "has_pii": False,
        "has_enough_info": True,
        "clarifying_questions": "",
        "route_to": "",
        "should_escalate": False,
        "drafted_response": "",
        "confidence": 0.0,
        "_known_issue": None
    }

    return graph.invoke(initial_state)


# ─────────────────────────────────────────────
# 9. MAIN — TEST THE AGENT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from dataset import SUPPORT_TICKETS, CLOUDWATCH_TICKETS

    print("Building agent graph...")
    graph = build_graph()
    print("✅ Agent ready\n")

    # Test human ticket
    print("=" * 60)
    print("TEST 1: Production outage (human ticket)")
    print("=" * 60)
    result = process_ticket(graph, SUPPORT_TICKETS[0]["input"])
    print(f"Source:    {result['ticket_source']}")
    print(f"Urgency:   {result['urgency']}")
    print(f"Type:      {result['ticket_type']}")
    print(f"Route to:  {result['route_to']}")
    print(f"Escalate:  {result['should_escalate']}")
    print(f"\nResponse:\n{result['drafted_response']}")

    print("\n" + "=" * 60)
    print("TEST 2: CloudWatch alarm")
    print("=" * 60)
    result = process_ticket(graph, CLOUDWATCH_TICKETS[0]["input"])
    print(f"Source:    {result['ticket_source']}")
    print(f"Urgency:   {result['urgency']}")
    print(f"Type:      {result['ticket_type']}")
    print(f"Route to:  {result['route_to']}")
    print(f"Escalate:  {result['should_escalate']}")
    print(f"\nResponse:\n{result['drafted_response']}")

    print("\n" + "=" * 60)
    print("TEST 3: Vague ticket (edge case)")
    print("=" * 60)
    result = process_ticket(graph, SUPPORT_TICKETS[10]["input"])
    print(f"Source:    {result['ticket_source']}")
    print(f"Urgency:   {result['urgency']}")
    print(f"Type:      {result['ticket_type']}")
    print(f"Route to:  {result['route_to']}")
    print(f"\nResponse:\n{result['drafted_response']}")
