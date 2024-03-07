from pydantic import BaseModel, Field
from mockfirestore import MockFirestore
import uuid
import abc
from functools import cached_property


try:
    from firesetup import db
except ImportError:
    db = MockFirestore()


def fire(firestore_ref=None, subcollections_fields=None):
    def decorator(cls):
        res = type(f"Fire{cls.__name__}", (cls,), {})
        setattr(cls, "firestore_ref", firestore_ref)
        return res
    return decorator


IdField = Field(default_factory=lambda: uuid.uuid4().hex, exclude=True)


class FireCollection:
    def __init__(self, type_model):
        self.type_model = type_model

    @property
    def collection_reference(self):
        return db.collection(
                self.type_model.firestore_ref or self.type_model.__name__.lower() + 's')

    def is_model_have_id(self, model):
        for key, value in model.model_fields.items():
            if key == 'id':
                return True
        return False

    @property
    def model_schema(self):
        return {key: value.annotation for key, value 
                in self.type_model.model_fields.items() 
                if isinstance(value.annotation, type(BaseModel))
                and self.is_model_have_id(value.annotation)}

    def _deserialize(self, id):
        obj = self.collection_reference.document(id).get().to_dict()
        obj['id'] = id
        for key, value in self.model_schema.items():
            obj[key] = self.__class__(value).deserialize(obj[key])
        return obj

    def deserialize(self, id):
        return self.type_model(**self._deserialize(id))



class FireModel:
    def __init__(self, model):
        self.model = model
        self.model_dict = dict(model)
        self.id = self.model_dict.pop('id')

    def serialize(self):
        for key, value in self.model_dict.items():
            if isinstance(value, BaseModel):
                self.model_dict[key] = getattr(value, 'id')
        return self.model_dict

    @property
    def document_reference(self):
        return db.collection(
                self.model.firestore_ref or self.model.__name__.lower() + 's').document(self.id)

    def save(self):
        self.document_reference.set(self.serialize())

    def delete(self):
        pass


def get_documents(model):
    for key, value in dict(model).items():
        if isinstance(value, BaseModel):
            yield from get_documents(value)
    yield FireModel(model)
