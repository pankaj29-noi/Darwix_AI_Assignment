# Final upload checklist

The assessment's final section requires the following package.

## Required links/files

- [ ] GitHub repository URL opens in an incognito/private browser window.
- [ ] Repository contains `README.md` and `.env.example`.
- [ ] Repository contains architecture, setup, sample inputs, and executed results.
- [ ] Repository contains transcripts and the labeled synthetic audio samples.
- [ ] Video walkthrough URL opens without requesting access.
- [ ] `DARWIX_AI_ASSIGNMENT_SUBMISSION.pdf` contains the final GitHub and video URLs.
- [ ] Upload the submission PDF to the form.
- [ ] Paste the GitHub URL into the form's repository/link field.
- [ ] Paste the video URL into a separate video field if the form provides one.

## Video must show

- [ ] System overview and live UI.
- [ ] Architecture and key design decisions.
- [ ] Q2 retrieval with citation and Q1 voice-agent flow.
- [ ] Unsupported question, safe fallback, and escalation.
- [ ] Philippines Taglish and Indonesia colloquial/localized handling.
- [ ] Q4 real-time-speed replay with nudges arriving before the call ends.
- [ ] Current test, RAG, false-positive, and latency results.
- [ ] Known limitations and production improvements.

Use `docs/DEMO_SCRIPT.md` as the recording script. Record the browser and terminal
with the mock-mode disclosure visible. Do not present the `.aiff` files as real
customers or claim unmeasured ASR/TTS performance.

## Security check before publishing

```bash
PYTHONPATH=backend .venv/bin/python scripts/check_secrets.py
git status
git ls-files | grep -E '(^|/)\.env$|\.db$|node_modules|\.venv'
```

The final command should print nothing. Review the Git diff manually because the
pattern scan is not a complete secret audit.

## Form answers

**Project title**  
Darwix AI Voice Intelligence Platform

**Short description**  
An end-to-end local AI voice-intelligence platform implementing a
knowledge-grounded health-insurance qualification agent, a traceable RAG knowledge
base, localized Philippines and Indonesia financial conversation prototypes, and a
real-time WebSocket nudge dashboard with measured local latency and false-positive
controls.

**Repository link**  
Replace with the final reviewer-accessible GitHub URL.

**Video/demo link**  
Replace with the unlisted YouTube or anyone-with-link Drive URL.

**PDF upload**  
`submission/DARWIX_AI_ASSIGNMENT_SUBMISSION.pdf`
