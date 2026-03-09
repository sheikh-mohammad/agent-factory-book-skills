# Industry-Specific ChatKit Patterns

Implementation patterns for 17+ industry domains using ChatKit framework.

---

## Pattern Selection by Industry

| Industry | Primary Pattern | Key Features | Tools Needed |
|----------|----------------|--------------|--------------|
| Manufacturing | Tool-Augmented | Equipment monitoring, maintenance scheduling | IoT APIs, ERP integration |
| Personal Productivity | Tool-Augmented | Task management, calendar sync | Calendar APIs, task systems |
| Enterprise Knowledge | Knowledge Assistant | Document search, policy retrieval | Vector stores, RAG |
| Sales | Hybrid | CRM integration, prospect research | CRM APIs, web search |
| Marketing | Tool-Augmented | Content generation, campaign planning | Content APIs, analytics |
| Customer Support | Hybrid | Ticket management, knowledge base | Ticketing APIs, vector stores |
| Product Management | Knowledge Assistant | Spec writing, roadmap tracking | Document stores, project APIs |
| Finance | Tool-Augmented | Financial analysis, modeling | Financial APIs, calculation tools |
| Accounting | Tool-Augmented | Bookkeeping, reconciliation | Accounting APIs, data validation |
| Legal | Knowledge Assistant | Document review, compliance | Vector stores, contract databases |
| Data Analysis | Tool-Augmented | Query generation, visualization | Database APIs, analytics tools |
| Healthcare | Hybrid | Clinical documentation, coding | EHR APIs, medical knowledge bases |
| HR & Recruiting | Tool-Augmented | Candidate screening, onboarding | ATS APIs, HR systems |
| Architecture & Engineering | Tool-Augmented | Design generation, BIM workflows | CAD APIs, design tools |
| ERP & Operations | Tool-Augmented | Procurement, inventory management | ERP APIs, supply chain systems |
| Education & Training | Knowledge Assistant | Curriculum creation, assessments | Learning content, assessment tools |
| Startup Consulting | Knowledge Assistant | Business planning, forecasting | Business templates, market data |

---

## 1. Manufacturing Domain Intelligence

### Use Cases
- Equipment monitoring and predictive maintenance
- Production scheduling optimization
- Quality control issue tracking
- Supply chain coordination

### Architecture: Tool-Augmented Agent

### Custom Tools

```python
# app/tools/manufacturing.py

def check_equipment_status(equipment_id: str) -> dict:
    """Query IoT sensors for equipment status."""
    # Integration with IoT platform
    return {
        "equipment_id": equipment_id,
        "status": "operational",
        "temperature": 72.5,
        "vibration": "normal",
        "next_maintenance": "2026-03-15"
    }

def schedule_maintenance(equipment_id: str, date: str, priority: str) -> dict:
    """Schedule maintenance in ERP system."""
    # Integration with ERP
    return {
        "maintenance_id": "MNT-12345",
        "scheduled_date": date,
        "priority": priority,
        "technician_assigned": "John Doe"
    }

def query_production_metrics(line_id: str, metric: str) -> dict:
    """Get production line metrics."""
    # Integration with MES (Manufacturing Execution System)
    return {
        "line_id": line_id,
        "metric": metric,
        "value": 95.2,
        "unit": "percent",
        "trend": "stable"
    }
```

### Agent Configuration

```python
manufacturing_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_equipment_status",
            "description": "Check real-time status of manufacturing equipment",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string", "description": "Equipment identifier"}
                },
                "required": ["equipment_id"]
            }
        }
    },
    # ... other tools
]

# System prompt
manufacturing_prompt = """You are a manufacturing intelligence assistant.
Help operators monitor equipment, schedule maintenance, and optimize production.
Always prioritize safety and provide data-driven recommendations."""
```

---

## 2. Personal Productivity

### Use Cases
- Task orchestration across multiple systems
- Calendar management and scheduling
- Email drafting and prioritization
- Daily workflow automation

### Architecture: Tool-Augmented Agent

### Custom Tools

