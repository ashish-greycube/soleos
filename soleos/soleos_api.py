import frappe
from erpnext import get_default_company
from frappe import _
from frappe.utils import  get_link_to_form,flt
import geopy
from geopy import distance

@frappe.whitelist()
def get_boq_items(boq_template_name):
	print('boq_template_name',boq_template_name)
	boq_template = frappe.get_doc('BOQ Template', boq_template_name)
	boq_template_details = []
	for i, boq_item in enumerate(boq_template.get("boq_template_details")):
		# boq_item = boq_item.as_dict()
		boq_template_details.append(boq_item)
	return boq_template_details


def dn_verify_cogs_against_payment_received(self,method):
	project=self.project
	if project:
		customer=self.customer

		current_dn_amt=0
		for item in self.items:
			current_dn_amt=current_dn_amt+item.incoming_rate
		
		values = {'project': project,'customer':customer}
		pervious_dn = frappe.db.sql("""
					SELECT
						sum(dn_items.incoming_rate) as total_incoming_rate
					FROM
						`tabDelivery Note` as dn
					inner join `tabDelivery Note Item` as dn_items on
						dn.name = dn_items.parent
					WHERE
						dn.project = %(project)s
						and dn.customer = %(customer)s
						and dn.status = 1 
					GROUP BY dn.project""", values=values, as_dict=1)	

		pervious_dn_amt=0
		if len(pervious_dn)>0:
			pervious_dn_amt=pervious_dn[0].total_incoming_rate

		total_dn_amt=pervious_dn_amt+current_dn_amt		
		
		company = get_default_company()
		default_receivable_account = frappe.db.get_value('Company', company, 'default_receivable_account')
		total_paid_amount=get_gl_data(default_receivable_account,customer,project)

		dn_threshold_percentage = frappe.db.get_single_value('SOLEOS Settings', 'dn_threshold_percentage')
		dn_warning_prefrence = frappe.db.get_single_value('SOLEOS Settings', 'dn_warning_prefrence')
		dn_role_allowed_to_exceed = frappe.db.get_single_value('SOLEOS Settings', 'dn_role_allowed_to_exceed')

		allowed_amount_to_be_used=(dn_threshold_percentage*total_paid_amount)/100
		current_balance_amount=total_paid_amount-total_dn_amt
		exceeded_amount=current_balance_amount-allowed_amount_to_be_used
		user = frappe.get_doc("User", frappe.session.user)
		user_roles = [d.role for d in user.roles or []]
		if current_balance_amount<0 or current_balance_amount>allowed_amount_to_be_used:
			msg=("Payment received is <b>{0}</b> <br> Total COGS till date including current DN is <b>{1}</b><br>Allowed threshold is <b>{2}%</b> i.e. <b>{3}</b> is allowed amount.<br>COGS will exceed by <b>{4}</b>").format(total_paid_amount, total_dn_amt,dn_threshold_percentage,allowed_amount_to_be_used,abs(exceeded_amount))

			if dn_warning_prefrence=="Warning":
				frappe.msgprint(
					msg=msg,
					title='Warning'
				)			

			elif dn_warning_prefrence=="Stop" and (dn_role_allowed_to_exceed in user_roles):
				frappe.msgprint(
					msg=msg,
					title='Warning for Allowed Role'
				)			
			elif dn_warning_prefrence=="Stop":
				frappe.throw(
					msg=msg,
					title='Error'
				)			
			 



