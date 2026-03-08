# Industry Patterns

Domain-specific agent implementations for common industries.

## Customer Support

### Triage and Routing Pattern

```python
from agents import Agent, Runner
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Specialized agents
billing_agent = Agent(
    name="Billing Specialist",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You handle billing inquiries, payment issues, refunds, and subscription changes.
    Be precise about amounts and dates. Always verify account details.""",
    handoff_description="Handles billing, payments, refunds, and subscriptions",
    tools=[check_account, process_refund, update_subscription],
)

technical_agent = Agent(
    name="Technical Support",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You provide technical support for product issues.
    Ask clarifying questions. Guide users through troubleshooting steps.""",
    handoff_description="Handles technical issues, bugs, and troubleshooting",
    tools=[check_system_status, create_ticket, search_knowledge_base],
)

# Triage agent
support_agent = Agent(
    name="Support Triage",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the first point of contact for customer support.
    - Billing/payment questions → Billing Specialist
    - Technical issues → Technical Support
    - General questions → Answer directly
    Be friendly and professional.""",
    handoffs=[billing_agent, technical_agent],
    tools=[search_faq, check_order_status],
)
```

## Data Analysis

### Analysis Agent Pattern

```python
@function_tool
async def query_database(sql: str) -> str:
    """Execute SQL query and return results."""
    # Implementation
    pass

@function_tool
async def create_visualization(data: dict, chart_type: str) -> str:
    """Create visualization from data."""
    # Implementation
    pass

analyst_agent = Agent(
    name="Data Analyst",
    instructions="""You are a data analyst assistant.
    - Query databases using SQL
    - Analyze trends and patterns
    - Create visualizations
    - Provide insights and recommendations
    Always show your reasoning and cite data sources.""",
    model="gpt-4o",  # Use full model for complex analysis
    tools=[query_database, create_visualization, calculate_statistics],
)
```

## Manufacturing

### Production Intelligence Pattern

```python
@function_tool
async def check_inventory(part_id: str) -> str:
    """Check inventory levels for a part."""
    pass

@function_tool
async def get_machine_status(machine_id: str) -> str:
    """Get current status of manufacturing equipment."""
    pass

@function_tool
async def schedule_maintenance(machine_id: str, date: str) -> str:
    """Schedule maintenance for equipment."""
    pass

manufacturing_agent = Agent(
    name="Manufacturing Intelligence",
    instructions="""You help manage manufacturing operations.
    - Monitor inventory levels and alert on low stock
    - Track machine status and predict maintenance needs
    - Optimize production schedules
    - Analyze quality metrics
    Use data-driven insights for recommendations.""",
    tools=[check_inventory, get_machine_status, schedule_maintenance, analyze_quality],
)
```

## Sales

### Sales Pipeline Agent

```python
@function_tool
async def search_prospects(criteria: dict) -> str:
    """Search for prospects matching criteria."""
    pass

@function_tool
async def enrich_lead(email: str) -> str:
    """Enrich lead data from external sources."""
    pass

@function_tool
async def update_crm(lead_id: str, data: dict) -> str:
    """Update CRM with lead information."""
    pass

sales_agent = Agent(
    name="Sales Assistant",
    instructions="""You help sales teams manage their pipeline.
    - Research prospects and companies
    - Enrich lead data
    - Draft personalized outreach
    - Track deal progress
    - Suggest next actions
    Be professional and data-driven.""",
    tools=[search_prospects, enrich_lead, update_crm, draft_email],
)
```

## Marketing

### Campaign Management Pattern

```python
@function_tool
async def analyze_audience(segment: str) -> str:
    """Analyze audience segment characteristics."""
    pass

@function_tool
async def generate_content(topic: str, format: str) -> str:
    """Generate marketing content."""
    pass

@function_tool
async def schedule_post(content: str, channels: list, date: str) -> str:
    """Schedule content across channels."""
    pass

marketing_agent = Agent(
    name="Marketing Assistant",
    instructions="""You help plan and execute marketing campaigns.
    - Analyze target audiences
    - Generate content ideas and drafts
    - Plan multi-channel campaigns
    - Track campaign performance
    - Suggest optimizations
    Be creative but data-driven.""",
    tools=[analyze_audience, generate_content, schedule_post, track_metrics],
)
```

