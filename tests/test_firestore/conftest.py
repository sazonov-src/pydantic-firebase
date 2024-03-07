import pytest
from idantic.firestore import IdField, fire
from pydantic import BaseModel

from typing import Any


@fire("cities")
class City(BaseModel):
    id: str = IdField
    name: str

@fire("users")
class User(BaseModel):
    id: str = IdField
    name: str
    email: str
    city: City

@fire("carts")
class Cart(BaseModel):
    id: str = IdField
    user: User
    items: list


@pytest.fixture
def city():
    return City(name='Kyiv')

@pytest.fixture
def user(city):
    return User(name='Vasya', email='a@a.ua', city=city)

@pytest.fixture
def cart(user):
    return Cart(user=user, items=[1, 2, 3])

