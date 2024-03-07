from idantic.firestore import FireCollection, db, get_documents
from pprint import pprint

def test_(cart):
    for doc in list(get_documents(cart)):
        print(doc.save())

    res = db.collections()
    for collection in res:
        for doc in collection.stream():
            print(doc.id, doc.to_dict())

    cart_id = db.collection('carts').list_documents()[0].id

    collection = FireCollection(type(cart))
    print(collection.deserialize(cart_id))

    
