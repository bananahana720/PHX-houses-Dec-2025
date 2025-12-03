# BMAD Agent Voice Mappings

Configure unique voices for each BMAD agent. When a BMAD agent activates, they'll speak with their assigned voice.

## Voice Mappings

| Agent ID | Agent Name | Intro | ElevenLabs Voice | Piper Voice | Personality |
|----------|------------|-------|------------------|-------------|-------------|
| pm | Product Manager | PM here | Josh | en_US-ryan-high | professional |
| dev | Developer | Dev ready | Bella | en_US-amy-medium | normal |
| analyst | Business Analyst | Analyst reporting | Rachel | en_US-kristin-medium | professional |
| architect | Architect | Architect online | Arnold | en_GB-alan-medium | professional |
| sm | Scrum Master | Scrum Master here | Adam | en_US-joe-medium | professional |
| tea | Test Architect | QA ready | Antoni | en_US-arctic-medium | professional |
| tech-writer | Technical Writer | Tech Writer here | Elli | en_US-lessac-medium | normal |
| ux-designer | UX Designer | UX Designer ready | Domi | en_US-lessac-medium | normal |
| frame-expert | Visual Designer | Designer here | Sam | en_GB-alan-medium | professional |
| bmad-master | BMAD Master | BMAD Master online | Josh | en_US-danny-low | professional |
| quick-flow-solo-dev | Solo Developer | Solo Dev mode | Bella | en_US-amy-medium | normal |
| bmad-builder | BMAD Builder | Builder ready | Arnold | en_GB-alan-medium | professional |

## Notes

- **ElevenLabs Voice**: Used when ElevenLabs is your active TTS provider (FREE TIER VOICES)
- **Piper Voice**: Used when Piper TTS (free/offline) is your active provider
- **Personality**: Applied to all TTS output for that agent

## Free Tier ElevenLabs Voices

Rachel, Domi, Bella, Antoni, Elli, Josh, Arnold, Adam, Sam

## Customization

Edit this table to change voice assignments. Run `/agent-vibes:bmad status` to verify changes.
