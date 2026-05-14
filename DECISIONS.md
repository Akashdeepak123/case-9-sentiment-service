## Development environment: Docker-first

We develop and test inside Docker (Linux containers) rather than
directly on macOS, because:

1. **Production matches dev.** Render runs our Dockerfile in Linux —
   testing in the same environment eliminates a class of "works on my
   machine" bugs.
2. **Apple Silicon ML toolchain stability.** During initial setup,
   transformers + torch on Apple Silicon Python 3.11 produced
   intermittent bus errors during pytest. Docker (Linux ARM64) is rock
   solid for the same code. Time invested in chasing this on macOS is
   time not invested in the actual differentiators (drift detection,
   eval harness, DRIFT_PLAYBOOK).
3. **Defensible engineering call.** When your deploy target is Linux
   containers, develop in Linux containers.

The native macOS workflow is documented in README as a fallback for
contributors on non-Apple-Silicon machines.
