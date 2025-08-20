from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from .models import DeliveryPerson, DeliveryZone, DeliveryAssignment
from .serializers import (
    DeliveryPersonSerializer, DeliveryPersonCreateUpdateSerializer,
    DeliveryZoneSerializer, DeliveryAssignmentSerializer,
    DeliveryAssignmentStatusUpdateSerializer, DeliveryStatsSerializer,
    LocationUpdateSerializer
)
from apps.users.permissions import IsDeliveryPerson, IsAdminUser
from apps.orders.models import Order


class DeliveryPersonProfileView(generics.RetrieveUpdateAPIView):
    """
    Delivery person profile view
    """
    permission_classes = [IsDeliveryPerson]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DeliveryPersonCreateUpdateSerializer
        return DeliveryPersonSerializer

    def get_object(self):
        try:
            return self.request.user.delivery_profile
        except DeliveryPerson.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response({
                'error': 'Delivery profile not found. Please create your profile first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = DeliveryPersonSerializer(profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            # Create new profile
            serializer = DeliveryPersonCreateUpdateSerializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            profile = serializer.save()
            return Response(
                DeliveryPersonSerializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        else:
            # Update existing profile
            serializer = DeliveryPersonCreateUpdateSerializer(
                profile, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            profile = serializer.save()
            return Response(DeliveryPersonSerializer(profile).data)


class DeliveryAssignmentListView(generics.ListAPIView):
    """
    List delivery assignments for delivery person
    """
    serializer_class = DeliveryAssignmentSerializer
    permission_classes = [IsDeliveryPerson]
    filterset_fields = ['status']
    ordering = ['-assigned_at']

    def get_queryset(self):
        return DeliveryAssignment.objects.filter(
            delivery_person=self.request.user
        ).select_related('order', 'order__customer', 'order__shop')


class DeliveryAssignmentDetailView(generics.RetrieveUpdateAPIView):
    """
    Delivery assignment detail and status update
    """
    serializer_class = DeliveryAssignmentStatusUpdateSerializer
    permission_classes = [IsDeliveryPerson]

    def get_queryset(self):
        return DeliveryAssignment.objects.filter(
            delivery_person=self.request.user
        ).select_related('order', 'order__customer', 'order__shop')

    def retrieve(self, request, *args, **kwargs):
        assignment = self.get_object()
        serializer = DeliveryAssignmentSerializer(assignment)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        assignment = self.get_object()
        serializer = self.get_serializer(assignment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Update timestamps based on status
        new_status = serializer.validated_data.get('status')
        if new_status:
            now = timezone.now()
            if new_status == 'accepted':
                assignment.accepted_at = now
            elif new_status == 'picked_up':
                assignment.picked_up_at = now
            elif new_status == 'delivered':
                assignment.delivered_at = now
                # Update delivery person stats
                try:
                    profile = assignment.delivery_person.delivery_profile
                    profile.total_deliveries += 1
                    profile.save()
                except DeliveryPerson.DoesNotExist:
                    pass

        assignment = serializer.save()

        # Update order status accordingly
        order = assignment.order
        if new_status == 'picked_up':
            order.status = 'out_for_delivery'
        elif new_status == 'delivered':
            order.status = 'delivered'
            order.actual_delivery_time = timezone.now()

        order.save()

        return Response(DeliveryAssignmentSerializer(assignment).data)


class DeliveryZoneListView(generics.ListAPIView):
    """
    List delivery zones
    """
    queryset = DeliveryZone.objects.filter(is_active=True)
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.AllowAny]
    ordering = ['name']


class AdminDeliveryZoneView(generics.ListCreateAPIView):
    """
    Admin delivery zone management
    """
    queryset = DeliveryZone.objects.all()
    serializer_class = DeliveryZoneSerializer
    permission_classes = [IsAdminUser]
    ordering = ['name']


class AdminDeliveryZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin delivery zone detail management
    """
    queryset = DeliveryZone.objects.all()
    serializer_class = DeliveryZoneSerializer
    permission_classes = [IsAdminUser]


@api_view(['GET'])
@permission_classes([IsDeliveryPerson])
def delivery_stats(request):
    """
    Get delivery person statistics
    """
    user = request.user

    # Get assignment statistics
    assignments = DeliveryAssignment.objects.filter(delivery_person=user)
    total_assignments = assignments.count()
    completed = assignments.filter(status='delivered').count()
    pending = assignments.filter(status__in=['assigned', 'accepted', 'picked_up', 'in_transit']).count()

    # Get profile for additional stats
    try:
        profile = user.delivery_profile
        total_deliveries = profile.total_deliveries
        average_rating = profile.rating
    except DeliveryPerson.DoesNotExist:
        total_deliveries = 0
        average_rating = 0

    # Calculate earnings (this would need a proper payment system)
    total_earnings = 0  # Placeholder

    stats = {
        'total_deliveries': total_deliveries,
        'completed_deliveries': completed,
        'pending_deliveries': pending,
        'average_rating': average_rating,
        'total_earnings': total_earnings
    }

    serializer = DeliveryStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsDeliveryPerson])
def update_location(request):
    """
    Update delivery person current location
    """
    try:
        profile = request.user.delivery_profile
    except DeliveryPerson.DoesNotExist:
        return Response({
            'error': 'Delivery profile not found'
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = LocationUpdateSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'message': 'Location updated successfully',
        'latitude': profile.current_latitude,
        'longitude': profile.current_longitude
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_delivery(request):
    """
    Admin endpoint to assign delivery person to order
    """
    order_id = request.data.get('order_id')
    delivery_person_id = request.data.get('delivery_person_id')

    if not order_id or not delivery_person_id:
        return Response({
            'error': 'order_id and delivery_person_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        order = Order.objects.get(id=order_id)
        delivery_person = get_object_or_404(
            User.objects.filter(role='delivery'),
            id=delivery_person_id
        )
    except Order.DoesNotExist:
        return Response({
            'error': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Check if order already has a delivery assignment
    if hasattr(order, 'delivery_assignment'):
        return Response({
            'error': 'Order already has a delivery assignment'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Create delivery assignment
    assignment = DeliveryAssignment.objects.create(
        delivery_person=delivery_person,
        order=order
    )

    # Update order
    order.delivery_person = delivery_person
    order.save()

    return Response({
        'message': 'Delivery assigned successfully',
        'assignment': DeliveryAssignmentSerializer(assignment).data
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def available_delivery_persons(request):
    """
    Get list of available delivery persons
    """
    delivery_persons = DeliveryPerson.objects.filter(
        is_available=True,
        user__is_active=True
    ).select_related('user')

    serializer = DeliveryPersonSerializer(delivery_persons, many=True)
    return Response(serializer.data)
