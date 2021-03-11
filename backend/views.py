import mimetypes

from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.views import View
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Site, Product, UserSite, UserProfile, BrandFollower, ProductLove, Board, BoardProduct
from backend.serializers import UserSerializer, CreateBoardSerializer, BoardSerializer, BoardProductSerializer


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
        if explore_all == 'true':
            if gender == 0:
                sql = """
                    SELECT p.*, pl.liked, bp.followed
                    FROM products p 
                            LEFT JOIN sites s ON p.site_id = s.id
                            left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                            left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                    WHERE s.type=%s ORDER BY random() LIMIT 60 OFFSET %s
                    """
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, site_type, offset])
            else:
                products = Product.objects.raw(
                    """
                    SELECT p.*, pl.liked, bp.followed
                    FROM products p 
                            LEFT JOIN sites s ON p.site_id = s.id
                            left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                            left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                    WHERE s.type=%s AND s.gender=%s ORDER BY random() LIMIT 60 OFFSET %s
                    """,
                    [user.id, user.id, site_type, gender, offset])
        else:
            if gender == 0:
                sql = """
                    select p.*, pl.liked, bp.followed
                    from products p
                             left join sites s on s.id = p.site_id
                             left join brand_followers bf on bf.brand_name = s.name
                             left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                             left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id
                    where bf.user_id = %s and s.type = %s order by random() limit 60 offset %s
                    """
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, user.id, site_type, offset])
            else:
                sql = """
                    select p.*, pl.liked, bp.followed
                    from products p
                             left join sites s on s.id = p.site_id
                             left join brand_followers bf on bf.brand_name = s.name
                             left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                             left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                    where bf.user_id = %s and s.type = %s and s.gender = %s order by random() limit 60 offset %s
                    """
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, user.id, site_type, gender, offset])

        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.followed is None:
                followed = False
            else:
                followed = True
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
                'display_name': product.site.display_name,
                'liked': liked,
                'followed': followed,
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
            sql = """
            SELECT p.*, pl.liked, bp.followed
            FROM products p 
                    LEFT JOIN sites s ON p.site_id = s.id
                    left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                    left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
            WHERE s.type=%s AND s.name=%s ORDER BY random() LIMIT 60 OFFSET %s
            """
            products = Product.objects.raw(
                sql,
                [user.id, user.id, site_type, name, offset])
        else:
            sql = """
            SELECT p.*, pl.liked, bp.followed
            FROM products p 
                    LEFT JOIN sites s ON p.site_id = s.id
                    left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                    left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
            WHERE s.type=%s AND s.name=%s AND s.gender=%s ORDER BY random() LIMIT 60 OFFSET %s
            """
            products = Product.objects.raw(
                sql,
                [user.id, user.id, site_type, name, gender, offset])
        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.followed is None:
                followed = False
            else:
                followed = True
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
                'display_name': product.site.display_name,
                'liked': liked,
                'followed': followed
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
        sql = """
        select count(*) genders from (select gender from sites where name = %s group by gender) g
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [name])
            row = cursor.fetchone()

        followers = BrandFollower.objects.filter(brand_name=name).count()
        user = request.user
        try:
            BrandFollower.objects.get(brand_name=name, user_id=user.id)
            is_following = True
        except BrandFollower.DoesNotExist:
            is_following = False
        result = {
            'followers': followers,
            'is_following': is_following,
            'genders': row[0]
        }
        return Response(result)


class ToggleLoveProduct(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = JSONParser().parse(request)
        product_id = payload.get('id')
        user = request.user

        try:
            product_love = ProductLove.objects.get(product_id=product_id, user_id=user.id)
            product_love.delete()
            result = {
                'is_love': False
            }
            return Response(result)

        except ProductLove.DoesNotExist:
            ProductLove.objects.create(product_id=product_id, user_id=user.id)
            result = {
                'is_love': True
            }
            return Response(result)


class MyLovesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        page_number = int(request.GET.get('page', 0))
        offset = page_number * 60
        products = Product.objects.raw(
            """
            select p.*, pl.*, bp.followed
            from (select product_id, user_id liked from product_love where user_id = %s) pl
                     left join products p on p.id = pl.product_id
                     left join (select product_id, user_id followed from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
            ORDER BY random() LIMIT 60 OFFSET %s
            """,
            [user.id, user.id, offset])

        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.followed is None:
                followed = False
            else:
                followed = True
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
                'display_name': product.site.display_name,
                'liked': liked,
                'followed': followed
            })
        result = {
            'data': product_list
        }
        return Response(result)


class BoardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.GET.get('product_id')
        user = request.user

        board_list = []
        if product_id:
            sql = """
            select b.id, b.name, bp.product_id followed
            from boards b
                     left join (select * from board_product where product_id = %s and user_id = %s) bp on b.id = bp.board_id
            where b.type = 1
            """
            boards = Board.objects.raw(sql, [product_id, user.id])
            for board in boards:
                if board.followed is None:
                    followed = False
                else:
                    followed = True
                board_list.append({
                    'id': board.id,
                    'name': board.name,
                    'followed': followed
                })
            return Response({
                'data': board_list,
                'product_id': product_id,
            })
        else:
            page_number = int(request.GET.get('page'))
            offset = page_number * 60
            sql = """
            select b.*
            from boards b
            where b.type = 1 order by random() limit 60 OFFSET %s
            """
            boards = Board.objects.raw(sql, [offset])
            for board in boards:
                board_list.append({
                    'id': board.id,
                    'name': board.name,
                    'image_filename': board.image_filename
                })
            return Response({
                'data': board_list,
            })

    def post(self, request):
        serializer = CreateBoardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        board_name = serializer.validated_data['board_name']
        board_type = serializer.validated_data['board_type']
        product_id = serializer.validated_data['product_id']
        product = Product.objects.get(pk=product_id)
        image_filename = product.image_filename

        board = Board.objects.create(name=board_name, type=board_type, user_id=user.id, image_filename=image_filename)
        board_serializer = BoardSerializer(board)
        BoardProduct.objects.create(product_id=product_id, board_id=board.id, user_id=user.id)
        return Response({
            'board': board_serializer.data,
            'followed': True
        })


class ProductToggleSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BoardProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.validated_data['board']
        product = serializer.validated_data['product']
        try:
            board_product = BoardProduct.objects.get(user_id=request.user.id, board_id=board.id, product_id=product.id)
            board_product.delete()
            return Response({
                'followed': False
            })
        except BoardProduct.DoesNotExist:
            serializer.save(user=request.user)
            return Response({
                'followed': True
            })


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
