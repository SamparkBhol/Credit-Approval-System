from django.urls import path
from .views import (
    RegisterView, CheckEligibilityView, CreateLoanView,
    ViewLoanView, ViewLoansByCustomerView
)

urlpatterns = [
    # /api/register/
    path('register/', RegisterView.as_view(), name='register-customer'),
    
    # /api/check-eligibility/
    path('check-eligibility/', CheckEligibilityView.as_view(), name='check-eligibility'),
    
    # /api/create-loan/
    path('create-loan/', CreateLoanView.as_view(), name='create-loan'),
    
    # /api/view-loan/<loan_id>/
    # The <int:loan_id> part captures the ID from the URL
    path('view-loan/<int:loan_id>/', ViewLoanView.as_view(), name='view-loan'),
    
    # /api/view-loans/<customer_id>/
    path('view-loans/<int:customer_id>/', ViewLoansByCustomerView.as_view(), name='view-loans-by-customer'),
]