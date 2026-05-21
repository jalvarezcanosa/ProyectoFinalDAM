import token
from datetime import datetime, timedelta
import json
from json import JSONDecodeError

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db.models import F, Sum, Q, Value
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from cont01app.models import Counter, CounterMembership, CustomUser

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    data = request.data

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    telephone = data.get('telephone')

    if not username or not email or not password or not telephone:
        return JsonResponse({'error': 'Missing required data'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already exists'}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'email already exists'}, status=400)

    if User.objects.filter(telephone=telephone).exists():
        return JsonResponse({'error': 'telephone already exists'}, status=400)

    ## create_user hashea automáticamente la contraseña
    new_user = User.objects.create_user(
        username=username,
        email=email,
        telephone=telephone,
        password=password,
    )

    refresh = RefreshToken.for_user(new_user)

    return JsonResponse({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'telephone': new_user.telephone,
        }
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    data = request.data

    identifier = data.get('username') or data.get('email') or data.get('telephone')
    password = data.get('password')

    if not identifier or not password:
        return JsonResponse({'error': 'Identifier and password are required'}, status=400)

    user = User.objects.filter(
        Q(username=identifier) |
        Q(email=identifier) |
        Q(telephone=identifier)
    ).first()

    if user is None or not user.check_password(password):
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)

    return JsonResponse({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'telephone': user.telephone,
        }
    }, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_counter_mine(request):
    memberships = CounterMembership.objects.filter(user=request.user).select_related('counter')

    memberships = memberships.annotate(
        global_count_annotated=Sum('counter__countermembership__individual_count')
    )

    counters_list = []

    for membership in memberships:
        counter = membership.counter

        counters_list.append({
            "id": counter.id,
            "title": counter.title,
            "image_url": counter.image.url if counter.image else None,
            "status": counter.status,
            "individual_count": membership.individual_count,
            "global_count": membership.global_count_annotated or 0,
        })

    return JsonResponse(counters_list, safe=False, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_counter(request):
    title = request.data.get('title')
    description = request.data.get('description')
    closed_at = request.data.get('closed_at')
    image = request.data.get('image')

    if not title or not closed_at:
        return JsonResponse({'message': 'Title and closed_at are required'}, status=400)

    closed_at_parse = parse_datetime(closed_at)

    if closed_at_parse is None:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    if timezone.is_naive(closed_at_parse):
        closed_at_parse = timezone.make_aware(closed_at_parse)

    if closed_at_parse < timezone.now():
        return JsonResponse({'error': 'The closed_at date cannot be in the past!'}, status=400)

    new_counter = Counter(
        title=title,
        description=description,
        closed_at=closed_at,
        creator=request.user,
    )

    if image:
        new_counter.image = image

    new_counter.save()

    CounterMembership.objects.create(user=request.user, counter=new_counter, individual_count=0)

    return JsonResponse({
        "message": "Counter created successfully!",
        "counter_id": new_counter.id,
        "invite_code": str(new_counter.invite_code)
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_counter_by_id(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)

    membership = CounterMembership.objects.filter(user=request.user, counter=counter).first()

    if not membership:
        return JsonResponse({'error': 'You are not a member of this counter'}, status=403)

    ranking_query = CounterMembership.objects.filter(counter=counter).values(
        username=F('user__username'),
        total_clicks=F('individual_count')
    ).order_by('-individual_count')

    global_count = CounterMembership.objects.filter(counter=counter).aggregate(total=Sum('individual_count'))['total'] or 0

    image_url = None
    if counter.image:
        image_url = request.build_absolute_uri(counter.image.url)

    response_data = {
        "id": counter.id,
        "title": counter.title,
        "description": counter.description,
        "image_url": image_url,
        "status": counter.status,
        "closed_at": counter.closed_at.isoformat() if counter.closed_at else None,
        "participants": counter.participants.count(),
        "global_count": global_count,
        "individual_count": membership.individual_count,
        "ranking": list(ranking_query),
        "invite_code": str(counter.invite_code),
    }

    return JsonResponse(response_data, safe=False, status=200)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_counter(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)

    if counter.creator != request.user:
        return JsonResponse({'error': 'Not authorized'}, status=403)

    if counter.status == 'closed':
        return JsonResponse({'error': 'Counter is closed and cannot be modified'}, status=400)

    data = request.data

    if 'title' in data and data['title']:
        counter.title = data['title']

    if 'description' in data:
        counter.description = data['description']

    if 'closed_at' in data:
        closed_at_str = data['closed_at']
        if closed_at_str == "":
            counter.closed_at = None
        else:
            closed_at_parse = parse_datetime(closed_at_str)
            if closed_at_parse is not None:
                if timezone.is_naive(closed_at_parse):
                    closed_at_parse = timezone.make_aware(closed_at_parse)
                counter.closed_at = closed_at_parse

    if 'image' in request.FILES:
        counter.image = request.FILES['image']

    counter.save()

    return JsonResponse({
        "message": "Counter updated successfully!",
        "counter_id": counter.id,
    }, status=200)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_counter(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)

    if counter.creator != request.user:
        return JsonResponse({"message": "Forbidden: Only the creator can delete this counter."}, status=403)

    counter.delete()

    return HttpResponse(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def increment_counter(request, counter_id):
    counter = get_object_or_404(Counter, id=counter_id)

    if counter.status == 'closed':
        return JsonResponse({'error': 'Counter is already closed!'}, status=400)

    membership = CounterMembership.objects.filter(user=request.user, counter=counter).first()

    if not membership:
        return JsonResponse({'error': 'You must join the counter first'}, status=401)

    membership.individual_count += 1
    membership.save()

    global_count = CounterMembership.objects.filter(counter=counter).aggregate(total=Sum('individual_count'))['total'] or 0

    return JsonResponse({
        'message': 'Counter incremented successfully!',
        'individual_count': membership.individual_count,
        'global_count': global_count
    }, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_counter(request):
    data = request.data

    invite_code = data.get('invite_code')
    if not invite_code:
        return JsonResponse({'error': 'invite_code is required'}, status=400)

    counter = Counter.objects.filter(invite_code=invite_code).first()
    if not counter:
        return JsonResponse({'error': 'Counter not found'}, status=404)

    if counter.status != 'open':
        return JsonResponse({'error': 'Counter is closed'}, status=400)

    if CounterMembership.objects.filter(user=request.user, counter=counter).exists():
        return JsonResponse({'error': 'You are already a member'}, status=400)

    CounterMembership.objects.create(user=request.user, counter=counter, individual_count=0)

    return JsonResponse({
        'id': counter.id,
        'title': counter.title,
        'description': counter.description,
        'status': counter.status,
        'invite_code': str(counter.invite_code)
    }, status=201)