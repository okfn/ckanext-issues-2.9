import mock
import pytest

from ckan import model
from ckan.tests import factories, helpers
from ckan.plugins import toolkit

from ckanext.issues.tests import factories as issue_factories
from ckanext.issues.model import Issue, IssueComment
from ckanext.issues.logic.action.action import _get_recipients


@pytest.fixture
def dataset():
    return factories.Dataset()


class TestIssueShow(object):
    @pytest.fixture
    def issue1(self):
        return issue_factories.Issue(title='Test Issue')

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_show(self, issue1):
        issue = helpers.call_action(
            'issue_show',
            dataset_id=issue1['dataset_id'],
            issue_number=issue1['number'],
        )
        assert 'Test Issue' == issue['title']
        assert 'Some description' == issue['description']

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_show_api(self, issue1):
        issue = helpers.call_action(
            'issue_show',
            dataset_id=issue1['dataset_id'],
            issue_number=issue1['number'],
            api_version=3
        )
        assert 'Test Issue' == issue['title']
        assert 'Some description' == issue['description']

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_user_dictization(self, issue1):
        issue = helpers.call_action(
            'issue_show',
            dataset_id=issue1['dataset_id'],
            issue_number=issue1['number'],
        )
        user_id = issue['user_id']
        user = model.Session.query(model.User).\
            filter(model.User.id == user_id).first()
        user = vars(user)
        assert 'test.ckan.net' == user['name']


