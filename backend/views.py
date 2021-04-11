import mimetypes
import os
import uuid
from datetime import timedelta
from shutil import copyfile

import facebook
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views import View
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from slugify import slugify

from backend.forms import UploadFileForm, TicketForm
from backend.models import Product, UserProfile, BrandFollower, ProductLove, Board, BoardProduct, \
    BoardFollower, Ticket, UserSocialAuth
from backend.serializers import ForgotPasswordSerializer, TicketSerializer, UserSerializer, CreateBoardSerializer, \
    BoardSerializer, \
    BoardProductSerializer, FollowBoardSerializer, CustomAuthTokenSerializer, ResetPasswordSerializer
from backend.utils import api_auth, make_username


class CustomAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return api_auth(user, token)


class SocialLogin(APIView):
    def post(self, request, provider):
        if provider == 'google':
            token = request.data.get('token')
            client_id = settings.GOOGLE_SIGNIN_CLIENT_ID
            try:
                idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
            except GoogleAuthError:
                return Response({
                    'message': 'invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
            email = idinfo.get('email')
            userid = idinfo.get('sub')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                first_name = idinfo.get('given_name')
                last_name = idinfo.get('family_name')
                password = get_random_string(length=16)
                user = User.objects.create_user(
                    email=email, password=password, first_name=first_name, last_name=last_name,
                    username=make_username(first_name, last_name)
                )
                UserProfile.objects.create(
                    user=user,
                    gender=0,
                    birthday=None
                )
            try:
                UserSocialAuth.objects.get(provider='google', uid=userid)
            except UserSocialAuth.DoesNotExist:
                UserSocialAuth.objects.create(user=user, provider='google', uid=userid, extra_data=idinfo)
        elif provider == 'facebook':
            token = request.data.get('token')
            graph = facebook.GraphAPI(access_token=token)
            try:
                profile = graph.get_object("me", fields="id,first_name,last_name,name,picture,email")
            except facebook.GraphAPIError:
                return Response({
                    'message': 'invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
            email = profile.get("email")
            userid = profile.get('id')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                first_name = profile.get('first_name')
                last_name = profile.get('last_name')
                password = get_random_string(length=16)
                user = User.objects.create_user(
                    email=email, password=password, first_name=first_name, last_name=last_name,
                    username=make_username(first_name, last_name)
                )
                UserProfile.objects.create(
                    user=user,
                    gender=0,
                    birthday=None
                )
            try:
                UserSocialAuth.objects.get(provider='facebook', uid=userid)
            except UserSocialAuth.DoesNotExist:
                UserSocialAuth.objects.create(user=user, provider=provider, uid=userid, extra_data=profile)
        else:
            user = None
        token, created = Token.objects.get_or_create(user=user)
        return api_auth(user, token)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


class UserCreateView(APIView):
    def post(self, request):
        data = request.data
        serializer = UserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
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
                "birthday": profile.birthday
            },
            'meta': {
                'token': token.key
            }
        })


class SendResetPasswordLink(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data=data)


class ResetPassword(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data=data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            request.user.profile
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=request.user)
        content = {
            "last_name": request.user.last_name,
            "last_login": request.user.last_login,
            "gender": request.user.profile.gender,
            "first_name": request.user.first_name,
            "email": request.user.email,
            "birthday": request.user.profile.birthday
        }
        return Response(content)

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


class ProductsView(APIView):
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
            gender_condition = "inserted_at desc"
        elif period == 7:
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_time = start_of_week.strftime("'%Y-%m-%d 00:00:00'")
            end_time = end_of_week.strftime("'%Y-%m-%d 23:59:59'")
            period_condition = "and p.inserted_at between {0} and {1}".format(start_time, end_time)
            gender_condition = "random()"
        else:
            period_condition = ""
            gender_condition = "random()"

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
                    WHERE s.type=%s {0} ORDER BY {1} LIMIT 60 OFFSET %s
                    """.format(period_condition, gender_condition)
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
                    WHERE s.type=%s AND s.gender=%s {0} ORDER BY {1} LIMIT 60 OFFSET %s
                    """.format(period_condition, gender_condition)
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
                    where bf.user_id = %s and s.type = %s {0} order by {1} limit 60 offset %s
                    """.format(period_condition, gender_condition)
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
                    where bf.user_id = %s and s.type = %s and s.gender = %s {0} order by {1} limit 60 offset %s
                    """.format(period_condition, gender_condition)
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
            gender_condition = "inserted_at desc"
        elif period == 7:
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_time = start_of_week.strftime("'%Y-%m-%d 00:00:00'")
            end_time = end_of_week.strftime("'%Y-%m-%d 23:59:59'")
            period_condition = "and p.inserted_at between {0} and {1}".format(start_time, end_time)
            gender_condition = "random()"
        else:
            period_condition = ""
            gender_condition = "random()"

        user = request.user

        offset = page_number * 60
        if gender == 0:
            sql = """
                SELECT p.*, pl.liked, bp.saved
                FROM products p 
                        LEFT JOIN sites s ON p.site_id = s.id
                        left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id
                        left join (select product_id, user_id saved from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = p.id 
                WHERE s.type=%s AND s.name=%s {0} ORDER BY {1} LIMIT 60 OFFSET %s
                """.format(period_condition, gender_condition)

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
                WHERE s.type=%s AND s.name=%s AND s.gender=%s {0} ORDER BY {1} LIMIT 60 OFFSET %s
                """.format(period_condition, gender_condition)
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
            sort_type = int(request.GET.get('order'))
            if sort_type == 0:
                order = 'random()'
            elif sort_type == 1:
                order = 'followers desc'
            else:
                order = 'random()'
            offset = page_number * 60
            sql = """
                select * from (select b.id, name, type, slug, image_filename, username, COALESCE(followers, 0) followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where b.type = 1
                union (
                select b.id, name, type, slug, image_filename, username, COALESCE(followers, 0) followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where b.type = 0 and b.user_id = %s
                )) foo
                order by {} limit 60 offset %s
                """.format(order)
            boards = Board.objects.raw(sql, [user.id, offset])
            for board in boards:
                if board.followers is not None:
                    followers = board.followers
                else:
                    followers = 0
                board_list.append({
                    'id': board.id,
                    'name': board.name,
                    'slug': board.slug,
                    'image_filename': board.image_filename,
                    'username': board.username,
                    'followers': followers,
                })
            return Response({
                'data': board_list,
            })

    def post(self, request):
        user = request.user
        serializer = CreateBoardSerializer(data=request.data, user=user)
        serializer.is_valid(raise_exception=True)
        board_name = serializer.validated_data['board_name']
        board_type = serializer.validated_data['board_type']
        product_id = serializer.validated_data['product_id']
        product = Product.objects.get(pk=product_id)
        image_filename = product.image_filename
        base_path = "/home/deploy/images"
        source = "{}/{}".format(base_path, image_filename)
        board_filename = "boards/{}".format(os.path.basename(source))
        target = "{}/{}".format(base_path, board_filename)
        try:
            copyfile(source, target)
        except IOError as e:
            print("Unable to copy file. %s" % e)
        slug = slugify(board_name)
        board = Board.objects.create(name=board_name, type=board_type, user_id=user.id, image_filename=board_filename,
                                     slug=slug)
        board_serializer = BoardSerializer(board)
        BoardProduct.objects.create(product_id=product_id, board_id=board.id, user_id=user.id)
        return Response({
            'board': board_serializer.data,
            'saved': True
        })


class BoardsByUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        user = request.user
        page_number = int(request.GET.get('page'))
        offset = page_number * 60

        if user.username == username:
            sql = """
                select b.id, name, slug, type, image_filename, username, followers
                from boards b
                         left join auth_user au on b.user_id = au.id
                         left join (select board_id, count(board_id) followers from board_follower group by board_id) bf
                                   on b.id = bf.board_id
                where au.username = %s
                order by random() limit 60 offset %s
                """
        else:
            sql = """
                select b.id, name, slug, type, image_filename, username, followers
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
                'slug': board.slug,
                'image_filename': board.image_filename,
                'username': board.username,
                'followers': followers,
            })
        return Response({
            'data': board_list,
        })


class ProductsByBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username, slug):
        user = request.user
        board = Board.objects.get(slug=slug, user__username=username)
        page_number = int(request.GET.get('page'))
        offset = page_number * 60
        sql = """
            select p.*, bp.user_id saved, pl.liked
            from (select board_id, product_id from board_product where board_id = %s group by product_id, board_id) b
                     left join (select product_id, user_id from board_product where user_id = %s group by product_id, user_id) bp on bp.product_id = b.product_id
                     left join products p on p.id = b.product_id
                     left join (select product_id, user_id liked from product_love where user_id = %s) pl on pl.product_id = p.id 
            order by random() LIMIT 60 OFFSET %s
            """
        products = Product.objects.raw(
            sql,
            [board.id, user.id, user.id, offset])

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

    def get(self, request, username, slug):
        user = request.user
        board = Board.objects.get(slug=slug, user__username=username)

        followers = BoardFollower.objects.filter(board__slug=slug).count()
        try:
            BoardFollower.objects.get(board__slug=slug, user_id=user.id)
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

    def post(self, request, username, slug):
        payload = JSONParser().parse(request)
        board_type = payload.get("type")
        board_name = payload.get('name')
        description = payload.get('description')
        user = request.user
        board = Board.objects.get(user_id=user.id, slug=slug)
        if board.name != board_name:
            c = Board.objects.filter(user_id=user.id, name=board_name).count()
            if c > 0:
                return Response({
                    'message': 'This name already exists in your boards.'
                }, status=status.HTTP_400_BAD_REQUEST)
        if board_type == 0 or board_type == 1:
            board.type = board_type
        if board_name:
            board.name = board_name
        if description or description == '':
            board.description = description
        board.save()
        return Response({
            'type': board.type,
            'name': board.name
        })

    def delete(self, request, username, slug):
        user = request.user
        Board.objects.filter(slug=slug, user_id=user.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username, slug):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if file.size > 1048576:
                return Response({
                    'message': 'Your image is too big. Max size 1MB'
                }, status=status.HTTP_400_BAD_REQUEST)
            filename = file.name
            extension = filename.split(".")[-1]
            filename = uuid.uuid4().hex
            filename = "{0}.{1}".format(filename, extension)
            with open("/home/deploy/images/boards/{0}".format(filename), 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)

                board = Board.objects.get(slug=slug, user__username=username)
                board.image_filename = "boards/{0}".format(filename)
                board.save()

            return Response({
                'message': 'OK',
            })
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ToggleFollowBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FollowBoardSerializer(data=request.data, user=request.user)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data=data)


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
                'slug': board.slug,
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


class ReplyTicket(View):
    def post(self, request, object_id):
        ticket = Ticket.objects.get(pk=object_id)
        form = TicketForm(data=request.POST, instance=ticket)
        if form.is_valid():
            email = form.data.get('email')
            reply_message = form.data.get('reply_message')
            if reply_message:
                result = send_mail(
                    subject='Reply',
                    message='',
                    html_message=reply_message,
                    recipient_list=[email],
                    from_email=settings.DEFAULT_FROM_EMAIL
                )
                form.save()
                messages.success(request, 'Successfully replied.')
            else:
                messages.error(request, 'The error')
        else:
            messages.error(request, 'The error')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


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


class EmailPreview(View):
    def get(self, request, name):
        template_name = "emails/{}.html".format(name)
        return render(request, template_name)
