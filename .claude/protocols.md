# Operational Protocols

Detailed protocols referenced from root `CLAUDE.md`.

## TIER 0: NON-NEGOTIABLE SAFETY PROTOCOLS

### Git Safety Protocol

**ABSOLUTE PROHIBITIONS:**
- NEVER use `git commit --no-verify` or `git commit -n`
- NEVER bypass pre-commit hooks
- NEVER suggest bypassing hooks to users

**Hook Failure Response:**
1. Read error messages thoroughly
2. Fix all reported issues (linting, formatting, types)
3. Stage fixes: `git add <fixed-files>`
4. Commit again (hooks run automatically)
5. NEVER use `--no-verify`

### No Deviation Protocol

**ABSOLUTE PROHIBITIONS:**
- NEVER switch to alternative solutions when encountering issues
- NEVER take "the easy way out" by choosing different technologies
- NEVER substitute requested components without explicit user approval
- MUST fix the EXACT issue encountered, not work around it

**When Encountering Issues:**
1. STOP - Do not proceed with alternatives
2. DIAGNOSE - Read error messages, identify root cause
3. FIX - Resolve the specific issue
4. VERIFY - Confirm original request now works
5. NEVER suggest alternatives unless genuinely impossible

## TIER 1: CRITICAL PROTOCOLS

### Protocol 1: Root Cause Analysis

**BEFORE implementing ANY fix:**
- Apply "5 Whys" methodology - trace to root cause
- Search entire codebase for similar patterns
- Fix ALL affected locations, not just discovery point
- Document: "Root cause: [X], affects: [Y], fixing: [Z]"

**NEVER:**
- Fix symptoms without understanding root cause
- Declare "Fixed!" without codebase-wide search
- Use try-catch to mask errors without fixing underlying problem

### Protocol 2: Scope Completeness

**BEFORE any batch operation:**
- Use comprehensive glob patterns to find ALL matching items
- List all items explicitly: "Found N items: [list]"
- Check multiple locations (root, subdirectories, dot-directories)
- Verify completeness: "Processed N/N items"

**NEVER:**
- Process only obvious items
- Assume first search captured everything
- Declare complete without explicit count verification

### Protocol 3: Verification Loop

**MANDATORY iteration pattern:**
1. Make change
2. Run tests/verification IMMEDIATELY
3. Analyze failures
4. IF failures exist: fix and GOTO step 1
5. ONLY declare complete when ALL tests pass

**Completion criteria (ALL must be true):**
- ✅ All tests passing
- ✅ All linters passing
- ✅ Verified in running environment
- ✅ No errors in logs

**ABSOLUTE PROHIBITIONS:**
- NEVER dismiss test failures as "pre-existing issues"
- NEVER dismiss linting errors as "pre-existing issues"
- NEVER ignore ANY failing test, regardless of origin
- MUST fix ALL failures before declaring complete

## TIER 1.5: MULTI-AGENT ORCHESTRATION AXIOMS

### Axiom 1: Dependency Verification
Test script preconditions before workflow integration.
- Verify scripts exist and are executable before spawning agents
- Test with sample input to confirm expected output format

### Axiom 2: Output Constraints
Subagent prompts must specify format and length limits.
- Include explicit output format (JSON schema, markdown structure)
- Specify max response length to prevent context overflow
- Define required vs optional fields

### Axiom 3: Right-Sized Tools
Use grep for targeted lookups; reserve agents for exploration.
- Use Grep/Glob for specific file/field lookups
- Reserve Task agents for open-ended exploration or multi-step analysis
- NEVER spawn agents for single-field extraction
- **Rationale:** 10x cost/latency difference

### Axiom 4: Completeness Gates
Check data completeness before launching verification agents.
- Pre-check data availability before spawning dependent agents
- Skip agent phases when preconditions already satisfied
- Log skip reasons for debugging

### Axiom 5: External State Respect
Accept externally-modified state as authoritative.
- Read state before modifying
- Preserve external modifications (timestamps, manual entries)
- NEVER overwrite state without merge logic

### Axiom 6: Attempt Over Assume
MCP operations should be attempted, not assumed blocked.
- Attempt at least one MCP call before declaring blocked
- Cache blocking status to avoid redundant attempts
- Log actual error for debugging

