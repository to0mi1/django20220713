from django.db import models


# Create your models here.
class Pi(models.Model):
    id = models.UUIDField('UUID', primary_key=True)
    pi = models.FloatField('円周率', null=False)
    status = models.CharField('ステータス', max_length=32, null=False, default='')
    created_at = models.DateTimeField('作成日', auto_now_add=True, null=False)
