from typing import get_args
from pydantic import BaseModel, Field
from mockfirestore import MockFirestore, document
import uuid

from icecream import ic


try:
    from firesetup import db
except ImportError:
    db = MockFirestore()


def fire(firestore_ref=None, subcollections_fields=None):
    def decorator(cls):
        res = type(f"Fire{cls.__name__}", (cls,), {})
        setattr(res, "firestore_ref", firestore_ref)
        setattr(res, "subcollections_fields", subcollections_fields or [])
        setattr(res, 'fire_collection', FireCollection(res))
        return res
    return decorator


IdField = Field(default_factory=lambda: uuid.uuid4().hex, exclude=True)


class FireDocumentReference:
    def __init__(self, model):
        self.model = model

    @classmethod
    def _ref_str(cls, model):
        return model.firestore_ref or model.__name__.lower() + 's'

    @property
    def document(self):
        return db.collection(self._ref_str(self.model)).document(self.model.id)


class FireDocumentReferenceSubcollection(FireDocumentReference):
    def __init__(self, model, parent_model):
        super().__init__(model)
        self.parent_model = parent_model

    @property
    def document(self):
        return super().document.collection(
                self._ref_str(self.parent_model)).document(self.model.id)



class FireCollection:
    def __init__(self, type_model):
        self.type_model = type_model
        self.collection_reference = FireDocumentReference(self.type_model)

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
        obj = self.collection_reference.collection.document(id).get().to_dict()
        obj['id'] = id
        for key, value in self.model_schema.items():
            obj[key] = self.__class__(value)._deserialize(obj[key])
        return obj

    def _deserialize_subcollections(self, id):
        for key in self.type_model.subcollections_fields:
            pass

    def deserialize(self, id):
        return self.type_model(**self._deserialize(id))


class FireDocument:
    def __init__(self, model):
        self.model = model
        self._str_reference = model.firestore_ref + '/' + model.id

    def __repr__(self):
        return f'FireDocument({self._str_reference})'

    def __hash__(self):
        return hash(self._str_reference)

    @property
    def reference(self):
        ref_obj = db
        ref = (_ for _ in self._str_reference.split('/'))
        try:
            while True:
                ref_obj = ref_obj.collection(next(ref)).document(next(ref))
        except StopIteration:
            return ref_obj
        
    @property
    def document_data(self):
        return {key: self.__class__(value)._str_reference
                    if getattr(value, 'id', None) 
                    else value.model_dump() 
                        if isinstance(value, BaseModel) 
                        else value
                for key, value in dict(self.model).items() 
                    if not key in self.model.subcollections_fields 
                    and not key == 'firestore_ref' and not key == 'id'}


    def _get_subcollections_absolute_ref(self, ref=''):
        ref += '/' + self._str_reference if ref else self._str_reference
        for key in self.model.subcollections_fields:
            for item in getattr(self.model, key):
                yield from self.__class__(item)._get_subcollections_absolute_ref(ref)
        if self._str_reference != ref:
            self._str_reference = ref
            yield self

    @property
    def subcollections_documents(self):
        return self._get_subcollections_absolute_ref()

    @property
    def child_documents(self):
        for model in dict(self.model).values():
            if isinstance(model, BaseModel) and getattr(model, 'id', None):
                yield from self.__class__(model).child_documents
                yield self.__class__(model)

    @property
    def all_documents(self):
        for doc in self.child_documents:
            yield doc
        for subdoc in self.subcollections_documents:
            yield subdoc
            for doc in subdoc.child_documents:
                yield doc
        yield self

    def set(self):
        self.reference.set(self.document_data)