### Axiom 7: Single Writer
Only orchestrators modify shared state files.
- Subagents MUST return data, not write files
- Orchestrator MUST aggregate and write atomically

### Axiom 8: Atomic State
Use locking/CAS for concurrent state access.
- Read-modify-write as atomic operation
- Validate state hasn't changed since read
- Retry on conflict or fail explicitly

### Axiom 9: Fail Fast
Propagate systemic failures to skip redundant attempts.
- Detect pattern of failures (3+ same error type)
- Propagate to skip remaining similar attempts
- Log consolidated error, not repeated messages

### Axiom 10: Reuse Logic
Call existing scripts for calculations; don't reimplement.
- Search for existing scripts before implementing logic
- Call scripts via subprocess, not copy logic
- Use script output as authoritative source

## TIER 2: IMPORTANT PROTOCOLS

### Protocol 4: Design Consistency

**BEFORE implementing any UI:**
- Study 3-5 existing similar pages/components
- Extract patterns: colors, typography, components, layouts
- Reuse existing components (create new ONLY if no alternative)
- Compare against mockups if provided
- Document: "Based on [pages], using pattern: [X]"

**NEVER:**
- Use generic defaults or placeholder colors
- Deviate from mockups without explicit approval
- Create new components without checking existing ones

### Protocol 5: Requirements Completeness

**For EVERY feature, verify ALL layers:**
UI Fields → API Endpoint → Validation → Business Logic → Database Schema

**BEFORE declaring complete:**
- Verify each UI field has corresponding API parameter, validation rule, business logic handler, database column
- Test end-to-end with realistic data

**NEVER:**
- Implement UI without checking backend support
- Change data model without database migration
- Skip any layer in the stack

### Protocol 6: Infrastructure Management

**Service management rules:**
- Search for orchestration scripts: start.sh, launch.sh, stop.sh, docker-compose.yml
- NEVER start/stop individual services if orchestration exists
- Follow sequence: Stop ALL → Change → Start ALL → Verify
- Test complete cycle: stop → launch → verify → stop

**NEVER:**
- Start individual containers when orchestration exists
- Skip testing complete start/stop cycle
- Use outdated installation methods without validation

## TIER 3: STANDARD PROTOCOLS

### Protocol 7: Documentation Accuracy

**When creating documentation:**
- ONLY include information from actual project files
- Cite sources for every section
- Skip sections with no source material
- NEVER include generic tips not in project docs

**NEVER include:**
- "Common Development Tasks" unless in README
- Made-up architecture descriptions
- Commands that don't exist in package.json/Makefile
- Assumed best practices not documented

### Protocol 8: Batch Operations

**For large task sets:**
- Analyze conflicts (same file, same service, dependencies)
- Use batch size: 3-5 parallel tasks (ask user if unclear)
- Wait for entire batch completion before next batch
- IF service restart needed: complete batch first, THEN restart ALL services

**Progress tracking format:**
```
Total: N tasks
Completed: M tasks
Current batch: P tasks
Remaining: Q tasks
```

## TOOL SELECTION RULES

- MUST use `fd` instead of `find`
- MUST use `rg` (ripgrep) instead of `grep`

## WORKFLOW STANDARDS

### Pre-Task Requirements
- Get current system date before starting work
- Ask clarifying questions when requirements ambiguous (use AskUserQuestion tool)
- Aim for complete clarity before execution

### During Task Execution

**Information Accuracy:**
- NEVER assume or fabricate information
- Cite sources or explicitly state when unavailable

**Code Development:**
- NEVER assume code works without validation
- ALWAYS test with real inputs/outputs
- ALWAYS verify language/framework documentation
- NEVER create stub/mock tests except for: slow external APIs, databases
- NEVER create tests solely to meet coverage metrics

**Communication Style:**
- NEVER use flattery ("Great idea!", "Excellent!")
- ALWAYS provide honest, objective feedback

### Post-Task Requirements

**File Organization:**
- Artifacts → `./docs/artifacts/`
- Scripts → `./scripts/`
- Documentation → `./docs/`
- NEVER create artifacts in project root

