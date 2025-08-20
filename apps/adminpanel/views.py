from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import SystemSettings, AdminAction, Notification
from .serializers import (
    SystemSettingsSerializer, AdminActionSerializer, NotificationSerializer,
    NotificationCreateSerializer, DashboardStatsSerializer, UserStatsSerializer,
    OrderStatsSerializer, RevenueStatsSerializer, BulkActionSerializer
)
from apps.users.permissions import IsAdminUser
from apps.users.serializers import AdminUserSerializer
from apps.shop.models import Shop
from apps.products.models import Product
from apps.orders.models import Order
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardView(generics.GenericAPIView):
    """
    Admin dashboard with system statistics
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()

        # User statistics
        total_users = User.objects.filter(role='user').count()
        total_shopkeepers = User.objects.filter(role='shopkeeper').count()
        total_delivery_persons = User.objects.filter(role='delivery').count()

        # Shop statistics
        total_shops = Shop.objects.count()
        pending_shops = Shop.objects.filter(status='pending').count()
        approved_shops = Shop.objects.filter(status='approved').count()

        # Product statistics
        total_products = Product.objects.count()

        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        completed_orders = Order.objects.filter(status='delivered').count()
        orders_today = Order.objects.filter(created_at__date=today).count()

        # Revenue statistics
        total_revenue = Order.objects.filter(
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        revenue_today = Order.objects.filter(
            created_at__date=today,
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        stats = {
            'total_users': total_users,
            'total_shopkeepers': total_shopkeepers,
            'total_delivery_persons': total_delivery_persons,
            'total_shops': total_shops,
            'pending_shops': pending_shops,
            'approved_shops': approved_shops,
            'total_products': total_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'orders_today': orders_today,
            'revenue_today': revenue_today,
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)


class SystemSettingsView(generics.ListCreateAPIView):
    """
    System settings management
    """
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAdminUser]
    ordering = ['key']


class SystemSettingsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    System settings detail management
    """
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAdminUser]


class AdminActionListView(generics.ListAPIView):
    """
    Admin action audit log
    """
    queryset = AdminAction.objects.all()
    serializer_class = AdminActionSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['action_type', 'target_model', 'admin_user']
    ordering = ['-created_at']


class NotificationListView(generics.ListCreateAPIView):
    """
    Notification management
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['notification_type', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.all().select_related('recipient')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NotificationCreateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notifications = serializer.save()

        return Response({
            'message': 'Notifications sent successfully',
            'count': 1 if notifications else 0
        }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_statistics(request):
    """
    Get detailed user statistics
    """
    stats = []

    for role, role_display in User.ROLE_CHOICES:
        users = User.objects.filter(role=role)
        stats.append({
            'role': role_display,
            'count': users.count(),
            'active_count': users.filter(is_active=True).count(),
            'inactive_count': users.filter(is_active=False).count(),
        })

    serializer = UserStatsSerializer(stats, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def order_statistics(request):
    """
    Get detailed order statistics
    """
    stats = []

    for status_code, status_display in Order.STATUS_CHOICES:
        orders = Order.objects.filter(status=status_code)
        total_amount = orders.aggregate(total=Sum('total_amount'))['total'] or 0

        stats.append({
            'status': status_display,
            'count': orders.count(),
            'total_amount': total_amount,
        })

    serializer = OrderStatsSerializer(stats, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def revenue_statistics(request):
    """
    Get revenue statistics for the last 30 days
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    stats = []
    current_date = start_date

    while current_date <= end_date:
        orders = Order.objects.filter(
            created_at__date=current_date,
            status='delivered'
        )

        stats.append({
            'date': current_date,
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
        })

        current_date += timedelta(days=1)

    serializer = RevenueStatsSerializer(stats, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_user_action(request):
    """
    Perform bulk actions on users
    """
    serializer = BulkActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    action = serializer.validated_data['action']
    target_ids = serializer.validated_data['target_ids']
    reason = serializer.validated_data.get('reason', '')

    users = User.objects.filter(id__in=target_ids)

    if action == 'activate':
        users.update(is_active=True)
        message = f"Activated {users.count()} users"
    elif action == 'deactivate':
        users.update(is_active=False)
        message = f"Deactivated {users.count()} users"
    elif action == 'delete':
        count = users.count()
        users.delete()
        message = f"Deleted {count} users"
    else:
        return Response({
            'error': 'Invalid action for users'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Log admin action
    AdminAction.objects.create(
        admin_user=request.user,
        action_type='user_update',
        target_model='User',
        target_id=0,  # Bulk action
        description=f"Bulk {action}: {message}. Reason: {reason}",
        metadata={'target_ids': target_ids, 'reason': reason}
    )

    return Response({'message': message})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_shop_action(request):
    """
    Perform bulk actions on shops
    """
    serializer = BulkActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    action = serializer.validated_data['action']
    target_ids = serializer.validated_data['target_ids']
    reason = serializer.validated_data.get('reason', '')

    shops = Shop.objects.filter(id__in=target_ids)

    if action == 'approve':
        shops.update(status='approved')
        message = f"Approved {shops.count()} shops"
    elif action == 'reject':
        shops.update(status='rejected')
        message = f"Rejected {shops.count()} shops"
    elif action == 'suspend':
        shops.update(status='suspended')
        message = f"Suspended {shops.count()} shops"
    elif action == 'activate':
        shops.update(is_active=True)
        message = f"Activated {shops.count()} shops"
    elif action == 'deactivate':
        shops.update(is_active=False)
        message = f"Deactivated {shops.count()} shops"
    else:
        return Response({
            'error': 'Invalid action for shops'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Log admin action
    AdminAction.objects.create(
        admin_user=request.user,
        action_type='shop_update',
        target_model='Shop',
        target_id=0,  # Bulk action
        description=f"Bulk {action}: {message}. Reason: {reason}",
        metadata={'target_ids': target_ids, 'reason': reason}
    )

    return Response({'message': message})
