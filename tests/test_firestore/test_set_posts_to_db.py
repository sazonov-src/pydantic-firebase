import pytest
from pydantic import ValidationError
from firestore.db_document import FireDBDocument

from firestore.db_document import (
    get_all_documents,
)
from tests.test_firestore.conftest import User


def test_set_user_to_db(user_model):
    fire_user = FireDBDocument(user_model)
    fire_user.set()
    for doc in get_all_documents(fire_user):
        doc.set()


def test_get_user_from_db(user_model_db):
    fire_user = User.fire_collection.get_document("1")
    assert isinstance(fire_user.model, User)
    print(fire_user.model)


def test_get_user_from_empty_db(empty_db):
    with pytest.raises(ValidationError):
        User.fire_collection.get_document("1")


def test_get_user_from_db_without_profile(user_model_db_without_user_profile):
    with pytest.raises(ValidationError):
        User.fire_collection.get_document("1")
