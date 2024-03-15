from idantic.firestore import FireCollection, db, FireDocument
from pprint import pprint

    
def test_(cart):
    doc_obj = FireDocument(cart)
    doc = FireCollection(type(cart))
    print(doc.get_obj(doc_obj._str_reference))

