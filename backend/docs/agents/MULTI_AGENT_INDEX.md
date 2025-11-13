# FIZKO MULTI-AGENT SYSTEM - DOCUMENTATION INDEX

Complete analysis and documentation of the Fizko multi-agent system architecture.

## Quick Navigation

### For Quick Understanding (Start Here)
- **[MULTI_AGENT_QUICK_REFERENCE.md](MULTI_AGENT_QUICK_REFERENCE.md)** (7 KB)
  - System overview
  - Core components summary
  - Extension points
  - Critical issues
  - Quick patterns table

### For Visual Learning
- **[MULTI_AGENT_DIAGRAMS.md](MULTI_AGENT_DIAGRAMS.md)** (15 KB)
  - System architecture flowchart
  - Agent hierarchy tree
  - Component relationships
  - Data flow diagrams
  - Execution sequence
  - Cache architecture

### For Deep Dive
- **[MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md)** (35 KB)
  - Complete 15-section analysis
  - Detailed explanations
  - Code examples
  - Design patterns
  - Extension guides
  - Issues and improvements

---

## Document Breakdown

### 1. MULTI_AGENT_QUICK_REFERENCE.md
**Target Audience:** Developers, product managers, quick understanding

**Contains:**
- System overview (1 page)
- 6 core components with sub-details
- Agent definitions (table)
- Tools system organization
- UI tools system architecture
- Context & state management
- Security multi-layer approach
- Key data flows (3 main flows)
- Configuration files and constants
- Design patterns (table)
- Extension points (3 scenarios)
- Critical issues (3 critical, 3 improvements)
- Performance benchmarks

**Best for:**
- Getting up to speed quickly
- Finding key files
- Understanding extension points
- Identifying issues to fix

### 2. MULTI_AGENT_DIAGRAMS.md
**Target Audience:** Architects, visual learners, code reviewers

**Contains:**
- System architecture overview (ASCII art)
- Agent hierarchy tree
- Orchestration component relationships
- UI tools data flow
- Company info loading pipeline
- Subscription validation flow
- Message execution sequence
- Tool execution architecture
- Guardrails execution (parallel)
- Cache architecture (3 types)

**Best for:**
- Understanding data flows visually
- Explaining to stakeholders
- Code review discussions
- Architectural decisions

### 3. MULTI_AGENT_ARCHITECTURE.md
**Target Audience:** Implementation teams, maintainers, architects

**Contains (15 sections):**
1. **Executive Summary** - High-level overview
2. **Core Architecture** - High-level flow, lifecycle, patterns
3. **Orchestration System** - 6 key components explained
4. **Agent Definitions** - Supervisor + 7 specialists
5. **Tools System** - Organization, function tools, widgets, memory
6. **UI Tools System** - Purpose, interfaces, registry, current tools
7. **Context & State** - FizkoContext, company info, attachment stores
8. **Security & Guardrails** - Multi-layer auth, guardrails, RLS
9. **Multi-Channel Support** - ChatKit vs WhatsApp
10. **Execution Flow** - Detailed request-response cycle
11. **Data Flows** - Company info, tools, UI tools
12. **Configuration** - Models, scopes, instructions
13. **Design Patterns** - Identified patterns and principles
14. **Issues & Improvements** - Critical bugs, improvements, testing gaps
15. **Extension Points** - How to add agents, tools, UI tools, channels
16. **Summary Table** - Quick component reference

**Best for:**
- Complete understanding
- Implementation details
- Adding new features
- Fixing bugs
- Performance optimization

---

## Key Sections Summary

### Core Concepts Explained

#### 1. HandoffsManager (Entry Point)
- Global singleton that caches orchestrators per thread_id
- File: `backend/app/agents/orchestration/handoffs_manager.py`
- Entry method: `get_supervisor_agent(thread_id, db, company_id, ...)`
- Key insight: Caching maintains agent state across requests

#### 2. MultiAgentOrchestrator (Coordinator)
- Creates supervisor + available agents
- Configures handoffs between them
- File: `backend/app/agents/orchestration/multi_agent_orchestrator.py`
- Works with AgentFactory, HandoffFactory, SubscriptionValidator

#### 3. Subscription Validation (Access Control)
- 3-layer system: orchestration, handoff, agent
- Maps subscription tier to available agents
- File: `backend/app/agents/orchestration/subscription_validator.py`
- Only creates agents user has access to

#### 4. UI Tools System (Context Enrichment)
- Pre-fetches component-specific data
- Injects context before agent execution
- Registry pattern with auto-discovery
- 12+ tools for various components

#### 5. Company Info Loading (Auto Context)
- Automatic at context creation
- 30-minute TTL cache
- Formatted as XML for agent
- File: `backend/app/agents/core/context_loader.py`

---

## Quick Reference Tables

### Agent Models
| Agent | Model | Role |
|-------|-------|------|
| Supervisor | gpt-4o-mini | Fast router |
| Specialists (7) | gpt-4.1-mini | Domain experts |

### 7 Specialized Agents
| Name | Purpose | File |
|------|---------|------|
| General Knowledge | Tax concepts, theory | `general_knowledge_agent.py` |
| Tax Documents | Real data queries | `tax_documents_agent.py` |
| Monthly Taxes | F29 expertise | `monthly_taxes_agent.py` |
| Payroll | Labor law, employees | `payroll_agent.py` |
| Settings | Preferences, notifications | `settings_agent.py` |
| Expense | Manual expenses | `expense_agent.py` |
| Feedback | Bug reports | `feedback_agent.py` |

### Subscription Tiers
| Tier | Available Agents | Use Case |
|------|-----------------|----------|
| Free | [] | General knowledge only |
| Basic | tax_docs, payroll, settings | Small business |
| Pro | All agents | Enterprise |

