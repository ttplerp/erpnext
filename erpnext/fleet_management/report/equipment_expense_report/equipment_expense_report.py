# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint,add_days, cstr, flt, getdate, nowdate, rounded, date_diff
#from erpnext.hr.hr_custom_functions import get_month_details
def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data = []
	cond = " and 1 =1"
	if filters.get("branch"):
		cond += " and eh.branch = '{0}'".format(filters.branch)
			
		if filters.get("include_disabled"):
			cond += " and e.is_disabled = 1"

	equipments = """
		select * from (select e.name, eh.branch, eh.from_date, ifnull(eh.to_date, curdate()) as to_date, e.equipment_model,
		e.equipment_type from `tabEquipment` e, `tabEquipment History` eh  where eh.parent = e.name {0} group by e.name, eh.branch) 
		as equip left join
		(select eo.operator, eo.start_date, ifnull(eo.end_date, curdate()) as end_date, eo.parent 
		from `tabEquipment Operator` eo)
		as opr 
		on opr.parent = equip.name 
	""".format(cond)
	filter_date  = " between '{0}' and '{1}'".format(filters.from_date, filters.to_date) 
	for eq in frappe.db.sql(equipments, as_dict = True):
		date = " between '{0}' and '{1}'".format(eq.from_date, eq.to_date)
		gross_pay = tc = le = ot = 0.0
		if eq.operator:
			date = " between '{0}' and '{1}'".format(eq.start_date, eq.end_date)
		if eq.employee_type == "Muster Roll Employee":
			#PRoCESS FROM "PROCESS MR PAYMENT"
			mr_pay = frappe.db.sql("""
					select sum(ifnull(mi.total_wage,0)) as mr_wage, sum(ifnull(mi.total_ot_amount,0)) as mr_ot 
					from `tabProcess MR Payment` mr , `tabMR Payment Item` mi
					where mi.parent = mr.name
					and mi.id_card = '{0}' 
					and mr.docstatus = 1 and mr.branch = '{2}'
					and mr.posting_date {1} and mr.posting_date {3}
				""".format(eq.operator, date, eq.branch, filter_date), as_dict=1)[0]
			gross_pay    = flt(mr_pay.mr_wage)
			ot = flt(mr_pay.mr_ot)
		elif eq.employee_type == "Employee":
			#get tc
			tc = frappe.db.sql("""
					select sum(ifnull(tc.total_claim_amount,0)) as travel_claim
					from `tabTravel Claim` tc 
					where tc.employee = '{0}'
					and   tc.docstatus = 1
					and tc.branch = '{2}' and tc.posting_date {1} and tc.posting_date {3}
				""".format(eq.operator, date, eq.branch, filter_date), as_dict=1)[0]

			tc = flt(tc.travel_claim)
			#Leave Encashment Aomunt
			lea = frappe.db.sql("""
					select sum(ifnull(le.encashment_amount,0)) as e_amount 
					from `tabLeave Encashment` le
					where le.employee = '{0}'
					and   le.docstatus = 1 and le.branch = '{3}'
					and   le.encashment_date {1} and le.encashment_date {2}
					""".format(eq.operator, date, filter_date, eq.branch), as_dict=1)[0]
			le = flt(lea.e_amount)
			ota = frappe.db.sql("""
					select sum(ifnull((ot.rate*oti.number_of_hours), 0)) as amount from `tabOvertime Application` ot, 
					`tabOvertime Application Item` oti 
					where oti.parent = ot.name and ot.docstatus = 1 and 
					oti.date {0} and ot.employee = '{1}'  and oti.date {2} and ot.branch = '{3}'
					""".format(date, eq.operator, filter_date, eq.branch), as_dict =1)[0]
			ot = flt(ota.amount)
			#process salary
			ss_date = " between ssi.from_date and ssi.to_date"
			'''sal = frappe.db.sql("""
				select ss.name, ss.employee, ss.branch,  ss.gross_pay, ssi.from_date, ssi.to_date
				from `tabSalary Slip` ss, `tabSalary Slip Item` ssi 
				where ss.employee = '{0}' and ssi.parent = ss.name
				and ss.docstatus = 1
				and ss.branch = '{1}' and (((ssi.from_date {2}) or (ssi.to_date {2}))  or 
				(( '{3}' {5})  or ('{4}' {5}))) 
						""".format(eq.operator, eq.branch, date, filters.from_date, filters.to_date, ss_date), as_dict = True)'''

			sal = frappe.db.sql("""
								select ss.name, ss.employee, ss.branch,  ss.gross_pay, ssi.from_date, ssi.to_date
								from `tabSalary Slip` ss, `tabSalary Slip Item` ssi 
								where ss.employee = '{0}' and ssi.parent = ss.name
								and ss.docstatus = 1
								and ss.branch = '{1}' and (((ssi.from_date {2}) or (ssi.to_date {2})) or (( '{3}' {5}) or ('{4}' {5}))) and '{3}' 
				<= '{6}' 
						""".format(eq.operator, eq.branch, date, eq.start_date, eq.end_date, ss_date, filters.to_date), as_dict = True)

			if sal:
				gross_pay= 0.0
			for s in sal:
					total_days = flt(date_diff(s.to_date, s.from_date) + 1)
					s_start_date = getdate(s.from_date)
					s_end_date = getdate(s.to_date)
					f_from_date =  getdate(filters.from_date)
					f_to_date =    getdate(filters.to_date)
					if f_from_date <= s_start_date and s_end_date <=  f_to_date:
						if f_from_date < getdate(eq.start_date) < f_to_date:
							work_date = flt(date_diff(s_end_date, eq.start_date) +1)
							gross_pay += flt(s.gross_pay)*flt(work_date)/flt(total_days)
							#frappe.msgprint("a000")
						elif f_from_date < getdate(eq.end_date) < f_to_date:
							#frappe.msgprint("a00")
							work_date = flt(date_diff(eq.end_date, f_from_date) +1)
							gross_pay += flt(s.gross_pay)*flt(work_date)/flt(total_days)
						else:
							gross_pay += flt(s.gross_pay)
							#frappe.msgprint("a0")
					if getdate(eq.end_date) < f_from_date:
							gross_pay == 0.0
							#frappe.msgprint("a")
					if s_start_date < f_from_date < s_end_date and  s_start_date < f_to_date < s_end_date:
						work_date = flt(date_diff(s_start_date, f_from_date) +1)
						gross_pay += flt(s.gross_pay)*flt(work_date)/flt(total_days)
						#frappe.msgprint("b a {0}, w{1}, t{2}".format(gross_pay, work_date, total_days))

					if s_start_date < f_from_date and f_from_date <= s_end_date <=  f_to_date and getdate(eq.end_date) > f_from_date:
						work_date = flt(date_diff(s_end_date, f_from_date) +1)
						gross_pay += flt(s.gross_pay)*flt(work_date)/flt(total_days)  
						#frappe.msgprint("c a {0}, w{1}, t{2}".format(gross_pay, work_date, total_days))

					if f_from_date <=  s_start_date <= f_to_date and s_end_date > f_to_date:
						work_date = flt(date_diff(f_to_date, s_start_date) +1)
						gross_pay += flt(s.gross_pay)*flt(work_date)/flt(total_days)
						#frappe.msgprint("b a {0}, w{1}, t{2}".format(gross_pay, work_date, total_days))

		pol, insurance, registration, fitness, goods_amount, service_amount = equipment_expense(filters, eq.name, eq.branch, date, filter_date)
		total = flt(pol) + flt(insurance) + flt(registration) + flt(fitness) + flt(goods_amount) + flt(service_amount) + flt(gross_pay) +  flt(le) + flt(tc) + flt(ot)
		row = [eq.name, eq.branch, eq.registration_number, eq.equipment_type, eq.operator, pol, insurance, registration, fitness, goods_amount, service_amount, total]
		data.append(row)
	return data