```python
# app/tools/productivity.py

def create_task(title: str, due_date: str, priority: str, project: str) -> dict:
    """Create task in task management system."""
    # Integration with Todoist, Asana, etc.
    return {
        "task_id": "TSK-789",
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "project": project
    }

def check_calendar(date: str) -> dict:
    """Check calendar availability."""
    # Integration with Google Calendar, Outlook
    return {
        "date": date,
        "events": [
            {"time": "09:00", "title": "Team standup", "duration": 30},
            {"time": "14:00", "title": "Client meeting", "duration": 60}
        ],
        "free_slots": ["10:00-12:00", "15:00-17:00"]
    }

def schedule_meeting(title: str, attendees: list, duration: int, preferred_time: str) -> dict:
    """Schedule meeting with attendees."""
    # Integration with calendar API
    return {
        "meeting_id": "MTG-456",
        "scheduled_time": "2026-03-10 10:00",
        "attendees_confirmed": attendees,
        "calendar_link": "https://calendar.example.com/mtg-456"
    }
```

---

## 3. Enterprise Knowledge

### Use Cases
- Search across company documentation
- Policy and procedure retrieval
- Onboarding knowledge base
- Cross-department information synthesis

### Architecture: Knowledge Assistant

### Vector Store Setup

```python
# Create vector store with company documents
vector_store = client.beta.vector_stores.create(
    name="Enterprise Knowledge Base"
)

# Upload documents
document_types = [
    "policies/*.pdf",
    "procedures/*.docx",
    "handbooks/*.pdf",
    "technical-docs/*.md"
]

# Configure assistant with file search
assistant = client.beta.assistants.create(
    name="Enterprise Knowledge Assistant",
    instructions="""You are an enterprise knowledge assistant.
    Search company documents to answer employee questions.
    Always cite sources and indicate confidence level.""",
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [vector_store.id]
        }
    },
    model="gpt-4"
)
```

---

## 4. Sales Intelligence

### Use Cases
- Prospect research and qualification
- Deal preparation and strategy
- Pipeline management automation
- Competitive intelligence

### Architecture: Hybrid (Tools + Knowledge)

### Custom Tools

```python
# app/tools/sales.py

def search_prospect(company_name: str) -> dict:
    """Research prospect company information."""
    # Integration with LinkedIn, Clearbit, etc.
    return {
        "company": company_name,
        "industry": "Technology",
        "size": "500-1000 employees",
        "revenue": "$50M-$100M",
        "key_contacts": [
            {"name": "Jane Smith", "title": "VP Sales", "linkedin": "..."}
        ]
    }

def update_crm_deal(deal_id: str, field: str, value: str) -> dict:
    """Update deal in CRM."""
    # Integration with Salesforce, HubSpot
    return {
        "deal_id": deal_id,
        "updated_field": field,
        "new_value": value,
        "last_modified": "2026-03-09T10:30:00Z"
    }

def get_deal_insights(deal_id: str) -> dict:
    """Get AI insights for deal strategy."""
    # Integration with CRM + AI analysis
    return {
        "deal_id": deal_id,
        "stage": "Proposal",
        "probability": 65,
        "next_steps": ["Schedule demo", "Send pricing"],
        "risks": ["Budget concerns", "Competitor evaluation"]
    }
```

### Knowledge Base

Include sales playbooks, competitive intelligence, product information in vector store.

---

## 5. Marketing Automation

### Use Cases
- Content drafting and ideation
- Campaign planning and execution
- Multi-channel launch coordination
- Performance analysis

### Architecture: Tool-Augmented Agent

### Custom Tools

