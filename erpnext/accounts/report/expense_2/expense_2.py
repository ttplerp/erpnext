from erpnext.accounts.report.financial_statements import (
    get_period_list,
    get_data,
    get_columns,  # Make sure get_columns is imported
)
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    period_list = get_period_list(
        filters.from_fiscal_year,
        filters.to_fiscal_year,
        filters.period_start_date,
        filters.period_end_date,
        filters.filter_based_on,
        filters.periodicity,
        company=filters.company,
    )

    # Retrieve income data
    income = get_data(
        filters.company,
        "Income",
        "Credit",
        period_list,
        filters=filters,
        accumulated_values=filters.accumulated_values,
        ignore_closing_entries=True,
        ignore_accumulated_values_for_fy=True,
    )

    # Retrieve all expense data
    all_expenses = get_data(
        filters.company,
        "Expense",
        "Debit",
        period_list,
        filters=filters,
        accumulated_values=filters.accumulated_values,
        ignore_closing_entries=True,
        ignore_accumulated_values_for_fy=True,
    )

    # Filter and sum up data for a specific expense account
    expense_account_name = "Your Expense Account Name"  # Replace with your actual expense account name
    expense = filter_expense_account(all_expenses, expense_account_name)

    # Calculate net profit or loss based on income and the specific expense account
    net_profit_loss = get_net_profit_loss(
        income,
        expense,
        period_list,
        filters.company,
        filters.presentation_currency,
    )

    # Prepare data for the report
    data = []
    data.extend(income or [])
    data.extend(expense or [])
    if net_profit_loss:
        data.append(net_profit_loss)

    # Retrieve columns for the report
    columns = get_columns(
        filters.periodicity, period_list, filters.accumulated_values, filters.company
    )

    return columns, data, None

def filter_expense_account(expenses, account_name):
    """
    Filter expenses for a specific account name and sum up the values.
    """
    filtered_expenses = []
    for expense in expenses:
        if expense.get("account") == account_name:
            filtered_expenses.append(expense)

    if filtered_expenses:
        # Sum up the filtered expenses
        total_expense = {
            "account": account_name,
            "amount": sum(expense.get("amount", 0) for expense in filtered_expenses),
            # Add any other necessary fields for reporting
        }
        return [total_expense]
    else:
        return []

def get_net_profit_loss(
    income,
    expense,
    period_list,
    company,
    currency=None,
    consolidated=False,
):
    total = 0
    net_profit_loss = {
        "account_name": "'" + _("Profit for the year") + "'",
        "account": "'" + _("Profit for the year") + "'",
        "warn_if_negative": True,
        "currency": currency
        or frappe.get_cached_value("Company", company, "default_currency"),
    }

    has_value = False

    for period in period_list:
        key = period if consolidated else period.key
        total_income = flt(income[-2][key], 3) if income else 0
        total_expense = flt(expense[0].get("amount", 0), 3) if expense else 0  # Sum of filtered expense
        net_profit_loss[key] = total_income - total_expense

        if net_profit_loss[key]:
            has_value = True

        total += flt(net_profit_loss[key])
        net_profit_loss["total"] = total

    if has_value:
        return net_profit_loss
