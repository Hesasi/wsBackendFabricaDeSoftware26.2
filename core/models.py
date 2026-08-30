from django.db import models
from django.contrib.auth.models import User

class Personagem(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personagens')
    nome = models.CharField(max_length=100)
    classe = models.CharField(max_length=50)
    nivel = models.IntegerField(default=1)

    class Meta:
        ordering = ['id']

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

    # Detalhes de conjuração (também vindos da D&D 5e API, exibidos ao expandir a magia)
    tempo_conjuracao = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: 1 action, 1 bonus action")
    alcance = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: 60 feet, Self, Touch")
    componentes = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: V, S, M")
    material = models.TextField(blank=True, null=True, help_text="Descrição do componente material, quando houver")
    duracao = models.CharField(max_length=100, blank=True, null=True, help_text="Ex: Instantaneous, Concentration, up to 1 minute")
    ritual = models.BooleanField(default=False)
    concentracao = models.BooleanField(default=False)
    dano = models.CharField(max_length=150, blank=True, null=True, help_text="Resumo do dano, quando a magia causa dano")
    cd = models.CharField(max_length=150, blank=True, null=True, help_text="Resumo do teste de resistência, quando houver")
    area_efeito = models.CharField(max_length=150, blank=True, null=True, help_text="Ex: 20-foot radius sphere")

    class Meta:
        ordering = ['id']
        # Garante que um mago não tenha duas magias iguais no banco de dados
        constraints = [
            models.UniqueConstraint(fields=['personagem', 'fonte_api'], name='magia_unica_por_personagem')
        ]

    def __str__(self):
        return f"{self.nome} - {self.personagem.nome}"