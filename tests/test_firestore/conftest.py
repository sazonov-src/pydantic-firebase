import pytest
from pydantic import BaseModel

from idantic.firestore import IdField, fire


class Profile(BaseModel):
    name: str
    login: str


@fire(firestore_ref="comments")
class Comment(BaseModel):
    id: str = IdField
    text: str


@fire(firestore_ref="tags")
class Tag(BaseModel):
    id: str = IdField
    name: str


@fire(firestore_ref="post_data")
class PostData(BaseModel):
    id: str = IdField
    title: str
    text: str


@fire(firestore_ref="posts", subcollections_fields=["comments", "tags"])
class Post(BaseModel):
    id: str = IdField
    title: str
    comments: list[Comment]
    tags: list[Tag]
    data: PostData


@fire(firestore_ref="users", subcollections_fields=["posts"])
class User(BaseModel):
    id: str = IdField
    name: str
    posts: list[Post]
    profile: Profile


@pytest.fixture
def post_data_model():
    return PostData(id="5", title="title", text="some long text")


@pytest.fixture
def profile_model():
    return Profile(name="name", login="login")


@pytest.fixture
def comment_model():
    return Comment(id="1", text="text")


@pytest.fixture
def tag_model2():
    return Tag(id="2", name="name2")


@pytest.fixture
def tag_model():
    return Tag(id="1", name="name")


@pytest.fixture
def post_model(comment_model, tag_model, post_data_model, tag_model2):
    return Post(
        id="1",
        title="title",
        comments=[comment_model],
        tags=[tag_model, tag_model2],
        data=post_data_model,
    )


@pytest.fixture
def user_model(post_model, profile_model):
    return User(id="1", name="name", posts=[post_model], profile=profile_model)
