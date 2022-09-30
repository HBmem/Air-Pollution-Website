from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=200)
    x_coord = models.FloatField(max_length=200)
    y_coord = models.FloatField(max_length=200)

    def __str__(self):
        return self.name

class kmlFile(models.Model):
    name = models.CharField(max_length=50)
    file = models.FileField(upload_to='kml/')
    
    def __str__(self):
        return self.name
