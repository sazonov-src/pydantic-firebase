import pytest
from pydantic_firebase.db_document import (
    FireDBDocument,
    get_all_documents,
)
from pydantic import ValidationError


def test_set_user_to_db(user_model):
    fire_user = FireDBDocument(user_model)
    fire_user.set()
    for doc in get_all_documents(fire_user):
        doc.set()


def test_get_user_from_db(user_model_db, user_type):
    fire_user = user_type.fire_collection.get_document("1")
    assert isinstance(fire_user.model, user_type)


def test_get_user_from_empty_db(empty_db, user_type):
    with pytest.raises(ValidationError):
        user_type.fire_collection.get_document("1")


def test_get_user_from_db_without_profile(
    user_model_db_without_user_profile, user_type
):
    with pytest.raises(ValidationError):
        user_type.fire_collection.get_document("1")
