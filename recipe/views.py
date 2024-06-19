from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeDetailSerializer,
    RecipeSerializer,
    RecipeImageSerializer,
    TagSerializer,
    IngredientSerializer,
)


class RecipeViewset(viewsets.ModelViewSet):
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        tags = self.request.query_params.get("tags")
        ingredients = self.request.query_params.get("ingredients")
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        return queryset.filter(user=self.request.user).order_by("-id").distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "list":
            return RecipeSerializer
        elif self.action == "upload_image":
            return RecipeImageSerializer
        return self.serializer_class

    """useful for setting attributes that are implicit in the request,
     but are not part of the request data."""

    """
    Also, used to provide additional validation before database save
    """

    # def perform_create(self, serializer):
    #     queryset = SignupRequest.objects.filter(user=self.request.user)
    #     if queryset.exists():
    #         raise ValidationError('You have already signed up')
    #     serializer.save(user=self.request.user)

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(user=self.request.user)

    # defining extra action for uploading image aside list, create, put view actions
    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """
     useful for adding behavior that occurs before or after saving an object, 
     such as emailing a confirmation, or logging the update
    """

    # def perform_update(self, serializer):
    #     instance = serializer.save()
    #     send_email_confirmation(user=self.request.user, modified=instance)


class BaseRecipeAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for recipe attributes."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Check for a query parameter assigned_only. 
    If this parameter is set to 1 (or true), it filters the queryset to include only 
    those attributes (tags or ingredients) that are assigned to a recipe (recipe__isnull=False)
    
    Further filters the queryset to include only the attributes that belong to the authenticated user
     (user=self.request.user).
    """

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user).order_by("-name").distinct()


"""
-- Users can retrieve lists of tags and ingredients they have created or are associated with their recipes.
-- Users can update the details of existing tags and ingredients.
-- Users can delete tags and ingredients they no longer need.
"""


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