### Design Patterns Used
| Pattern | Location | Count |
|---------|----------|-------|
| Singleton | HandoffsManager, UIToolRegistry | 2 |
| Factory | AgentFactory, HandoffFactory | 2 |
| Registry | UIToolRegistry | 1 |
| Decorator | @function_tool, @ui_tool_registry.register | 2 |
| Lazy Init | HandoffsManager.get_orchestrator() | 1 |
| DI | Throughout | Multiple |

---

## Common Tasks

### I need to...

**Understand the system**
1. Read MULTI_AGENT_QUICK_REFERENCE.md (5 min)
2. View MULTI_AGENT_DIAGRAMS.md (10 min)
3. Skim MULTI_AGENT_ARCHITECTURE.md sections 1-3 (15 min)

**Add a new agent**
→ See MULTI_AGENT_ARCHITECTURE.md section 14.1

**Add a new tool**
→ See MULTI_AGENT_ARCHITECTURE.md section 14.2

**Add a new UI tool**
→ See MULTI_AGENT_ARCHITECTURE.md section 14.3

**Fix a bug**
→ See MULTI_AGENT_ARCHITECTURE.md sections 13.1 (issues)

**Improve performance**
→ See MULTI_AGENT_ARCHITECTURE.md sections 13.2 (improvements)

**Debug agent execution**
→ See MULTI_AGENT_ARCHITECTURE.md sections 9-11 (execution flows)

**Understand subscription logic**
→ See MULTI_AGENT_ARCHITECTURE.md section 7.1 or diagrams.md

---

## File Locations Reference

### Orchestration
- `backend/app/agents/orchestration/handoffs_manager.py` - Entry point
- `backend/app/agents/orchestration/multi_agent_orchestrator.py` - Coordinator
- `backend/app/agents/orchestration/agent_factory.py` - Agent creation
- `backend/app/agents/orchestration/handoff_factory.py` - Handoff creation
- `backend/app/agents/orchestration/subscription_validator.py` - Access control
- `backend/app/agents/orchestration/session_manager.py` - Active agent tracking

### Agent Definitions
- `backend/app/agents/supervisor_agent.py` - Entry point agent
- `backend/app/agents/specialized/general_knowledge_agent.py`
- `backend/app/agents/specialized/tax_documents_agent.py`
- `backend/app/agents/specialized/monthly_taxes_agent.py`
- `backend/app/agents/specialized/payroll_agent.py`
- `backend/app/agents/specialized/settings_agent.py`
- `backend/app/agents/specialized/expense_agent.py`
- `backend/app/agents/specialized/feedback_agent.py`

### Tools
- `backend/app/agents/tools/tax/` - Tax tools
- `backend/app/agents/tools/payroll/` - Payroll tools
- `backend/app/agents/tools/widgets/` - Widget tools
- `backend/app/agents/tools/memory/` - Memory tools
- `backend/app/agents/tools/settings/` - Settings tools

### UI Tools
- `backend/app/agents/ui_tools/core/base.py` - Base interface
- `backend/app/agents/ui_tools/core/dispatcher.py` - Router
- `backend/app/agents/ui_tools/core/registry.py` - Registry
- `backend/app/agents/ui_tools/tools/` - Tool implementations

### Context & State
- `backend/app/agents/core/context.py` - FizkoContext
- `backend/app/agents/core/context_loader.py` - Company info loading
- `backend/app/agents/core/memory_attachment_store.py` - Dev storage
- `backend/app/agents/core/supabase_attachment_store.py` - Prod storage

### Security
- `backend/app/agents/guardrails/` - Guardrails system
- `backend/app/agents/guardrails/implementations/` - Specific guardrails

### Configuration
- `backend/app/config/constants.py` - Models, timeouts
- `backend/app/agents/config/scopes.py` - Subscription scopes
- `backend/app/agents/instructions/` - Agent instructions (modular)

---

## Architecture Checklist

- [ ] Understand HandoffsManager caching strategy
- [ ] Understand MultiAgentOrchestrator initialization
- [ ] Understand subscription validation layers
- [ ] Understand how company info is auto-loaded
- [ ] Understand UI tool dispatcher flow
- [ ] Understand tool execution with FizkoContext
- [ ] Understand agent handoff flow
- [ ] Understand guardrails execution
- [ ] Understand multi-channel support
- [ ] Know all 7 specialized agents
- [ ] Know how to add a new agent
- [ ] Know how to add a new tool
- [ ] Know how to add a new UI tool
- [ ] Know critical issues to fix
- [ ] Know improvement opportunities

---

## Statistics

**Total Lines of Analysis:** 1,200+
**Total Documentation Files:** 3
**Code Examples Included:** 20+
**Diagrams:** 10
**Design Patterns Identified:** 8
**Critical Issues Identified:** 3
**Improvement Opportunities:** 5+
**Agents:** 8 (1 supervisor + 7 specialized)
**Agent Tools:** 50+ (tax, payroll, widgets, memory, etc.)
**UI Tools:** 12+
**Orchestration Components:** 6
**Subscription Tiers:** 3

---

## Version Info

- **Analysis Date:** November 13, 2025
- **Codebase Branch:** staging
- **Agents SDK:** OpenAI Agents SDK (ChatKit-based)
- **Python Version:** 3.11+
- **Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)

---

## How to Use These Documents

1. **For Code Review:** Use diagrams + architecture doc
2. **For Onboarding:** Start with quick reference + diagrams
3. **For Implementation:** Use architecture doc sections 14.x
4. **For Bug Fixes:** Use issues section (13.1)
5. **For Performance:** Use improvements section (13.2)
6. **For Architecture Discussion:** Use diagrams + patterns section

---

**Created with comprehensive code analysis and architecture review.**
