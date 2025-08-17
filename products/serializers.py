from rest_framework import serializers
from .models import Product, Category
from shop.serializers import ShopListSerializer


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model
    """
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model
    """
    shop = ShopListSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    can_be_ordered = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'shop', 'name', 'description', 'category', 'category_id',
            'price', 'discounted_price', 'stock_quantity', 'image', 'is_available',
            'weight', 'dimensions', 'sku', 'discount_percentage',
            'is_in_stock', 'can_be_ordered', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'shop', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set the shop to the current user's shop
        validated_data['shop'] = self.context['request'].user.shop
        return super().create(validated_data)


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products (shopkeeper only)
    """
    category_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category_id', 'price', 'stock_quantity',
            'image', 'is_available', 'weight', 'dimensions', 'sku', 'discount_percentage'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'price': {'required': True},
        }
    
    def validate_category_id(self, value):
        if value is not None:
            try:
                Category.objects.get(id=value, is_active=True)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Invalid category ID")
        return value
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        validated_data['shop'] = self.context['request'].user.shop
        
        if category_id:
            validated_data['category_id'] = category_id
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        
        if category_id is not None:
            validated_data['category_id'] = category_id
        
        return super().update(instance, validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer for product list view (public)
    """
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    can_be_ordered = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'shop_name', 'category_name',
            'price', 'discounted_price', 'stock_quantity', 'image',
            'is_available', 'discount_percentage', 'is_in_stock', 'can_be_ordered'
        ]


class ProductSearchSerializer(serializers.ModelSerializer):
    """
    Serializer for product search results
    """
    shop = ShopListSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'shop', 'category_name',
            'price', 'discounted_price', 'image', 'discount_percentage'
        ]


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating categories (admin only)
    """
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'is_active']
        extra_kwargs = {
            'name': {'required': True},
        }
