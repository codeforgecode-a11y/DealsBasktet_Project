from rest_framework import serializers
from .models import Shop
from apps.users.serializers import UserProfileSerializer


class ShopSerializer(serializers.ModelSerializer):
    """
    Serializer for Shop model
    """
    owner = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id', 'owner', 'name', 'description', 'address', 'phone', 'email',
            'status', 'is_active', 'latitude', 'longitude', 'opening_time',
            'closing_time', 'created_at', 'updated_at', 'is_approved',
            'is_pending', 'can_accept_orders'
        ]
        read_only_fields = ['id', 'owner', 'status', 'created_at', 'updated_at']


class ShopRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for shop registration
    """
    
    class Meta:
        model = Shop
        fields = [
            'name', 'description', 'address', 'phone', 'email',
            'latitude', 'longitude', 'opening_time', 'closing_time'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'address': {'required': True},
            'phone': {'required': True},
        }
    
    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ShopUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for shop updates (shopkeeper only)
    """
    
    class Meta:
        model = Shop
        fields = [
            'name', 'description', 'address', 'phone', 'email',
            'latitude', 'longitude', 'opening_time', 'closing_time', 'is_active'
        ]


class AdminShopSerializer(serializers.ModelSerializer):
    """
    Serializer for admin shop management (full access)
    """
    owner = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Shop
        fields = '__all__'
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class ShopListSerializer(serializers.ModelSerializer):
    """
    Serializer for shop list view (public)
    """
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Shop
        fields = [
            'id', 'name', 'description', 'address', 'phone', 'email',
            'latitude', 'longitude', 'opening_time', 'closing_time',
            'owner_name', 'created_at'
        ]


class ShopStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to update shop status
    """
    
    class Meta:
        model = Shop
        fields = ['status']
        
    def validate_status(self, value):
        if value not in ['pending', 'approved', 'suspended', 'rejected']:
            raise serializers.ValidationError("Invalid status")
        return value
