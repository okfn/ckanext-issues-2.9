"""
CKAN Issue Extension
"""
import click
import logging

import ckan.plugins as p

from ckan.lib.plugins import DefaultTranslation
from ckan.plugins import toolkit

from ckanext.issues import auth
from ckanext.issues.lib import helpers, util
from ckanext.issues.logic import action
from ckanext.issues.views.issues import issues
from ckanext.issues.views.moderation import moderation

log = logging.getLogger(__name__)


class IssuesPlugin(p.SingletonPlugin, DefaultTranslation):
    """
    CKAN Issues Extension
    """
    p.implements(p.ITranslation)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IClick)
    p.implements(p.IBlueprint)

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'issues')

    # IClick
    def get_commands(self):
        """CLI commands - Creates or Updated issues data tables"""

        @click.command()
        def issuesdb():
            """Creates issues data tables"""
            from ckanext.issues.model import setup
            setup()

        @click.command()
        def issuesupdate():
            """Updates issues data tables"""
            from ckanext.issues.model import upgrade
            upgrade()
            print('Issues tables are up to date')

        return [issuesdb, issuesupdate]

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'issues_installed': lambda: True,
            'issue_count': util.issue_count,
            'issue_comment_count': util.issue_comment_count,
            'issues_enabled_for_organization':
                helpers.issues_enabled_for_organization,
            'replace_url_param': helpers.replace_url_param,
            'get_issue_filter_types': helpers.get_issue_filter_types,
            'get_issues_per_page': helpers.get_issues_per_page,
            'issues_enabled': helpers.issues_enabled,
            'issues_list': helpers.issues_list,
            'issues_user_has_reported_issue':
                helpers.issues_user_has_reported_issue,
            'issues_user_is_owner':
                helpers.issues_user_is_owner,
            'issues_users_who_reported_issue':
                helpers.issues_users_who_reported_issue,
            'use_autocomplete':
                helpers.use_autocomplete
        }

    # IBlueprint
    def get_blueprint(self):
        return [issues, moderation]

    # IActions
    def get_actions(self):
        return dict((name, function) for name, function
                    in action.__dict__.items()
                    if callable(function))

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'issue_admin': auth.issue_admin,
            'issue_search': auth.issue_search,
            'issue_show': auth.issue_show,
            'issue_create': auth.issue_create,
            'issue_comment_create': auth.issue_comment_create,
            'issue_update': auth.issue_update,
            'issue_delete': auth.issue_delete,
            'issue_report': auth.issue_report,
            'issue_report_clear': auth.issue_report_clear,
            'issue_comment_search': auth.issue_comment_search,
        }
