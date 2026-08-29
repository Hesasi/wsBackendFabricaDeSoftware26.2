from django.db import models
from django.contrib.auth.models import User

class Personagem(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personagens')
    nome = models.CharField(max_length=100)
    classe = models.CharField(max_length=50)
    nivel = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.nome} (Nvl {self.nivel} {self.classe})"

class Magia(models.Model):
    # Relacionamento (Chave Estrangeira obrigatória do projeto)
    personagem = models.ForeignKey(Personagem, on_delete=models.CASCADE, related_name='magias')
    
    # Atributos preenchidos pela API do D&D
    nome = models.CharField(max_length=100)
    nivel = models.IntegerField(default=0)
    escola = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.TextField()
    fonte_api = models.CharField(max_length=100, help_text="Slug da magia na API (ex: acid-arrow)")

    class Meta:
        # Garante que um mago não tenha duas magias iguais no banco de dados
        constraints = [
            models.UniqueConstraint(fields=['personagem', 'fonte_api'], name='magia_unica_por_personagem')
        ]

    def __str__(self):
        return f"{self.nome} - {self.personagem.nome}"