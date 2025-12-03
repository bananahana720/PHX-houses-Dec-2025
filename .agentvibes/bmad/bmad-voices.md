# BMAD Agent Voice Mappings

Configure unique voices for each BMAD agent. When a BMAD agent activates, they'll speak with their assigned voice.

## Voice Mappings

| Agent ID | Agent Name | Intro | ElevenLabs Voice | Piper Voice | Personality |
|----------|------------|-------|------------------|-------------|-------------|
| pm | Product Manager | PM here | Matthew Schmitz | en_US-ryan-high | professional |
| dev | Developer | Dev ready | Aria | en_US-amy-medium | normal |
| analyst | Business Analyst | Analyst reporting | Jessica Anne Bogart | en_US-kristin-medium | professional |
| architect | Architect | Architect online | Michael | en_GB-alan-medium | professional |
| sm | Scrum Master | Scrum Master here | Matthew Schmitz | en_US-joe-medium | professional |
| tea | Test Architect | QA ready | Michael | en_US-arctic-medium | professional |
| tech-writer | Technical Writer | Tech Writer here | Aria | en_US-lessac-medium | normal |
| ux-designer | UX Designer | UX Designer ready | Jessica Anne Bogart | en_US-lessac-medium | normal |
| frame-expert | Visual Designer | Designer here | Matthew Schmitz | en_GB-alan-medium | professional |
| bmad-master | BMAD Master | BMAD Master online | Michael | en_US-danny-low | professional |
| quick-flow-solo-dev | Solo Developer | Solo Dev mode | Aria | en_US-amy-medium | normal |

## Notes

- **ElevenLabs Voice**: Used when ElevenLabs is your active TTS provider
- **Piper Voice**: Used when Piper TTS (free/offline) is your active provider
- **Personality**: Applied to all TTS output for that agent

## Customization

Edit this table to change voice assignments. Run `/agent-vibes:bmad status` to verify changes.