```python
# app/tools/marketing.py

def generate_content_brief(topic: str, audience: str, format: str) -> dict:
    """Generate content brief for writers."""
    return {
        "topic": topic,
        "target_audience": audience,
        "format": format,
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "seo_keywords": ["keyword1", "keyword2"],
        "tone": "professional yet approachable"
    }

def schedule_social_post(platform: str, content: str, schedule_time: str) -> dict:
    """Schedule social media post."""
    # Integration with Buffer, Hootsuite
    return {
        "post_id": "POST-123",
        "platform": platform,
        "scheduled_for": schedule_time,
        "status": "scheduled"
    }

def analyze_campaign_performance(campaign_id: str) -> dict:
    """Get campaign analytics."""
    # Integration with Google Analytics, marketing platforms
    return {
        "campaign_id": campaign_id,
        "impressions": 50000,
        "clicks": 2500,
        "conversions": 125,
        "ctr": 5.0,
        "conversion_rate": 5.0
    }
```

---

## 6. Customer Support

### Use Cases
- Issue triage and categorization
- Response drafting with knowledge base
- Intelligent escalation
- Ticket management automation

### Architecture: Hybrid (Tools + Knowledge)

### Custom Tools

```python
# app/tools/support.py

def create_ticket(title: str, description: str, priority: str, category: str) -> dict:
    """Create support ticket."""
    # Integration with Zendesk, Freshdesk
    return {
        "ticket_id": "TKT-9876",
        "title": title,
        "priority": priority,
        "category": category,
        "assigned_to": "Support Team",
        "status": "open"
    }

def search_similar_tickets(description: str) -> list:
    """Find similar resolved tickets."""
    # Vector search in ticket history
    return [
        {"ticket_id": "TKT-1234", "resolution": "Reset password", "similarity": 0.92},
        {"ticket_id": "TKT-5678", "resolution": "Account unlock", "similarity": 0.85}
    ]

def escalate_ticket(ticket_id: str, reason: str, escalate_to: str) -> dict:
    """Escalate ticket to specialist."""
    return {
        "ticket_id": ticket_id,
        "escalated_to": escalate_to,
        "reason": reason,
        "escalation_time": "2026-03-09T10:45:00Z"
    }
```

### Knowledge Base

Include support documentation, troubleshooting guides, product manuals in vector store.

---

## 7. Product Management

### Use Cases
- Product spec writing
- Roadmap prioritization
- Feature tracking and delivery
- Stakeholder communication

### Architecture: Knowledge Assistant + Tools

### Custom Tools

```python
# app/tools/product.py

def create_feature_spec(feature_name: str, description: str, priority: str) -> dict:
    """Create feature specification."""
    return {
        "feature_id": "FEAT-456",
        "name": feature_name,
        "description": description,
        "priority": priority,
        "status": "draft"
    }

def update_roadmap(feature_id: str, quarter: str, status: str) -> dict:
    """Update product roadmap."""
    # Integration with Jira, Productboard
    return {
        "feature_id": feature_id,
        "planned_quarter": quarter,
        "status": status,
        "dependencies": []
    }
```

---

## 8. Finance & Accounting

### Use Cases
- Financial analysis and modeling
- Bookkeeping automation
- Reconciliation workflows
- Key metrics monitoring

### Architecture: Tool-Augmented Agent

### Custom Tools

```python
# app/tools/finance.py

def query_financial_data(metric: str, period: str) -> dict:
    """Query financial metrics."""
    # Integration with QuickBooks, Xero, NetSuite
    return {
        "metric": metric,
        "period": period,
        "value": 1250000,
        "currency": "USD",
        "change_percent": 12.5
    }

def create_journal_entry(account: str, debit: float, credit: float, description: str) -> dict:
    """Create accounting journal entry."""
    return {
        "entry_id": "JE-789",
        "account": account,
        "debit": debit,
        "credit": credit,
        "description": description,
        "date": "2026-03-09"
    }

def reconcile_transactions(account: str, start_date: str, end_date: str) -> dict:
    """Reconcile bank transactions."""
    return {
        "account": account,
        "period": f"{start_date} to {end_date}",
        "matched": 145,
        "unmatched": 3,
        "discrepancies": []
    }
```

---

## 9. Legal & Compliance

### Use Cases
- Document review and analysis
- Risk flagging
- Compliance tracking
- Contract management

### Architecture: Knowledge Assistant

### Vector Store Setup

