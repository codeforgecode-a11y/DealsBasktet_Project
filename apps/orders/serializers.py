from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductListSerializer
from apps.shop.serializers import ShopListSerializer
from apps.users.serializers import UserProfileSerializer
from apps.products.models import Product
from decimal import Decimal


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model
    """
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 
            'unit_price', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'unit_price', 'total_price', 'created_at']
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
            if not product.can_be_ordered:
                raise serializers.ValidationError("Product is not available for ordering")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist")
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model
    """
    customer = UserProfileSerializer(read_only=True)
    shop = ShopListSerializer(read_only=True)
    delivery_person = UserProfileSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    is_delivered = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'customer', 'shop', 'delivery_person',
            'status', 'payment_status', 'delivery_address', 'delivery_phone',
            'notes', 'total_amount', 'delivery_fee', 'estimated_delivery_time',
            'actual_delivery_time', 'items', 'total_items', 'can_be_cancelled',
            'is_delivered', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_id', 'customer', 'shop', 'delivery_person',
            'total_amount', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders
    """
    items = OrderItemSerializer(many=True, write_only=True)
    shop_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'shop_id', 'delivery_address', 'delivery_phone', 'notes', 'items'
        ]
        extra_kwargs = {
            'delivery_address': {'required': True},
            'delivery_phone': {'required': True},
        }
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        
        # Check if all items are from the same shop
        shop_ids = set()
        for item in value:
            try:
                product = Product.objects.get(id=item['product_id'])
                shop_ids.add(product.shop.id)
                
                # Validate stock
                if product.stock_quantity < item['quantity']:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
                    )
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with id {item['product_id']} does not exist")
        
        if len(shop_ids) > 1:
            raise serializers.ValidationError("All items must be from the same shop")
        
        return value
    
    def validate_shop_id(self, value):
        try:
            from apps.shop.models import Shop
            shop = Shop.objects.get(id=value)
            if not shop.can_accept_orders:
                raise serializers.ValidationError("Shop is not accepting orders")
            return value
        except Shop.DoesNotExist:
            raise serializers.ValidationError("Shop does not exist")
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        shop_id = validated_data.pop('shop_id')
        
        # Calculate total amount
        total_amount = Decimal('0.00')
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            item_total = product.discounted_price * item_data['quantity']
            total_amount += item_total
        
        # Create order
        order = Order.objects.create(
            customer=self.context['request'].user,
            shop_id=shop_id,
            total_amount=total_amount,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                unit_price=product.discounted_price
            )
            
            # Update product stock
            product.stock_quantity -= item_data['quantity']
            product.save()
        
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating order status
    """
    
    class Meta:
        model = Order
        fields = ['status']
    
    def validate_status(self, value):
        order = self.instance
        user = self.context['request'].user
        
        # Define allowed status transitions
        allowed_transitions = {
            'pending': ['accepted', 'cancelled'],
            'accepted': ['packed', 'cancelled'],
            'packed': ['out_for_delivery', 'cancelled'],
            'out_for_delivery': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        
        if value not in allowed_transitions.get(order.status, []):
            raise serializers.ValidationError(f"Cannot change status from {order.status} to {value}")
        
        # Check user permissions for status changes
        if user.is_shopkeeper and value not in ['accepted', 'packed', 'cancelled']:
            raise serializers.ValidationError("Shopkeepers can only accept, pack, or cancel orders")
        
        if user.is_delivery_person and value not in ['out_for_delivery', 'delivered']:
            raise serializers.ValidationError("Delivery persons can only update delivery status")
        
        return value


class DeliveryOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery person order view
    """
    customer = UserProfileSerializer(read_only=True)
    shop = ShopListSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'customer', 'shop', 'status',
            'delivery_address', 'delivery_phone', 'notes',
            'total_amount', 'delivery_fee', 'estimated_delivery_time',
            'items', 'created_at'
        ]
