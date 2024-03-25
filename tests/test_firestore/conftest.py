import pytest
from pydantic import BaseModel

from firesetup import db
from pydantic_firebase.utils import IdField, firestore_collection


class Profile(BaseModel):
    name: str
    login: str


@firestore_collection(ref="comments")
class Comment(BaseModel):
    id: str = IdField
    text: str


@firestore_collection(ref="tags")
class Tag(BaseModel):
    id: str = IdField
    name: str


@firestore_collection(ref="post_data")
class PostData(BaseModel):
    id: str = IdField
    title: str
    text: str


@firestore_collection(ref="posts", subcollections_fields=["comments", "tags"])
class Post(BaseModel):
    id: str = IdField
    title: str
    comments: list[Comment]
    tags: list[Tag]
    data: PostData


@firestore_collection(ref="users", subcollections_fields=["posts"])
class User(BaseModel):
    id: str = IdField
    name: str
    posts: list[Post]
    profile: Profile


@pytest.fixture
def user_model():
    post_model = Post(
        id="1",
        title="Post Title",
        comments=[Comment(id="1", text="Comment Text")],
        tags=[Tag(id="1", name="Tag Name")],
        data=PostData(id="1", title="Post Data Title", text="Post Data Text"),
    )
    profile_model = Profile(name="User Name", login="user_login")
    return User(id="1", name="User Name", posts=[post_model], profile=profile_model)


@pytest.fixture
def empty_db():
    db.reset()
    return db


@pytest.fixture
def user_model_db(empty_db):
    empty_db.collection("users").document("1").set(
        {"name": "User Name", "profile": {"name": "User Name", "login": "user_login"}}
    )
    empty_db.collection("users").document("1").collection("posts").document(
        "1"
    ).collection("tags").document("1").set({"name": "Tag Name"})
    empty_db.collection("users").document("1").collection("posts").document(
        "1"
    ).collection("comments").document("1").set({"text": "Comment Text"})
    empty_db.collection("users").document("1").collection("posts").document("1").set(
        {"title": "Post Title", "data": "post_data/1"}
    )
    empty_db.collection("post_data").document("1").set(
        {"title": "Post Data Title", "text": "Post Data Text"}
    )
    return empty_db


@pytest.fixture
def user_model_db_without_user_profile(user_model_db):
    user_model_db.collection("users").document("1").update({"profile": None})
    return user_model_db


@pytest.fixture
def user_type():
    return User
