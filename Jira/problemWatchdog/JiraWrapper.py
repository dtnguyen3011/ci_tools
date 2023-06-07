#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ==============================================================================
#  C O P Y R I G H T
# ------------------------------------------------------------------------------
#  Copyright (c) 2019 by Robert Bosch GmbH. All rights reserved.
#
#  This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
#  distribution is an offensive act against international law and may be
#  prosecuted under federal law. Its content is company confidential.
# ==============================================================================

from jira import JIRA, JIRAError
class JiraWrapper(JIRA):

	JIRA_URL = "https://rb-tracker.bosch.com/tracker08"
	TICKET_URL = "https://rb-tracker.bosch.com/tracker08/browse/"

	def __init__(self, *args, **kwargs):
		super().__init__(self.JIRA_URL, *args, **kwargs)


	def get_issue(self, id):
		"""
		Get Jira ticket 
		:param id: number or id of the Jira ticket
		"""
		try:
			return self.issue(id)
		except JIRAError as e:
			print("[ERROR] could not get Jira issue. Error code {}: {}".format(e.status_code, e.text))
			raise


	def __get_user_id(self, email):
		"""
		Get user id. Returns email parameter if email doesn't end with .com 
		:param email: email of the user
		"""
		if '@' in email:
			try:
				return self.search_users(email)[0].name
			except JIRAError as e:
				print("[ERROR] could not get user id. Error code {}: {}".format(e.status_code, e.text))
				raise
			except IndexError as e:
				print("[ERROR] user email {} does not exist".format(email))
				raise
		else:
			return email


	def __update_issue(self, id, field, data):
		"""
		Update a field of a Jira ticket
		:param id: number or id of the Jira ticket
		:param field: name of the field to update e.g. customfield_10160
		:param data: data for the field
		"""
		try:
			self.get_issue(id).update(fields={field: data})
		except JIRAError as e:
			print("[ERROR] could not update Jira issue. Error code {}: {}".format(e.status_code, e.text))
			raise

	def search_issues(self, jql_str, *args, **kwargs):
		try:
			return super().search_issues(jql_str, maxResults=False, *args, **kwargs)
		except JIRAError as e:
			print("[ERROR] could not search Jira issues. Error code {}: {}".format(e.status_code, e.text))
			raise


	def	add_title(self, id, title):
		"""
		Updates the title of a Jira ticket
		:param id: number or id of the Jira ticket
		:param title: title of the Jira ticket
		"""
		self.__update_issue(id, 'summary', title)

	def update_assignee(self, id, assignee):
		"""
		(Re)assign Jira ticket
		:param id: number or id of the Jira ticket 
		:param assignee: user id or email the Jira ticket shall be assigned to
		"""
		self.__update_issue(id, 'assignee', {'name': self.__get_user_id(assignee)})


	def add_assistance(self, id, assistance):
		"""
		Add assistance to a Jira ticket
		:param id: number or id of the Jira ticket
		:param assistance: list of user ids which shall be added as assistance
		"""
		current_ass = []
		if self.get_issue(id).fields.customfield_10160:
			for ass in self.get_issue(id).fields.customfield_10160: # customfield_10160 = Assitance
				current_ass.append({'name': ass.key})
		for ass in assistance:
			current_ass.append({'name': self.__get_user_id(ass)})
		self.__update_issue(id, 'customfield_10160', current_ass)


	def add_description(self, id, description, variables={}, add_hint=True):
		"""
		Add description to a Jira ticket
		:param id: number or id of the Jira ticket
		:param description: list of lines to add to the description
		"""
		des = ''
		if self.get_issue(id).fields.description:
			des = self.get_issue(id).fields.description + "\n"
		for line in description:
			des += line + "\n"
		if variables:
			des = des.format(**variables)
		if add_hint:
			des += "\n" + "You want to adapt the ticket (assignee, description, ...)? Please see https://inside-docupedia.bosch.com/confluence/display/DP/XL+Release 'How to adapt the release flow?'"
		self.__update_issue(id, 'description', des)


	def add_ac(self, id, acs, variables={}):
		"""
		Add acceptance criteria to a Jira ticket
		:param id: number or id of the Jira ticket
		:param acs: list of acceptance criteria 
		"""
		ac = ''
		if self.get_issue(id).fields.customfield_16428: # customfield_16428 = Acceptance criteria
			ac = self.get_issue(id).fields.customfield_16428 + "\n"
		i = 1 # TODO check if number has to be increased if there are already acs
		for c in acs:
			ac += "#{}: ".format(i) + c + "\n"
			i += 1
		if variables:
			ac = ac.format(**variables)
		self.__update_issue(id, 'customfield_16428', ac)
		
	
	def add_labels(self, id, labels):
		"""
		Add label to Jira ticket
		:param id: number or id of the Jira ticket
		:param labels: list of labels
		"""
		label_list = self.get_issue(id).fields.labels
		for label in labels:
			label_list.append(label)
		self.__update_issue(id, 'labels', label_list)
