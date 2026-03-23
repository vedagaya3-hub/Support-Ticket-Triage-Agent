SUPPORT_TICKETS = [
    {
        "id": "ticket_001",
        "input": {
            "subject": "Production outage - LangGraph agents not responding",
            "body": "Our entire LangGraph-based customer service pipeline went down 30 minutes ago after we upgraded langchain-core from 0.1.52 to 0.3.0. All agents are returning RecursionError: maximum recursion depth exceeded. This is affecting 50,000 active users. We are losing $10K per minute. Need immediate help.",
            "customer_tier": "Enterprise",
            "product": "LangGraph",
            "submitted_at": "2024-01-15T02:47:00Z"
        },
        "expected": {
            "urgency": "Critical",
            "ticket_type": "Production Bug",
            "route_to": "Engineering — P0 Response",
            "should_escalate": True,
            "response_should_include": ["rollback", "workaround", "immediate"]
        }
    },
    {
        "id": "ticket_002",
        "input": {
            "subject": "LangSmith traces not showing up in Docker on ECS",
            "body": "I set LANGCHAIN_TRACING_V2=true and added my API key but traces are not appearing in LangSmith. My code runs fine locally but in our Docker container on AWS ECS the traces just don't show up.",
            "customer_tier": "Pro",
            "product": "LangSmith",
            "submitted_at": "2024-01-15T10:15:00Z"
        },
        "expected": {
            "urgency": "Medium",
            "ticket_type": "Integration Issue",
            "route_to": "Standard Support",
            "should_escalate": False,
            "response_should_include": ["environment variables", "network", "NAT"]
        }
    },
    {
        "id": "ticket_003",
        "input": {
            "subject": "How do I add memory to my LangGraph agent?",
            "body": "I am building a customer support bot using LangGraph. I want it to remember previous conversations. I have read the docs but I am confused about checkpointers. Can you point me to an example?",
            "customer_tier": "Free",
            "product": "LangGraph",
            "submitted_at": "2024-01-15T14:30:00Z"
        },
        "expected": {
            "urgency": "Low",
            "ticket_type": "How-To Question",
            "route_to": "Documentation / Community",
            "should_escalate": False,
            "response_should_include": ["checkpointer", "MemorySaver", "example"]
        }
    },
    {
        "id": "ticket_004",
        "input": {
            "subject": "Agent stuck in infinite loop in production",
            "body": "Our LangGraph ReAct agent has been running for 6 hours on a single task. It keeps calling the same tool over and over. We set max_iterations=10 but it is not stopping. Affecting 200 enterprise customers.",
            "customer_tier": "Enterprise",
            "product": "LangGraph",
            "submitted_at": "2024-01-15T08:00:00Z"
        },
        "expected": {
            "urgency": "High",
            "ticket_type": "Production Bug",
            "route_to": "Senior Engineer",
            "should_escalate": True,
            "response_should_include": ["recursion limit", "interrupt", "workaround"]
        }
    },
    {
        "id": "ticket_005",
        "input": {
            "subject": "Please add dark mode to LangSmith UI",
            "body": "The LangSmith UI is great but it would be helpful to have a dark mode option. I use it for long debugging sessions and the bright white background is hard on my eyes.",
            "customer_tier": "Pro",
            "product": "LangSmith",
            "submitted_at": "2024-01-15T16:00:00Z"
        },
        "expected": {
            "urgency": "Low",
            "ticket_type": "Feature Request",
            "route_to": "Product Team",
            "should_escalate": False,
            "response_should_include": ["thank you", "logged", "feedback"]
        }
    },
    {
        "id": "ticket_006",
        "input": {
            "subject": "Getting 429 errors from OpenAI through LangChain",
            "body": "We are getting intermittent 429 RateLimitError when calling GPT-4 through LangChain in our RAG pipeline. It happens about 5% of the time during peak hours. We are on the OpenAI Tier 3 plan.",
            "customer_tier": "Pro",
            "product": "LangChain",
            "submitted_at": "2024-01-15T11:45:00Z"
        },
        "expected": {
            "urgency": "Medium",
            "ticket_type": "Integration Issue",
            "route_to": "Standard Support",
            "should_escalate": False,
            "response_should_include": ["retry", "backoff", "rate limit"]
        }
    },
    {
        "id": "ticket_007",
        "input": {
            "subject": "LangSmith evaluation scores all returning 0",
            "body": "I set up a LangSmith evaluation experiment with an LLM-as-judge evaluator. All my scores are coming back as 0 even for answers that are clearly correct. Here is my evaluator: Score this answer: {answer}. Return a number.",
            "customer_tier": "Pro",
            "product": "LangSmith",
            "submitted_at": "2024-01-15T13:00:00Z"
        },
        "expected": {
            "urgency": "Medium",
            "ticket_type": "How-To Question",
            "route_to": "Standard Support",
            "should_escalate": False,
            "response_should_include": ["evaluator prompt", "output format", "score schema"]
        }
    },
    {
        "id": "ticket_008",
        "input": {
            "subject": "Data privacy — are my LangSmith traces stored on your servers?",
            "body": "Our legal team is asking about data residency for LangSmith traces. We deal with PII in our LLM application and need to understand where traces are stored, how long they are retained, and whether a BAA is available for HIPAA compliance.",
            "customer_tier": "Enterprise",
            "product": "LangSmith",
            "submitted_at": "2024-01-15T09:30:00Z"
        },
        "expected": {
            "urgency": "High",
            "ticket_type": "Security Issue",
            "route_to": "Enterprise Sales / Legal",
            "should_escalate": True,
            "response_should_include": ["data residency", "retention", "BAA", "compliance"]
        }
    },
    {
        "id": "ticket_009",
        "input": {
            "subject": "LangGraph state not persisting between runs",
            "body": "I am using LangGraph with a PostgresSaver checkpointer. State persists within a single session but when I restart my application the state is gone. I am passing the same thread_id each time.",
            "customer_tier": "Pro",
            "product": "LangGraph",
            "submitted_at": "2024-01-15T15:20:00Z"
        },
        "expected": {
            "urgency": "Medium",
            "ticket_type": "Integration Issue",
            "route_to": "Standard Support",
            "should_escalate": False,
            "response_should_include": ["PostgresSaver", "connection string", "thread_id"]
        }
    },
    {
        "id": "ticket_010",
        "input": {
            "subject": "Billing — charged twice this month",
            "body": "I was charged twice for my LangSmith Pro subscription this month — once on Jan 1 and again on Jan 15. Total double charge of $39. Can you refund the duplicate and confirm my billing cycle?",
            "customer_tier": "Pro",
            "product": "LangSmith",
            "submitted_at": "2024-01-15T17:45:00Z"
        },
        "expected": {
            "urgency": "Medium",
            "ticket_type": "Billing Issue",
            "route_to": "Billing Team",
            "should_escalate": False,
            "response_should_include": ["apology", "refund", "billing team"]
        }
    },
    {
        "id": "ticket_011",
        "input": {
            "subject": "It's not working",
            "body": "Please help",
            "customer_tier": "Free",
            "product": "Unknown",
            "submitted_at": "2024-01-15T18:00:00Z"
        },
        "expected": {
            "urgency": "Low",
            "ticket_type": "Unclear",
            "route_to": "Needs More Info",
            "should_escalate": False,
            "response_should_include": ["clarifying questions", "product", "error message"]
        }
    },
    {
        "id": "ticket_012",
        "input": {
            "subject": "Cancelling our contract — completely unacceptable",
            "body": "We have been down for 3 days. I have submitted 4 tickets with no response. Our entire AI pipeline is broken and we are losing customers. We are cancelling our $50K enterprise contract and moving to a competitor.",
            "customer_tier": "Enterprise",
            "product": "LangGraph",
            "submitted_at": "2024-01-15T09:00:00Z"
        },
        "expected": {
            "urgency": "Critical",
            "ticket_type": "Escalation",
            "route_to": "Senior Engineer + Account Manager",
            "should_escalate": True,
            "response_should_include": ["empathy", "immediate action", "account manager"]
        }
    },
    {
        "id": "ticket_013",
        "input": {
            "subject": "Debug help needed",
            "body": "Here is my API key sk-proj-abc123secretkey and my config. Why is my agent not connecting to the database at postgresql://admin:mypassword@prod.db.example.com/users?",
            "customer_tier": "Pro",
            "product": "LangChain",
            "submitted_at": "2024-01-15T14:00:00Z"
        },
        "expected": {
            "urgency": "High",
            "ticket_type": "Security Issue",
            "route_to": "Security Queue",
            "should_escalate": True,
            "response_should_include": ["rotate credentials", "security warning"]
        }
    }
]

