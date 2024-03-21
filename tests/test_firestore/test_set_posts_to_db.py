from idantic.firestore import (
    FireDBDocument,
    get_all_child_documents,
    get_all_documents,
    get_all_subcollections_documents,
)
from tests.test_firestore.conftest import User


def test_set_uset_to_db(user_model):
    fire_user = FireDBDocument(user_model)
    print(list(get_all_subcollections_documents(fire_user)))
    print(list(get_all_child_documents(fire_user)))
    print(list(get_all_documents(fire_user)))

    # fire_user.set()
    for doc in get_all_documents(fire_user):
        # doc.set()
        print(doc, doc.document_data)

    user = User.fire_collection.get_document("1")
    print(user.model)