def po_verify_cogs_against_payment_received(self,method):
	project=self.project
	if project:
		customer=frappe.db.get_value('Project',project, 'customer')
		current_po_amt=self.base_rounded_total

		values = {'project': project,'customer':customer}
		pervious_po = frappe.db.sql("""
					SELECT
						sum(po.base_rounded_total) as total_rounded_total
					FROM
						`tabPurchase Order` as po
					WHERE
						po.project = %(project)s
						and po.docstatus = 1 
					GROUP BY po.project""", values=values, as_dict=1,debug=0)	

		pervious_po_amt=0
		if len(pervious_po)>0:
			pervious_po_amt=pervious_po[0].total_rounded_total

		total_po_amt=pervious_po_amt+current_po_amt		
		
		company = get_default_company()
		default_receivable_account = frappe.db.get_value('Company', company, 'default_receivable_account')
		total_paid_amount=get_gl_data(default_receivable_account,customer,project)

		po_threshold_percentage = frappe.db.get_single_value('SOLEOS Settings', 'po_threshold_percentage')
		po_warning_prefrence = frappe.db.get_single_value('SOLEOS Settings', 'po_warning_prefrence')
		po_role_allowed_to_exceed = frappe.db.get_single_value('SOLEOS Settings', 'po_role_allowed_to_exceed')

		allowed_amount_to_be_used=(po_threshold_percentage*total_paid_amount)/100
		current_balance_amount=total_paid_amount-total_po_amt
		exceeded_amount=current_balance_amount-allowed_amount_to_be_used
		user = frappe.get_doc("User", frappe.session.user)
		user_roles = [d.role for d in user.roles or []]
		if current_balance_amount<0 or current_balance_amount>allowed_amount_to_be_used:
			msg=("Payment received is <b>{0}</b> <br> Total PO amount till date, including current PO is <b>{1}</b><br>Allowed threshold is <b>{2}%</b> i.e. <b>{3}</b> is allowed amount.<br>Purchase will exceed by <b>{4}</b>").format(total_paid_amount, total_po_amt,po_threshold_percentage,allowed_amount_to_be_used,abs(exceeded_amount))

			if po_warning_prefrence=="Warning":
				frappe.msgprint(
					msg=msg,
					title='Warning'
				)			

			elif po_warning_prefrence=="Stop" and (po_role_allowed_to_exceed in user_roles):
				frappe.msgprint(
					msg=msg,
					title='Warning for Allowed Role'
				)			
			elif po_warning_prefrence=="Stop":
				frappe.throw(
					msg=msg,
					title='Error'
				)	


def get_gl_data(account,customer,project):
	paid_amount=0
	values = {'account':account,'customer':customer,'project': project}
	gl_data = frappe.db.sql("""SELECT
	 SUM(gl.credit_in_account_currency - gl.debit_in_account_currency) as paid_amount
FROM
	`tabGL Entry` as gl
WHERE
	gl.party_type = 'Customer'
	and gl.account =%(account)s
	and gl.party =%(customer)s
	and gl.project =%(project)s
GROUP BY
	gl.project """, values=values, as_dict=1,debug=0)	
	if len(gl_data)>0:
		paid_amount=gl_data[0].paid_amount
	return paid_amount


def validate_dependent_task_status(self,method):
	task_role_allowed_to_bypass_dependent_task = frappe.db.get_single_value('SOLEOS Settings', 'task_role_allowed_to_bypass_dependent_task')
	user = frappe.get_doc("User", frappe.session.user)
	user_roles = [d.role for d in user.roles or []]	
	if self.status == "Working":
		if self.depends_on and len(self.depends_on)>0:
			for dep_task in self.depends_on:
				dep_status = frappe.db.get_value('Task', dep_task.task, 'status')
				if dep_status!= "Completed":
					dep_task_url=get_link_to_form('Task',dep_task.task)
					if (task_role_allowed_to_bypass_dependent_task in user_roles):
						frappe.msgprint(
							msg='{0}  has status {1}. Please complete it first.'.format(frappe.bold(dep_task_url),frappe.bold(dep_status)),
							title='Dependent task is not complete'
						)	
					else:					
						frappe.throw(
							msg='{0}  has status {1}. Please complete it first.'.format(frappe.bold(dep_task_url),frappe.bold(dep_status)),
							title='Dependent task is not complete'
						)					

def check_with_geo_location_range(self,method):
	if self.employee:
		check_against_geo_location = frappe.db.get_value("Employee",self.employee,"custom_check_against_geo_location")
		if check_against_geo_location and check_against_geo_location == 1:
			if self.latitude and self.longitude:
				current_latitude, current_longitude = self.latitude, self.longitude
				current_geo_location = (current_latitude, current_longitude)
				soleos_settings_doc = frappe.get_doc("Soleos Settings","Soleos Settings")
				if len(soleos_settings_doc.office_location)>0:
					allowed = False
					for row in soleos_settings_doc.office_location:
						office_latitude, office_longitude = row.latitude, row.longitude
						office_geo_location = (office_latitude, office_longitude)
						distance_between_two_points = distance.distance(current_geo_location, office_geo_location).m

						if distance_between_two_points > row.allowed_check_in_range:
							allowed = False
						elif distance_between_two_points <= row.allowed_check_in_range:
							allowed = True
							break

				if allowed == True:
					frappe.msgprint(_("You are checked in, you are in {0} meters from office").format(flt(distance_between_two_points,2)),alert=True)
				elif allowed == False:
					frappe.throw(_("You are not allowed to check in because you are not in office location range."))