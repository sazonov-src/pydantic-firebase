import uuid
from typing import get_args

from google.cloud.firestore import CollectionReference, DocumentReference
from pydantic import BaseModel, Field

from firesetup import db


def fire(firestore_ref=None, subcollections_fields=None):
    def decorator(cls):
        res = type(f"{cls.__name__}", (cls,), {})
        setattr(res, "firestore_ref", firestore_ref)
        setattr(res, "subcollections_fields", subcollections_fields or [])
        setattr(res, "fire_collection", FireDBCollection(res))
        return res

    return decorator


IdField = Field(default_factory=lambda: uuid.uuid4().hex, exclude=True)


class FireDBCollection:
    def __init__(self, model_type):
        self.model_type = model_type

    def reference(self):
        return db.collection(self.model_type.firestore_ref)

    def get_document(self, document_id):
        return FireDBDocument(
            self.model_type(
                **deserialize_from_db(
                    self.model_type, self.model_type.firestore_ref + "/" + document_id
                )
            )
        )


class FireDBDocument:
    def __init__(self, model):
        self.model = model
        self._str_reference = model.firestore_ref + "/" + model.id

    @property
    def reference(self):
        return get_document_reference(self._str_reference)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._str_reference})"

    def __hash__(self):
        return hash((self._str_reference,))

    def __eq__(self, other):
        return self._str_reference == other._str_reference

    @property
    def document_data(self):
        return {
            key: value.firestore_ref + "/" + value.id
            if getattr(value, "id", None)
            else value.model_dump()
            if isinstance(value, BaseModel)
            else value
            for key, value in dict(self.model).items()
            if key not in self.model.subcollections_fields
            and not key == "firestore_ref"
            and not key == "id"
        }

    def set(self):
        self.reference.set(self.document_data)


class FireDocumentCollection(FireDBDocument):
    def __init__(self, model, parent_ref_str):
        super().__init__(model)
        self._str_reference = "/".join(
            (parent_ref_str, model.firestore_ref, self.model.id)
        )


def get_all_subcollections_documents(document: FireDBDocument):
    for key in document.model.subcollections_fields:
        for item in getattr(document.model, key):
            yield from get_all_subcollections_documents(
                FireDocumentCollection(item, document._str_reference)
            )
    if type(document) is not FireDBDocument:
        yield document


def get_all_child_documents(document: FireDBDocument):
    for model in dict(document.model).values():
        if isinstance(model, BaseModel) and getattr(model, "id", None):
            yield from get_all_subcollections_documents(FireDBDocument(model))
            yield FireDBDocument(model)


def get_all_documents(document: FireDBDocument):
    for doc in get_all_subcollections_documents(document):
        yield doc
        yield from get_all_child_documents(doc)
    yield from get_all_child_documents(document)


def deserialize_from_db(model_type, str_ref):
    obj_dict = get_document_reference(str_ref).get().to_dict()
    if obj_dict is None:
        raise ValueError

    def get_submodels_types():
        return {
            key: value.annotation
            for key, value in model_type.model_fields.items()
            if isinstance(value.annotation, type(BaseModel))
        }

    def get_sub_collections_types():
        return {
            key: get_args(model_type.model_fields[key].annotation)
            for key in model_type.subcollections_fields
        }

    def get_submodels():
        for key, value in get_submodels_types().items():
            if not isinstance(obj_dict[key], str):
                continue
            obj_dict.update({key: deserialize_from_db(value, obj_dict[key])})

    def get_sub_collections():
        for key, types in get_sub_collections_types().items():
            for type_ in types:
                subcollection_ref = get_collection_reference(
                    str_ref + "/" + type_.firestore_ref
                )
                obj_dict.update(
                    {
                        key: [
                            deserialize_from_db(type_, "/".join(doc._path))
                            for doc in subcollection_ref.list_documents()
                        ]
                    }
                )

    get_submodels()
    get_sub_collections()
    obj_dict["id"] = str_ref.split("/")[-1]
    return obj_dict


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
