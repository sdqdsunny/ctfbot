try:
    import ray
except ImportError:
    ray = None

def is_ray_actor(obj):
    """Check if an object is a Ray Actor."""
    return ray is not None and hasattr(obj, "__ray_actor_id__")
