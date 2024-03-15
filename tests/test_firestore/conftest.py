import pytest
from idantic.firestore import IdField, fire
from pydantic import BaseModel


@fire("names")
class Name(BaseModel):
    id: str = IdField
    first: str
    last: str

@fire("cities")
class City(BaseModel):
    id: str = IdField
    name: str

@fire("users")
class User(BaseModel):
    id: str = IdField
    name: Name
    email: str
    city: City


@fire("sales")
class Sale(BaseModel):
    id: str = IdField
    name: str

@fire("promos")
class Promo(BaseModel):
    id: str = IdField
    name: str

@fire("items")
class Item(BaseModel):
    id: str = IdField
    name: str
    sale: Sale

@fire("carts", subcollections_fields=('items',))
class Cart(BaseModel):
    id: str = IdField
    user: User 
    items: list[Item]

@pytest.fixture
def sale():
    return Sale(id='1', name='sale1')

@pytest.fixture
def item1(sale):
    return Item(id='1', name='item1', sale=sale)

@pytest.fixture
def item2(sale):
    return Item(id='2', name='item2', sale=sale)

@pytest.fixture
def city():
    return City(id='1', name='Kyiv')

@pytest.fixture
def name():
    return Name(id='1', first='Vasya', last='Pupkin')

@pytest.fixture
def user(city, name):
    return User(id='2', name=name, email='a@a.ua', city=city)

@pytest.fixture
def cart(user, item1, item2):
    return Cart(id='1', user=user, items=[item1, item2])

