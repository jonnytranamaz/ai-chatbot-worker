from django.db import models

class TrainingMessage(models.Model):
    request = models.TextField()
    response = models.TextField()

    def __str__(self):
        return f"Request: {self.request[:50]}... Response: {self.response[:50]}..."