```python
# Legal knowledge base
legal_vector_store = client.beta.vector_stores.create(
    name="Legal Knowledge Base"
)

# Upload legal documents
document_categories = [
    "contracts/*.pdf",
    "policies/*.docx",
    "regulations/*.pdf",
    "case-law/*.pdf"
]

# Configure with strict citation requirements
legal_assistant = client.beta.assistants.create(
    name="Legal Assistant",
    instructions="""You are a legal research assistant.
    Review documents for risks and compliance issues.
    ALWAYS cite specific clauses and sections.
    Flag any ambiguous or concerning language.
    Recommend consulting human legal counsel for final decisions.""",
    tools=[{"type": "file_search"}],
    model="gpt-4"
)
```

---

## 10. Data Analysis

### Use Cases
- SQL query generation
- Data visualization recommendations
- Dataset interpretation
- Insight extraction

### Architecture: Tool-Augmented Agent

### Custom Tools

```python
# app/tools/data_analysis.py

def execute_sql_query(query: str, database: str) -> dict:
    """Execute SQL query safely."""
    # Validate and execute query
    return {
        "query": query,
        "rows_returned": 150,
        "columns": ["id", "name", "value"],
        "sample_data": [...]
    }

def generate_visualization(data: dict, chart_type: str) -> dict:
    """Generate data visualization."""
    # Integration with plotting libraries
    return {
        "chart_type": chart_type,
        "chart_url": "https://charts.example.com/abc123",
        "insights": ["Trend increasing", "Outlier detected"]
    }
```

---

## 11. Healthcare

### Use Cases
- Clinical documentation automation
- Medical coding assistance
- Patient workflow coordination
- Compliance checking

### Architecture: Hybrid (Tools + Knowledge)

### Custom Tools

```python
# app/tools/healthcare.py

def lookup_icd_code(diagnosis: str) -> dict:
    """Look up ICD-10 diagnosis code."""
    return {
        "diagnosis": diagnosis,
        "icd10_code": "E11.9",
        "description": "Type 2 diabetes mellitus without complications"
    }

def check_drug_interactions(medications: list) -> dict:
    """Check for drug interactions."""
    return {
        "medications": medications,
        "interactions": [],
        "warnings": ["Monitor blood pressure"],
        "safe": True
    }
```

**IMPORTANT**: Healthcare applications require HIPAA compliance, PHI protection, and medical professional oversight.

---

## 12-17. Additional Industries

### HR & Recruiting
**Tools**: ATS integration, candidate screening, interview scheduling
**Pattern**: Tool-Augmented Agent

### Architecture & Engineering
**Tools**: CAD API integration, BIM workflows, design generation
**Pattern**: Tool-Augmented Agent

### ERP & Operations
**Tools**: Procurement APIs, inventory management, supply chain
**Pattern**: Tool-Augmented Agent

### Education & Training
**Tools**: Curriculum templates, assessment generation, learning paths
**Pattern**: Knowledge Assistant

### Startup Consulting
**Tools**: Business plan templates, financial modeling, market research
**Pattern**: Knowledge Assistant + Tools

---

## Implementation Checklist by Industry

- [ ] Identify primary use case and architecture pattern
- [ ] List required external integrations (APIs, databases)
- [ ] Design custom tools for domain-specific actions
- [ ] Prepare knowledge base documents (if using vector stores)
- [ ] Configure agent system prompt with domain expertise
- [ ] Implement error handling for industry-specific failures
- [ ] Add compliance and security measures (especially healthcare, finance, legal)
- [ ] Test with realistic industry scenarios
- [ ] Document industry-specific configuration

---

## Security Considerations by Industry

| Industry | Key Security Requirements |
|----------|--------------------------|
| Healthcare | HIPAA compliance, PHI encryption, audit logging |
| Finance | PCI DSS, SOC 2, data encryption, access controls |
| Legal | Attorney-client privilege, document confidentiality |
| Manufacturing | IP protection, operational security |
| All Industries | API key security, input validation, rate limiting |

See `security.md` for detailed security implementation patterns.
