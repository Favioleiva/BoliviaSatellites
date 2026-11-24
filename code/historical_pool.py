"""Fixed visual reference across every finite, eligible municipality-period value."""
import math
import numpy as np

def transformed_centres(values):
    """Never silently discard observations outside a logarithm's domain."""
    values = np.asarray(values, dtype=float).ravel()
    values = values[np.isfinite(values)]
    result = {}
    for name, k in [('linear', 0), ('log1p', 1), ('log1p1000', 1000)]:
        invalid = int(np.count_nonzero(1 + k * values <= 0)) if k else 0
        valid = len(values) > 0 and invalid == 0
        mean = math.fsum(values if not k else np.log1p(k * values)) / len(values) if valid else None
        result[name] = dict(available=valid, count=len(values), invalid_count=invalid,
            display_mean=mean, original_center=(mean if not k else math.expm1(mean)/k) if valid else None)
    return result

def historical_pool(values, first, last):
    values = np.asarray(values, dtype=float).ravel()
    values = values[np.isfinite(values)]
    return dict(
        minimum=float(values.min()) if len(values) else None,
        mean=math.fsum(values) / len(values) if len(values) else None,
        maximum=float(values.max()) if len(values) else None,
        count=len(values), first=first, last=last,
        centres=transformed_centres(values),
        weighting='equal municipality-period observations',
        eligibility='finite source value and no qa_flags bit 8; area ratio >1 retained',
        scope='all municipalities and all available periods, separately for each variable',
    )
