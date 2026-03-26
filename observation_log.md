Below are my genuine observations while setting up, creating the codebase, running my agent, and using LangSmith as an observability and evaluation tool.

1. Which API key variable name is correct?
When I was setting up my environment I found two different variable names across different docs and tutorials:

LANGCHAIN_API_KEY & LANGSMITH_API_KEY

I went with LANGCHAIN_API_KEY because most examples used it and it made sense to me — but I wasn't sure why LANGSMITH_API_KEY was added in few places.

2. LANGSMITH Trace View is very impressive.
My observation - The amount of information it gives and the visuals are really good. We can see all the details needed for investigating in one place — inputs and outputs for every node, latency per step, the full execution path. As someone who has spent years debugging high severity incidents at Amazon, this is exactly the kind of observability we need while debugging issues.

3. Running the same evaluation twice gives different scores
I expected temperature=0 would make consistent results everytime. But my scores varied slightly between runs even with the same code and same dataset.

Run 1: urgency_accuracy = 31% Run 2: urgency_accuracy = 31% (same) Run 3 after prompt change: urgency_accuracy = 44%

Run 4: I also saw 62% when running sequentially in a diagnostic test vs 44% when running concurrently in LangSmith with max_concurrency=2.

My observation: The LLM appears sensitive to concurrent load even at temperature=0.

4. More specific prompts = dramatically better results
My first classification prompt was vague: "Critical = production down / High = major feature broken"

The LLM classified 13 of 16 tickets as High or Critical. Adding specific examples and explicit downgrade rules improved accuracy from 31% to 44% in one iteration with sequential way.

My observation: If you only define what Critical looks like the model defaults upward. You have to be just as explicit about what keeps something at Medium or Low.

5. Running the script twice creates duplicate dataset examples
When I ran evaluate.py a second time LangSmith added all 16 tickets again — creating 32 examples instead of 16. My scores were then calculated over duplicates.

I added a manual check to skip if the dataset already exists but this should probably be the default behavior.

Question: Is the manual check the recommended approach or did I approach it in a wrong way?

6. You can only compare two experiments at a time
After several iterations I wanted to see all my experiments in oneview — baseline, v2, v3. The compare view only supports two at a time. At any given time, I was only able to compare two experiments.

Question: Is multi-experiment comparison coming up as a new feature? Even a simple table showing all experiments ordered by date with their scores would be very useful during iterative development.

My observation: comparision between experiments is really good, gives lot of good data.

7. I considered adding a loop for this agent. But I decided against it - I made ticket triage as a single-pass decision, not an iterative dialogue as it would pause and wait for human clarification.
Question - What is the recommended pattern for human-in-the-loop workflows in LangGraph where the agent needs to pause and wait for input? I saw interrupt() in the docs but wasn't sure if that was the right approach for this use case.

8. No sensitive data scrubbing is happening before traces are uploaded
I added PII detection into my agent as one of the edge cases — when a customer accidentally pastes an API key or database password the agent should catch it and send an immediate security warning. But I noticed the original ticket's body with the credentials still gets logged in the LangSmith trace.

Question - Is there a way to configure field-level redaction before traces are uploaded? This feels like a critical feature that need to be addressed on priority (security concern)
