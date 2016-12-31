import os

signin_link = 'https://slack.com/oauth/authorize?scope=identity.basic,identity.team&client_id={}&state=resumeSignIn'.format(os.environ.get('SLACK_CLIENT_ID'))
badge_link = 'https://img.shields.io/badge/{badge}-{value}-brightgreen.svg'.format

def error_msg(msg):
    return {
        'icon_emoji' : ':warning:',
        'response_type' : 'ephemeral',
        'text' : msg
    }

def verified_token(token):
    app_verification_token = os.environ.get('SLACK_VERIFICATION_TOKEN')
    return app_verification_token == token