# def equipment_expense(filters, eq_name, eq_branch, date, filter_date):	

# 	# `tabPOL`
# 	pol = frappe.db.sql("""
# 			select (sum(qty*rate)/sum(qty)) as rate
# 			from `tabPOL Receive`
# 			where branch = '{0}'
# 			and   docstatus = 1 and posting_date {1} and posting_date {2}
#                     """.format(eq_branch, date, filter_date), as_dict=1)[0]
                
# 	#Insurance
# 	ins = frappe.db.sql("""
# 			select sum(ifnull(id.total_amount,0)) as insurance  
# 			from `tabInsurance Details` id,	`tabInsurance and Registration` ir 
# 			where id.parent = ir.name and id.insurance_type = '{0}'
# 			and   id.insured_date {1} and id.insured_date {2}
# 		 """.format(eq_name, date, filter_date), as_dict=1)[0]

# 	# ins = frappe.db.sql("""
#     #     SELECT SUM(IFNULL(id.insured_amount, 0)) AS insurance  
#     #     FROM `tabInsurance Details` id
#     #     JOIN `tabInsurance and Registration` ir 
#     #     ON id.parent = ir.name
#     #     WHERE ir.insurance_type = '{0}'
#     #     AND id.insured_date {1} 
#     #     AND id.insured_date {2}
#     # """.format(eq_name, date, filter_date), as_dict=1)[0]
	
# 	#Reg fee
# 	reg = frappe.db.sql("""
# 			select sum(ifnull(rd.registration_amount,0)) as r_amount
# 			from `tabRegistration Details` rd, `tabInsurance and Registration` i  
# 				where rd.parent = i.name  
# 				and i.equipment = '{0}'
#                                 and   rd.registration_date {1} and rd.registration_date {2}
# 			""".format(eq_name, date, filter_date), as_dict=1)[0]
	
# 	# return round(flt(vl.consumption)*flt(pol.rate),2), round(flt(ins.insurance)+flt(reg.r_amount),2), round(flt(jc.goods_amount),2), round(flt(jc.services_amount),2)
# 	return round(flt(ins.insurance),2)

