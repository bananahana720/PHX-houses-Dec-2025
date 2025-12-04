# Appendix A: Action Items

### Immediate (Before Development Continues)

1. **Update constants.py** - Fix assertion to match 605-point scoring:
   ```python
   SCORE_SECTION_A_TOTAL = 250
   SCORE_SECTION_B_TOTAL = 175
   SCORE_SECTION_C_TOTAL = 180
   MAX_POSSIBLE_SCORE = 605
   TIER_UNICORN_MIN = 484
   TIER_CONTENDER_MIN = 363
   ```

2. **Add SqftKillSwitch** - Implement >1800 sqft HARD criterion

3. **Update LotSizeKillSwitch** - Change from range (7k-15k) to minimum (>8000)

4. **Update SewerKillSwitch** - Change from SOFT (2.5 severity) to HARD (instant fail)

5. **Update GarageKillSwitch** - Clarify as indoor garage required

### Short-Term (Week 1-2)

6. **Validate prerequisite script** - Ensure exit codes match documentation

7. **Test crash recovery** - Verify resume works after simulated failures

8. **Document API rate limits** - Add monitoring for external APIs

### Medium-Term (Post-MVP)

9. **Add flood zone kill-switch** - When FEMA integration complete

10. **Consider soft severity** - For non-critical preferences

---

**Document Version:** 2.0
**Generated:** 2025-12-03
**Author:** Winston - System Architect
**Status:** Complete - Ready for Implementation
