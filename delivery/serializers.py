from rest_framework import serializers
from .models import DeliveryPerson, DeliveryZone, DeliveryAssignment
from users.serializers import UserProfileSerializer
from orders.serializers import OrderSerializer


class DeliveryPersonSerializer(serializers.ModelSerializer):
    """
    Serializer for DeliveryPerson model
    """
    user = UserProfileSerializer(read_only=True)
    can_accept_orders = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = DeliveryPerson
        fields = [
            'id', 'user', 'vehicle_type', 'vehicle_number', 'license_number',
            'is_available', 'current_latitude', 'current_longitude',
            'rating', 'total_deliveries', 'can_accept_orders',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'rating', 'total_deliveries', 'created_at', 'updated_at']


class DeliveryPersonCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating delivery person profile
    """
    
    class Meta:
        model = DeliveryPerson
        fields = [
            'vehicle_type', 'vehicle_number', 'license_number',
            'is_available', 'current_latitude', 'current_longitude'
        ]
        extra_kwargs = {
            'vehicle_type': {'required': True},
        }
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DeliveryZoneSerializer(serializers.ModelSerializer):
    """
    Serializer for DeliveryZone model
    """
    
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'description', 'delivery_fee',
            'estimated_delivery_time', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for DeliveryAssignment model
    """
    delivery_person = UserProfileSerializer(read_only=True)
    order = OrderSerializer(read_only=True)
    
    class Meta:
        model = DeliveryAssignment
        fields = [
            'id', 'delivery_person', 'order', 'status',
            'assigned_at', 'accepted_at', 'picked_up_at',
            'delivered_at', 'notes'
        ]
        read_only_fields = [
            'id', 'delivery_person', 'order', 'assigned_at',
            'accepted_at', 'picked_up_at', 'delivered_at'
        ]


class DeliveryAssignmentStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating delivery assignment status
    """
    
    class Meta:
        model = DeliveryAssignment
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        assignment = self.instance
        
        # Define allowed status transitions
        allowed_transitions = {
            'assigned': ['accepted', 'cancelled'],
            'accepted': ['picked_up', 'cancelled'],
            'picked_up': ['in_transit'],
            'in_transit': ['delivered', 'failed'],
            'delivered': [],
            'failed': ['picked_up'],  # Allow retry
            'cancelled': []
        }
        
        if value not in allowed_transitions.get(assignment.status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {assignment.status} to {value}"
            )
        
        return value


class DeliveryStatsSerializer(serializers.Serializer):
    """
    Serializer for delivery person statistics
    """
    total_deliveries = serializers.IntegerField()
    completed_deliveries = serializers.IntegerField()
    pending_deliveries = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)


class LocationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating delivery person location
    """
    
    class Meta:
        model = DeliveryPerson
        fields = ['current_latitude', 'current_longitude']
        extra_kwargs = {
            'current_latitude': {'required': True},
            'current_longitude': {'required': True},
        }
