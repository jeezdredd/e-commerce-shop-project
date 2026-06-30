from django.urls import path

from . import views

urlpatterns = [
    path("sign-in/", views.SignInView.as_view()),
    path("sign-up/", views.SignUpView.as_view()),
    path("sign-out/", views.SignOutView.as_view()),
    path("categories/", views.CategoriesView.as_view()),
    path("catalog/", views.CatalogView.as_view()),
    path("products/popular/", views.PopularProductsView.as_view()),
    path("products/limited/", views.LimitedProductsView.as_view()),
    path("banners", views.BannersView.as_view()),
    path("banners/", views.BannersView.as_view()),
    path("sales/", views.SalesView.as_view()),
    path("tags/", views.TagsView.as_view()),
    path("product/<int:pk>/", views.ProductDetailView.as_view()),
    path("product/<int:pk>/reviews/", views.ProductReviewView.as_view()),
    path("basket/", views.BasketView.as_view()),
    path("orders/", views.OrdersView.as_view()),
    path("order/<int:pk>/", views.OrderDetailView.as_view()),
    path("payment/<int:pk>/", views.PaymentView.as_view()),
    path("profile/", views.ProfileView.as_view()),
    path("profile/password/", views.ProfilePasswordView.as_view()),
    path("profile/avatar/", views.ProfileAvatarView.as_view()),
    path("account/", views.AccountView.as_view()),
]
