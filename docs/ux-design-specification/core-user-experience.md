# Core User Experience

### Defining Experience

The core user experience centers on **deal sheet review and go/no-go decision making**. The system's job is to transform 50+ weekly listings into a prioritized shortlist of 3-5 tour-worthy properties, with each property's quality and risks immediately apparent.

**Core Loop:**
1. Batch Analysis (background, 30+ minutes)
2. Deal Sheet Review (mobile, <2 minutes per property)
3. Tour Decision (instant, based on tier + warnings)
4. Physical Visit (with auto-generated checklist)
5. Offer or Pass (with confidence)

**Critical Interaction:** The deal sheet must be scannable in under 2 minutes on a 5-inch mobile screen, with tier badge, kill-switch verdict, and top 3 warnings visible above the fold.

### Platform Strategy

**Primary Platforms (MVP):**
- **CLI**: Batch analysis, pipeline control, configuration management
- **Mobile HTML**: Deal sheet review during property tours (responsive, offline-capable)

**Secondary Platforms (Post-MVP):**
- **Desktop Browser**: Visualization deep dives, comparison views
- **Config Wizard UI**: Guided scoring weight adjustment

**Platform Requirements:**
- Touch-first design for deal sheets (tap targets ≥44px)
- Offline capability for property tour scenarios
- High contrast for outdoor readability
- Keyboard-first for CLI operations

### Effortless Interactions

**Zero-effort interactions:**
- Kill-switch verdict (glanceable badge: 🟢 PASS / 🔴 FAIL / 🟡 WARNING)
- Tier classification (badge: 🦄 Unicorn / 🥊 Contender / ⏭️ Pass)
- Pipeline resume (single `--resume` flag, automatic state detection)
- Phase progression (automatic with prerequisite validation)

**Automatic behaviors:**
- State checkpointing after each successful property
- Error recovery suggestions based on failure type
- Score delta calculation when weights change
- Progress updates every ≤30 seconds during long runs

### Critical Success Moments

| Moment | User Feeling | Design Goal |
|--------|--------------|-------------|
| First batch results | "This works — I get it immediately" | Clear tier badges, instant comprehension |
| Score deep dive | "I trust this — I can see the evidence" | Every score traceable to source data |
| Kill-switch save | "This saved me from a mistake" | Prominent warning with consequence |
| Comparison view | "This is better than Zillow scrolling" | 60-70% elimination visible |
| Offer submission | "I'm confident — no nagging doubts" | Complete risk inventory reviewed |

**Make-or-break flows:**
1. First batch run — must be immediately understandable
2. Mobile deal sheet — must be readable in tour context
3. Pipeline recovery — must preserve all completed work

### Experience Principles

1. **Confidence over completeness**: Show certainty levels; don't hide uncertainty behind false precision. Display High/Medium/Low confidence tags.

2. **Consequences over flags**: Every warning answers "so what?" in terms of dollars, quality of life, or resale impact. Include recommended actions.

3. **Glanceability over density**: Critical info (tier, verdict, top warnings) visible in 5 seconds. Full detail available on demand through progressive disclosure.

4. **Recovery over prevention**: Expect pipeline failures; make resume seamless. Never require re-running completed work.

5. **Transparency over magic**: User can always trace any score, verdict, or warning back to source data and calculation logic.
