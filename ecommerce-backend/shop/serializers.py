from django.utils.text import slugify
from rest_framework import serializers
from .models import Category, Product, Profile, Cart, CartItem, Order
from django.contrib.auth.models import User





class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]
        
    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    # Only keep writable fields
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    
    slug = serializers.SlugField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    in_stock = serializers.ReadOnlyField() 

    class Meta:
        model = Product
        fields = [
            "name",
            "slug",
            "description",
            "price",
            "category",
            "stock",
            "in_stock"
        ]

    def create(self, validated_data):
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "slug" not in validated_data and validated_data.get("name"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().update(instance, validated_data)



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"]
        )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = ["username", "email", "phone", "address", "bio", "created_at"]
        read_only_fields = ["created_at"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "profile"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        Profile.objects.update_or_create(user=user, defaults=profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()
        Profile.objects.update_or_create(user=instance, defaults=profile_data)
        return instance


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "product_price", "quantity", "subtotal"]
        read_only_fields = ["id", "product_name", "product_price", "subtotal"]

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity



class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "items", "total_price", "created_at", "updated_at"]
        
    def get_total_price(self, obj):
        return obj.total_price()


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["product", "quantity"]
        
    def create(self, validated_data):
        # cart is passed in perform_create
        return CartItem.objects.create(**validated_data)


class OrderSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "created_at", "items"]