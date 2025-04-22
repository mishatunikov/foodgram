from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
)
from rest_framework.permissions import IsAuthenticated

from api import consts
from api.paginators import LimitPageNumberPagination
from foodgram.models import User
from api.serializers import (
    UserSerializer,
    AvatarSerializer,
    PasswordSerializer,
)


class UserViewSet(
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitPageNumberPagination

    @action(
        methods=['get'],
        detail=False,
        url_name='me',
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put'],
        detail=False,
        url_name='manage_avatar',
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        serializer_class=AvatarSerializer,
    )
    def update_avatar(self, request):
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        user: User = request.user
        if user.avatar:
            user.avatar = None
            user.save()
            message = consts.AVATAR_DELETED
        else:
            message = consts.AVATAR_NOT_INSTALLED
        return Response(
            data={'message': message}, status=status.HTTP_404_NOT_FOUND
        )

    @action(
        methods=['post'],
        url_name='set_password',
        permission_classes=[IsAuthenticated],
        detail=False,
        serializer_class=PasswordSerializer,
    )
    def set_password(self, request):
        user: User = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response(
            data={'message': consts.PASSWORD_UPDATED},
            status=status.HTTP_201_CREATED,
        )
