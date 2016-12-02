from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from slacker import OAuth, Slacker
from .models import Team
from . import verified_token, error_msg
import os
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
        data = OAuth().access(client_id, client_secret, code).__dict__['body']
        logger.debug(data)
    except Exception as e:
        logger.exception(e)
        return redirect('slack-info')

    team_id = data['team_id']
    access_token = data['access_token']

    if state is 'appAdded':
        logger.debug("Adding team \"{}\" to the database.".format(team_id))

        # Make a new team
        new_team = Team.objects.create(access_token=access_token,
                                       team_id=team_id)

        # TODO Make this start the signin process instead
        return redirect('slack-config', {'team': new_team})
    elif state is "resumeSignIn":

        # Pull this teams data and events out of the DB
        try:
            team = Team.objects.get(team_id=team_id)
        except Exception as e:
            logger.exception(e)
            return JsonResponse(error_msg("Failed to import team data from DB."))

        # Go display it
        return redirect('slack-config', {'team': team})
    else:
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
        attachments={
            'text':text,
            'actions':[{
                'name':'approve',
                'text':'Approve',
                'type':'button',
                'value':'{} {}'.format(user_id, text)
            }, {
                'name':'reject',
                'text':'Reject',
                'style':'danger',
                'type':'button',
                'value':'{} {}'.format(user_id, text)
            }]
        })

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
        return HttpResponse(status=401)

    team_id = request.POST.get('team_id')
    callback_id = request.POST.get('callback_id')
    action = request.POST.get('actions')

    logger.debug(team_id)
    logger.debug(callback_id)

    return JsonResponse(None)
