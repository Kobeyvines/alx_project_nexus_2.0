from django.utils.text import slugify
from rest_framework import serializers
from .models import Category, Product, Profile
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        # auto generate slugs from name if not provided
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    # accept category by PK for writes; return nested category details for reads
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    category_details = CategorySerializer(source="category", read_only=True)

    image = serializers.ImageField(required=False, allow_null=True)
    slug = serializers.SlugField(required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_details",  # ✅ fixed name
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "available",
            "image",
            "created",
            "updated",
        ]
        read_only_fields = ["id", "created", "updated", "category_details"]

    def create(self, validated_data):
        # auto generate slug if missing
        if not validated_data.get("slug"):
            validated_data["slug"] = slugify(validated_data["name"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # keep default behaviour
        if "slug" not in validated_data:
            # optionally update slug on name change
            name = validated_data.get("name")
            if name:
                validated_data["slug"] = slugify(name)
        return super().update(instance, validated_data)
    

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"]
        )
        return user


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
    profile = ProfileSerializer(required=False)  # nested profile

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




