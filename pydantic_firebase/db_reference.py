from google.cloud.firestore import CollectionReference, DocumentReference
from firesetup import db


def _get_reference(ref_str):
    ref = iter(ref_str.split("/"))
    ref_obj = db
    try:
        while True:
            ref_obj = ref_obj.collection(next(ref))
            ref_obj = ref_obj.document(next(ref))
    except StopIteration:
        return ref_obj


def get_document_reference(ref_str) -> DocumentReference:
    ref = _get_reference(ref_str)
    if getattr(ref, "collection", None):
        return ref
    raise ValueError


def get_collection_reference(ref_str) -> CollectionReference:
    ref = _get_reference(ref_str)
    if getattr(ref, "document", None):
        return ref
    raise ValueError
