import mimetypes
import uuid
from datetime import timedelta

from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.forms import UploadFileForm
from backend.models import Site, Product, UserProfile, BrandFollower, ProductLove, Board, BoardProduct, \
    BoardFollower
from backend.serializers import TicketSerializer, UserSerializer, CreateBoardSerializer, BoardSerializer, \
    BoardProductSerializer


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
        serializer = UserSerializer(data=request.data, instance=user)
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
        period = int(request.GET.get("period"))

        now = timezone.now()
        if period == 1:
            start_time = now.strftime("'%Y-%m-%d 00:00:00'")
            end_time = now.strftime("'%Y-%m-%d 23:59:59'")
            period_condition = "and p.inserted_at between {0} and {1}".format(start_time, end_time)
        elif period == 7:
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_time = start_of_week.strftime("'%Y-%m-%d 00:00:00'")
            end_time = end_of_week.strftime("'%Y-%m-%d 23:59:59'")
            period_condition = "and p.inserted_at between {0} and {1}".format(start_time, end_time)
        else:
            period_condition = ""

        user = request.user
        offset = page_number * 60
        if explore_all == 'true':
            if gender == 0:
                sql = """
                    SELECT p.*, pl.liked, bp.saved
                    FROM products p 
                            LEFT JOIN sites s ON p.site_id = s.id
                            left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                            left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                    WHERE s.type=%s {0} ORDER BY random() LIMIT 60 OFFSET %s
                    """.format(period_condition)
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, site_type, offset])
            else:
                sql = """
                    SELECT p.*, pl.liked, bp.saved
                    FROM products p 
                            LEFT JOIN sites s ON p.site_id = s.id
                            left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                            left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                    WHERE s.type=%s AND s.gender=%s {0} ORDER BY random() LIMIT 60 OFFSET %s
                    """.format(period_condition)
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, site_type, gender, offset])
        else:
            if gender == 0:
                sql = """
                    select p.*, pl.liked, bp.saved
                    from products p
                             left join sites s on s.id = p.site_id
                             left join brand_followers bf on bf.brand_name = s.name
                             left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                             left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id
                    where bf.user_id = %s and s.type = %s {0} order by random() limit 60 offset %s
                    """.format(period_condition)
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, user.id, site_type, offset])
            else:
                sql = """
                    select p.*, pl.liked, bp.saved
                    from products p
                             left join sites s on s.id = p.site_id
                             left join brand_followers bf on bf.brand_name = s.name
                             left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                             left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                    where bf.user_id = %s and s.type = %s and s.gender = %s {0} order by random() limit 60 offset %s
                    """.format(period_condition)
                products = Product.objects.raw(
                    sql,
                    [user.id, user.id, user.id, site_type, gender, offset])

        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.saved is None:
                saved = False
            else:
                saved = True
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
                'saved': saved,
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


