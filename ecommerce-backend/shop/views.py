from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, BooleanFilter, CharFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.generics import RetrieveAPIView
from django.contrib.auth.models import User
# DRF filters (for SearchFilter, OrderingFilter)
from rest_framework import filters as drf_filters

from .models import Category, Product, Profile, Cart, CartItem, Order, OrderItem
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    RegisterSerializer,
    LogoutSerializer,
    ProfileSerializer,
    UserSerializer,
    CartItemSerializer,
    AddCartItemSerializer,
    OrderSerializer,
    CartSerializer,
)
from .permissions import IsAdminOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# Custom Filters
class ProductFilter(FilterSet):
    min_price = NumberFilter(field_name="price", lookup_expr="gte")
    max_price = NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = BooleanFilter(method='filter_in_stock')
    category = CharFilter(field_name="category__slug", lookup_expr='iexact')

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "in_stock"]
        
    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset

# -----------------------
# Category & Product
# -----------------------

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "slug"
    
    
    @action(detail=True, methods=["get"], url_path="products", permission_classes=[IsAdminOrReadOnly])
    def products(self, request, slug=None):
        """
        Returns all products belonging to this category.
        """
        category = self.get_object()
        products = Product.objects.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = ProductFilter 
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created", "updated"]
    ordering = ["-created"]  # default ordering
    lookup_field = "slug"
    
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
        openapi.Parameter('in_stock', openapi.IN_QUERY, description="In stock", type=openapi.TYPE_BOOLEAN),
        openapi.Parameter('category', openapi.IN_QUERY, description="Category slug", type=openapi.TYPE_STRING),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)



# -----------------------
# Auth & Users
# -----------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        print("DEBUG USER:", self.request.user)
        print("DEBUG AUTH:", self.request.auth)
        if self.request.user.is_staff and "user_id" in self.request.query_params:
            return User.objects.get(pk=self.request.query_params["user_id"])
        return self.request.user


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_me(request):
    user = request.user
    return Response({"id": user.id, "username": user.username, "email": user.email})


# -----------------------
# Cart & Cart Items
# -----------------------

class CartViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

   # shop/views.py

def get_queryset(self):
    user = self.request.user
    if not user.is_authenticated:
        return Cart.objects.none()  # or handle anonymous carts differently
    return Cart.objects.filter(user=user)

    # For get_or_create
    if user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=user, status="active")
    else:
        cart = None  # Or handle guest cart logic

    @action(detail=False, methods=["get"], url_path="my-cart")
    def my_cart(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user, status='active')
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        cart = self.get_object()
        
        # Ensure only open/active carts can be checked out
        if cart.status != "active":
            return Response({"error": "Only active carts can be checked out"},
                            status=status.HTTP_400_BAD_REQUEST)

        if not cart.items.exists():
            return Response({"error": "Cart is empty"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Convert cart -> order
        order = Order.objects.create(user=request.user)
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order, product=item.product, quantity=item.quantity
            )

        # Close cart
        cart.items.all().delete()
        cart.status = "checked_out"
        cart.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user, status="active")
        return cart.items.all()

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user, status="active")
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)

        # Check if item already exists
        existing_item = CartItem.objects.filter(cart=cart, product=product).first()
        if existing_item:
            # Update quantity instead of inserting duplicate
            existing_item.quantity += quantity
            existing_item.save()
            self.instance = existing_item  # so response returns updated item
        else:
            serializer.save(cart=cart)
            
        # rebind serializer to final instance so response uses latest state
        serializer.instance = self.instance

    def perform_update(self, serializer):
        if not serializer.instance.cart.status == "active":
            raise ValidationError("Cannot modify items in a checked-out cart.")
        serializer.save()

    def perform_destroy(self, instance):
        if not instance.cart.status == "active":
            raise ValidationError("Cannot remove items from a checked-out cart.")
        instance.delete()
        


# -----------------------
# Orders
# -----------------------

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    # Allow only GET, PATCH globally — POST is reserved for cancel (custom action)
    http_method_names = ["get", "patch", "post"]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Block normal POST order creation
        return Response(
            {"error": "Orders cannot be created directly. Use checkout instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"error": "PUT not allowed. Use PATCH to update order status."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        status_value = request.data.get("status")

        if not status_value:
            return Response(
                {"error": "Only 'status' can be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only admins can update statuses (except cancel handled below)
        if not request.user.is_staff:
            return Response(
                {"error": "Only admins can update order status directly."},
                status=status.HTTP_403_FORBIDDEN,
            )

        order.status = status_value
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-orders")
    def my_orders(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()

        # Ensure only the owner can cancel
        if order.user != request.user:
            return Response(
                {"error": "You cannot cancel an order that isn’t yours."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Idempotent: if already canceled, just return it
        if order.status == "canceled":
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Otherwise cancel it
        order.status = "canceled"
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
