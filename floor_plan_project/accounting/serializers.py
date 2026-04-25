from rest_framework import serializers
from .models import Cheque

class ChequeSerializer(serializers.ModelSerializer):
    # This field shows the office number from the related lease and office
    office_number = serializers.ReadOnlyField(source='lease.office.office_number')

    class Meta:
        model = Cheque
        fields = [
            'id', 'lease', 'office_number', 'cheque_number', 
            'bank_name', 'due_date', 'amount', 'status'
        ]