## Finance

### Financial Analysis Pattern

```python
@function_tool
async def get_financial_data(company: str, metric: str) -> str:
    """Retrieve financial data for analysis."""
    pass

@function_tool
async def build_model(assumptions: dict) -> str:
    """Build financial model with given assumptions."""
    pass

@function_tool
async def calculate_ratios(financials: dict) -> str:
    """Calculate financial ratios."""
    pass

finance_agent = Agent(
    name="Financial Analyst",
    instructions="""You provide financial analysis and insights.
    - Analyze financial statements
    - Build financial models
    - Calculate key metrics and ratios
    - Identify trends and risks
    - Provide investment recommendations
    Always show calculations and assumptions.""",
    model="gpt-4o",  # Use full model for complex analysis
    tools=[get_financial_data, build_model, calculate_ratios],
)
```

## Healthcare

### Clinical Documentation Pattern

```python
@function_tool
async def search_icd_codes(description: str) -> str:
    """Search for ICD diagnosis codes."""
    pass

@function_tool
async def check_drug_interactions(medications: list) -> str:
    """Check for drug interactions."""
    pass

@function_tool
async def generate_note(encounter_data: dict) -> str:
    """Generate clinical note from encounter data."""
    pass

healthcare_agent = Agent(
    name="Clinical Documentation Assistant",
    instructions="""You assist with clinical documentation.
    - Generate clinical notes from encounter data
    - Suggest appropriate ICD codes
    - Check drug interactions
    - Ensure documentation completeness
    IMPORTANT: This is an assistant tool. All outputs must be reviewed by licensed clinicians.""",
    tools=[search_icd_codes, check_drug_interactions, generate_note],
)
```

## Legal

### Document Review Pattern

```python
@function_tool
async def extract_clauses(document: str, clause_type: str) -> str:
    """Extract specific clauses from legal document."""
    pass

@function_tool
async def flag_risks(document: str) -> str:
    """Identify potential legal risks in document."""
    pass

@function_tool
async def check_compliance(document: str, regulations: list) -> str:
    """Check document compliance with regulations."""
    pass

legal_agent = Agent(
    name="Legal Review Assistant",
    instructions="""You assist with legal document review.
    - Extract and summarize key clauses
    - Flag potential risks and issues
    - Check regulatory compliance
    - Suggest revisions
    IMPORTANT: This is an assistant tool. All legal decisions must be made by licensed attorneys.""",
    tools=[extract_clauses, flag_risks, check_compliance],
)
```

## HR and Recruiting

### Recruiting Assistant Pattern

```python
@function_tool
async def search_candidates(criteria: dict) -> str:
    """Search for candidates matching job criteria."""
    pass

@function_tool
async def screen_resume(resume: str, job_description: str) -> str:
    """Screen resume against job requirements."""
    pass

@function_tool
async def schedule_interview(candidate_id: str, interviewers: list) -> str:
    """Schedule interview with available times."""
    pass

recruiting_agent = Agent(
    name="Recruiting Assistant",
    instructions="""You help with recruiting and hiring.
    - Screen candidates against job requirements
    - Schedule interviews
    - Draft job descriptions
    - Manage candidate pipeline
    Be objective and focus on qualifications.""",
    tools=[search_candidates, screen_resume, schedule_interview],
)
```

## Personal Productivity

### Task Orchestration Pattern

