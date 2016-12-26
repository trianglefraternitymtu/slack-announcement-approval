from django import forms
from slacker import Slacker
from .models import Team

class TeamSettingsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TeamSettingsForm, self).__init__(*args, **kwargs)

        if 'token' in kwargs:
            token = kwargs.pop('token')
        else:
            token = kwargs['instance'].access_token

        slack = Slacker(token)

        priv_ch = [(g['id'], g['name']) for g in slack.groups.list().body['groups'] if not g['is_archived']]
        pub_ch = [(c['id'], c['name']) for c in slack.channels.list().body['channels'] if not c['is_archived']]
        users = [(u['id'], u['profile']['real_name']) for u in slack.users.list().body['members'] if not u['deleted']]

        self.fields['post_channel'].widget = forms.Select(choices=tuple(pub_ch))
        self.fields['approval_channel'].widget = forms.Select(choices=tuple(pub_ch + priv_ch + users))

    class Meta:
        model = Team
        fields = ['post_channel', 'approval_channel', 'admin_only_approval',
                  'admin_only_edit']
