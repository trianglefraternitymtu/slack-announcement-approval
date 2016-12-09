from django import forms
from slacker import Slacker
from .models import Team

class TeamSettingsForm(forms.Form):
    post_channel = forms.ChoiceField()
    approval_channel = forms.ChoiceField()
    admin_only_approval = forms.BooleanField()
    admin_only_edit = forms.BooleanField()

    def __init__(self, team):
        self.fields['admin_only_approval'].initial = team.admin_only_approval
        self.fields['admin_only_edit'].initial = team.admin_only_edit

        slack = Slacker(team.access_token)

        priv_ch = [(g['name'], g['id']) for g in slack.groups.list().body['groups']]
        pub_ch = [(c['name'], c['id']) for c in slack.channels.list().body['channels']]
        users = [(u['profile']['real_name'], u['id']) for u in slack.users.list().body['members']]

        self.fields['post_channel'].choices(tuple(pub_ch))
        self.fields['approval_channel'].choices(tuple(pub_ch + priv_ch + users))

    class Meta:
        model = Team
