from typing import get_args

from pydantic import BaseModel

from firesetup import db
from firestore.db_document import FireDBDocument
from firestore.db_reference import (
    get_collection_reference,
    get_document_reference,
)


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
            if not isinstance(obj_dict.get(key, None), str):
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
