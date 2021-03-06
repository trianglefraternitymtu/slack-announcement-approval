from django.db import models

class Team(models.Model):
    team_id = models.CharField(editable=False, primary_key=True, max_length=30)
    access_token = models.CharField(max_length=128, editable=False)
    post_channel = models.CharField(max_length=21, default=None)
    approval_channel = models.CharField(max_length=21, default=None)
    last_edit = models.CharField(max_length=21, default=None)
    admin_only_approval = models.BooleanField(default=True)
    admin_only_edit = models.BooleanField(default=True)

class UserBlock(models.Model):
    team_id = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.CharField(max_length=21)
    until = models.DateTimeField()
