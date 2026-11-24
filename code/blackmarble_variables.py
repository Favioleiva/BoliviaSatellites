"""Untransformed source fields: names are not claims of verified physical units."""
FIELDS=['mean','median','min','max','sum','std','mean0','sumsq','count','nan','total_pixels','count_valid','count_invalid','count_zeros','count_positive','prop_non_na_pixels','zero_share','positive_share','tile_count','available_tile_count_day','missing_tile_count_day','is_observed','is_missing_due_to_tile']
def metadata(native):
    category='statistics'
    unit='source radiance · scale unverified'
    if native=='sum':unit='sum of source pixel radiances · scale unverified'
    if native=='sumsq':category='auxiliary';unit='sum of squared source radiances · scale unverified'
    if native=='mean0':category='auxiliary';unit='source mean0 · definition unverified'
    if native in ['count','nan','total_pixels','count_valid','count_invalid','count_zeros','count_positive']:
        category='pixels';unit='pixels'
    if native in ['prop_non_na_pixels','zero_share','positive_share']:
        category='coverage';unit='proportion'
    if native in ['tile_count','available_tile_count_day','missing_tile_count_day']:
        category='tiles';unit='tiles'
    if native in ['is_observed','is_missing_due_to_tile']:
        category='flags';unit='source flag (0/1)'
    return dict(category=category,unit=unit)
