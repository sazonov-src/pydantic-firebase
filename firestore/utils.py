import uuid

from pydantic import Field

from firestore.db_collection import FireDBCollection


def firestore_collection(ref, subcollections_fields=None):
    def decorator(cls):
        res = type(f"{cls.__name__}", (cls,), {})
        setattr(res, "firestore_ref", ref)
        setattr(res, "subcollections_fields", subcollections_fields or [])
        setattr(res, "fire_collection", FireDBCollection(res))
        return res

    return decorator


IdField = Field(default_factory=lambda: uuid.uuid4().hex, exclude=True)