class TestIssueNew(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_create(self):
        creator = factories.User(name='creator')
        admin = factories.User(name='admin')
        org = factories.Organization(
            users=[{'name': admin['id'], 'capacity': 'admin'}])
        dataset = factories.Dataset(owner_org=org['id'])

        issue_create_result = toolkit.get_action('issue_create')(
            context={'user': creator['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )

        issue_object = Issue.get(issue_create_result['id'])
        assert 'Title' == issue_object.title
        assert 'Description' == issue_object.description
        assert 1 == issue_object.number

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_create_second(self, user, dataset):
        issue_0 = toolkit.get_action('issue_create')(
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )
        issue_1 = toolkit.get_action('issue_create')(
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )

        issue_object = Issue.get(issue_0['id'])
        assert 1 == issue_object.number
        issue_object = Issue.get(issue_1['id'])
        assert 2 == issue_object.number

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_create_multiple_datasets(self, user, dataset):
        issue_0 = toolkit.get_action('issue_create')(
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )
        issue_1 = toolkit.get_action('issue_create')(
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )

        issue_object = Issue.get(issue_0['id'])
        assert 1 == issue_object.number
        issue_object = Issue.get(issue_1['id'])
        assert 2 == issue_object.number

        # create a second dataset
        dataset2 = factories.Dataset()
        issue_2 = toolkit.get_action('issue_create')(
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset2['id'],
            }
        )
        issue_object = Issue.get(issue_2['id'])
        # check that the issue number starts from 1
        assert 1 == issue_object.number

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_create_dataset_does_not_exist(self, user):
        issue_create = toolkit.get_action('issue_create')
        pytest.raises(
            toolkit.ValidationError,
            issue_create,
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': 'nonsense',
            }
        )

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_create_test_validation(self, user):
        issue_create = toolkit.get_action('issue_create')
        pytest.raises(
            toolkit.ValidationError,
            issue_create,
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': 'not a datasest',
            }
        )

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_issue_create_cannot_set_abuse(self, user, dataset):
        issue_create_result = toolkit.get_action('issue_create')(
            context={'user': user['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
                'visibility': 'hidden'
            }
        )
        issue_object = Issue.get(issue_create_result['id'])
        assert 'visible' == issue_object.visibility

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_get_recipients(self, user):
        org = factories.Organization(user=user)
        dataset = factories.Dataset(owner_org=org['id'])
        dataset_obj = model.Package.get(dataset['id'])

        recip = _get_recipients(context={}, dataset=dataset_obj)

        assert len(recip) == 1
        assert recip[0]['user_id'] == user['id']
        assert recip[0]['capacity'] == 'Admin'
        assert recip[0]['organization_name'] == org['name']
        assert recip[0]['organization_title'] == org['title']


class TestIssueComment(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_create_comment_on_issue(self):
        creator = factories.User(name='creator')
        commenter = factories.User(name='commenter')
        admin = factories.User(name='admin')
        org = factories.Organization(
            users=[{'name': admin['id'], 'capacity': 'admin'}])
        dataset = factories.Dataset(owner_org=org['id'])

        issue = issue_factories.Issue(user=creator, user_id=creator['id'],
                                      dataset_id=dataset['id'])

        helpers.call_action(
            'issue_comment_create',
            context={'user': commenter['name']},
            issue_number=issue['number'],
            dataset_id=issue['dataset_id'],
            comment='some comment'
        )

        result = helpers.call_action(
            'issue_show',
            context={'user': commenter['name']},
            dataset_id=issue['dataset_id'],
            issue_number=issue['number']
        )
        comments = result['comments']
        assert len(comments) == 1
        assert comments[0]['comment'] == 'some comment'
        assert comments[0]['user']['name'] == 'commenter'

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_create_comment_on_closed_issue(self, user, dataset):
        # create and close our issue
        issue = issue_factories.Issue(user=user, user_id=user['id'],
                                      dataset_id=dataset['id'])

        closed = helpers.call_action(
            'issue_update',
            issue_number=issue['number'],
            dataset_id=dataset['id'],
            context={'user': user['name']},
            status='closed'
        )
        assert 'closed' == closed['status']

        # check we can comment on closed issues
        helpers.call_action(
            'issue_comment_create',
            context={'user': user['name']},
            issue_number=issue['number'],
            dataset_id=dataset['id'],
            comment='some comment'
        )

        result = helpers.call_action(
            'issue_show',
            context={'user': user['name']},
            issue_number=issue['number'],
            dataset_id=dataset['id'],
        )

        comments = result['comments']
        assert len(comments) == 1
        assert comments[0]['comment'] == 'some comment'

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_cannot_create_empty_comment(self, user, dataset):
        issue = issue_factories.Issue(user=user, user_id=user['id'],
                                      dataset_id=dataset['id'])

        pytest.raises(
            toolkit.ValidationError,
            helpers.call_action,
            'issue_comment_create',
            context={'user': user['name']},
            issue_number=issue['number'],
            dataset_id=issue['dataset_id'],
        )


class TestIssueSearch(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_list_all_issues_for_dataset(self, user, dataset):
        created_issues = [issue_factories.Issue(user=user, user_id=user['id'],
                                                dataset_id=dataset['id'],
                                                description=i)
                          for i in range(0, 10)]
        search_res = helpers.call_action('issue_search',
                                         context={'user': user['name']},
                                         dataset_id=dataset['id'],
                                         sort='oldest')
        issues_list = search_res['results']
        assert [i['id'] for i in created_issues] == [i['id'] for i in issues_list]
        assert search_res['count'] == 10

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_list_all_issues_for_organization(self, user):
        org = factories.Organization(user=user)
        dataset = factories.Dataset(owner_org=org['id'])

        created_issues = [issue_factories.Issue(user=user, user_id=user['id'],
                                                dataset_id=dataset['id'],
                                                description=i)
                          for i in range(0, 10)]
        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          organization_id=org['id'],
                                          sort='oldest')['results']
        assert [i['id'] for i in created_issues] == [i['id'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_list_all_issues(self, user, dataset):
        created_issues = [issue_factories.Issue(user=user, user_id=user['id'],
                                                dataset_id=dataset['id'],
                                                description=i)
                          for i in range(0, 10)]
        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          sort='oldest')['results']
        assert [i['id'] for i in created_issues] == [i['id'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_limit(self, user, dataset):
        created_issues = [issue_factories.Issue(user=user, user_id=user['id'],
                                                dataset_id=dataset['id'],
                                                description=i)
                          for i in range(0, 10)]
        search_res = helpers.call_action(
            'issue_search',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            sort='oldest',
            limit=5
        )
        issues_list = search_res['results']
        assert [i['id'] for i in created_issues][:5] == [i['id'] for i in issues_list]
        assert search_res['count'] == 5

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_offset(self, user, dataset):
        created_issues = [issue_factories.Issue(user=user, user_id=user['id'],
                                                dataset_id=dataset['id'],
                                                description=i)
                          for i in range(0, 10)]
        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          dataset_id=dataset['id'],
                                          sort='oldest',
                                          offset=5)['results']
        assert [i['id'] for i in created_issues][5:] == [i['id'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_pagination(self, user, dataset):
        created_issues = [issue_factories.Issue(user=user, user_id=user['id'],
                                                dataset_id=dataset['id'],
                                                description=i)
                          for i in range(0, 10)]
        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          dataset_id=dataset['id'],
                                          sort='oldest',
                                          offset=5,
                                          limit=3)['results']
        assert [i['id'] for i in created_issues][5:8] == [i['id'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_filter_newest(self, user, dataset):
        issues = [issue_factories.Issue(
            user=user,
            user_id=user['id'],
            dataset_id=dataset['id'],
            description=i
        ) for i in range(0, 10)]

        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          dataset_id=dataset['id'],
                                          sort='newest')['results']
        assert list(reversed([i['id'] for i in issues])) == [i['id'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_filter_least_commented(self, user, dataset):
        # issue#1 has 3 comment. #2 has 1 comments, etc
        comment_count = [3, 1, 2]
        issue_ids = []
        for i in comment_count:
            issue = issue_factories.Issue(user_id=user['id'],
                                          dataset_id=dataset['id'],
                                          description=i)
            issue_ids.append(issue['id'])

            for j in range(0, i):
                issue_factories.IssueComment(
                    user_id=user['id'],
                    issue_number=issue['number'],
                    dataset_id=issue['dataset_id'],
                )
        reordered_ids = [issue_ids[1], issue_ids[2], issue_ids[0]]

        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          dataset_id=dataset['id'],
                                          sort='least_commented')['results']
        assert reordered_ids == [i['id'] for i in issues_list]
        assert [1, 2, 3] == [i['comment_count'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_filter_most_commented(self, user, dataset):
        # issue#1 has 3 comment. #2 has 1 comments, etc
        comment_count = [3, 1, 2, 0]
        issue_ids = []
        for i in comment_count:
            issue = issue_factories.Issue(user_id=user['id'],
                                          dataset_id=dataset['id'],
                                          description=i)
            issue_ids.append(issue['id'])

            for j in range(0, i):
                issue_factories.IssueComment(
                    user_id=user['id'],
                    issue_number=issue['number'],
                    dataset_id=issue['dataset_id'],
                )

        reordered_ids = [issue_ids[0], issue_ids[2], issue_ids[1],
                         issue_ids[3]]

        issues_list = helpers.call_action('issue_search',
                                          context={'user': user['name']},
                                          dataset_id=dataset['id'],
                                          sort='most_commented')['results']
        assert reordered_ids == [i['id'] for i in issues_list]
        assert [3, 2, 1, 0] == [i['comment_count'] for i in issues_list]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_filter_by_title_string_search(self, user, dataset):
        issues = [issue_factories.Issue(user_id=user['id'],
                                        dataset_id=dataset['id'],
                                        title=title)
                  for title in ['some title', 'another Title', 'issue']]

        filtered_issues = helpers.call_action('issue_search',
                                              context={'user': user['name']},
                                              dataset_id=dataset['id'],
                                              q='title')['results']

        expected_issue_ids = set([i['id'] for i in issues[:2]])
        assert expected_issue_ids == set([i['id'] for i in filtered_issues])


class TestIssueUpdate(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_update_an_issue(self, user, dataset):
        issue = issue_factories.Issue(user=user, user_id=user['id'],
                                      dataset_id=dataset['id'])

        helpers.call_action(
            'issue_update',
            context={'user': user['name']},
            issue_number=issue['number'],
            dataset_id=dataset['id'],
            title='new title',
            description='new description'
        )

        updated = helpers.call_action(
            'issue_show',
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert 'new title' == updated['title']
        assert 'new description' == updated['description']

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_reopen_an_issue(self, user, dataset):
        '''This test is resolve a bug where updating/reopening an issue
        deletes it. Magical'''
        issue = issue_factories.Issue(user=user, user_id=user['id'],
                                      dataset_id=dataset['id'])

        closed = helpers.call_action(
            'issue_update',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            issue_number=issue['number'],
            status='closed'
        )
        assert 'closed' == closed['status']

        after_closed = helpers.call_action(
            'issue_show',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert 'closed' == after_closed['status']

        helpers.call_action(
            'issue_update',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            issue_number=issue['number'],
            status='open',
        )

        reopened = helpers.call_action(
            'issue_show',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            issue_number=issue['number'],
        )
        assert 'open' == reopened['status']

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_cannot_update_visiblity_using_update(self, user, dataset):
        '''we don't want users to be able to set their own abuse status'''
        issue = issue_factories.Issue(user=user, user_id=user['id'],
                                      dataset_id=dataset['id'])
        helpers.call_action(
            'issue_update',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            issue_number=issue['number'],
            visibility='hidden'
        )

        after_update = helpers.call_action(
            'issue_show',
            context={'user': user['name']},
            issue_number=issue['number'],
            dataset_id=dataset['id'],
        )
        assert 'visible' == after_update['visibility']

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_updating_issue_that_does_not_exist_raises_not_found(self, user, dataset):
        pytest.raises(
            toolkit.ObjectNotFound,
            helpers.call_action,
            'issue_update',
            context={'user': user['name']},
            dataset_id=dataset['id'],
            issue_number=10000000,
        )

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_updating_issue_nonexisting_dataset_raises_not_found(self, user):
        pytest.raises(
            toolkit.ValidationError,
            helpers.call_action,
            'issue_update',
            context={'user': user['name']},
            dataset_id='does-not-exist',
            issue_number=10000000,
        )


class TestIssueDelete(object):

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_deletion(self, user, dataset):
        issue = issue_factories.Issue(user=user, user_id=user['id'],
                                      dataset_id=dataset['id'])

        helpers.call_action('issue_delete',
                            context={'user': user['name']},
                            dataset_id=dataset['id'],
                            issue_number=issue['number'])

        pytest.raises(toolkit.ObjectNotFound,
                      helpers.call_action,
                      'issue_show',
                      dataset_id=dataset['id'],
                      issue_number=issue['number'])

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_delete_nonexistent_issue_raises_not_found(self, user, dataset):
        pytest.raises(toolkit.ObjectNotFound,
                      helpers.call_action,
                      'issue_delete',
                      context={'user': user['name']},
                      dataset_id=dataset['id'],
                      issue_number='2')

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_delete_non_integer_parameter_issue_raises_not_found(self, user, dataset):
        '''issue ids are a postgres seqeunce currently'''
        pytest.raises(toolkit.ValidationError,
                      helpers.call_action,
                      'issue_delete',
                      context={'user': user['name']},
                      dataset_id=dataset['id'],
                      issue_number='huh')


class TestOrganizationUsersAutocomplete(object):
    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_fetch_org_editors(self):
        owner = factories.User(name='test_owner')
        editor = factories.User(name='test_editor')
        admin = factories.User(name='test_admin')
        member = factories.User(name='test_member')
        factories.User(name='test_user')
        organization = factories.Organization(user=owner, users=[
            {'name': editor['id'], 'capacity': 'editor'},
            {'name': admin['id'], 'capacity': 'admin'},
            {'name': member['id']}, ])

        result = helpers.call_action('organization_users_autocomplete',
                                     q='test',
                                     organization_id=organization['id'])
        assert set(['test_owner', 'test_editor', 'test_admin']) == set([i['name'] for i in result])


class TestCommentSearch(object):
    @pytest.fixture
    def organization(self):
        return factories.Organization()

    @pytest.fixture
    def issue(self, organization):
        dataset = factories.Dataset(owner_org=organization['id'])
        return issue_factories.Issue(dataset_id=dataset['id'])

    @pytest.fixture
    def comment1(self, issue):
        comment1 = issue_factories.IssueComment(
            issue_number=issue['number'],
            dataset_id=issue['dataset_id'],
        )
        comment_object = IssueComment.get(comment1['id'])
        comment_object.change_visibility(model.Session, u'hidden')
        return comment1

    @pytest.fixture
    def comment2(self, issue):
        comment2 = issue_factories.IssueComment(
            issue_number=issue['number'],
            dataset_id=issue['dataset_id'],
        )
        return comment2

    @pytest.fixture
    def organization2(self):
        return factories.Organization()

    @pytest.fixture
    def issue2(self, organization2):
        dataset = factories.Dataset(owner_org=organization2['id'])
        return issue_factories.Issue(dataset_id=dataset['id'])

    @pytest.fixture
    def comment3(self, issue):
        comment3 = issue_factories.IssueComment(
            issue_number=issue['number'],
            dataset_id=issue['dataset_id'],
        )
        comment_object = IssueComment.get(comment3['id'])
        comment_object.change_visibility(model.Session, u'hidden')
        return comment3

    @pytest.fixture
    def comment4(self, issue):
        comment4 = issue_factories.IssueComment(
            issue_number=issue['number'],
            dataset_id=issue['dataset_id'],
        )
        return comment4

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_reported_search_for_org(self, organization, comment1):
        result = helpers.call_action('issue_comment_search',
                                     organization_id=organization['id'],
                                     only_hidden=True)

        assert [comment1['id']] == [c['id'] for c in result]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_reported_search(self, comment1, comment3):
        result = helpers.call_action(
            'issue_comment_search', only_hidden=True
            )
        ids = [comment1['id'], comment3['id']]
        assert ids == [c['id'] for c in result]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_search_for_org(self, organization, comment1, comment2):
        result = helpers.call_action('issue_comment_search',
                                     organization_id=organization['id'])

        assert [comment1['id'], comment2['id']] == [c['id'] for c in result]

    @pytest.mark.usefixtures("clean_db", "issues_setup")
    def test_search(self, comment1, comment2, comment3, comment4):
        result = helpers.call_action('issue_comment_search')

        ids = [comment1['id'], comment2['id'], comment3['id'], comment4['id']]

        assert ids == [c['id'] for c in result]


@pytest.mark.usefixtures("clean_db", "issues_setup")
@mock.patch("ckanext.issues.logic.action.action.mail_user")
class TestEmailNotifications:

    @pytest.mark.ckan_config("ckanext.issues.send_email_notifications", False)
    def test_email_notifications_are_not_sent_if_disabled(self, mock_mail_user):
        creator = factories.User(name='creator')
        org = factories.Organization()
        dataset = factories.Dataset(owner_org=org["id"])

        toolkit.get_action('issue_create')(
            context={'user': creator['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )
        mock_mail_user.assert_not_called()

    @pytest.mark.ckan_config("ckanext.issues.send_email_notifications", True)
    def test_org_admin_editors_are_notified_when_creating_issue(self, mock_mail_user):
        creator = factories.User(name='creator')
        admin = factories.User(name='admin')
        editor = factories.User(name='editor')
        member = factories.User(name='member')
        org = factories.Organization(
            users=[
                {'name': admin['id'], 'capacity': 'admin'},
                {'name': editor['id'], 'capacity': 'editor'},
                {'name': member['id'], 'capacity': 'member'},
                ]
            )
        dataset = factories.Dataset(owner_org=org['id'])

        toolkit.get_action('issue_create')(
            context={'user': creator['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )

        # CKAN factories adds default user as org admin
        assert len(org["users"]) == 4

        # Assert emails is sent to admin/editors but not members
        assert mock_mail_user.call_count == 3

    @pytest.mark.ckan_config("ckanext.issues.send_email_notifications", True)
    def test_email_notifications_content(self, mock_mail_user):
        sysadmin = factories.Sysadmin(
            name="sys_admin",
            fullname="System Administrator",
            email="sys_admin@example.org"
        )
        creator = factories.User()
        org = helpers.call_action(
            "organization_create",
            {"user": sysadmin["name"]},
            name="test-organization",
            title="Test Organization"
            )
        helpers.call_action(
            "member_create",
            {"user": sysadmin["name"]},
            id=org["id"],
            object=sysadmin["id"],
            object_type="user",
            capacity="admin"
        )
        dataset = helpers.call_action(
            'package_create',
            context={"user": sysadmin["name"]},
            name="my_issue_dataset",
            title="My Issue Dataset",
            owner_org=org["id"]
            )
        issue = toolkit.get_action('issue_create')(
            context={'user': creator['name']},
            data_dict={
                'title': 'Title',
                'description': 'Description',
                'dataset_id': dataset['id'],
            }
        )
        kall = mock_mail_user.mock_calls[0]
        kall_args = kall[1]
        recipient_user, subject, body = kall_args

        # Assert is sent to org admin
        assert recipient_user.id == sysadmin['id']
        assert subject == '[CKAN Issue] My Issue Dataset'
        # Assert creator is mentioned in the body
        assert f"A user {creator['fullname']} has raised" in body

        mock_mail_user.reset_mock()

        commentor = factories.User()
        helpers.call_action(
            "issue_comment_create",
            context={"user": commentor["name"]},
            comment="This is a good comment!",
            issue_number=issue['number'],
            dataset_id=dataset["id"]
        )

        kall = mock_mail_user.mock_calls[0]
        kall_args = kall[1]
        recipient_user, subject, body = kall_args
        # Assert is sent to org admin
        assert recipient_user.id == sysadmin['id']
        assert subject == '[CKAN Issue] My Issue Dataset'

        # Assert commentor is mentioned in the body
        assert f"A user {commentor['fullname']} has added a comment" in body
