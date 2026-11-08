"""Shared M3/M8 civil-date boundary operation. Half-open intervals."""
def overlap_bounds(a,b):
    return max(a[0],b[0]),min(a[1],b[1])