class ProductsByBrandView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name):
        page_number = int(request.GET.get('page', 0))
        site_type = request.GET.get('site_type', 0)
        gender = int(request.GET.get('gender', 0))
        period = int(request.GET.get("period"))
        now = timezone.now()
        if period == 1:
            start_time = now.strftime("'%Y-%m-%d 00:00:00'")
            end_time = now.strftime("'%Y-%m-%d 23:59:59'")
            period_condition = "and p.inserted_at between {0} and {1}".format(start_time, end_time)
        elif period == 7:
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_time = start_of_week.strftime("'%Y-%m-%d 00:00:00'")
            end_time = end_of_week.strftime("'%Y-%m-%d 23:59:59'")
            period_condition = "and p.inserted_at between {0} and {1}".format(start_time, end_time)
        else:
            period_condition = ""

        user = request.user

        offset = page_number * 60
        if gender == 0:
            sql = """
                SELECT p.*, pl.liked, bp.saved
                FROM products p 
                        LEFT JOIN sites s ON p.site_id = s.id
                        left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                        left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                WHERE s.type=%s AND s.name=%s {0} ORDER BY random() LIMIT 60 OFFSET %s
                """.format(period_condition)

            products = Product.objects.raw(
                sql,
                [user.id, user.id, site_type, name, offset])
        else:
            sql = """
                SELECT p.*, pl.liked, bp.saved
                FROM products p 
                        LEFT JOIN sites s ON p.site_id = s.id
                        left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                        left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                WHERE s.type=%s AND s.name=%s AND s.gender=%s {0} ORDER BY random() LIMIT 60 OFFSET %s
                """.format(period_condition)
            products = Product.objects.raw(
                sql,
                [user.id, user.id, site_type, name, gender, offset])
        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.saved is None:
                saved = False
            else:
                saved = True
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
                'saved': saved
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
        sql2 = "select display_name from sites where name = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [name])
            row = cursor.fetchone()
            cursor.execute(sql2, [name])
            row2 = cursor.fetchone()

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
            'genders': row[0],
            'display_name': row2[0]
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
            select p.*, pl.*, bp.saved
            from (select product_id, user_id liked from product_love where user_id = %s) pl
                     left join products p on p.id = pl.product_id
                     left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
            ORDER BY random() LIMIT 60 OFFSET %s
            """,
            [user.id, user.id, offset])

        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.saved is None:
                saved = False
            else:
                saved = True
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
                'saved': saved
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
                select b.id, b.name, bp.product_id saved
                from boards b
                         left join (select * from board_product where product_id = %s and user_id = %s) bp on bp.board_id = b.id
                where b.user_id = %s
                """

            boards = Board.objects.raw(sql, [product_id, user.id, user.id, ])
            for board in boards:
                if board.saved is None:
                    saved = False
                else:
                    saved = True
                board_list.append({
                    'id': board.id,
                    'name': board.name,
                    'saved': saved
                })
            return Response({
                'data': board_list,
                'product_id': product_id,
            })
        else:
            page_number = int(request.GET.get('page'))
            offset = page_number * 60
            sql = """
                select * from (select b.id, name, type, image_filename, username, followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where b.type = 1
                union (
                select b.id, name, type, image_filename, username, followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where b.type = 0 and b.user_id = %s
                )) foo
                order by random() limit 60 offset %s
                """
            boards = Board.objects.raw(sql, [user.id, offset])
            for board in boards:
                if board.followers is not None:
                    followers = board.followers
                else:
                    followers = 0
                board_list.append({
                    'id': board.id,
                    'name': board.name,
                    'image_filename': board.image_filename,
                    'username': board.username,
                    'followers': followers,
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
            'saved': True
        })


class BoardsByCreatorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        user = request.user
        page_number = int(request.GET.get('page'))
        offset = page_number * 60

        if user.username == username:
            sql = """
                select b.id, name, type, image_filename, username, followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where au.username = %s
                order by random() limit 60 offset %s
                """
        else:
            sql = """
                select b.id, name, type, image_filename, username, followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where b.type = 1 and au.username = %s
                order by random() limit 60 offset %s
                """
        board_list = []
        boards = Board.objects.raw(sql, [username, offset])
        for board in boards:
            if board.followers is not None:
                followers = board.followers
            else:
                followers = 0
            board_list.append({
                'id': board.id,
                'name': board.name,
                'image_filename': board.image_filename,
                'username': board.username,
                'followers': followers,
            })
        return Response({
            'data': board_list,
        })


class ProductsByBoardNameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name):
        user = request.user
        board = Board.objects.get(name=name)
        page_number = int(request.GET.get('page'))
        offset = page_number * 60
        sql = """
            select p.*, bp.user_id saved, pl.liked
            from (select board_id, product_id from board_product where board_id = %s group by product_id, board_id) b
                     left join (select * from board_product where board_id = %s and user_id = %s) bp on bp.product_id = b.product_id
                     left join products p on p.id = b.product_id
                     left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id 
            order by random() LIMIT 60 OFFSET %s
            """
        products = Product.objects.raw(
            sql,
            [board.id, board.id, user.id, user.id, offset])

        product_list = []
        for product in products:
            if product.liked is None:
                liked = False
            else:
                liked = True
            if product.saved is None:
                saved = False
            else:
                saved = True
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
                'saved': saved
            })
        result = {
            'data': product_list
        }
        return Response(result)


class BoardInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, name):
        user = request.user
        board = Board.objects.get(name=name)

        followers = BoardFollower.objects.filter(board__name=name).count()
        try:
            BoardFollower.objects.get(board__name=name, user_id=user.id)
            is_following = True
        except BoardFollower.DoesNotExist:
            is_following = False

        if board.user_id == user.id:
            is_mine = True
        else:
            is_mine = False

        result = {
            'name': board.name,
            'type': board.type,
            'image_filename': board.image_filename,
            'description': board.description,
            'is_mine': is_mine,
            'followers': followers,
            'is_following': is_following,
        }
        return Response(result)

    def post(self, request, name):
        payload = JSONParser().parse(request)
        board_type = payload.get("type")
        board_name = payload.get('name')
        user = request.user
        board = Board.objects.get(user_id=user.id, name=name)
        if board_type:
            board.type = board_type
        if board_name:
            board.name = board_name
        board.save()
        return Response({
            'type': board.type
        })

    def delete(self, request, name):
        user = request.user
        Board.objects.filter(name=name, user_id=user.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, name):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            filename = file.name
            extension = filename.split(".")[-1]
            filename = uuid.uuid4().hex
            filename = "{0}.{1}".format(filename, extension)
            with open("/home/deploy/images/boards/{0}".format(filename), 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)

                board = Board.objects.get(name=name)
                board.image_filename = "boards/{0}".format(filename)
                board.save()

            return Response({
                'message': 'OK',
            })
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ToggleFollowBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = JSONParser().parse(request)
        board_name = payload.get('name')
        if board_name:
            user = request.user
            try:
                board = Board.objects.get(name=board_name)
            except Board.DoesNotExist:
                result = {
                    'message': 'Bad request'
                }
                return Response(result, status=404)
            try:
                board_follower = BoardFollower.objects.get(board_id=board.id, user_id=user.id)
                board_follower.delete()
                followers = BoardFollower.objects.filter(board_id=board.id).count()
                result = {
                    'followers': followers,
                    'is_following': False
                }
                return Response(result)
            except BoardFollower.DoesNotExist:
                BoardFollower.objects.create(board_id=board.id, user_id=user.id)
                followers = BoardFollower.objects.filter(board_id=board.id).count()
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
                'saved': False
            })
        except BoardProduct.DoesNotExist:
            serializer.save(user=request.user)
            return Response({
                'saved': True
            })


class MyFollowingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        page_number = int(request.GET.get('page'))
        offset = page_number * 60

        sql = """
        select b.*, bf2.followers, au.username, bf.user_id follower_id
        from board_follower bf
                 left join boards b on bf.board_id = b.id
                 left join (select board_id, count(board_id) followers from board_follower group by board_id) bf2
                           on bf2.board_id = b.id
                 left join auth_user au on b.user_id = au.id
        where b.type = 1 and bf.user_id= %s
        order by random() limit 60 offset %s
        """

        board_list = []
        boards = Board.objects.raw(sql, [user.id, offset])
        for board in boards:
            if board.followers is not None:
                followers = board.followers
            else:
                followers = 0
            board_list.append({
                'id': board.id,
                'name': board.name,
                'image_filename': board.image_filename,
                'username': board.username,
                'followers': followers,
            })
        return Response({
            'data': board_list,
        })


class TicketView(APIView):
    def post(self, request):
        serializer = TicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return Response({
            'message': "We've received your message. We'll inform you soon."
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
