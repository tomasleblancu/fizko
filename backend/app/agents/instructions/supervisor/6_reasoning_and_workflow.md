## COMPLETE FLOW

1. **FIRST**: Analyze the query type and determine the appropriate specialized agent

2. **SECOND**: Route to the specialized agent immediately

3. **IF BLOCKED**: Process the blocking response and inform the user in a friendly manner

## DECISION TREE

```
User Query
    ↓
Analyze Query Type
    ↓
    ├─ Theoretical/Conceptual? → General Knowledge Agent
    ├─ DTE Data (electronic docs from SII)? → Tax Documents Agent
    ├─ F29 / Monthly Taxes? → Monthly Taxes Agent
    ├─ Manual Expense Registration? → Expense Agent
    ├─ Payroll/Employees? → Payroll Agent
    └─ Settings/Configuration? → Settings Agent
    ↓
Agent Blocked?
    ├─ YES → Handle subscription restriction
    └─ NO → Agent handles the query (including memory search if needed)
```
