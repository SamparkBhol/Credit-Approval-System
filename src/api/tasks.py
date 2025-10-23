import pandas as pd
from celery import shared_task
from .models import Customer, Loan
import logging
from decimal import Decimal

# Set up a logger to see output from the worker
logger = logging.getLogger(__name__)

@shared_task
def ingest_data_task():
    try:
        # --- Ingest Customer Data ---
        logger.info("Starting customer data ingestion...")
        # We specify 'openpyxl' as the engine to read .xlsx files
        customer_df = pd.read_excel('customer_data.xlsx', engine='openpyxl')
        
        # We need to handle 'Age' as it's not in the file, but it is in the model
        # We'll fill any missing 'Age' with None (which becomes NULL in the DB)
        if 'Age' not in customer_df.columns:
            customer_df['Age'] = None

        customers_to_create = []
        for _, row in customer_df.iterrows():
            customers_to_create.append(
                Customer(
                    customer_id=row['Customer ID'],
                    first_name=row['First Name'],
                    last_name=row['Last Name'],
                    age=row['Age'] if pd.notnull(row['Age']) else None,
                    phone_number=row['Phone Number'],
                    monthly_salary=Decimal(str(row['Monthly Salary'])),
                    approved_limit=Decimal(str(row['Approved Limit'])),
                    current_debt=0  # Set initial debt to 0
                )
            )
        
        # bulk_create is much faster than creating one by one
        # ignore_conflicts=True will skip any rows that have a Customer ID
        # that already exists, preventing crashes.
        Customer.objects.bulk_create(customers_to_create, ignore_conflicts=True)
        logger.info(f"Successfully ingested {len(customers_to_create)} customer records.")

        # --- Ingest Loan Data ---
        logger.info("Starting loan data ingestion...")
        loan_df = pd.read_excel('loan_data.xlsx', engine='openpyxl')
        
        # Get a set of all valid customer IDs from the database
        # This is fast and efficient
        customer_ids = set(Customer.objects.values_list('customer_id', flat=True))
        
        loans_to_create = []
        for _, row in loan_df.iterrows():
            # Only create a loan if its customer_id actually exists in our DB
            if row['Customer ID'] in customer_ids:
                loans_to_create.append(
                    Loan(
                        customer_id=row['Customer ID'],
                        loan_id=row['Loan ID'],
                        loan_amount=Decimal(str(row['Loan Amount'])),
                        tenure=row['Tenure'],
                        interest_rate=Decimal(str(row['Interest Rate'])),
                        monthly_repayment=Decimal(str(row['Monthly payment'])),
                        emis_paid_on_time=row['EMIs paid on Time'],
                        start_date=row['Date of Approval'],
                        end_date=row['End Date']
                    )
                )
            else:
                logger.warning(f"Skipping loan {row['Loan ID']}: Customer {row['Customer ID']} not found.")
        
        Loan.objects.bulk_create(loans_to_create, ignore_conflicts=True)
        logger.info(f"Successfully ingested {len(loans_to_create)} loan records.")

    except FileNotFoundError as e:
        logger.error(f"Data ingestion failed: File not found - {e}. Make sure 'customer_data.xlsx' and 'loan_data.xlsx' are in the 'src/' directory.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during data ingestion: {e}")

    return "Data ingestion process completed."