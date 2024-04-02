# Copyright (c) 2024, quantbit technologies pvt ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BulkPaymentEntry(Document):
	

	def on_submit(self):
		self.payment_entry()

	
	@frappe.whitelist()
	def set_party_type(self):
		# if self.party_type and self.payment_type:
		# 	for entry in self.get(["bulk_payment_entry_details", "deduction", "taxes"]):
		# 		for i in entry:
		# 			i.party_type = self.party_type
		# 			i.payment_type = self.payment_type

		for i in self.get("bulk_payment_entry_details"):
			i.party_type = self.party_type
			i.payment_type = self.payment_type

		for i in self.get("deduction"):
			i.party_type = self.party_type
			i.payment_type = self.payment_type

		for i in self.get("taxes"):
			i.party_type = self.party_type
			i.payment_type = self.payment_type
		
            


	@frappe.whitelist()
	def set_pn(self):
		# frappe.throw("hiiii")
		for account in self.get('bulk_payment_entry_details'):
			if account.party:
				# frappe.throw(str(account.name))
				account.reference_id = account.name
				if account.party_type == "Customer":
					field = 'customer_name'
				elif account.party_type == "Supplier":
					field = 'supplier_name'
				elif account.party_type == "Employee":
					field = 'employee_name'
				else:
					field = 'title'
				account.party_name = frappe.db.get_value(account.party_type, {"name": account.party}, field)

	@frappe.whitelist()
	def trigger_party(self):
		self.set_party()
		self.set_party_taxes()
		self.set_reference_id()

	@frappe.whitelist()
	def set_party(self):
		# frappe.throw("hiiii")
		for account in self.get('deduction'):
			if account.party:
				if account.party_type == "Customer":
					field = 'customer_name'
				elif account.party_type == "Supplier":
					field = 'supplier_name'
				elif account.party_type == "Employee":
					field = 'employee_name'
				else:
					field = 'title'
				account.party_name = frappe.db.get_value(account.party_type, {"name": account.party}, field)


	@frappe.whitelist()
	def set_party_taxes(self):
		# frappe.throw("hiiii")
		for account in self.get('taxes'):
			if account.party:
				if account.party_type == "Customer":
					field = 'customer_name'
				elif account.party_type == "Supplier":
					field = 'supplier_name'
				elif account.party_type == "Employee":
					field = 'employee_name'
				else:
					field = 'title'
				account.party_name = frappe.db.get_value(account.party_type, {"name": account.party}, field)
    
     
	@frappe.whitelist()
	def set_reference_id(self):
		for j in self.get("bulk_payment_entry_details"):
			for i in self.get("deduction",filters={'party':j.party}):		
				i.reference_id = j.reference_id     
			for m in self.get("taxes",filters={'party':j.party}):
				m.reference_id = j.reference_id
     



	@frappe.whitelist()
	def get_accounts(self):
		self.get_bank_account()
		self.get_paid_to_account()


	@frappe.whitelist()
	def get_bank_account(self):
		# frappe.msgprint("hiii")
		for i in self.get("bulk_payment_entry_details"):
			if i.party and i.party_type == "Supplier":  # Fixed party_type comparison
				ba = frappe.get_value('Party Account', {'parent': i.party}, "account")
				if ba:
					i.paid_to = ba
				else:
					gets = frappe.get_value('Supplier', {'name': i.party}, "supplier_group")
					if gets:
						grpba = frappe.get_value('Party Account', {'parent': gets}, "account")
						if grpba:
							i.paid_to = grpba
						else:
							cdpba = frappe.get_value('Company', {'name': self.company}, "default_payable_account")
							if cdpba:
								i.paid_to = cdpba

			else:
				if i.party and i.party_type == "Customer":  
					ba = frappe.get_value('Party Account', {'parent': i.party}, "account")
					if ba:
						i.paid_from = ba
					else:
						gets = frappe.get_value('Customer', {'name': i.party}, "customer_group")
						if gets:
							grpba = frappe.get_value('Party Account', {'parent': gets}, "account")
							if grpba:
								i.paid_from = grpba
							else:
								cdpba = frappe.get_value('Company', {'name': self.company}, "default_receivable_account")
								if cdpba:
									i.paid_from = cdpba


	@frappe.whitelist()
	def get_paid_to_account(self):
		mode_of_payment_account = frappe.get_value("Mode of Payment Account", {'parent': self.mode_of_payment, 'company': self.company}, "default_account")
		# frappe.throw(str(mode_of_payment_account))
		for i in self.get("bulk_payment_entry_details"):
			if i.party_type == "Supplier" and i.payment_type == "Pay":
				# frappe.throw(str(mode_of_payment_account))
				i.paid_from = mode_of_payment_account
			elif i.party_type == "Customer" and i.payment_type == "Receive":
				i.paid_to = mode_of_payment_account

	


	@frappe.whitelist()
	def call_two_in_one(self):
		self.check_invoice()
		self.check_orders()

	@frappe.whitelist()
	def check_orders(self):
		self.get_entries_so()
		self.get_entries_po()
		
	@frappe.whitelist()
	def check_invoice(self):
		self.get_entries()
		self.get_entries_pi()
		

	@frappe.whitelist()
	def get_entries(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name
			if i.party_type == "Customer" and self.payment_type =="Receive":
			
				doc = frappe.get_list("Sales Invoice", 
							filters={"customer": i.party,"posting_date": ["between", [i.from_date, i.to_date]], "outstanding_amount": (">", 0), "status":["in",["Overdue","Partly Paid","Unpaid","Unpaid and Discounted","Overdue and Discounted","Partly Paid and Discounted"]]},
							fields=["name","grand_total","outstanding_amount","posting_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Sales Invoice",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.reference_id,
															"outstanding_amount":d.outstanding_amount,
															"posting_date":d.posting_date,

															})
			else:
				if i.party_type == "Customer" and self.payment_type =="Pay":
					frappe.throw("Cannot Pay to Customer without any negative outstanding invoice")


	@frappe.whitelist()
	def get_entries_so(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name		
			if i.party_type == "Customer" and self.payment_type =="Receive":
				doc = frappe.get_list("Sales Order", 
						filters={"customer": i.party,"transaction_date": ["between", [i.from_date1, i.to_date1]],"billing_status":["in",["Not Billed","Partly Billed"]]},
						fields=["name","grand_total","rounded_total","advance_paid","transaction_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Sales Order",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.reference_id,
															"outstanding_amount":(d.rounded_total)-(d.advance_paid),
															"posting_date":d.transaction_date,
						
													})

			else:
				if i.party_type == "Customer" and self.payment_type =="Pay":
					frappe.throw("Cannot Pay to Customer without any negative outstanding invoice")


	@frappe.whitelist()
	def get_entries_pi(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name
			if i.party_type == "Supplier" and self.payment_type =="Pay":
			
				doc = frappe.get_list("Purchase Invoice", 
							filters={"supplier": i.party,"posting_date": ["between", [i.from_date, i.to_date]],"outstanding_amount": (">", 0),"status":["in",["Overdue", "Partly Paid", "Unpaid"]]},
							fields=["name","grand_total","outstanding_amount","posting_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Purchase Invoice",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.name,
															"outstanding_amount":d.outstanding_amount,
															"posting_date":d.posting_date,

															})
			else:
				if i.party_type == "Supplier" and self.payment_type =="Receive":
					frappe.throw("Cannot Receive from Supplier without any negative outstanding invoice")


				
	@frappe.whitelist()
	def get_entries_po(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name
			if i.party_type == "Supplier" and self.payment_type =="Pay":
				doc = frappe.get_list("Purchase Order", 
							filters={"supplier": i.party,"transaction_date": ["between", [i.from_date1, i.to_date1]],"status":["in",["To Bill", "To Receive and Bill", "To Receive" ]]},
							fields=["name","grand_total","rounded_total","advance_paid","transaction_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Purchase Order",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.name,
															"outstanding_amount":(d.rounded_total)-(d.advance_paid),
															"posting_date":d.transaction_date,

															})
			else:
				if i.party_type == "Supplier" and self.payment_type =="Receive":
					frappe.throw("Cannot Receive from Supplier without any negative outstanding invoice")


	@frappe.whitelist()
	def get_outstanding(self):
		self.invoices()
		self.orders()

	@frappe.whitelist()
	def invoices(self):
		self.get_all_sinvoices()
		self.get_all_pinvoices()
	
	@frappe.whitelist()
	def get_all_sinvoices(self):
		for i in self.get("bulk_payment_entry_details"):
			if i.party_type == "Customer" and self.payment_type =="Receive" and self.from_date and self.to_date:	
				doc = frappe.get_list("Sales Invoice", 
							filters={"customer": i.party,"posting_date": ["between", [self.from_date, self.to_date]], "outstanding_amount": (">", 0), "status":["in",["Overdue","Partly Paid","Unpaid","Unpaid and Discounted","Overdue and Discounted","Partly Paid and Discounted"]]},
							fields=["name","grand_total","outstanding_amount","posting_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Sales Invoice",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.name,
															"outstanding_amount":d.outstanding_amount,
															"posting_date":d.posting_date,

															})
			else:
				if i.party_type == "Customer" and self.payment_type =="Pay":
					frappe.throw("Cannot Pay to Customer without any negative outstanding invoice")

	@frappe.whitelist()
	def get_all_pinvoices(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name
			if i.party_type == "Supplier" and self.payment_type =="Pay" and self.from_date and self.to_date:
			
				doc = frappe.get_list("Purchase Invoice", 
							filters={"supplier": i.party,"posting_date": ["between", [self.from_date, self.to_date]],"outstanding_amount": (">", 0),"status":["in",["Overdue", "Partly Paid", "Unpaid"]]},
							fields=["name","grand_total","outstanding_amount","posting_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Purchase Invoice",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.reference_id,
															"outstanding_amount":d.outstanding_amount,
															"posting_date":d.posting_date,

															})
			else:
				if i.party_type == "Supplier" and self.payment_type =="Receive":
					frappe.throw("Cannot Receive from Supplier without any negative outstanding invoice")
	
	

	@frappe.whitelist()
	def orders(self):
		self.get_all_sorders()
		self.get_all_porders()

	@frappe.whitelist()
	def get_all_sorders(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name		
			if i.party_type == "Customer" and self.payment_type =="Receive" and self.from_date and self.to_date:
				doc = frappe.get_list("Sales Order", 
						filters={"customer": i.party,"transaction_date": ["between", [self.from_date, self.to_date]],"billing_status":["in",["Not Billed","Partly Billed"]]},
						fields=["name","grand_total","rounded_total","advance_paid","transaction_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Sales Order",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.reference_id,
															"outstanding_amount":(d.rounded_total)-(d.advance_paid),
															"posting_date":d.transaction_date,
						
													})

			else:
				if i.party_type == "Customer" and self.payment_type =="Pay":
					frappe.throw("Cannot Pay to Customer without any negative outstanding invoice")

	@frappe.whitelist()
	def get_all_porders(self):
		for i in self.get("bulk_payment_entry_details"):
			# i.reference_id = i.name
			if i.party_type == "Supplier" and self.payment_type =="Pay" and self.from_date and self.to_date:
				doc = frappe.get_list("Purchase Order", 
							filters={"supplier": i.party,"transaction_date": ["between", [self.from_date, self.to_date]],"status":["in",["To Bill", "To Receive and Bill", "To Receive" ]]},
							fields=["name","grand_total","rounded_total","advance_paid","transaction_date"],)

				# frappe.throw(str(doc))
				if(doc):
					for d in doc:
						self.append('payment_reference', {
															"party_type":i.party_type,
															"party_name":i.party_name,
															"reference_doctype":"Purchase Order",
															"reference_name":d.name,
															"total_amount":d.grand_total,
															'reference_id':i.reference_id,
															"outstanding_amount":(d.rounded_total)-(d.advance_paid),
															"posting_date":d.transaction_date,

															})
			else:
				if i.party_type == "Supplier" and self.payment_type =="Receive":
					frappe.throw("Cannot Receive from Supplier without any negative outstanding invoice")


	@frappe.whitelist()
	def allocated_trigger(self):
		self.check_yield()
		
		
	@frappe.whitelist()
	def calculate_taxes(self):
		for i in self.get("bulk_payment_entry_details"):	
			total_value=0
			flag=True
			for j in self.get("taxes", filters={'party': i.party, 'reference_id': i.reference_id}):
				if j.add_deduct_tax == "Add" and j.charge_type == "Actual":
					if(flag):
						j.total = float(i.paid_amount + j.tax_amount or 0)
						total_value=j.total
						flag=False
					else:
						j.total = float(total_value + j.tax_amount or 0)
						total_value= j.total 
					j.rate = None
				elif j.add_deduct_tax == "Deduct" and j.charge_type == "Actual":
					if(flag):
						j.total = float(i.paid_amount - j.tax_amount or 0)
						total_value=j.total
						flag=False
					else:
						j.total = float(total_value - j.tax_amount or 0)
						total_value= j.total 
					j.rate = None
				elif j.add_deduct_tax == "Add" and j.charge_type == "On Paid Amount":
					if(flag):
						j.tax_amount = float((j.rate / 100) * i.paid_amount or 0)
						j.total = float(i.paid_amount + j.tax_amount or 0)
						total_value = j.total
						flag = False
					else:
						j.tax_amount = float((j.rate / 100) * i.paid_amount or 0)
						j.total = float(total_value + j.tax_amount or 0)
						total_value = j.total
					
				elif j.add_deduct_tax == "Deduct" and j.charge_type == "On Paid Amount":
					if(flag):
						j.tax_amount = float((j.rate / 100) * i.paid_amount or 0)
						j.total = float(i.paid_amount - j.tax_amount or 0)
						total_value = j.total
						flag = False
					else:
						j.tax_amount = float((j.rate / 100) * i.paid_amount or 0)
						j.total = float(total_value - j.tax_amount or 0)
						total_value = j.total
				


	
	@frappe.whitelist()
	def check_yield(self):
		bulk_entries = self.get("bulk_payment_entry_details")
		references = self.get("payment_reference")
		
		for bulk_entry in bulk_entries:
			total_allocated = 0
			paid_amount = bulk_entry.paid_amount
			if paid_amount != 0:
				for reference in references:
					if reference.reference_id == bulk_entry.reference_id:
						field_value = reference.allocated_amount
						if field_value is not None:
							total_allocated += field_value
							
				if total_allocated > paid_amount:
					frappe.throw("Total Allocated Amount cannot be greater than Paid Amount")
			else:
				frappe.throw("Please enter Paid Amount")



	@frappe.whitelist()
	def get_party_filter(self):
		party_list = [str(entry.party) for entry in self.get("bulk_payment_entry_details")]
		return party_list

				
	

	# For Payment Entry creation after Saving Payment Advice Document
	@frappe.whitelist()
	def payment_entry(self):
		for i in self.get("bulk_payment_entry_details"):
			
			doc = frappe.new_doc("Payment Entry")
			doc.posting_date =self.posting_date
			doc.company = self.company	
			doc.mode_of_payment = self.mode_of_payment
			doc.payment_type = self.payment_type
			doc.party_type = self.party_type
			doc.party = i.party
			doc.paid_amount = i.paid_amount
			doc.paid_from = i.paid_from
			doc.paid_to = i.paid_to
			doc.base_paid_amount = i.base_paid_amount
			doc.received_amount = i.paid_amount
			doc.base_paid_amount = i.base_paid_amount
			doc.source_exchange_rate = i.source_exchange_rate
			doc.target_exchange_rate =i.target_exchange_rate
			doc.paid_from_account_currency = i.paid_from_account_currency
			doc.paid_to_account_currency = i.paid_to_account_currency
			
			for j in self.get("payment_reference",{"reference_id":i.reference_id,"allocated_amount": (">", 0)}):
				# frappe.throw("hiiii")
				doc.append("references",{
						"reference_doctype":j.reference_doctype,
						"reference_name":j.reference_name,
						"total_amount":j.total_amount,
						"outstanding_amount":j.outstanding_amount,
						"allocated_amount":j.allocated_amount,					
					})

			if i.reference_no and i.reference_date:
				doc.reference_date = i.reference_date
				doc.reference_no = i.reference_no

			for k in self.get("deduction",{'party':i.party,'reference_id':i.reference_id}):
					doc.append("deductions",{
						"account":k.account,
						"cost_center":k.cost_center,
						"amount": (k.amount)*(-1),
						"description":k.description,			
					})
			for m in self.get("taxes",{'party':i.party,'reference_id':i.reference_id}):
					# frappe.throw("hii")
					doc.append("taxes",{
						"add_deduct_tax":m.add_deduct_tax,
						"charge_type":m.charge_type,
						"account_head": m.account_head,
						"tax_amount":m.tax_amount,
						"rate":m.rate,
						"description":m.description,			
					})

			# if self.payment_reference:	
   

			doc.custom_bulk_payment_entry = self.name
			doc.insert()
			doc.save()
			doc.submit()

	# # def on_trash(self):
	# # 	self.cancel_linked_payment_entries()
	# # 	self.delete()

	# # def cancel_linked_payment_entries(self):
	# # 	linked_payment_entries = frappe.get_all("Payment Entry", filters={"custom_bulk_payment_entry": self.name})
	# # 	for entry in linked_payment_entries:
	# # 		payment_entry_doc = frappe.get_doc("Payment Entry", entry.name)
	# # 		payment_entry_doc.cancel()


