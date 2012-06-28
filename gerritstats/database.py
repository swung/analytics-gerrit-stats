#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gerrit-stats: Generate codereview stats based from Gerrit commits
Copyright (C) 2012  Diederik van Liere, Wikimedia Foundation

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from peewee import MySQLDatabase, Model, DateTimeField, IntegerField, TextField, CharField, BigIntegerField, ForeignKeyField, PrimaryKeyField
from config import settings

database = MySQLDatabase('reviewdb', **settings)

class UnknownFieldType(object):
    pass

class BaseModel(Model):
    class Meta:
        database = database

class AccountAgreements(BaseModel):
    accepted_on = DateTimeField()
    account = IntegerField(db_column='account_id')
    cla = IntegerField(db_column='cla_id')
    review_comments = TextField()
    reviewed_by = IntegerField()
    reviewed_on = DateTimeField()
    status = CharField()

    class Meta:
        db_table = 'account_agreements'

class AccountDiffPreferences(BaseModel):
    context = IntegerField()
    expand_all_comments = CharField()
    ignore_whitespace = CharField()
    intraline_difference = CharField()
    line_length = IntegerField()
    retain_header = CharField()
    show_tabs = CharField()
    show_whitespace_errors = CharField()
    skip_deleted = CharField()
    skip_uncommented = CharField()
    syntax_highlighting = CharField()
    tab_size = IntegerField()

    class Meta:
        db_table = 'account_diff_preferences'

class AccountExternalIds(BaseModel):
    account = IntegerField(db_column='account_id')
    email_address = CharField()
    external = CharField(db_column='external_id')
    password = CharField()

    class Meta:
        db_table = 'account_external_ids'

class AccountGroupAgreements(BaseModel):
    accepted_on = DateTimeField()
    cla = IntegerField(db_column='cla_id')
    group = IntegerField(db_column='group_id')
    review_comments = TextField()
    reviewed_by = IntegerField()
    reviewed_on = DateTimeField()
    status = CharField()

    class Meta:
        db_table = 'account_group_agreements'

class AccountGroupId(BaseModel):
    s = BigIntegerField()

    class Meta:
        db_table = 'account_group_id'

class AccountGroupIncludes(BaseModel):
    group = IntegerField(db_column='group_id')
    include = IntegerField(db_column='include_id')

    class Meta:
        db_table = 'account_group_includes'

class AccountGroupIncludesAudit(BaseModel):
    added_by = IntegerField()
    added_on = DateTimeField()
    group = IntegerField(db_column='group_id')
    include = IntegerField(db_column='include_id')
    removed_by = IntegerField()
    removed_on = DateTimeField()

    class Meta:
        db_table = 'account_group_includes_audit'

class AccountGroupMembers(BaseModel):
    account = IntegerField(db_column='account_id')
    group = IntegerField(db_column='group_id')

    class Meta:
        db_table = 'account_group_members'

class AccountGroupMembersAudit(BaseModel):
    account = IntegerField(db_column='account_id')
    added_by = IntegerField()
    added_on = DateTimeField()
    group = IntegerField(db_column='group_id')
    removed_by = IntegerField()
    removed_on = DateTimeField()

    class Meta:
        db_table = 'account_group_members_audit'

class AccountGroupNames(BaseModel):
    group = IntegerField(db_column='group_id')
    name = CharField()

    class Meta:
        db_table = 'account_group_names'

class AccountGroups(BaseModel):
    description = TextField()
    email_only_authors = CharField()
    external_name = CharField()
    group = IntegerField(db_column='group_id')
    group_type = CharField()
    group_uuid = CharField()
    name = CharField()
    owner_group = IntegerField(db_column='owner_group_id')
    visible_to_all = CharField()

    class Meta:
        db_table = 'account_groups'

class AccountId(BaseModel):
    s = BigIntegerField()

    class Meta:
        db_table = 'account_id'

class AccountPatchReviews(BaseModel):
    account = IntegerField(db_column='account_id')
    change = IntegerField(db_column='change_id')
    file_name = CharField()
    patch_set = IntegerField(db_column='patch_set_id')

    class Meta:
        db_table = 'account_patch_reviews'

class AccountProjectWatches(BaseModel):
    account = IntegerField(db_column='account_id')
    filter = CharField()
    notify_all_comments = CharField()
    notify_new_changes = CharField()
    notify_submitted_changes = CharField()
    project_name = CharField()

    class Meta:
        db_table = 'account_project_watches'

class AccountSshKeys(BaseModel):
    account = IntegerField(db_column='account_id')
    seq = IntegerField()
    ssh_public_key = TextField()
    valid = CharField()

    class Meta:
        db_table = 'account_ssh_keys'

class Accounts(BaseModel):
    account = PrimaryKeyField(db_column='account_id')
    contact_filed_on = DateTimeField()
    copy_self_on_email = CharField()
    date_format = CharField()
    display_patch_sets_in_reverse_order = CharField()
    display_person_name_in_review_category = CharField()
    download_command = CharField()
    download_url = CharField()
    full_name = CharField()
    inactive = CharField()
    maximum_page_size = IntegerField()
    preferred_email = CharField()
    registered_on = DateTimeField()
    show_site_header = CharField()
    time_format = CharField()
    use_flash_clipboard = CharField()

    class Meta:
        db_table = 'accounts'

