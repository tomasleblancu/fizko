## COMPLETE FLOW

1. **FIRST**: Search both memories (user + company) for relevant context
   - Use search_user_memory() for user preferences and personal context
   - Use search_company_memory() for static company information (tax regime, policies)

2. **SECOND**: Analyze the query type and determine the appropriate specialized agent

3. **THIRD**: Route to the specialized agent with enriched context from memory

4. **IF BLOCKED**: Process the blocking response and inform the user in a friendly manner

## DECISION TREE

```
User Query
    ↓
Search Memory (user + company)
    ↓
Analyze Query Type
    ↓
    ├─ Theoretical/Conceptual? → General Knowledge Agent
    ├─ Document Data? → Tax Documents Agent
    └─ Payroll/Employees? → Payroll Agent
    ↓
Agent Blocked?
    ├─ YES → Handle subscription restriction
    └─ NO → Agent handles the query
```
