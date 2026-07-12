"""Tuning constants for the NVIDIA NIM API client."""

BASE_URL = "https://integrate.api.nvidia.com/v1"

# Reasoning models routinely spend 2500-4000 completion tokens on a
# full-resume evaluation; at 4096 responses truncated in practice.
MAX_TOKENS = 8192

# Full-resume evaluations on nemotron-3-super regularly take 45-60+ seconds;
# a 60s limit produced timeouts on otherwise healthy calls.
TIMEOUT_SECONDS = 180.0

# The SDK retries only retryable failures (connection errors, 429s, 5xx),
# honoring Retry-After; a bad API key fails immediately.
MAX_TRANSPORT_RETRIES = 2