def equipment_expense(filters, eq_name, eq_branch, date, filter_date):	
    # Initialize all variables with 0.0
    pol = insurance = registration = fitness = goods_amount = service_amount = 0.0

    # `tabPOL`
    pol_data = frappe.db.sql("""
            select sum(qty*rate) as rate
            from `tabPOL Receive`
            where branch = '{0}'
            and   docstatus = 1 and posting_date {1} and posting_date {2}
            """.format(eq_branch, date, filter_date), as_dict=1)
    
    if pol_data:
        pol = flt(pol_data[0].get('rate', 0))

    # Insurance
    # ins_data = frappe.db.sql("""
    #         select sum(ifnull(id.total_amount,0)) as insurance  
    #         from `tabInsurance Details` id, `tabInsurance and Registration` ir 
    #         where id.parent = ir.name and id.insurance_type = '{0}'
    #         and   id.insured_date {1} and id.insured_date {2}
    #         """.format(eq_name, date, filter_date), as_dict=1)
    
    # if ins_data:
    #     insurance = flt(ins_data[0].get('insurance', 0))

    # Reg fee
    reg_data = frappe.db.sql("""
            select sum(ifnull(rd.registration_amount,0)) as r_amount
            from `tabRegistration Details` rd, `tabInsurance and Registration` i  
            where rd.parent = i.name  
            and i.equipment = '{0}'
            and rd.registration_date {1} and rd.registration_date {2}
            """.format(eq_name, date, filter_date), as_dict=1)
    
    if reg_data:
        insurance += flt(reg_data[0].get('r_amount', 0))  # Adding registration amount to insurance

    # You should also query for goods_amount and service_amount here
    # For example:
    serv_data = frappe.db.sql("""
		select sum(ifnull(rsi.charge_amount, 0)) as amount
		from `tabRepair And Service Invoice` rs, `tabRepair And Services Invoice Item` rsi, `tabItem` i where rsi.parent = rs.name and rsi.item_code = i.name and rs.equipment = '{0}'
		and i.item_group like '%Service%'
		and rs.docstatus = 1 and rs.posting_date {1} and rs.posting_date {2}
	""".format(eq_name, date, filter_date), as_dict=1)
    goods_data = frappe.db.sql("""
		select sum(ifnull(rsi.charge_amount, 0)) as amount
		from `tabRepair And Service Invoice` rs, `tabRepair And Services Invoice Item` rsi, `tabItem` i where rsi.parent = rs.name and rsi.item_code = i.name and rs.equipment = '{0}'
		and i.item_group = 'Consumable'
		and rs.docstatus = 1 and rs.posting_date {1} and rs.posting_date {2}
	""".format(eq_name, date, filter_date), as_dict=1)
    if serv_data:
        service_amount = flt(serv_data[0].get('amount', 0))
    if goods_data:
        goods_amount = flt(goods_data[0].get('amount', 0))

	# Insurance and Registration
    insurance_data = frappe.db.sql("""
		select sum(ifnull(id.total_amount, 0)) as amount
		from `tabInsurance and Registration` ir, `tabInsurance Details` id where id.parent = ir.name and ir.equipment = '{0}'
		and ir.docstatus = 0 and id.insured_date {1} and id.insured_date {2}
	""".format(eq_name, date, filter_date), as_dict=1)
    registration_data = frappe.db.sql("""
		select sum(ifnull(rd.registration_amount, 0)) as amount
		from `tabInsurance and Registration` ir, `tabRegistration Details` rd where rd.parent = ir.name and ir.equipment = '{0}'
		and ir.docstatus = 0 and rd.registration_date {1} and rd.registration_date {2}
	""".format(eq_name, date, filter_date), as_dict=1)
    fitness_data = frappe.db.sql("""
		select sum(ifnull(be.total_amount, 0)) as amount
		from `tabInsurance and Registration` ir, `tabBluebook and Emission` be where be.parent = ir.name and ir.equipment = '{0}'
		and ir.docstatus = 0 and be.receipt_date {1} and be.receipt_date {2}
	""".format(eq_name, date, filter_date), as_dict=1)
    if insurance_data:
        insurance = flt(insurance_data[0].get('amount', 0))
    if registration_data:
        registration = flt(registration_data[0].get('amount', 0))
    if fitness_data:
        fitness = flt(fitness_data[0].get('amount', 0))
    return (
        round(pol, 2), 
        round(insurance, 2), 
        round(registration, 2), 
        round(fitness, 2), 
        round(goods_amount, 2), 
        round(service_amount, 2)
    )

	
def get_columns(filters):
	cols = [
		("ID") + ":Link/Equipment:120",
		("Branch") + ":Data:120",
		("Registration No") + ":Link/Equipment Model:120",
		("Equipment Type") + ":Data:120",
		("Operator/Driver") + ":Data:120",
		("HSD Consumption(Nu.)") + ":Float:200",
		("Insurance(Nu.)") + ":Float:150",
		("Registration(Nu.)") + ":Float:150",
		("Fitness & Emission(Nu.)") + ":Float:150",
		("Goods Amount") + ":Float:120",
		("Services Amount") + ":Float:120",
		("Total Expense") + ":Float:120"
	]
	return cols
