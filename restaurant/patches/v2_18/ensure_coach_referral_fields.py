"""Provision the native ERPNext fields used by the coach/referral flow."""


def execute():
	from restaurant import api

	api._club_ensure_ops_ready()
