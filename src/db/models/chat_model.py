import uuid
from tortoise.models import Model
from tortoise import fields


class Chat(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="chats")


class Mensagem(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    chat = fields.ForeignKeyField("models.Chat", related_name="mensagens")
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    role = fields.CharField(max_length=20)
    name = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "mensagem"
