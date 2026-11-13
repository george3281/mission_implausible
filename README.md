# mission_implausible

Context for the "Mission: Implausible 2.0" live-show pipeline: Zoom webinar chat
in, short performable instructions for the actors out. No code yet, only the
spec and the AI instructions.

## How the show uses it

The audience watches the show in a Zoom webinar. Someone on stage starts
collecting chat, the audience suggests questions or actions, and then that
person stops collecting. The round of chat goes to Claude, which judges every
message using `prompt.md` and returns 3 lines for the performer to
read out.

## Files

- `REQUIREMENTS.md` - what the system must do.
- `TODO.md` - open decisions and next steps.
- `prompt.md` - the AI instructions: show context, how to judge chat, output format. Show staff can edit this to change tone or rules.
