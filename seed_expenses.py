from reports.models import ProjectRecord, ProjectExpense, ExpenseTag
from datetime import date
from decimal import Decimal

tag, _ = ExpenseTag.objects.get_or_create(
    name="Opening Expense"
)

expense_data = [
    ("Supply of Office Items (ZATP II)", Decimal("19712.00")),
    ("LAN Installation / Supply", Decimal("2563850.00")),
    ("Supply & Delivery of Skip Bins", Decimal("400000.00")),
    ("Aviation Fuel Drums (260)", Decimal("400000.00")),
]

for project_name, amount in expense_data:

    project = ProjectRecord.objects.filter(
        project_supply=project_name
    ).first()

    if project:

        ProjectExpense.objects.get_or_create(
            project=project,
            reason="Opening expense balance",

            defaults={
                "date": project.start_date or date.today(),
                "amount": amount,
                "tag": tag,
                "notes": "Initial imported expense value."
            }
        )

print("Opening expenses added successfully.")