CLOUDWATCH_TICKETS = [
    {
        "id": "cw_ticket_001",
        "input": {
            "subject": "[AUTO] ALARM: PaymentService-DBConnectionsHigh",
            "body": """=== CLOUDWATCH ALERT ===
Alarm Name: PaymentService-DBConnectionsHigh
State: ALARM
Reason: Threshold Crossed: 1 datapoint [498.0] was greater than threshold (450.0)
Metric: DatabaseConnections
Namespace: AWS/RDS
Dimension: DBInstanceIdentifier = payment-db-prod
Region: us-east-1
Time: 2024-01-15T02:47:32Z

=== ADDITIONAL CONTEXT ===
p99_latency_ms: 10400
error_rate_percent: 23
affected_endpoint: /api/checkout
recent_deployment: v2.3.1 deployed 6 hours ago""",
            "customer_tier": "Enterprise",
            "product": "AWS/RDS",
            "source": "cloudwatch"
        },
        "expected": {
            "urgency": "Critical",
            "ticket_type": "Performance Degradation",
            "route_to": "On-Call SRE — Immediate Page",
            "should_escalate": True,
            "response_should_include": ["DB connections", "RDS", "immediate steps"]
        }
    },
    {
        "id": "cw_ticket_002",
        "input": {
            "subject": "[AUTO] ALARM: OrderService-MemoryUtilizationHigh",
            "body": """=== CLOUDWATCH ALERT ===
Alarm Name: OrderService-MemoryUtilizationHigh
State: ALARM
Reason: Threshold Crossed: 1 datapoint [94.2] was greater than threshold (85.0)
Metric: MemoryUtilization
Namespace: ECS/ContainerInsights
Dimension: ServiceName = order-service
Region: us-west-2
Time: 2024-01-15T11:23:15Z

=== ADDITIONAL CONTEXT ===
oom_kill_count_last_30min: 3
pod_restarts: 8
error_rate_percent: 8
recent_change: Memory limit reduced from 2GB to 1GB in last deployment""",
            "customer_tier": "Enterprise",
            "product": "AWS/ECS",
            "source": "cloudwatch"
        },
        "expected": {
            "urgency": "High",
            "ticket_type": "Infrastructure Alert",
            "route_to": "On-Call SRE",
            "should_escalate": True,
            "response_should_include": ["memory limit", "OOMKill", "deployment rollback"]
        }
    },
    {
        "id": "cw_ticket_003",
        "input": {
            "subject": "[AUTO] ALARM: LoggingService-DiskSpaceCritical",
            "body": """=== CLOUDWATCH ALERT ===
Alarm Name: LoggingService-DiskSpaceCritical
State: ALARM
Reason: Threshold Crossed: 1 datapoint [96.3] was greater than threshold (90.0)
Metric: DiskSpaceUtilization
Namespace: CWAgent
Dimension: path = /var/log
Region: us-east-1
Time: 2024-01-15T06:20:05Z

=== ADDITIONAL CONTEXT ===
disk_fill_rate: 2GB/hour (normal: 200MB/hour)
estimated_time_to_full: 2 hours
application_errors: none yet
note: DEBUG logging left enabled in payment-service deploy yesterday""",
            "customer_tier": "Enterprise",
            "product": "AWS/EC2",
            "source": "cloudwatch"
        },
        "expected": {
            "urgency": "High",
            "ticket_type": "Capacity Issue",
            "route_to": "SRE Team",
            "should_escalate": True,
            "response_should_include": ["disk space", "debug logging", "immediate action"]
        }
    }
]

# Combined for full evaluation run
ALL_TICKETS = SUPPORT_TICKETS + CLOUDWATCH_TICKETS
