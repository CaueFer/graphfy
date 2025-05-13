from tortoise.models import Model
from tortoise import fields
from enum import Enum
import uuid


class Chat(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="chats")
    created_at = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=50, null=True)


class Role(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    function = "function"
    data = "data"
    tool = "tool"
    error = "error"
    loading = "loading"


class Mensagem(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    chat = fields.ForeignKeyField("models.Chat", related_name="mensagens")
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    role = fields.CharEnumField(Role, max_length=20)
    name = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "mensagem"