```python
@function_tool
async def get_calendar(date_range: str) -> str:
    """Get calendar events for date range."""
    pass

@function_tool
async def create_task(title: str, due_date: str, priority: str) -> str:
    """Create task in task management system."""
    pass

@function_tool
async def send_email(to: str, subject: str, body: str) -> str:
    """Send email."""
    pass

productivity_agent = Agent(
    name="Productivity Assistant",
    instructions="""You help manage tasks, calendar, and communications.
    - Organize and prioritize tasks
    - Schedule meetings and events
    - Draft emails and messages
    - Set reminders
    - Suggest time management improvements
    Be proactive and anticipate needs.""",
    tools=[get_calendar, create_task, send_email, set_reminder],
)
```

## Enterprise Knowledge

### Knowledge Search Pattern

```python
@function_tool
async def search_documents(query: str, filters: dict) -> str:
    """Search across company documents."""
    pass

@function_tool
async def summarize_document(doc_id: str) -> str:
    """Summarize a document."""
    pass

@function_tool
async def find_experts(topic: str) -> str:
    """Find internal experts on a topic."""
    pass

knowledge_agent = Agent(
    name="Knowledge Assistant",
    instructions="""You help find and synthesize company knowledge.
    - Search across documents, wikis, and databases
    - Summarize relevant information
    - Connect people with expertise
    - Identify knowledge gaps
    Always cite sources.""",
    tools=[search_documents, summarize_document, find_experts],
)
```

## Product Management

### Product Planning Pattern

```python
@function_tool
async def analyze_feedback(source: str, date_range: str) -> str:
    """Analyze customer feedback from various sources."""
    pass

@function_tool
async def prioritize_features(features: list, criteria: dict) -> str:
    """Prioritize features based on criteria."""
    pass

@function_tool
async def generate_spec(feature: str, requirements: dict) -> str:
    """Generate product specification."""
    pass

product_agent = Agent(
    name="Product Management Assistant",
    instructions="""You help with product planning and management.
    - Analyze customer feedback and requests
    - Prioritize features and roadmap
    - Write product specifications
    - Track delivery and metrics
    Be user-focused and data-driven.""",
    tools=[analyze_feedback, prioritize_features, generate_spec],
)
```

## Accounting

### Bookkeeping Automation Pattern

```python
@function_tool
async def categorize_transaction(transaction: dict) -> str:
    """Categorize financial transaction."""
    pass

@function_tool
async def reconcile_account(account_id: str, statement: dict) -> str:
    """Reconcile account with bank statement."""
    pass

@function_tool
async def generate_report(report_type: str, period: str) -> str:
    """Generate financial report."""
    pass

accounting_agent = Agent(
    name="Accounting Assistant",
    instructions="""You help automate bookkeeping and accounting tasks.
    - Categorize transactions
    - Reconcile accounts
    - Generate financial reports
    - Flag anomalies
    - Ensure compliance
    Be accurate and detail-oriented.""",
    tools=[categorize_transaction, reconcile_account, generate_report],
)
```

## Architecture and Engineering

### Design Automation Pattern

```python
@function_tool
async def generate_design(specifications: dict) -> str:
    """Generate design from specifications."""
    pass

@function_tool
async def check_codes(design: dict, codes: list) -> str:
    """Check design against building codes."""
    pass

@function_tool
async def estimate_materials(design: dict) -> str:
    """Estimate materials needed for design."""
    pass

architecture_agent = Agent(
    name="Architecture Assistant",
    instructions="""You assist with architectural design and engineering.
    - Generate design options from requirements
    - Check code compliance
    - Estimate materials and costs
    - Manage BIM workflows
    IMPORTANT: All designs must be reviewed by licensed professionals.""",
    tools=[generate_design, check_codes, estimate_materials],
)
```

## ERP and Operations

### Operations Orchestration Pattern

```python
@function_tool
async def check_inventory_levels() -> str:
    """Check inventory across all locations."""
    pass

@function_tool
async def create_purchase_order(items: list, supplier: str) -> str:
    """Create purchase order."""
    pass

@function_tool
async def track_shipment(order_id: str) -> str:
    """Track shipment status."""
    pass

operations_agent = Agent(
    name="Operations Assistant",
    instructions="""You help manage business operations.
    - Monitor inventory levels
    - Manage procurement
    - Track shipments
    - Optimize workflows
    - Identify bottlenecks
    Be proactive and efficiency-focused.""",
    tools=[check_inventory_levels, create_purchase_order, track_shipment],
)
```

