from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Shop
from .serializers import (
    ShopSerializer, ShopRegistrationSerializer, ShopUpdateSerializer,
    AdminShopSerializer, ShopListSerializer, ShopStatusUpdateSerializer
)
from users.permissions import IsShopkeeper, IsAdminUser, IsShopOwnerOrAdmin


class ShopRegistrationView(generics.CreateAPIView):
    """
    Shop registration endpoint for shopkeepers
    """
    serializer_class = ShopRegistrationSerializer
    permission_classes = [IsShopkeeper]

    def create(self, request, *args, **kwargs):
        # Check if user already has a shop
        if hasattr(request.user, 'shop'):
            return Response({
                'error': 'You already have a registered shop'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shop = serializer.save()

        return Response({
            'message': 'Shop registered successfully. Awaiting admin approval.',
            'shop': ShopSerializer(shop).data
        }, status=status.HTTP_201_CREATED)


class ShopDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Shop detail view for owner or admin
    """
    queryset = Shop.objects.all()
    permission_classes = [IsShopOwnerOrAdmin]

    def get_serializer_class(self):
        if self.request.user.is_admin_user:
            return AdminShopSerializer
        return ShopUpdateSerializer


class MyShopView(generics.RetrieveUpdateAPIView):
    """
    Current user's shop view
    """
    serializer_class = ShopUpdateSerializer
    permission_classes = [IsShopkeeper]

    def get_object(self):
        try:
            return self.request.user.shop
        except Shop.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        shop = self.get_object()
        if shop is None:
            return Response({
                'error': 'No shop registered for this user'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ShopSerializer(shop)
        return Response(serializer.data)


class ShopListView(generics.ListAPIView):
    """
    Public shop list view (approved shops only)
    """
    serializer_class = ShopListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Shop.objects.filter(status='approved', is_active=True)


class AdminShopListView(generics.ListAPIView):
    """
    Admin shop list view (all shops)
    """
    queryset = Shop.objects.all()
    serializer_class = AdminShopSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'is_active']
    search_fields = ['name', 'description', 'address', 'owner__username']
    ordering_fields = ['name', 'created_at', 'status']
    ordering = ['-created_at']


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_shop_status(request, pk):
    """
    Admin endpoint to update shop status
    """
    shop = get_object_or_404(Shop, pk=pk)
    serializer = ShopStatusUpdateSerializer(shop, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': f'Shop status updated to {serializer.validated_data["status"]}',
            'shop': AdminShopSerializer(shop).data
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def shop_search(request):
    """
    Search shops by location or name
    """
    query = request.GET.get('q', '')
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lng')
    radius = request.GET.get('radius', 10)  # km

    shops = Shop.objects.filter(status='approved', is_active=True)

    if query:
        shops = shops.filter(name__icontains=query)

    # TODO: Implement location-based filtering if lat/lng provided
    # This would require additional geographic libraries like GeoDjango

    serializer = ShopListSerializer(shops, many=True)
    return Response(serializer.data)
