from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from .models import Product, Category
from .serializers import (
    ProductSerializer, ProductCreateUpdateSerializer, ProductListSerializer,
    ProductSearchSerializer, CategorySerializer, CategoryCreateUpdateSerializer
)
from users.permissions import IsShopkeeper, IsAdminUser, IsShopOwnerOrAdmin
import cloudinary.uploader


class ProductListView(generics.ListAPIView):
    """
    Public product list view
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'shop', 'is_available']
    search_fields = ['name', 'description', 'shop__name']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Product.objects.filter(
            is_available=True,
            shop__status='approved',
            shop__is_active=True
        ).select_related('shop', 'category')


class ProductDetailView(generics.RetrieveAPIView):
    """
    Public product detail view
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Product.objects.filter(
            is_available=True,
            shop__status='approved',
            shop__is_active=True
        ).select_related('shop', 'category')


class ShopProductListView(generics.ListCreateAPIView):
    """
    Shop products list and create view (shopkeeper only)
    """
    permission_classes = [IsShopkeeper]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(
            shop=self.request.user.shop
        ).select_related('shop', 'category')

    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, 'shop'):
            return Response({
                'error': 'You must have a registered shop to create products'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.shop.is_approved:
            return Response({
                'error': 'Your shop must be approved to create products'
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)


class ShopProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Shop product detail view (shopkeeper only)
    """
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsShopOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_admin_user:
            return Product.objects.all().select_related('shop', 'category')
        return Product.objects.filter(
            shop=self.request.user.shop
        ).select_related('shop', 'category')


class CategoryListView(generics.ListAPIView):
    """
    Public category list view
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    ordering = ['name']


class AdminCategoryView(generics.ListCreateAPIView):
    """
    Admin category management view
    """
    queryset = Category.objects.all()
    serializer_class = CategoryCreateUpdateSerializer
    permission_classes = [IsAdminUser]
    ordering = ['name']


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin category detail view
    """
    queryset = Category.objects.all()
    serializer_class = CategoryCreateUpdateSerializer
    permission_classes = [IsAdminUser]


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_search(request):
    """
    Product search endpoint
    """
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    shop_id = request.GET.get('shop')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.filter(
        is_available=True,
        shop__status='approved',
        shop__is_active=True
    ).select_related('shop', 'category')

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(shop__name__icontains=query)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if shop_id:
        products = products.filter(shop_id=shop_id)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    serializer = ProductSearchSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsShopkeeper])
def upload_product_image(request):
    """
    Upload product image to Cloudinary
    """
    if 'image' not in request.FILES:
        return Response({
            'error': 'No image file provided'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            request.FILES['image'],
            folder='products/',
            transformation=[
                {'width': 800, 'height': 600, 'crop': 'limit'},
                {'quality': 'auto'},
                {'format': 'auto'}
            ]
        )

        return Response({
            'image_url': upload_result['secure_url'],
            'public_id': upload_result['public_id']
        })

    except Exception as e:
        return Response({
            'error': f'Image upload failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
