from tortoise.models import Model
from tortoise import fields


class Chat(Model):
    id = fields.IntField(pk=True)
    session_id = fields.CharField(max_length=255)


class Mensagem(Model):
    id = fields.IntField(pk=True)
    chat_id = fields.ForeignKeyField("models.Chat")
    mensagem = fields.CharField
    sended_at = fields.DatetimeField(auto_now_add=True)
