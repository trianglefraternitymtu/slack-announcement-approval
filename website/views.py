from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from slacker import OAuth, Slacker, BaseAPI
from .models import Team
from . import verified_token, error_msg
import os
import json
import logging

logger = logging.getLogger('basicLogger')

def info(request):
    return render(request, 'slack.html')

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
            logger.debug(ch_list)

            ch_ids = [c['id'] for c in ch_list]
            logger.debug(ch_ids)

            general = None

            for ch in ch_ids:
                info = slack.channels.info(ch).body['channel']
                if info['is_general']:
                    general = info['id']
                    break

            logger.debug("The general channel for team {} has id {}".format(team_id, general))
        except Exception as e:
            logger.exception(e)
            return redirect('slack-info')

        # Make a new team
        new_team = Team.objects.create(access_token=access_token,
                                       team_id=team_id,
                                       approval_channel=user_id,
                                       post_channel=general)

        # TODO Make this start the signin process instead
        return redirect('slack-config', {'team': new_team})
    elif state == "resumeSignIn":

        user_id = data['user']['id']
        team_id = data['team']['id']

        # Pull this teams data and events out of the DB
        try:
            team = Team.objects.get(team_id=team_id)
        except Exception as e:
            logger.exception(e)
            return JsonResponse(error_msg("Failed to import team data from DB."))

        logger.info("Team data loaded for " + team_id)

        # Go display it
        return redirect('slack-config', {'team': team})
    else:
        logger.info('Unknown auth state passed.')
        return redirect('slack-info')

def config(request):
    # TODO Make a team settings panel
    return render (request, 'config.html')

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
        logger.debug(token)
        logger.warning("Token verification failed.")
        return HttpResponse(status=401)

    team_id = request.POST.get('team_id')
    user_id = request.POST.get('user_id')
    text = request.POST.get('text')

    for team in Team.objects.all():
        logger.debug(team)

    # Pull this teams data out of the DB
    try:
        logger.debug("Getting data for \"{}\" out of the database".format(team_id))
        team = Team.objects.get(team_id=team_id)
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Failed to import team data from DB."))

    logger.info("Team data loaded for " + team_id)

    slack = Slacker(team.access_token)

    # Make a post to approval_channel with buttons
    slack.chat.post_message(team.approval_channel,
        '<@{}> has made a request to post something to <#{}>'.format(user_id,
                                                            team.post_channel),
        attachments=[{
            'text':text,
            'fallback':'<@{}> has made a request to post something to <#{}>'.format(user_id, team.post_channel),
            'callback_id':user_id,
            'actions':[{
                'name':'approve',
                'text':'Approve',
                'type':'button',
                'color':'good',
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

    token = request.POST.get('token')

    if not verified_token(token):
        logger.warning("Token verification failed.")
        return HttpResponse(status=401)

    team_id = request.POST.get('team_id')
    callback_id = request.POST.get('callback_id')
    action = request.POST.get('actions')
    org_msg = json.loads(request.POST.get('original_message'))

    logger.debug(team_id)
    logger.debug(callback_id)
    logger.debug(action)
    logger.debug(org_msg)

    # Pull this teams data out of the DB
    try:
        logger.debug("Getting data for \"{}\" out of the database".format(team_id))
        team = Team.objects.get(team_id=team_id)
    except Exception as e:
        logger.exception(e)
        return JsonResponse(error_msg("Failed to import team data from DB."))

    logger.info("Team data loaded for " + team_id)

    # slack = Slacker(team.access_token)

    # because Heroku takes its damn sweet time re-starting a free web dyno
    # we're going to do a chat.update instead of just responding
    # slack.chat.update()

    return HttpResponse(status=200)
