from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer,
    DeliveryOrderSerializer
)
from apps.users.permissions import IsShopkeeper, IsDeliveryPerson, IsAdminUser
import random
import string


class OrderCreateView(generics.CreateAPIView):
    """
    Create new order endpoint
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Only regular users can place orders
        if request.user.role != 'user':
            return Response({
                'error': 'Only customers can place orders'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        return Response({
            'message': 'Order placed successfully',
            'order': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)


class CustomerOrderListView(generics.ListAPIView):
    """
    Customer's order history
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-created_at']

    def get_queryset(self):
        return Order.objects.filter(
            customer=self.request.user
        ).select_related('shop', 'delivery_person').prefetch_related('items__product')


class CustomerOrderDetailView(generics.RetrieveAPIView):
    """
    Customer order detail view
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            customer=self.request.user
        ).select_related('shop', 'delivery_person').prefetch_related('items__product')


class ShopOrderListView(generics.ListAPIView):
    """
    Shop orders list for shopkeepers
    """
    serializer_class = OrderSerializer
    permission_classes = [IsShopkeeper]
    filterset_fields = ['status', 'payment_status']
    ordering = ['-created_at']

    def get_queryset(self):
        return Order.objects.filter(
            shop=self.request.user.shop
        ).select_related('customer', 'delivery_person').prefetch_related('items__product')


class ShopOrderDetailView(generics.RetrieveUpdateAPIView):
    """
    Shop order detail and status update view
    """
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsShopkeeper]

    def get_queryset(self):
        return Order.objects.filter(
            shop=self.request.user.shop
        ).select_related('customer', 'delivery_person').prefetch_related('items__product')

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class DeliveryOrderListView(generics.ListAPIView):
    """
    Delivery person's assigned orders
    """
    serializer_class = DeliveryOrderSerializer
    permission_classes = [IsDeliveryPerson]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_queryset(self):
        return Order.objects.filter(
            delivery_person=self.request.user
        ).select_related('customer', 'shop').prefetch_related('items__product')


class DeliveryOrderDetailView(generics.RetrieveUpdateAPIView):
    """
    Delivery order detail and status update view
    """
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsDeliveryPerson]

    def get_queryset(self):
        return Order.objects.filter(
            delivery_person=self.request.user
        ).select_related('customer', 'shop').prefetch_related('items__product')

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = DeliveryOrderSerializer(order)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_order(request, pk):
    """
    Cancel order endpoint
    """
    try:
        order = Order.objects.get(pk=pk, customer=request.user)
    except Order.DoesNotExist:
        return Response({
            'error': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if not order.can_be_cancelled:
        return Response({
            'error': 'Order cannot be cancelled at this stage'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Restore product stock
    for item in order.items.all():
        item.product.stock_quantity += item.quantity
        item.product.save()

    order.status = 'cancelled'
    order.save()

    return Response({
        'message': 'Order cancelled successfully'
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_delivery_person(request, pk):
    """
    Assign delivery person to order (admin only)
    """
    order = get_object_or_404(Order, pk=pk)
    delivery_person_id = request.data.get('delivery_person_id')

    if not delivery_person_id:
        return Response({
            'error': 'delivery_person_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        delivery_person = User.objects.get(
            id=delivery_person_id,
            role='delivery'
        )
    except User.DoesNotExist:
        return Response({
            'error': 'Invalid delivery person'
        }, status=status.HTTP_400_BAD_REQUEST)

    order.delivery_person = delivery_person
    order.save()

    return Response({
        'message': 'Delivery person assigned successfully',
        'order': OrderSerializer(order).data
    })


@api_view(['POST'])
@permission_classes([IsDeliveryPerson])
def generate_delivery_otp(request, pk):
    """
    Generate OTP for delivery verification
    """
    try:
        order = Order.objects.get(
            pk=pk,
            delivery_person=request.user,
            status='out_for_delivery'
        )
    except Order.DoesNotExist:
        return Response({
            'error': 'Order not found or not assigned to you'
        }, status=status.HTTP_404_NOT_FOUND)

    # Generate 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))
    order.otp = otp
    order.save()

    return Response({
        'message': 'OTP generated successfully',
        'otp': otp  # In production, this should be sent via SMS
    })


@api_view(['POST'])
@permission_classes([IsDeliveryPerson])
def verify_delivery_otp(request, pk):
    """
    Verify OTP and mark order as delivered
    """
    try:
        order = Order.objects.get(
            pk=pk,
            delivery_person=request.user,
            status='out_for_delivery'
        )
    except Order.DoesNotExist:
        return Response({
            'error': 'Order not found or not assigned to you'
        }, status=status.HTTP_404_NOT_FOUND)

    provided_otp = request.data.get('otp')
    if not provided_otp:
        return Response({
            'error': 'OTP is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if order.otp != provided_otp:
        return Response({
            'error': 'Invalid OTP'
        }, status=status.HTTP_400_BAD_REQUEST)

    order.status = 'delivered'
    order.actual_delivery_time = timezone.now()
    order.otp = None  # Clear OTP after successful verification
    order.save()

    return Response({
        'message': 'Order delivered successfully'
    })
