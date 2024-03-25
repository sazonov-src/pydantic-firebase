from pydantic_firebase.db_reference import get_document_reference


from pydantic import BaseModel


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


class FireDBDocumentCollection(FireDBDocument):
    def __init__(self, model, parent_ref_str):
        super().__init__(model)
        self._str_reference = "/".join(
            (parent_ref_str, model.firestore_ref, self.model.id)
        )


def get_all_subcollections_documents(document: FireDBDocument):
    for key in document.model.subcollections_fields:
        for item in getattr(document.model, key):
            yield from get_all_subcollections_documents(
                FireDBDocumentCollection(item, document._str_reference)
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