class ApprovalCategories(BaseModel):
    abbreviated_name = CharField()
    category = CharField(db_column='category_id')
    copy_min_score = CharField()
    function_name = CharField()
    name = CharField()
    position = IntegerField()

    class Meta:
        db_table = 'approval_categories'

class ApprovalCategoryValues(BaseModel):
    category = CharField(db_column='category_id')
    name = CharField()
    value = IntegerField()

    class Meta:
        db_table = 'approval_category_values'

class ChangeId(BaseModel):
    s = BigIntegerField()

    class Meta:
        db_table = 'change_id'

class ChangeMessageId(BaseModel):
    s = BigIntegerField()

    class Meta:
        db_table = 'change_message_id'

class ChangeMessages(BaseModel):
    author = IntegerField(db_column='author_id')
    change = IntegerField(db_column='change_id')
    message = TextField()
    patchset_change = IntegerField(db_column='patchset_change_id')
    patchset_patch_set = IntegerField(db_column='patchset_patch_set_id')
    uuid = CharField()
    written_on = DateTimeField()

    class Meta:
        db_table = 'change_messages'

class Changes(BaseModel):
    change = PrimaryKeyField()
    change_key = CharField()
    created_on = DateTimeField()
    current_patch_set = IntegerField(db_column='current_patch_set_id')
    dest_branch_name = CharField()
    dest_project_name = CharField()
    last_sha1_merge_tested = CharField()
    last_updated_on = DateTimeField()
    mergeable = CharField()
    nbr_patch_sets = IntegerField()
    open = CharField()
    owner_account = IntegerField(db_column='owner_account_id')
    row_version = IntegerField()
    sort_key = CharField()
    status = CharField()
    subject = CharField()
    topic = CharField()

    class Meta:
        db_table = 'changes'

class ContributorAgreements(BaseModel):
    active = CharField()
    agreement_url = CharField()
    auto_verify = CharField()
    require_contact_information = CharField()
    short_description = CharField()
    short_name = CharField()

    class Meta:
        db_table = 'contributor_agreements'

class PatchComments(BaseModel):
    author = IntegerField(db_column='author_id')
    change = ForeignKeyField(Changes, db_column='change_id')
    file_name = CharField()
    line_nbr = IntegerField()
    message = TextField()
    parent_uuid = CharField()
    patch_set = IntegerField(db_column='patch_set_id')
    side = IntegerField()
    status = CharField()
    uuid = CharField()
    written_on = DateTimeField()

    class Meta:
        db_table = 'patch_comments'

class PatchSetAncestors(BaseModel):
    ancestor_revision = CharField()
    change = ForeignKeyField(Changes, db_column='change_id')
    patch_set = IntegerField(db_column='patch_set_id')
    position = IntegerField()

    class Meta:
        db_table = 'patch_set_ancestors'

class PatchSetApprovals(BaseModel):
    account = IntegerField(db_column='account_id')
    category = CharField(db_column='category_id')
    change = ForeignKeyField(Changes, db_column='change_id')
    change_open = CharField()
    change_sort_key = CharField()
    granted = DateTimeField()
    patch_set = IntegerField(db_column='patch_set_id')
    value = IntegerField()

    class Meta:
        db_table = 'patch_set_approvals'

class PatchSets(BaseModel):
    change = ForeignKeyField(Changes, db_column='change_id')
    created_on = DateTimeField()
    draft = CharField()
    patch_set = IntegerField(db_column='patch_set_id')
    revision = CharField()
    uploader_account = IntegerField(db_column='uploader_account_id')

    class Meta:
        db_table = 'patch_sets'

class SchemaVersion(BaseModel):
    singleton = CharField()
    version_nbr = IntegerField()

    class Meta:
        db_table = 'schema_version'

class StarredChanges(BaseModel):
    account = IntegerField(db_column='account_id')
    change = IntegerField(db_column='change_id')

    class Meta:
        db_table = 'starred_changes'

class SubmoduleSubscriptions(BaseModel):
    submodule_branch_name = CharField()
    submodule_path = CharField()
    submodule_project_name = CharField()
    super_project_branch_name = CharField()
    super_project_project_name = CharField()

    class Meta:
        db_table = 'submodule_subscriptions'

class SystemConfig(BaseModel):
    admin_group = IntegerField(db_column='admin_group_id')
    admin_group_uuid = CharField()
    anonymous_group = IntegerField(db_column='anonymous_group_id')
    batch_users_group = IntegerField(db_column='batch_users_group_id')
    batch_users_group_uuid = CharField()
    owner_group = IntegerField(db_column='owner_group_id')
    register_email_private_key = CharField()
    registered_group = IntegerField(db_column='registered_group_id')
    singleton = CharField()
    site_path = CharField()
    wild_project_name = CharField()

    class Meta:
        db_table = 'system_config'

class TrackingIds(BaseModel):
    change = IntegerField(db_column='change_id')
    tracking = CharField(db_column='tracking_id')
    tracking_system = CharField()

    class Meta:
        db_table = 'tracking_ids'

