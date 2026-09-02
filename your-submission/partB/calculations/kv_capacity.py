"""
kv_capacity.py

Compute KV-cache capacity using the units stated in the model specification:
24 GB, 0.92 utilization, 1.6 GB non-KV overhead.

The primary result uses decimal GB (1 GB = 1e9 bytes), because the model spec
states memory in GB and does not say GiB. We also compute the binary-GiB
reinterpretation as a sensitivity check.

Usage:
    python kv_capacity.py
"""

import json

layers = 28
kv_heads = 8
head_dim = 128
fp16_bytes = 2
max_model_len = 4096

gpu_mem_gb = 24.0
gpu_util = 0.92
non_kv_overhead_gb = 1.6

# bytes/token = layers * kv_heads * head_dim * 2(K+V) * bytes_per_value
bytes_per_token = layers * kv_heads * head_dim * 2 * fp16_bytes

# Primary calculation uses the units from the spec: GB means 1e9 bytes.
available_kv_bytes = (gpu_mem_gb * gpu_util - non_kv_overhead_gb) * 1e9
max_tokens_cached = int(available_kv_bytes // bytes_per_token)
concurrent_4096 = max_tokens_cached // max_model_len

# Sensitivity check: if the same arithmetic were wrongly interpreted as GiB.
units_sensitivity_gib = (gpu_mem_gb * gpu_util - non_kv_overhead_gb) * (1024 ** 3)
max_tokens_cached_gib = int(units_sensitivity_gib // bytes_per_token)
concurrent_4096_gib = max_tokens_cached_gib // max_model_len

out = {
    "layers": layers,
    "kv_heads": kv_heads,
    "head_dim": head_dim,
    "fp16_bytes": fp16_bytes,
    "bytes_per_token": bytes_per_token,
    "gpu_mem_gb": gpu_mem_gb,
    "gpu_util": gpu_util,
    "non_kv_overhead_gb": non_kv_overhead_gb,
    "available_kv_bytes_primary": available_kv_bytes,
    "available_kv_bytes_gib_sensitivity": units_sensitivity_gib,
    "max_tokens_cached_primary": max_tokens_cached,
    "max_tokens_cached_gib_sensitivity": max_tokens_cached_gib,
    "concurrent_4096_primary": concurrent_4096,
    "concurrent_4096_gib_sensitivity": concurrent_4096_gib,
    "primary_units_note": "GB is interpreted as decimal GB (1e9 bytes) because the model spec states memory in GB, not GiB.",
}
print(json.dumps(out, indent=2))