**Change Tracking:**
- ALWAYS update `./CHANGELOG` before commits
- Format: Date + bulleted list of changes

## CONSOLIDATED VERIFICATION CHECKLIST

### Before Starting Any Work
- [ ] Searched for existing patterns/scripts/components?
- [ ] Listed ALL items in scope?
- [ ] Understood full stack impact (UI → API → DB)?
- [ ] Identified root cause (not just symptom)?
- [ ] Current date retrieved (if time-sensitive)?
- [ ] All assumptions clarified with user?

### Before Declaring Complete
- [ ] Ran ALL tests and they pass?
- [ ] All linters passing?
- [ ] Verified in running environment?
- [ ] No errors/warnings in logs?
- [ ] Fixed ALL related issues (searched codebase)?
- [ ] Updated ALL affected layers?
- [ ] Files organized per standards?
- [ ] CHANGELOG updated (if committing)?
- [ ] Pre-commit hooks will NOT be bypassed?
- [ ] Used correct tools (fd, rg)?
- [ ] No flattery or false validation in communication?

## META-PATTERN: THE FIVE COMMON MISTAKES

1. **Premature Completion:** Saying "Done!" without thorough verification
   - **Fix:** Always include verification results section

2. **Missing Systematic Inventory:** Processing obvious items, missing edge cases
   - **Fix:** Use glob patterns, list ALL items, verify count

3. **Insufficient Research:** Implementing without studying existing patterns
   - **Fix:** Study 3-5 examples first, extract patterns

4. **Incomplete Stack Analysis:** Fixing one layer, missing others
   - **Fix:** Trace through UI → API → DB, update ALL layers

5. **Not Following Established Patterns:** Creating new when patterns exist
   - **Fix:** Search for existing scripts/components/procedures first

## CRITICAL LESSONS (Story 4.1 - 2025-11-20)

**Multi-Agent Orchestration:**
- Phase-based waves prevent premature completion
- Parallel non-destructive, sequential destructive tasks maximize efficiency
- 9 agents across 4 iterations caught issues single-agent flow would miss

**Verification Loop Supremacy:**
- Agent 2A declared "complete" without tests - 39% failure rate discovered in Agent 3A review
- Iteration 2 fixed infrastructure (92.8% pass) - revealed REAL implementation bugs
- Iteration 3 fixed accuracy (100% pass) - ngram config wrong for semantic duplicates
- **Never trust "looks good" - run tests immediately after ANY change**

**Behavioral Testing Value:**
- Test failures revealed 40% recall (need 80%) - not test bug, implementation bug
- Root cause: `ngram_range=(1,2)` inappropriate for word reordering
- Fix: unigrams only, disable sublinear_tf, adjust threshold → 100% precision/recall

**Singleton Test Pollution:**
- CacheManager singleton caused cross-test pollution
- Required explicit `_reset()` method for test isolation

**Configuration Must Match Use Case:**
- Generic TF-IDF defaults failed semantic similarity
- Small test corpora need `min_df=1`, not `min_df=2`
- Tune parameters for actual data characteristics, not assumptions

## USAGE INSTRUCTIONS

### When to Reference Specific Protocols

- ANY task → No Deviation Protocol (Tier 0)
- Fixing bugs → Root Cause Analysis Protocol (Tier 1)
- Batch operations → Scope Completeness Protocol (Tier 1)
- After changes → Verification Loop Protocol (Tier 1)
- Multi-agent workflows → Orchestration Axioms (Tier 1.5)
- UI work → Design Consistency Protocol (Tier 2)
- Feature development → Requirements Completeness Protocol (Tier 2)
- Service management → Infrastructure Management Protocol (Tier 2)
- Git commits → Git Safety Protocol (Tier 0)

### Integration Approach

- Tier 0 protocols: ALWAYS enforced, no exceptions
- Tier 1 protocols: ALWAYS apply before/during/after work
- Tier 1.5 axioms: Apply for multi-agent and subagent coordination
- Tier 2 protocols: Apply when context matches
- Tier 3 protocols: Apply as needed for specific scenarios

### Solution Pattern

**Before starting → Research & Inventory**
**After finishing → Verify & Iterate**
