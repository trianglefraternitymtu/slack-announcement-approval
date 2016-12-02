# Announcement Approval for Slack [![Build Status](https://travis-ci.org/raveious/slack-announcement-approval.svg?branch=master)](https://travis-ci.org/raveious/slack-announcement-approval)

This is for teams where posting to the #general channel (often renamed to #announcements) has been restricted to team owners and/or admins. This would allow a user to have a message posted to the #general channel after getting approval from an admin or another private channel.

## Setup

<a href="https://slack.com/oauth/authorize?scope=incoming-webhook,commands&client_id=19225015925.110455013810"><img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>

After the app is added to your team, you will be asked to sign in with Slack.

<a href="https://slack.com/oauth/authorize?scope=identity.basic&client_id=19225015925.110455013810"><img alt="Sign in with Slack" height="40" width="172" src="https://platform.slack-edge.com/img/sign_in_with_slack.png" srcset="https://platform.slack-edge.com/img/sign_in_with_slack.png 1x, https://platform.slack-edge.com/img/sign_in_with_slack@2x.png 2x" /></a>

You will then be sent to the configuration page for your team.

Note: By default, only team admins and owners are allowed to edit the team configuration. Everyone else will be denied access until an admin or team owner logs in and allows everyone access.

## Configuration

Option | Default Value | Description
:---|:---:|:---:
Post channel | #general (or whatever it was renamed too) | The selected channel that is ultimatly trying to be posted too.
Approval channel | The user who added the app to the team. | The channel where an post needs approval from. Typically a "Executive Board" kind of channel that is private.
Admin only approval | False | In the channel that the request will be sent to, allow only a team admin to respond. This is for the case where there are both team admins and non-admins in the approval channel.
Admin only login | True | Only an admin can change these settings. This can be disabled, but requires and team admin or owner to login to disable it.