## Education and Training

### Learning Assistant Pattern

```python
@function_tool
async def assess_knowledge(topic: str, responses: list) -> str:
    """Assess learner's knowledge level."""
    pass

@function_tool
async def generate_curriculum(topic: str, level: str) -> str:
    """Generate personalized curriculum."""
    pass

@function_tool
async def create_assessment(topic: str, difficulty: str) -> str:
    """Create assessment questions."""
    pass

education_agent = Agent(
    name="Learning Assistant",
    instructions="""You help create and deliver personalized education.
    - Assess learner knowledge and skills
    - Generate personalized curricula
    - Create assessments
    - Provide explanations and feedback
    - Track learning progress
    Adapt to individual learning styles.""",
    tools=[assess_knowledge, generate_curriculum, create_assessment],
)
```

## Startup Consulting

### Business Planning Pattern

```python
@function_tool
async def analyze_market(industry: str, geography: str) -> str:
    """Analyze market size and trends."""
    pass

@function_tool
async def build_financial_model(assumptions: dict) -> str:
    """Build startup financial model."""
    pass

@function_tool
async def generate_business_plan(company_data: dict) -> str:
    """Generate business plan sections."""
    pass

startup_agent = Agent(
    name="Startup Consultant",
    instructions="""You help startups with business planning and strategy.
    - Analyze market opportunities
    - Build financial models and forecasts
    - Draft business plans
    - Suggest growth strategies
    - Identify risks and mitigation
    Be realistic but encouraging.""",
    model="gpt-4o",  # Use full model for strategic thinking
    tools=[analyze_market, build_financial_model, generate_business_plan],
)
```

## Common Patterns Across Industries

### Multi-Agent Coordination

```python
# Research → Analysis → Recommendation pattern
research_agent = Agent(name="Researcher", instructions="Gather information")
analysis_agent = Agent(name="Analyst", instructions="Analyze data")
advisor_agent = Agent(name="Advisor", instructions="Provide recommendations")

research_agent.handoffs = [analysis_agent]
analysis_agent.handoffs = [advisor_agent]
```

### Approval Workflows

```python
@function_tool
async def request_approval(action: str, details: dict) -> str:
    """Request human approval for action."""
    # Send to approval queue
    pass

agent = Agent(
    name="Assistant",
    instructions="""For sensitive operations:
    1. Explain what you plan to do
    2. Request approval using request_approval tool
    3. Wait for approval before proceeding
    4. Execute only if approved""",
    tools=[request_approval, execute_action],
)
```

### Audit Trail

```python
@function_tool
async def log_action(action: str, details: dict) -> str:
    """Log action for audit trail."""
    logger.log('agent_action', action=action, details=details)
    return "Action logged"

# Add to all agents that need audit trails
agent = Agent(
    name="Assistant",
    instructions="Log all significant actions using log_action tool.",
    tools=[log_action, *other_tools],
)
```

## Best Practices by Industry

### Regulated Industries (Healthcare, Finance, Legal)
- Always include disclaimers
- Require human review for critical decisions
- Maintain detailed audit trails
- Implement strict access controls
- Regular compliance reviews

### Customer-Facing (Support, Sales, Marketing)
- Prioritize response time
- Use streaming for better UX
- Implement sentiment analysis
- Track customer satisfaction
- Escalation paths for complex issues

### Data-Intensive (Analytics, Finance, Manufacturing)
- Use gpt-4o for complex analysis
- Implement caching for repeated queries
- Validate data quality
- Show calculations and reasoning
- Provide confidence levels

### Creative (Marketing, Product, Education)
- Use higher temperature for creativity
- Generate multiple options
- Incorporate feedback loops
- Balance creativity with constraints
- Test with diverse audiences
