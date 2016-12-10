from django import forms
from slacker import Slacker
from .models import Team

class TeamSettingsForm(forms.ModelForm):
    post_channel = forms.ChoiceField()
    approval_channel = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(TeamSettingsForm, self).__init__(*args, **kwargs)

        slack = Slacker(kwargs['instance'].access_token)

        priv_ch = [(g['name'], g['id']) for g in slack.groups.list().body['groups']]
        pub_ch = [(c['name'], c['id']) for c in slack.channels.list().body['channels']]
        users = [(u['profile']['real_name'], u['id']) for u in slack.users.list().body['members']]

        self.fields['post_channel'].widget.choices(tuple(pub_ch))
        self.fields['approval_channel'].widget.choices(tuple(pub_ch + priv_ch + users))

    class Meta:
        model = Team
        fields = ['post_channel', 'approval_channel', 'admin_only_approval',
                  'admin_only_edit']
