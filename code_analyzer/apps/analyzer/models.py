from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
user_model = get_user_model()

class Repository(models.Model):
    repo_name = models.CharField(max_length=255)
    repo_url = models.CharField(max_length=255)
    user = models.ForeignKey(
        user_model,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.repo_name