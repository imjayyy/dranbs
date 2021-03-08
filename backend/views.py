import mimetypes

from django.http import JsonResponse, HttpResponse
from django.views import View
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Site, Product, UserSite, UserProfile, BrandFollower
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
            'user': {
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


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


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


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        user_data = request.data['user']
        serializer = UserSerializer(data=user_data, instance=user)
        if serializer.is_valid():
            serializer.save()
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
        gender = int(request.GET.get('gender', 0))

        user = request.user
        offset = page_number * 60
        if explore_all == 'false':
            if gender == 0:
                products = Product.objects.raw(
                    "SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id LEFT JOIN user_site us on sites.id = us.site_id WHERE us.user_id=%s AND sites.type=%s ORDER BY random() LIMIT 60 OFFSET %s",
                    [user.id, site_type, offset])
            else:
                products = Product.objects.raw(
                    "SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id LEFT JOIN user_site us on sites.id = us.site_id WHERE us.user_id=%s AND sites.type=%s AND sites.gender=%s ORDER BY random() LIMIT 60 OFFSET %s",
                    [user.id, site_type, gender, offset])
        else:
            if gender == 0:
                products = Product.objects.raw(
                    "SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id WHERE sites.type=%s ORDER BY random() LIMIT 60 OFFSET %s",
                    [site_type, offset])
            else:
                products = Product.objects.raw(
                    "SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id WHERE sites.type=%s AND sites.gender=%s ORDER BY random() LIMIT 60 OFFSET %s",
                    [site_type, gender, offset])

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
                                          'scrape_url', 'short_url', )
        site_list = list(sites)
        result = {
            'data': site_list
        }

        return JsonResponse(result)


class MyBrandsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sites = Site.objects.all().values('id', 'name', 'display_name',
                                          'scrape_url', 'short_url', 'gender', )
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
                                          'scrape_url', 'short_url', 'gender', )
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
        gender = int(request.GET.get('gender', 0))

        user = request.user

        offset = page_number * 60
        if gender == 0:
            products = Product.objects.raw(
                "SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id WHERE sites.type=%s AND sites.name=%s ORDER BY random() LIMIT 60 OFFSET %s",
                [site_type, name, offset])
        else:
            products = Product.objects.raw(
                "SELECT products.* FROM products LEFT JOIN sites ON products.site_id = sites.id WHERE sites.type=%s AND sites.name=%s AND sites.gender=%s ORDER BY random() LIMIT 60 OFFSET %s",
                [site_type, name, gender, offset])
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


class ToggleFollowBrandView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = JSONParser().parse(request)
        brand_name = payload.get('name')
        if brand_name:
            user = request.user
            try:
                brand_follower = BrandFollower.objects.get(brand_name=brand_name, user_id=user.id)
                brand_follower.delete()
                followers = BrandFollower.objects.filter(brand_name=brand_name).count()
                result = {
                    'followers': followers,
                    'is_following': False
                }
                return Response(result)
            except BrandFollower.DoesNotExist:
                BrandFollower.objects.create(brand_name=brand_name, user_id=user.id)
                followers = BrandFollower.objects.filter(brand_name=brand_name).count()
                result = {
                    'followers': followers,
                    'is_following': True
                }
                return Response(result)
        else:
            result = {
                'message': 'Bad request'
            }
            return Response(result, status=400)


class BrandInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name):
        followers = BrandFollower.objects.filter(brand_name=name).count()
        user = request.user
        try:
            BrandFollower.objects.get(brand_name=name, user_id=user.id)
            is_following = True
        except BrandFollower.DoesNotExist:
            is_following = False
        result = {
            'followers': followers,
            'is_following': is_following
        }
        return Response(result)


class ImageView(View):
    def get(self, request, subdir, filename):
        try:
            with open("/home/deploy/images/{0}/{1}".format(subdir, filename), "rb") as f:
                mime = mimetypes.MimeTypes().guess_type("/home/deploy/images/{0}/{1}".format(subdir, filename))[0]
                response = HttpResponse(f.read(), content_type=mime)
                return response
        except IOError:
            response = HttpResponse(status=404)
            return response
