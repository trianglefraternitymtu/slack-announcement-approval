from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from slacker import OAuth, Slacker, BaseAPI

import os
import json
import logging

from .models import Team
from . import verified_token, error_msg

logger = logging.getLogger('basicLogger')

def info(request):
    return render(request, 'index.html')

def privacy(request):
    return render(request, 'privacy.html')

@require_GET
def auth(request):
    logger.info('Authentication')

    code = request.GET.get('code')
    state = request.GET.get('state', None)
    client_id = os.environ.get('SLACK_CLIENT_ID')
    client_secret = os.environ.get('SLACK_CLIENT_SECRET')

    logger.debug(request.GET)
    logger.debug(code)
    logger.debug(state)

    try:
        data = OAuth().access(client_id, client_secret, code).body
        logger.debug(data)
    except Exception as e:
        logger.exception(e)
        return redirect('slack-info')

    access_token = data['access_token']

    slack = Slacker(access_token)
    logger.info("Slack API interfaced")

    for team in Team.objects.all():
        logger.debug(team)

    if state == 'appAdded':
        user_id = data['user_id']
        team_id = data['team_id']

        logger.debug("Adding team \"{}\" to the database.".format(team_id))

        try:
            ch_list = slack.channels.list().body['channels']
            # logger.debug(ch_list)

            ch_ids = [c['id'] for c in ch_list]
            # logger.debug(ch_ids)

            general = None

            for ch in ch_ids:
                info = slack.channels.info(ch).body['channel']
                if info['is_general']:
                    general = info['id']
                    break

            logger.info("The general channel for team {} has id {}".format(team_id, general))
        except Exception as e:
            logger.exception(e)
            return redirect('slack-info')

        # Make a new team
        new_team = Team.objects.update_or_create(access_token=access_token,
                                       team_id=team_id,
                                       approval_channel=user_id,
                                       post_channel=general,
                                       last_edit=user_id)
        logger.info("Team added to database!")

        return redirect('https://slack.com/oauth/authorize?scope=identity.basic&client_id={}&state=resumeSignIn'.format(client_id))
    elif state == "resumeSignIn":

        user = slack.users.info(data['user']['id']).body['user']
        is_admin = user['is_admin'] or user['is_owner']
        team_id = data['team']['id']

        if not is_admin and team.admin_only_edit:
            logger.info("Signin requires an admin and wasn't.")
            # TODO Make slack-info post a dialog about not being an admin
            return redirect('slack-info')

        # Pull this teams data and events out of the DB
        try:
            team = Team.objects.get(team_id=team_id)
        except Exception as e:
            logger.exception(e)
            # TODO Make slack-info post a dialog about not being able to login
            return redirect('slack-info')

        logger.info("Team data loaded for " + team_id)

        # Go display it
        return redirect('slack-config', {'team': team, 'priv_ch':priv_ch,
                                         'pub_ch':pub_ch, 'admin':is_admin})
    else:
        logger.warning('Unknown auth state passed.')
        return redirect('slack-info')

def config(request):
    logger.info("Loading config menu")
    # TODO Make a team settings panel
    return render(request, 'config.html')

@csrf_exempt
@require_POST
def command(request):
    """
    Processes commands from a slash command.
    https://api.slack.com/slash-commands
    """
    logger.info('Slash command')
    logger.debug(request.POST)

    if request.POST.get('ssl_check') == '1':
        logger.info("SSL check.")
        return HttpResponse(status=200)

    token = request.POST.get('token')

    if not verified_token(token):
        logger.warning("Token verification failed. ({})".format(token))
        return HttpResponse(status=401)

    team_id = request.POST.get('team_id')
    user_id = request.POST.get('user_id')
    text = request.POST.get('text')

    # Pull this teams data out of the DB
    try:
        logger.debug("Getting data for \"{}\" out of the database".format(team_id))
        team = Team.objects.get(team_id=team_id)
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Failed to import team data from DB."))

    logger.info("Team data loaded for " + team_id)

    try:
        slack = Slacker(team.access_token)
        logger.info("Slack API interfaced")
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Slack API not initialized. Might want to try re-adding this app."))

    try:
        # Make a post to approval_channel with buttons
        slack.chat.post_message(team.approval_channel,
            '<@{}> has made a request to post a message to <#{}>'.format(user_id,
                                                                team.post_channel),
            as_user=False,
            attachments=[{
                'text':text,
                'pretext':'Message body:',
                'fallback':'<@{}> has made a request to post something to <#{}>'.format(user_id, team.post_channel),
                'callback_id':user_id,
                'mrkdwn_in':['text'],
                'actions':[{
                    'name':'approve',
                    'text':'Approve',
                    'type':'button',
                    'color':'primary',
                    'value':'{} {}'.format(user_id, text)
                }, {
                    'name':'reject',
                    'text':'Reject',
                    'style':'danger',
                    'type':'button',
                    'color':'danger',
                    'value':'{} {}'.format(user_id, text)
                }]
            }])

        logger.info("Approval request posted to {}".format(team.approval_channel))
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Approval post failed."))

    # Respond to persons slash command
    response = {
        'text':'Your post has been sent for approval.',
        'response_type':'ephemeral'
    }

    # Post response to Slack
    return JsonResponse(response)

