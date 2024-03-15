from typing import get_args
from pydantic import BaseModel, Field
from mockfirestore import MockFirestore
import uuid

from icecream import ic


try:
    from firesetup import db
except ImportError:
    db = MockFirestore()


def fire(firestore_ref=None, subcollections_fields=None):
    def decorator(cls):
        res = type(f"{cls.__name__}", (cls,), {})
        setattr(res, "firestore_ref", firestore_ref)
        setattr(res, "subcollections_fields", subcollections_fields or [])
        setattr(res, 'fire_collection', FireCollection(res))
        return res
    return decorator

IdField = Field(default_factory=lambda: uuid.uuid4().hex, exclude=True)


class FireCollection:
    def __init__(self, model_type):
        self.model_type = model_type
        self.collection_ref = FireReference(model_type.firestore_ref)

    def _get_submodels_types(self):
        return {key: value.annotation 
                for key, value in self.model_type.model_fields.items() 
                if isinstance(value.annotation, type(BaseModel))}

    def _get_subcollectons_types(self):
        return {key: get_args(self.model_type.model_fields[key].annotation) for key in self.model_type.subcollections_fields}

    def _get_obj(self, document_str_ref):
        obj_ref = FireReference(document_str_ref)
        obj_dict = obj_ref.reference.get().to_dict()
        for key, value in self._get_submodels_types().items():
            obj_dict[key] = self.__class__(value)._get_obj(obj_dict[key])
        for key, types in self._get_subcollectons_types().items():
            for type_ in types:
                subcollection_ref = FireReference(document_str_ref + '/' + type_.firestore_ref)
                obj_dict[key] = [
                        self.__class__(type_)._get_obj('/'.join(doc._path))
                        for doc in subcollection_ref.reference.list_documents()]
        obj_dict['id'] = obj_ref.id
        return obj_dict

    def get_obj(self, document_str_ref):
        return self.model_type(**self._get_obj(document_str_ref))



class FireReference:
    def __init__(self, ref_str):
        self._path = ref_str.split('/')

    @property
    def id(self):
        return self._path[-1]

    @property
    def reference(self):
        return self._get_reference(self._path)

    @property
    def reference_doc(self):
        path = self._path if len(self._path) % 2  else self._path[:-1]
        return self._get_reference(path)

    @staticmethod
    def _get_reference(_path):
        ref_obj = db
        ref = iter(_path)
        try:
            while True:
                ref_obj = ref_obj.collection(next(ref))
                ref_obj = ref_obj.document(next(ref))
        except StopIteration:
            return ref_obj


class FireDocument:
    def __init__(self, model):
        self.model = model
        self._str_reference = model.firestore_ref + '/' + model.id

    @property
    def reference(self):
        return FireReference(self._str_reference).reference

    def __repr__(self):
        return f'FireDocument({self._str_reference})'

    def __hash__(self):
        return hash((self._str_reference, ))

    def __eq__(self, other):
        return self._str_reference == other._str_reference
        
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
        yield from self._get_subcollections_absolute_ref()

    @property
    def child_documents(self):
        for model in dict(self.model).values():
            if isinstance(model, BaseModel) and getattr(model, 'id', None):
                yield from self.__class__(model).child_documents
                yield self.__class__(model)

    @property
    def all_documents(self):
        yield from self.child_documents
        for subdoc in self.subcollections_documents:
            yield subdoc
            yield from subdoc.child_documents
        yield self

    def set(self):
        self.reference.set(self.document_data)
