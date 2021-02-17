from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views import View
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Site, Product, UserSite, UserProfile
from backend.serializers import UserSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=request.user)
        content = {
            "data": {
                "username": request.user.username,
                "last_name": request.user.last_name,
                "last_login": request.user.last_login,
                "id": request.user.id,
                "gender": request.user.profile.gender,
                "first_name": request.user.first_name,
                "email": request.user.email,
                "country": request.user.profile.country,
                "birthday": request.user.profile.birthday
            }
        }
        return Response(content)


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'meta': {
                'token': token.key
            },
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'last_name': user.last_name,
                'first_name': user.first_name,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'last_login': user.last_login,
            }
        })


class UserCreateView(APIView):
    def post(self, request):
        data = request.data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            profile = user.profile
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'user': {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "last_login": user.last_login,
                    "gender": profile.gender,
                    "country": profile.country,
                    "birthday": profile.birthday
                },
                'meta': {
                    'token': token.key
                }
            })
        else:
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return response


class UserUpdateView(APIView):
    def patch(self, request, pk):
        user = User.objects.get(pk=pk)
        user_data = request.data['user']
        serializer = UserSerializer(data=user_data, instance=user)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Success'
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HomePageDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page_number = int(request.GET.get('page', 0))
        site_type = request.GET.get('site_type', 0)
        explore_all = request.GET.get('all', False)

        user = request.user
        offset = page_number * 60
        if explore_all == 'false':
            products = Product.objects.raw("SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id LEFT JOIN user_site us on sites.id = us.site_id WHERE us.user_id=%s AND sites.type=%s ORDER BY random() LIMIT 60 OFFSET %s", [user.id, site_type, offset])
        else:
            products = Product.objects.raw("SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id WHERE sites.type=%s ORDER BY random() LIMIT 60 OFFSET %s", [site_type, offset])

        product_list = []
        for product in products:
            product_list.append({
                'id': product.id,
                'title': product.title,
                'image_filename': product.image_filename,
                'price': product.price,
                'sale_price': product.sale_price,
                'product_link': product.product_link,
                'hq_image_filename': product.hq_image_filename,
                'site': product.site_id,
                'name': product.site.name,
                'display_name': product.site.display_name
            })
        result = {
            'data': product_list
        }
        return Response(result)


class SiteListView(View):
    def get(self, request):
        sites = Site.objects.all().values('id', 'name', 'display_name',
                                          'scrape_url', 'short_url',)
        site_list = list(sites)
        result = {
            'data': site_list
        }

        return JsonResponse(result)


class MyBrandsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sites = Site.objects.all().values('id', 'name', 'display_name',
                                          'scrape_url', 'short_url', 'gender',)
        site_list = list(sites)
        user_sites = UserSite.objects.filter(user=request.user).values('id', 'site_id', 'user_id')
        user_site_list = list(user_sites)
        return Response({
            'sites': site_list,
            'my_profiles': user_site_list
        })


class ToggleUserSiteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = JSONParser().parse(request)

        data = payload.get('data')
        used = data.get('used')
        ids = data.get('ids')
        if not used:
            for pk in ids:
                UserSite.objects.create(user=request.user, site_id=pk)
        else:
            for pk in ids:
                UserSite.objects.filter(user=request.user, site_id=pk).delete()

        sites = Site.objects.all().values('id', 'name', 'display_name',
                                          'scrape_url', 'short_url', 'gender',)
        site_list = list(sites)
        user_sites = UserSite.objects.filter(user=request.user).values('user_id', 'site_id')
        user_site_list = list(user_sites)
        return Response({
            'sites': site_list,
            'my_profiles': user_site_list
        })


class ProductsByBrandView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name):
        page_number = int(request.GET.get('page', 0))
        site_type = request.GET.get('site_type', 0)

        user = request.user

        offset = page_number * 60
        products = Product.objects.raw("SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id WHERE sites.type=%s AND sites.name=%s ORDER BY random() LIMIT 60 OFFSET %s", [site_type, name, offset])
        # products = Product.objects.raw("SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id LEFT JOIN user_site us on sites.id = us.site_id WHERE sites.type=%s AND sites.name=%s ORDER BY random() LIMIT 60 OFFSET %s", [site_type, name, offset])
        product_list = []
        for product in products:
            product_list.append({
                'id': product.id,
                'title': product.title,
                'image_filename': product.image_filename,
                'price': product.price,
                'sale_price': product.sale_price,
                'product_link': product.product_link,
                'hq_image_filename': product.hq_image_filename,
                'site': product.site_id,
                'name': product.site.name,
                'display_name': product.site.display_name
            })
        result = {
            'data': product_list
        }
        return Response(result)