@csrf_exempt
@require_POST
def button_callback(request):
    """
    Process call backs from slack interactive buttons
    https://api.slack.com/docs/message-buttons
    """
    logger.info('Button Callback')

    payload = json.loads(request.POST.get('payload'))
    logger.debug(payload)

    token = payload.get('token')

    if not verified_token(token):
        logger.warning("Token verification failed. ({})".format(token))
        return HttpResponse(status=401)

    team_id = payload['team']['id']
    clicker = payload['user']['id']
    action = payload['actions'][0]
    org_msg = payload['original_message']
    click_ts = payload['action_ts']
    msg_ts = payload['message_ts']
    org_channel = payload['channel']['id']

    action['value'] = action['value'].split(' ', 1)

    logger.debug(team_id)
    logger.debug(clicker)
    logger.debug(action)
    logger.debug(org_msg)

    # Pull this teams data out of the DB
    try:
        logger.debug("Getting data for \"{}\" out of the database".format(team_id))
        team = Team.objects.get(team_id=team_id)
        logger.info("Team data loaded for " + team_id)
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Failed to import team data from DB."))

    try:
        slack = Slacker(team.access_token)
        clicker = slack.users.info(clicker).body['user']
        requester = slack.users.info(action['value'][0]).body['user']
        logger.info("Slack API interfaced")
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Slack API not initialized. Might want to try re-adding this app."))

    # if not an admin or an owner, and "Admin only approval" is required
    if not (clicker['is_admin'] or clicker['is_owner']) and team.admin_only_approval:
        logger.info("Clicker needs to be an admin and wasn't.")
        return HttpResponse(status=200)

    # because Heroku takes its damn sweet time re-starting a free web dyno
    # we're going to do a chat.update instead of just responding

    # Update the message
    if action['name'] == 'approve':
        org_msg['attachments'][0]['footer'] = ":ok_hand: <@{}> approved this message.".format(clicker['id'])
    elif action['name'] == 'reject':
        org_msg['attachments'][0]['footer'] = ":no_entry_sign: <@{}> rejected this message.".format(clicker['id'])
    else:
        return HttpResponse(status=403)

    org_msg['attachments'][0]['ts'] = click_ts
    org_msg['attachments'][0].pop('actions', None)

    logger.debug(org_msg)

    # Pushing updated message
    try:
        slack.chat.update(org_channel, msg_ts, org_msg['text'],
            attachments=org_msg['attachments'])
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Something bad happened while posting an update."))

    # Push approved announcement out
    try:
        post_response = {}
        if action['name'] == 'approve':
            post_response['channel'] = team.post_channel
            post_response['username'] = requester['profile']['real_name']
            post_response['icon_url'] = requester['profile']['image_192']
            post_response['text'] = action['value'][1]
            post_response['as_user'] = False

        elif action['name'] == 'reject':
            post_response['text'] = 'Your announcement request has been rejected.'
            post_response['channel'] = action['value'][0]
            post_response['attachments'] = [{
                    'text':action['value'][1],
                    'pretext':'Message body:',
                    'fallback':'<@{}> has rejected your post <#{}>'.format(clicker['id'], team.post_channel),
                    'mrkdwn_in':['text'],
                    'ts':click_ts,
                    'footer':":no_entry_sign: <@{}> rejected this message.".format(clicker['id'])
                }]

        else:
            logger.warning("Unknown response from a button was received.")
            return JsonResponse(error_msg("Something bad happened while posting an update."))

        logger.debug("Posting a button response:")
        logger.debug(post_response)
        slack.chat.post_message(**post_response)
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Failed to post announcement."))

    return HttpResponse(status=200)
