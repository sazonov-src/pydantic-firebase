from idantic.firestore import FireCollection, db, get_document_reference
from tests.test_firestore.conftest import User
from idantic.firestore import FireDocument


def test_set_uset_to_db(user_model):
    fire_user = FireDocument(user_model)
    for doc in fire_user.all_documents:
        print(doc, doc.document_data)
        print(get_document_reference(doc._str_reference).get().to_dict())
    user = User.fire_collection.get_obj('users/1')
    print(user)





    
