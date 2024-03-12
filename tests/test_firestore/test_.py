from itertools import batched
from idantic.firestore import FireCollection, db, FireDocument
from pprint import pprint
from typing import get_args


def test_cart(cart):
    pprint('set:')
    doc = FireDocument(cart)
    for doc in doc.all_documents:
        doc.set()

def test_transaction(cart):
    doc = FireDocument(cart)
    for doc in doc.all_documents:
        pprint(doc.document_data)




    
