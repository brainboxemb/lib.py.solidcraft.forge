# API probes

API probes are small executable experiments used to answer one specific API or
backend question before that behavior becomes public API or permanent
qualification.

Each probe owner must contain:

- `probe.yml` — probe id, builder and source;
- the smallest executable source needed for the question;
- `README.md` — why the probe exists, the exact question, what success proves,
  what it does not prove, and the decision it informs.

Probe geometry may be intentionally simplified. The README must say so when the
geometry is only transport for an API/backend experiment.

A probe is not a permanent regression suite by default. If its result becomes a
public contract, graduate the relevant behavior into the owning package,
module or model tests and keep or retire the probe according to whether it
still answers a distinct design question.
