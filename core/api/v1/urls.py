from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from api.v1.views.auth_views import (
    RegistrationAPIView,
    LoginAPIView,
    GetAccessTokenView,
    LogoutAPIView,
    PasswordRecoveryAPIView,
    PasswordRecoveryConfirmAPIView,
    RegistrationConfirmAPIView,
    GetAuthInfoAPIView
)
from api.v1.views.examples_views import ExampleViewSet, ExampleCommandViewSet, ExampleCommandUpdateStatusAPIView
from api.v1.views.geant_documentation_views import (
    ArticleViewSet,
    ChapterViewSet,
    CategoryViewSet,
    SubscriptionViewSet,
    ElementViewSet,
    FileViewSet
)
from api.v1.views.groups_views import GroupAPIViewSet
from api.v1.views.users_views import (
    UserProfileViewSet,
    UserProfileUpdateImportantInfoViewSet,
    UserExampleView,
    UserProfileImageViewSet,
    ConfirmEmailUpdateAPIView
)

user_update_router = SimpleRouter()
user_update_router.register(
    r'profile', UserProfileUpdateImportantInfoViewSet, basename='user-profile')

group_router = SimpleRouter()
group_router.register(
    r'groups', GroupAPIViewSet, basename='groups')

example_router = SimpleRouter()
example_router.register(r'examples', ExampleViewSet, basename='examples')

documentation_router = SimpleRouter()
documentation_router.register(r'articles', ArticleViewSet, basename='articles')
documentation_router.register(r'chapters', ChapterViewSet, basename='chapters')
documentation_router.register(r'categories', CategoryViewSet, basename='categories')

documentation_subscription_router = NestedSimpleRouter(
    parent_router=documentation_router, parent_prefix=r'articles', lookup='article')
documentation_subscription_router.register(
    r'subscriptions', SubscriptionViewSet, basename='article-subscriptions'
)

documentation_subscription_element_router = NestedSimpleRouter(
    parent_router=documentation_subscription_router, parent_prefix=r'subscriptions', lookup='subscription')
documentation_subscription_element_router.register(
    r'elements', ElementViewSet, basename='article-subscription-elements'
)

example_command_router = NestedSimpleRouter(
    parent_router=example_router, parent_prefix=r'examples', lookup='example')
example_command_router.register(
    r'example_geant', ExampleCommandViewSet, basename='example-example-command')

urlpatterns = [
    path('', include(group_router.urls)),
    path('', include(example_router.urls)),
    path('', include(user_update_router.urls)),
    path('', include(example_command_router.urls)),
    path('documentations/', include(documentation_router.urls)),
    path('documentations/', include(documentation_subscription_element_router.urls)),
    path('documentations/', include(documentation_subscription_router.urls)),
    path(
        'documentations/<uuid:uuid>/<str:file_format>/',
        FileViewSet.as_view(actions=FileViewSet.get_action_map()),
        name='file-manage'
    ),
    path('registration/', RegistrationAPIView.as_view(), name='registration'),
    path('registration/confirm/<str:token>', RegistrationConfirmAPIView.as_view(),
         name='confirm-registration'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('token/refresh/', GetAccessTokenView.as_view(), name='refresh'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('password_recovery/', PasswordRecoveryAPIView.as_view(),
         name='password-recovery'),
    path('password_recovery/confirm/<str:token>',
         PasswordRecoveryConfirmAPIView.as_view(), name='confirm-password-recovery'),
    path(
        'profile/image/',
        UserProfileImageViewSet.as_view(actions=UserProfileImageViewSet.get_action_map()),
        name='user-profile-image'
    ),
    path(
        'profile/',
        UserProfileViewSet.as_view(actions=UserProfileViewSet.get_actions()),
        name='user-profile'
    ),
    path('profile/update_email/<str:token>',
         ConfirmEmailUpdateAPIView.as_view(), name='confirm-email-update'),
    path('update_example_status/', ExampleCommandUpdateStatusAPIView.as_view(),
         name='update-example-status'),
    path('profile/my_examples/', UserExampleView.as_view(), name='user-examples'),
    path('is_authorized/', GetAuthInfoAPIView.as_view(), name='is-authorized'),
]
