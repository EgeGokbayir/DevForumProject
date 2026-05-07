import os
import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Count, F, Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .models import (
    Answer,
    AnswerVote,
    BlogComment,
    BlogFavorite,
    BlogLike,
    BlogPost,
    BlogSaved,
    Conversation,
    Follow,
    Message,
    Notification,
    Profile,
    Question,
    QuestionFavorite,
    QuestionFollow,
    QuestionView,
    QuestionVote,
    Tag,
    TagFollow,
)


# ------------------------------------------------------------
# Yetki yardımcıları
# ------------------------------------------------------------

def is_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name='Admin').exists()
    )


def is_moderator_user(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name='Admin').exists()
        or user.groups.filter(name='Moderator').exists()
    )


def is_blogger_user(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name='Admin').exists()
        or user.groups.filter(name='Blogger').exists()
    )


def get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={'avatar_seed': user.username},
    )
    return profile


def can_user_interact(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser or is_admin_user(user):
        return True

    profile = get_or_create_profile(user)
    return profile.is_platform_active


def make_tag_slug(tag_name):
    tag_name = tag_name.strip().lower()

    replacements = {
        'c#': 'csharp',
        'c++': 'cpp',
        '.net': 'dotnet',
        'node.js': 'nodejs',
        'vue.js': 'vuejs',
        'next.js': 'nextjs',
    }

    for old, new in replacements.items():
        tag_name = tag_name.replace(old, new)

    tag_name = tag_name.replace('#', 'sharp')
    tag_name = tag_name.replace('+', 'plus')

    return slugify(tag_name) or 'etiket'


def parse_tag_names(tag_text):
    tag_names = [
        item.strip().lower()
        for item in re.split(r'[,\s]+', tag_text or '')
        if item.strip()
    ]
    return list(dict.fromkeys(tag_names))[:5]


def get_or_create_tags_from_text(tag_text, actor=None):
    tags = []
    created_tags = []

    for tag_name in parse_tag_names(tag_text):
        tag_slug = make_tag_slug(tag_name)
        tag, created = Tag.objects.get_or_create(
            slug=tag_slug,
            defaults={
                'name': tag_name,
                'description': f'{tag_name} ile ilgili içerikler',
                'is_active': True,
            }
        )
        tags.append(tag)

        if created:
            created_tags.append(tag)

    for tag in created_tags:
        notify_new_tag(tag, actor)

    return tags


# ------------------------------------------------------------
# Bildirim yardımcıları
# ------------------------------------------------------------

def notification_context(request):
    if not request.user.is_authenticated:
        return {
            'recent_notifications': [],
            'unread_notification_count': 0,
            'unread_message_count': 0,
            'is_admin_nav': False,
            'is_blogger_nav': False,
        }

    unread_message_count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()

    return {
        'recent_notifications': Notification.objects.filter(user=request.user).select_related(
            'actor', 'question', 'answer', 'tag', 'conversation', 'blog'
        )[:8],
        'unread_notification_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        'unread_message_count': unread_message_count,
        'is_admin_nav': is_admin_user(request.user),
        'is_blogger_nav': is_blogger_user(request.user),
    }


def render_page(request, template_name, context=None, status=None):
    context = context or {}
    context.update(notification_context(request))
    context.setdefault('is_admin', is_admin_user(request.user))
    context.setdefault('is_moderator', is_moderator_user(request.user))
    context.setdefault('is_blogger', is_blogger_user(request.user))
    return render(request, template_name, context, status=status)


def create_notification(
    user,
    title,
    message='',
    notification_type='system',
    actor=None,
    question=None,
    answer=None,
    tag=None,
    conversation=None,
    blog=None,
):
    if not user:
        return None

    if actor and user.id == actor.id:
        return None

    return Notification.objects.create(
        user=user,
        actor=actor,
        title=title,
        message=message,
        notification_type=notification_type,
        question=question,
        answer=answer,
        tag=tag,
        conversation=conversation,
        blog=blog,
    )


def create_notifications_for_user_ids(
    user_ids,
    title,
    message='',
    notification_type='system',
    actor=None,
    question=None,
    answer=None,
    tag=None,
    conversation=None,
    blog=None,
):
    user_ids = set(user_ids)

    if actor:
        user_ids.discard(actor.id)

    notifications = [
        Notification(
            user=user,
            actor=actor,
            title=title,
            message=message,
            notification_type=notification_type,
            question=question,
            answer=answer,
            tag=tag,
            conversation=conversation,
            blog=blog,
        )
        for user in User.objects.filter(id__in=user_ids)
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_question_watchers_about_answer(question, answer, actor):
    user_ids = {question.author_id}

    user_ids.update(
        QuestionFavorite.objects.filter(question=question).values_list('user_id', flat=True)
    )
    user_ids.update(
        QuestionFollow.objects.filter(question=question).values_list('user_id', flat=True)
    )
    user_ids.update(
        Answer.objects.filter(question=question, parent_answer__isnull=True).values_list('author_id', flat=True)
    )

    create_notifications_for_user_ids(
        user_ids=user_ids,
        title='Takip ettiğiniz soruya yeni cevap geldi',
        message=f'“{question.title}” sorusuna yeni bir cevap yazıldı.',
        notification_type='new_answer',
        actor=actor,
        question=question,
        answer=answer,
    )


def notify_followed_tags_about_question(question, actor):
    tag_ids = question.tags.values_list('id', flat=True)

    user_ids = (
        TagFollow.objects
        .filter(tag_id__in=tag_ids)
        .values_list('user_id', flat=True)
        .distinct()
    )

    create_notifications_for_user_ids(
        user_ids=user_ids,
        title='Takip ettiğiniz etikette yeni soru açıldı',
        message=f'“{question.title}” sorusu takip ettiğiniz etiketlerden biriyle açıldı.',
        notification_type='followed_tag_question',
        actor=actor,
        question=question,
    )


def notify_new_tag(tag, actor=None):
    create_notifications_for_user_ids(
        user_ids=User.objects.values_list('id', flat=True),
        title='Yeni etiket oluşturuldu',
        message=f'“{tag.name}” etiketi oluşturuldu.',
        notification_type='new_tag',
        actor=actor,
        tag=tag,
    )


def notify_followers_for_blog(blog):
    followers = Follow.objects.filter(following=blog.author).values_list('follower_id', flat=True)

    create_notifications_for_user_ids(
        user_ids=followers,
        title='Takip ettiğiniz kullanıcı blog paylaştı',
        message=f'{blog.author.username} yeni bir blog yazısı paylaştı: {blog.title}',
        notification_type='blog_new',
        actor=blog.author,
        blog=blog,
    )


def notify_blog_watchers(blog):
    user_ids = set()
    user_ids.update(blog.favorites.values_list('user_id', flat=True))
    user_ids.update(blog.saved_by.values_list('user_id', flat=True))
    user_ids.discard(blog.author_id)

    create_notifications_for_user_ids(
        user_ids=user_ids,
        title='Favori/kayıtlı blog güncellendi',
        message=f'“{blog.title}” blog yazısında değişiklik yapıldı.',
        notification_type='blog_updated',
        actor=blog.author,
        blog=blog,
    )


# ------------------------------------------------------------
# Genel sayfalar
# ------------------------------------------------------------

def anasayfa(request):
    questions = (
        Question.objects
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')[:10]
    )

    popular_tags = (
        Tag.objects
        .filter(is_active=True)
        .annotate(question_total=Count('questions', distinct=True))
        .order_by('-question_total', 'name')[:12]
    )

    return render_page(request, 'forum/index.html', {
        'questions': questions,
        'popular_tags': popular_tags,
        'question_count': Question.objects.count(),
        'user_count': User.objects.count(),
        'tag_count': Tag.objects.count(),
        'answer_count': Answer.objects.count(),
    })


def ara(request):
    q = request.GET.get('q', '').strip()

    questions = Question.objects.none()
    users = User.objects.none()
    tags = Tag.objects.none()
    blogs = BlogPost.objects.none()

    if q:
        questions = Question.objects.filter(
            Q(title__icontains=q) |
            Q(body__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct().select_related('author', 'author__profile').prefetch_related('tags', 'answers', 'votes')

        users = User.objects.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(profile__bio__icontains=q) |
            Q(profile__skills__icontains=q)
        ).distinct()

        tags = Tag.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q),
            is_active=True,
        )

        blogs = BlogPost.objects.filter(
            Q(title__icontains=q) |
            Q(summary__icontains=q) |
            Q(content__icontains=q),
            is_published=True,
        ).distinct()

    return render_page(request, 'forum/arama.html', {
        'search_query': q,
        'questions': questions,
        'users': users,
        'tags': tags,
        'blogs': blogs,
    })


def custom_404(request, exception):
    return render_page(request, 'forum/404.html', status=404)


# ------------------------------------------------------------
# Auth
# ------------------------------------------------------------

def giris_yap(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username_or_email, password=password)

        if user is None:
            try:
                found_user = User.objects.get(email=username_or_email)
                user = authenticate(request, username=found_user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            get_or_create_profile(user)
            messages.success(request, 'Başarıyla giriş yaptınız.')
            return redirect('anasayfa')

        messages.error(request, 'Kullanıcı adı/e-posta veya şifre hatalı.')

    return render_page(request, 'forum/giris.html')


def kayit_ol(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not username or not email or not password:
            messages.error(request, 'Tüm zorunlu alanları doldurun.')
            return redirect('kayit')

        if password != password2:
            messages.error(request, 'Şifreler eşleşmiyor.')
            return redirect('kayit')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor.')
            return redirect('kayit')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu e-posta zaten kullanılıyor.')
            return redirect('kayit')

        user = User.objects.create_user(username=username, email=email, password=password)
        get_or_create_profile(user)

        login(request, user)
        messages.success(request, 'Kayıt başarılı.')
        return redirect('anasayfa')

    return render_page(request, 'forum/kayit.html')


def cikis_yap(request):
    logout(request)
    messages.success(request, 'Çıkış yaptınız.')
    return redirect('anasayfa')


# ------------------------------------------------------------
# Sorular
# ------------------------------------------------------------

def sorular(request):
    q = request.GET.get('q', '').strip()
    filter_type = request.GET.get('filter', 'new')

    questions = (
        Question.objects
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .all()
    )

    if q:
        questions = questions.filter(
            Q(title__icontains=q) |
            Q(body__icontains=q) |
            Q(tags__name__icontains=q)
        ).distinct()

    if filter_type == 'unanswered':
        questions = questions.filter(answers__isnull=True)
    elif filter_type == 'solved':
        questions = questions.filter(is_solved=True)
    elif filter_type == 'popular':
        questions = questions.annotate(vote_total=Count('votes')).order_by('-views', '-vote_total')
    else:
        questions = questions.order_by('-created_at')

    popular_tags = (
        Tag.objects
        .filter(is_active=True)
        .annotate(question_total=Count('questions', distinct=True))
        .order_by('-question_total', 'name')[:12]
    )

    return render_page(request, 'forum/sorular.html', {
        'questions': questions,
        'popular_tags': popular_tags,
        'total_questions': questions.count(),
        'search_query': q,
        'filter_type': filter_type,
    })


def soru_detay(request, soru_id):
    question = get_object_or_404(
        Question.objects.select_related('author', 'author__profile').prefetch_related('tags', 'votes'),
        id=soru_id,
    )

    if request.user.is_authenticated:
        if question.author_id != request.user.id:
            _, created = QuestionView.objects.get_or_create(question=question, user=request.user)
            if created:
                Question.objects.filter(id=question.id).update(views=F('views') + 1)
                question.refresh_from_db(fields=['views'])
    else:
        viewed_questions = request.session.get('viewed_questions', [])
        key = str(question.id)
        if key not in viewed_questions:
            viewed_questions.append(key)
            request.session['viewed_questions'] = viewed_questions
            request.session.modified = True
            Question.objects.filter(id=question.id).update(views=F('views') + 1)
            question.refresh_from_db(fields=['views'])

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Cevap yazmak için giriş yapmalısınız.')
            return redirect('giris')

        if not can_user_interact(request.user):
            messages.error(request, 'Hesabınız cevap yazma işlemi için pasif durumda. Lütfen moderatöre ulaşın.')
            return redirect('soru_detay', soru_id=question.id)

        body = request.POST.get('body', '').strip()
        code = request.POST.get('code', '').strip()

        if not body:
            messages.error(request, 'Cevap alanı boş bırakılamaz.')
            return redirect('soru_detay', soru_id=question.id)

        answer = Answer.objects.create(question=question, author=request.user, body=body, code=code)
        notify_question_watchers_about_answer(question, answer, request.user)

        messages.success(request, 'Cevabınız eklendi.')
        return HttpResponseRedirect(f"{reverse('soru_detay', args=[question.id])}#answer-{answer.id}")

    answers = (
        question.answers
        .filter(parent_answer__isnull=True)
        .select_related('author', 'author__profile')
        .prefetch_related('votes', 'replies', 'replies__author', 'replies__author__profile', 'replies__votes')
        .order_by('-is_accepted', '-created_at')
    )

    related_questions = (
        Question.objects
        .filter(tags__in=question.tags.filter(is_active=True))
        .exclude(id=question.id)
        .distinct()
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')[:5]
    )

    popular_tags = (
        Tag.objects
        .filter(is_active=True)
        .annotate(question_total=Count('questions', distinct=True))
        .order_by('-question_total', 'name')[:10]
    )

    is_favorited = False
    is_followed = False

    if request.user.is_authenticated:
        is_favorited = QuestionFavorite.objects.filter(user=request.user, question=question).exists()
        is_followed = QuestionFollow.objects.filter(user=request.user, question=question).exists()

    return render_page(request, 'forum/soru-detay.html', {
        'question': question,
        'answers': answers,
        'related_questions': related_questions,
        'popular_tags': popular_tags,
        'is_favorited': is_favorited,
        'is_followed': is_followed,
        'question_tag_string': ', '.join(question.tags.values_list('name', flat=True)),
    })


@login_required
def soru_sor(request):
    if not can_user_interact(request.user):
        messages.error(request, 'Hesabınız soru sorma işlemi için pasif durumda. Lütfen moderatöre ulaşın.')
        return redirect('anasayfa')

    popular_tags = (
        Tag.objects.filter(is_active=True)
        .annotate(question_total=Count('questions', distinct=True))
        .order_by('-question_total', 'name')[:12]
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        code = request.POST.get('code', '').strip()
        tag_text = request.POST.get('tags', '').strip()

        if not title or not body:
            messages.error(request, 'Başlık ve soru detayı zorunludur.')
            return redirect('soru_sor')

        tags = get_or_create_tags_from_text(tag_text, actor=request.user)

        if not tags:
            messages.error(request, 'En az bir etiket eklemelisiniz.')
            return redirect('soru_sor')

        question = Question.objects.create(author=request.user, title=title, body=body, code=code)
        question.tags.set(tags)

        notify_followed_tags_about_question(question, request.user)

        messages.success(request, 'Sorunuz başarıyla oluşturuldu.')
        return redirect('soru_detay', soru_id=question.id)

    return render_page(request, 'forum/soru-sor.html', {'popular_tags': popular_tags})


@login_required
def soru_duzenle(request, soru_id):
    question = get_object_or_404(Question.objects.prefetch_related('tags'), id=soru_id)

    if question.author_id != request.user.id and not is_admin_user(request.user):
        messages.error(request, 'Bu soruyu düzenleme yetkiniz yok.')
        return redirect('soru_detay', soru_id=question.id)

    if request.method != 'POST':
        return redirect('soru_detay', soru_id=question.id)

    title = request.POST.get('title', '').strip()
    body = request.POST.get('body', '').strip()
    code = request.POST.get('code', '').strip()
    tag_text = request.POST.get('tags', '').strip()

    if not title or not body:
        messages.error(request, 'Başlık ve soru detayı boş bırakılamaz.')
        return redirect('soru_detay', soru_id=question.id)

    tags = get_or_create_tags_from_text(tag_text, actor=request.user)
    if not tags:
        messages.error(request, 'En az bir etiket eklemelisiniz.')
        return redirect('soru_detay', soru_id=question.id)

    question.title = title
    question.body = body
    question.code = code
    question.save(update_fields=['title', 'body', 'code', 'updated_at'])
    question.tags.set(tags)

    messages.success(request, 'Soru başarıyla güncellendi.')
    return redirect('soru_detay', soru_id=question.id)


@login_required
def soru_sil(request, soru_id):
    question = get_object_or_404(Question, id=soru_id)

    if question.author_id != request.user.id and not is_admin_user(request.user):
        messages.error(request, 'Bu soruyu silme yetkiniz yok.')
        return redirect('soru_detay', soru_id=question.id)

    if question.answers.exists() and not is_admin_user(request.user):
        messages.error(request, 'Bu soruya cevap geldiği için artık silemezsiniz.')
        return redirect('soru_detay', soru_id=question.id)

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Soru başarıyla silindi.')
        return redirect('sorular')

    return redirect('soru_detay', soru_id=question.id)


@login_required
def soru_oyla(request, soru_id, yon):
    question = get_object_or_404(Question, id=soru_id)
    value = 1 if yon == 'up' else -1

    QuestionVote.objects.update_or_create(
        question=question,
        user=request.user,
        defaults={'value': value},
    )

    return redirect('soru_detay', soru_id=question.id)


@login_required
def soru_favori(request, soru_id):
    question = get_object_or_404(Question, id=soru_id)
    fav, created = QuestionFavorite.objects.get_or_create(user=request.user, question=question)

    if not created:
        fav.delete()
        messages.info(request, 'Soru favorilerden çıkarıldı.')
    else:
        messages.success(request, 'Soru favorilere eklendi.')

    return redirect('soru_detay', soru_id=question.id)


@login_required
def soru_takip(request, soru_id):
    question = get_object_or_404(Question, id=soru_id)
    follow, created = QuestionFollow.objects.get_or_create(user=request.user, question=question)

    if not created:
        follow.delete()
        messages.info(request, 'Soru takibi kaldırıldı.')
    else:
        messages.success(request, 'Soru takip edildi.')

    return redirect('soru_detay', soru_id=question.id)


@login_required
def cevap_oyla(request, cevap_id, yon):
    answer = get_object_or_404(Answer, id=cevap_id)
    value = 1 if yon == 'up' else -1

    AnswerVote.objects.update_or_create(
        answer=answer,
        user=request.user,
        defaults={'value': value},
    )

    return redirect('soru_detay', soru_id=answer.question_id)


@login_required
def cevap_duzenle(request, cevap_id):
    answer = get_object_or_404(Answer, id=cevap_id)

    if answer.author_id != request.user.id and not is_admin_user(request.user):
        messages.error(request, 'Bu cevabı düzenleme yetkiniz yok.')
        return redirect('soru_detay', soru_id=answer.question_id)

    if request.method != 'POST':
        return redirect('soru_detay', soru_id=answer.question_id)

    body = request.POST.get('body', '').strip()
    code = request.POST.get('code', '').strip()

    if not body:
        messages.error(request, 'Cevap boş bırakılamaz.')
        return redirect('soru_detay', soru_id=answer.question_id)

    answer.body = body
    answer.code = code
    answer.save(update_fields=['body', 'code', 'updated_at'])

    messages.success(request, 'Cevap güncellendi.')
    return HttpResponseRedirect(f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}")


@login_required
def cevap_sil(request, cevap_id):
    answer = get_object_or_404(Answer, id=cevap_id)
    question_id = answer.question_id

    if answer.author_id != request.user.id and not is_admin_user(request.user):
        messages.error(request, 'Bu cevabı silme yetkiniz yok.')
        return redirect('soru_detay', soru_id=question_id)

    if answer.is_accepted and not is_admin_user(request.user):
        messages.error(request, 'En iyi cevap seçilmiş bir cevabı silemezsiniz.')
        return redirect('soru_detay', soru_id=question_id)

    if Answer.objects.filter(parent_answer=answer).exists() and not is_admin_user(request.user):
        messages.error(request, 'Bu cevaba yanıt geldiği için artık silemezsiniz.')
        return redirect('soru_detay', soru_id=question_id)

    if request.method == 'POST':
        answer.delete()
        messages.success(request, 'Cevap başarıyla silindi.')
        return redirect('soru_detay', soru_id=question_id)

    return redirect('soru_detay', soru_id=question_id)


@login_required
def cevap_kabul_et(request, cevap_id):
    answer = get_object_or_404(Answer.objects.select_related('question', 'author'), id=cevap_id)
    question = answer.question

    if question.author_id != request.user.id and not is_admin_user(request.user):
        messages.error(request, 'Bu işlem için sadece soru sahibi veya admin yetkilidir.')
        return redirect('soru_detay', soru_id=question.id)

    if answer.is_accepted:
        answer.is_accepted = False
        answer.save(update_fields=['is_accepted'])
        question.is_solved = False
        question.save(update_fields=['is_solved'])
        messages.info(request, 'En iyi cevap işareti kaldırıldı.')
    else:
        question.answers.update(is_accepted=False)
        answer.is_accepted = True
        answer.save(update_fields=['is_accepted'])
        question.is_solved = True
        question.save(update_fields=['is_solved'])

        create_notification(
            user=answer.author,
            actor=request.user,
            title='Cevabınız En İyi Cevap seçildi',
            message=f'“{question.title}” sorusundaki cevabınız en iyi cevap seçildi.',
            notification_type='best_answer',
            question=question,
            answer=answer,
        )

        messages.success(request, 'En iyi cevap seçildi.')

    return redirect('soru_detay', soru_id=question.id)


@login_required
def cevap_yanitla(request, cevap_id):
    parent = get_object_or_404(Answer, id=cevap_id)

    if not can_user_interact(request.user):
        messages.error(request, 'Hesabınız yanıt yazma işlemi için pasif durumda. Lütfen moderatöre ulaşın.')
        return redirect('soru_detay', soru_id=parent.question_id)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()

        if body:
            reply = Answer.objects.create(
                question=parent.question,
                author=request.user,
                parent_answer=parent,
                body=body,
            )

            create_notification(
                user=parent.author,
                actor=request.user,
                title='Cevabınıza yanıt geldi',
                message=f'“{parent.question.title}” sorusundaki cevabınıza yanıt yazıldı.',
                notification_type='answer_reply',
                question=parent.question,
                answer=reply,
            )

            messages.success(request, 'Yanıtınız eklendi.')
            return HttpResponseRedirect(f"{reverse('soru_detay', args=[parent.question_id])}#answer-{parent.id}")

    return redirect('soru_detay', soru_id=parent.question_id)


# ------------------------------------------------------------
# Etiketler
# ------------------------------------------------------------

def etiketler(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'popular')

    tags = Tag.objects.filter(is_active=True).prefetch_related('questions', 'followers').annotate(
        question_total=Count('questions', distinct=True),
        follower_total=Count('followers', distinct=True),
    )

    if q:
        tags = tags.filter(Q(name__icontains=q) | Q(description__icontains=q))

    if sort == 'name':
        tags = tags.order_by('name')
    elif sort == 'new':
        tags = tags.order_by('-created_at')
    else:
        tags = tags.order_by('-question_total', 'name')

    followed_tag_ids = []
    if request.user.is_authenticated:
        followed_tag_ids = list(TagFollow.objects.filter(user=request.user).values_list('tag_id', flat=True))

    return render_page(request, 'forum/etiketler.html', {
        'tags': tags,
        'followed_tag_ids': followed_tag_ids,
        'search_query': q,
        'sort': sort,
    })


def etiket_detay(request, slug):
    tag = get_object_or_404(Tag, slug=slug, is_active=True)

    questions = (
        tag.questions
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')
    )

    popular_tags = (
        Tag.objects.filter(is_active=True)
        .annotate(question_total=Count('questions', distinct=True))
        .order_by('-question_total', 'name')[:12]
    )

    return render_page(request, 'forum/sorular.html', {
        'questions': questions,
        'active_tag': tag,
        'total_questions': questions.count(),
        'popular_tags': popular_tags,
    })


@login_required
def etiket_takip(request, etiket_id):
    tag = get_object_or_404(Tag, id=etiket_id, is_active=True)

    follow, created = TagFollow.objects.get_or_create(user=request.user, tag=tag)

    if not created:
        follow.delete()
        messages.info(request, f'{tag.name} etiketi takibi kaldırıldı.')
    else:
        messages.success(request, f'{tag.name} etiketi takip edildi.')

    return redirect('etiketler')


# ------------------------------------------------------------
# Kullanıcılar / profiller
# ------------------------------------------------------------

def kullanicilar(request):
    q = request.GET.get('q', '').strip()

    users = User.objects.select_related('profile').all().order_by('-date_joined')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(profile__bio__icontains=q) |
            Q(profile__skills__icontains=q)
        ).distinct()

    for user_obj in users:
        get_or_create_profile(user_obj)

    followed_user_ids = []
    if request.user.is_authenticated:
        followed_user_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))

    return render_page(request, 'forum/kullanicilar.html', {
        'users': users,
        'followed_user_ids': followed_user_ids,
        'search_query': q,
    })


def _build_skill_rows(user_obj, profile):
    skill_names = [
        item.strip()
        for item in re.split(r'[,;]+', profile.skills or '')
        if item.strip()
    ]

    rows = []
    used = set()
    colors = ['primary', 'success', 'secondary', 'info', 'warning', 'danger', 'dark']

    for index, skill in enumerate(skill_names):
        slug = make_tag_slug(skill)
        if slug in used:
            continue

        used.add(slug)
        tag = Tag.objects.filter(slug=slug).first()

        question_count = 0
        answer_count = 0

        if tag:
            question_count = Question.objects.filter(author=user_obj, tags=tag).count()
            answer_count = Answer.objects.filter(author=user_obj, question__tags=tag, parent_answer__isnull=True).count()

        rows.append({
            'name': skill,
            'question_count': question_count,
            'answer_count': answer_count,
            'badge_class': colors[index % len(colors)],
        })

    return rows


def _profile_badges(user_obj):
    q_count = user_obj.questions.count()
    a_count = user_obj.answers.filter(parent_answer__isnull=True).count()
    best_count = user_obj.answers.filter(is_accepted=True).count()

    badges = []

    if q_count > 0:
        badges.append({'emoji': '❓', 'title': 'Soru Soran', 'desc': f'{q_count} soru sordu', 'class': 'primary'})
    if a_count > 0:
        badges.append({'emoji': '💬', 'title': 'Cevaplayan', 'desc': f'{a_count} cevap verdi', 'class': 'success'})
    if best_count > 0:
        badges.append({'emoji': '✅', 'title': 'En İyi Cevap', 'desc': f'{best_count} cevabı seçildi', 'class': 'warning'})
    if user_obj.groups.filter(name='Blogger').exists():
        badges.append({'emoji': '📝', 'title': 'Blogger', 'desc': 'Blog yazısı paylaşabilir', 'class': 'info'})
    if is_admin_user(user_obj):
        badges.append({'emoji': '👑', 'title': 'Admin', 'desc': 'Yönetim yetkisine sahip', 'class': 'danger'})

    return badges


@login_required
def profilim(request):
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        if username and username != request.user.username:
            if User.objects.filter(username=username).exclude(id=request.user.id).exists():
                messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor.')
                return redirect('profilim')
            request.user.username = username

        if email and email != request.user.email:
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.error(request, 'Bu e-posta zaten kullanılıyor.')
                return redirect('profilim')
            request.user.email = email

        request.user.save()

        profile.bio = request.POST.get('bio', '').strip()
        profile.location = request.POST.get('location', '').strip()
        profile.website = request.POST.get('website', '').strip()
        profile.github = request.POST.get('github', '').strip()
        profile.linkedin = request.POST.get('linkedin', '').strip()
        profile.twitter = request.POST.get('twitter', '').strip()
        profile.skills = request.POST.get('skills', '').strip()
        profile.avatar_seed = request.POST.get('avatar_seed', '').strip() or request.user.username
        profile.show_favorites_public = request.POST.get('show_favorites_public') == 'on'
        profile.show_saved_public = request.POST.get('show_saved_public') == 'on'

        avatar = request.FILES.get('avatar')
        if avatar:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(avatar.name.lower())[1]

            if ext not in allowed_extensions:
                messages.error(request, 'Profil fotoğrafı JPG, PNG, GIF veya WEBP formatında olmalıdır.')
                return redirect('profilim')

            if avatar.size > 3 * 1024 * 1024:
                messages.error(request, 'Profil fotoğrafı en fazla 3 MB olmalıdır.')
                return redirect('profilim')

            profile.avatar = avatar

        profile.save()

        messages.success(request, 'Profil bilgileriniz güncellendi.')
        return redirect('profilim')

    questions = (
        request.user.questions
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')
    )
    answers = (
        request.user.answers
        .filter(parent_answer__isnull=True)
        .select_related('question')
        .prefetch_related('votes')
        .order_by('-created_at')
    )

    activity_items = []
    for q in questions[:5]:
        activity_items.append({'type': 'question', 'title': 'Soru sordu', 'question': q, 'created_at': q.created_at})
    for a in answers[:5]:
        activity_items.append({'type': 'answer', 'title': 'Cevap verdi', 'answer': a, 'question': a.question, 'created_at': a.created_at})

    activity_items = sorted(activity_items, key=lambda x: x['created_at'], reverse=True)[:10]

    favorite_questions = QuestionFavorite.objects.filter(user=request.user).select_related('question').order_by('-created_at')
    favorite_blogs = BlogFavorite.objects.filter(user=request.user).select_related('blog').order_by('-id')
    saved_blogs = BlogSaved.objects.filter(user=request.user).select_related('blog').order_by('-id')

    return render_page(request, 'forum/profilim.html', {
        'profile': profile,
        'questions': questions,
        'answers': answers,
        'activity_items': activity_items,
        'skills': _build_skill_rows(request.user, profile),
        'badges': _profile_badges(request.user),
        'follower_count': request.user.follower_relations.count(),
        'following_count': request.user.following_relations.count(),
        'favorite_questions': favorite_questions,
        'favorite_blogs': favorite_blogs,
        'saved_blogs': saved_blogs,
    })


def kullanici_profil(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = get_or_create_profile(profile_user)

    questions = (
        profile_user.questions
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')
    )
    answers = (
        profile_user.answers
        .filter(parent_answer__isnull=True)
        .select_related('question')
        .prefetch_related('votes')
        .order_by('-created_at')
    )

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    can_view_favorites = request.user == profile_user or profile.show_favorites_public
    can_view_saved = request.user == profile_user or profile.show_saved_public

    favorite_questions = QuestionFavorite.objects.filter(user=profile_user).select_related('question').order_by('-created_at') if can_view_favorites else QuestionFavorite.objects.none()
    favorite_blogs = BlogFavorite.objects.filter(user=profile_user).select_related('blog').order_by('-id') if can_view_favorites else BlogFavorite.objects.none()
    saved_blogs = BlogSaved.objects.filter(user=profile_user).select_related('blog').order_by('-id') if can_view_saved else BlogSaved.objects.none()

    activity_items = []
    for q in questions[:5]:
        activity_items.append({'type': 'question', 'title': 'Soru sordu', 'question': q, 'created_at': q.created_at})
    for a in answers[:5]:
        activity_items.append({'type': 'answer', 'title': 'Cevap verdi', 'answer': a, 'question': a.question, 'created_at': a.created_at})

    activity_items = sorted(activity_items, key=lambda x: x['created_at'], reverse=True)[:10]

    return render_page(request, 'forum/kullanici-profil.html', {
        'profile_user': profile_user,
        'profile': profile,
        'questions': questions,
        'answers': answers,
        'activity_items': activity_items,
        'skills': _build_skill_rows(profile_user, profile),
        'badges': _profile_badges(profile_user),
        'is_following': is_following,
        'follower_count': profile_user.follower_relations.count(),
        'following_count': profile_user.following_relations.count(),
        'can_view_favorites': can_view_favorites,
        'can_view_saved': can_view_saved,
        'favorite_questions': favorite_questions,
        'favorite_blogs': favorite_blogs,
        'saved_blogs': saved_blogs,
    })


@login_required
def kullanici_takip(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, 'Kendinizi takip edemezsiniz.')
        return redirect('kullanici_profil', username=target_user.username)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)

    if not created:
        follow.delete()
        messages.info(request, f'{target_user.username} takibi kaldırıldı.')
    else:
        create_notification(
            user=target_user,
            actor=request.user,
            title='Yeni takipçiniz var',
            message=f'{request.user.username} sizi takip etmeye başladı.',
            notification_type='new_follower',
        )
        messages.success(request, f'{target_user.username} takip edildi.')

    return redirect('kullanici_profil', username=target_user.username)


# ------------------------------------------------------------
# Bildirimler
# ------------------------------------------------------------

@login_required
def bildirimler(request):
    notifications = Notification.objects.filter(user=request.user).select_related(
        'actor', 'question', 'answer', 'tag', 'conversation', 'blog'
    )

    return render_page(request, 'forum/bildirimler.html', {
        'notifications': notifications,
    })


@login_required
def bildirim_okundu(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.target_url())


@login_required
def bildirimleri_okundu_yap(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Tüm bildirimler okundu olarak işaretlendi.')
    return redirect('bildirimler')


# ------------------------------------------------------------
# Mesajlaşma
# ------------------------------------------------------------

@login_required
def mesaj_baslat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, 'Kendinize mesaj gönderemezsiniz.')
        return redirect('kullanicilar')

    conversation = None

    for conv in request.user.conversations.prefetch_related('participants'):
        if conv.participants.filter(id=target_user.id).exists() and conv.participants.count() == 2:
            conversation = conv
            break

    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, target_user)

    return redirect('mesaj_detay', conversation_id=conversation.id)


@login_required
def mesajlarim(request):
    conversations = list(
        request.user.conversations
        .prefetch_related('participants', 'messages', 'participants__profile')
        .order_by('-updated_at')
    )

    for conversation in conversations:
        conversation.other_user = conversation.other_participant(request.user)
        conversation.last_msg = conversation.last_message()

    return render_page(request, 'forum/mesajlarim.html', {
        'conversations': conversations,
    })


@login_required
def mesaj_detay(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()

        if body:
            msg = Message.objects.create(conversation=conversation, sender=request.user, body=body)
            conversation.save()

            receiver = conversation.participants.exclude(id=request.user.id).first()
            if receiver:
                create_notification(
                    user=receiver,
                    actor=request.user,
                    title='Yeni mesajınız var',
                    message=f'{request.user.username} size yeni bir mesaj gönderdi.',
                    notification_type='message',
                    conversation=conversation,
                )

            messages.success(request, 'Mesaj gönderildi.')
            return redirect('mesaj_detay', conversation_id=conversation.id)

    conversation.messages.exclude(sender=request.user).update(is_read=True)

    return render_page(request, 'forum/mesaj-detay.html', {
        'conversation': conversation,
        'conversation_messages': conversation.messages.select_related('sender', 'sender__profile').order_by('created_at'),
        'other_user': conversation.participants.exclude(id=request.user.id).first(),
    })


# ------------------------------------------------------------
# Blog
# ------------------------------------------------------------

def bloglar(request):
    q = request.GET.get('q', '').strip()
    tag_slug = request.GET.get('tag', '').strip()
    sort = request.GET.get('sort', 'new')

    blogs = BlogPost.objects.filter(is_published=True).select_related('author', 'author__profile').prefetch_related('tags')

    if q:
        blogs = blogs.filter(
            Q(title__icontains=q) |
            Q(summary__icontains=q) |
            Q(content__icontains=q)
        ).distinct()

    if tag_slug:
        blogs = blogs.filter(tags__slug=tag_slug)

    if sort == 'popular':
        blogs = blogs.annotate(like_total=Count('likes')).order_by('-like_total', '-views')
    else:
        blogs = blogs.order_by('-created_at')

    tags = Tag.objects.filter(is_active=True).annotate(blog_total=Count('blog_posts')).order_by('-blog_total', 'name')[:15]

    return render_page(request, 'forum/bloglar.html', {
        'blogs': blogs,
        'tags': tags,
        'q': q,
        'active_tag': tag_slug,
        'sort': sort,
        'can_create_blog': is_blogger_user(request.user),
    })


@login_required
def blog_olustur(request):
    if not is_blogger_user(request.user):
        messages.error(request, 'Blog yazısı ekleme yetkiniz yok.')
        return redirect('bloglar')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        content = request.POST.get('content', '').strip()
        tag_text = request.POST.get('tags', '').strip()

        if not title or not summary or not content:
            messages.error(request, 'Başlık, özet ve içerik zorunludur.')
            return redirect('blog_olustur')

        blog = BlogPost.objects.create(author=request.user, title=title, summary=summary, content=content)
        tags = get_or_create_tags_from_text(tag_text, actor=request.user)
        blog.tags.set(tags)

        notify_followers_for_blog(blog)

        messages.success(request, 'Blog yazısı başarıyla oluşturuldu.')
        return redirect('blog_detay', slug=blog.slug)

    return render_page(request, 'forum/blog-olustur.html')


def blog_detay(request, slug):
    blog = get_object_or_404(BlogPost.objects.select_related('author', 'author__profile').prefetch_related('tags'), slug=slug, is_published=True)
    BlogPost.objects.filter(id=blog.id).update(views=F('views') + 1)
    blog.refresh_from_db(fields=['views'])

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Yorum yazmak için giriş yapmalısınız.')
            return redirect('giris')

        if not can_user_interact(request.user):
            messages.error(request, 'Yorum yazmak için hesabınız aktif olmalıdır. Lütfen moderatöre ulaşın.')
            return redirect('blog_detay', slug=blog.slug)

        body = request.POST.get('body', '').strip()

        if body:
            BlogComment.objects.create(blog=blog, author=request.user, body=body)

            if blog.author_id != request.user.id:
                create_notification(
                    user=blog.author,
                    actor=request.user,
                    title='Blog yazınıza yorum geldi',
                    message=f'{request.user.username}, “{blog.title}” yazınıza yorum yaptı.',
                    notification_type='blog_comment',
                    blog=blog,
                )

            messages.success(request, 'Yorum eklendi.')
            return redirect('blog_detay', slug=blog.slug)

    is_liked = is_favorited = is_saved = False
    if request.user.is_authenticated:
        is_liked = BlogLike.objects.filter(user=request.user, blog=blog).exists()
        is_favorited = BlogFavorite.objects.filter(user=request.user, blog=blog).exists()
        is_saved = BlogSaved.objects.filter(user=request.user, blog=blog).exists()

    return render_page(request, 'forum/blog-detay.html', {
        'blog': blog,
        'comments': blog.comments.filter(parent__isnull=True).select_related('author', 'author__profile').prefetch_related('replies', 'replies__author').order_by('-created_at'),
        'is_liked': is_liked,
        'is_favorited': is_favorited,
        'is_saved': is_saved,
        'can_edit_blog': request.user.is_authenticated and (blog.author_id == request.user.id or is_admin_user(request.user)),
    })


@login_required
def blog_duzenle(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)

    if blog.author_id != request.user.id and not is_admin_user(request.user):
        messages.error(request, 'Bu blog yazısını düzenleme yetkiniz yok.')
        return redirect('blog_detay', slug=blog.slug)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        content = request.POST.get('content', '').strip()
        tag_text = request.POST.get('tags', '').strip()

        if not title or not summary or not content:
            messages.error(request, 'Başlık, özet ve içerik zorunludur.')
            return redirect('blog_duzenle', slug=blog.slug)

        blog.title = title
        blog.summary = summary
        blog.content = content
        blog.save()
        blog.tags.set(get_or_create_tags_from_text(tag_text, actor=request.user))

        notify_blog_watchers(blog)

        messages.success(request, 'Blog yazısı güncellendi.')
        return redirect('blog_detay', slug=blog.slug)

    return render_page(request, 'forum/blog-duzenle.html', {
        'blog': blog,
        'tag_string': ', '.join(blog.tags.values_list('name', flat=True)),
    })


@login_required
def blog_begeni(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)
    like, created = BlogLike.objects.get_or_create(blog=blog, user=request.user)

    if not created:
        like.delete()
        messages.info(request, 'Beğeni kaldırıldı.')
    else:
        messages.success(request, 'Blog beğenildi.')

    return redirect('blog_detay', slug=blog.slug)


@login_required
def blog_favori(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)
    favorite, created = BlogFavorite.objects.get_or_create(blog=blog, user=request.user)

    if not created:
        favorite.delete()
        messages.info(request, 'Blog favorilerden çıkarıldı.')
    else:
        messages.success(request, 'Blog favorilere eklendi.')

    return redirect('blog_detay', slug=blog.slug)


@login_required
def blog_kaydet(request, slug):
    blog = get_object_or_404(BlogPost, slug=slug)
    saved, created = BlogSaved.objects.get_or_create(blog=blog, user=request.user)

    if not created:
        saved.delete()
        messages.info(request, 'Blog kaydedilenlerden çıkarıldı.')
    else:
        messages.success(request, 'Blog kaydedildi.')

    return redirect('blog_detay', slug=blog.slug)


@login_required
def blog_yorum_yanitla(request, comment_id):
    parent = get_object_or_404(BlogComment.objects.select_related('blog', 'author'), id=comment_id)

    if not can_user_interact(request.user):
        messages.error(request, 'Yorum yazmak için hesabınız aktif olmalıdır. Lütfen moderatöre ulaşın.')
        return redirect('blog_detay', slug=parent.blog.slug)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()

        if body:
            BlogComment.objects.create(
                blog=parent.blog,
                author=request.user,
                parent=parent,
                body=body,
            )

            create_notification(
                user=parent.author,
                actor=request.user,
                title='Blog yorumunuza yanıt geldi',
                message=f'{request.user.username}, “{parent.blog.title}” yazısındaki yorumunuza yanıt verdi.',
                notification_type='blog_comment',
                blog=parent.blog,
            )

            messages.success(request, 'Yanıt eklendi.')

    return redirect('blog_detay', slug=parent.blog.slug)


# ------------------------------------------------------------
# Yönetim paneli
# ------------------------------------------------------------

@login_required
def yonetim_paneli(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Yönetim paneline erişim yetkiniz yok.')
        return redirect('anasayfa')

    return render_page(request, 'forum/yonetim/index.html', {
        'question_count': Question.objects.count(),
        'answer_count': Answer.objects.count(),
        'tag_count': Tag.objects.count(),
        'user_count': User.objects.count(),
        'blog_count': BlogPost.objects.count(),
    })


@login_required
def yonetim_etiketler(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    tags = Tag.objects.annotate(
        question_total=Count('questions', distinct=True),
        blog_total=Count('blog_posts', distinct=True),
        follower_total=Count('followers', distinct=True),
    ).order_by('name')

    return render_page(request, 'forum/yonetim/etiketler.html', {'tags': tags})


@login_required
def yonetim_etiket_ekle(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Etiket adı zorunludur.')
            return redirect('yonetim_etiket_ekle')

        slug = make_tag_slug(name)
        tag, created = Tag.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'description': description, 'is_active': True}
        )

        if not created:
            messages.error(request, 'Bu etiket zaten mevcut.')
            return redirect('yonetim_etiketler')

        notify_new_tag(tag, request.user)

        messages.success(request, 'Etiket başarıyla eklendi.')
        return redirect('yonetim_etiketler')

    return render_page(request, 'forum/yonetim/etiket-form.html', {'tag': None})


@login_required
def yonetim_etiket_duzenle(request, tag_id):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Etiket adı zorunludur.')
            return redirect('yonetim_etiket_duzenle', tag_id=tag.id)

        tag.name = name
        tag.slug = make_tag_slug(name)
        tag.description = description
        tag.save()

        messages.success(request, 'Etiket güncellendi.')
        return redirect('yonetim_etiketler')

    return render_page(request, 'forum/yonetim/etiket-form.html', {'tag': tag})


@login_required
def yonetim_etiket_durum(request, tag_id):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        tag.is_active = not tag.is_active
        tag.save(update_fields=['is_active'])

        if tag.is_active:
            messages.success(request, 'Etiket aktif hale getirildi.')
        else:
            messages.warning(request, 'Etiket pasif hale getirildi.')

    return redirect('yonetim_etiketler')


@login_required
def yonetim_kullanicilar(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    users = User.objects.select_related('profile').prefetch_related('groups').order_by('username')

    for user_obj in users:
        get_or_create_profile(user_obj)

    return render_page(request, 'forum/yonetim/kullanicilar.html', {
        'users': users,
        'groups': Group.objects.all(),
    })


@login_required
def yonetim_kullanici_durum(request, user_id):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, 'Kendi hesabınızı pasif yapamazsınız.')
        return redirect('yonetim_kullanicilar')

    if request.method == 'POST':
        profile = get_or_create_profile(target_user)
        profile.is_platform_active = not profile.is_platform_active
        profile.save(update_fields=['is_platform_active', 'updated_at'])
        messages.success(request, 'Kullanıcı durumu güncellendi.')

    return redirect('yonetim_kullanicilar')


@login_required
def yonetim_kullanici_duzenle(request, user_id):
    if not is_admin_user(request.user):
        messages.error(request, 'Yetkiniz yok.')
        return redirect('anasayfa')

    target_user = get_object_or_404(User, id=user_id)
    profile = get_or_create_profile(target_user)

    if request.method == 'POST':
        group_ids = request.POST.getlist('groups')
        target_user.groups.set(Group.objects.filter(id__in=group_ids))

        profile.is_platform_active = request.POST.get('is_platform_active') == 'on'
        profile.save(update_fields=['is_platform_active', 'updated_at'])

        messages.success(request, 'Kullanıcı rol ve durum bilgileri güncellendi.')
        return redirect('yonetim_kullanicilar')

    return render_page(request, 'forum/yonetim/kullanici-duzenle.html', {
        'target_user': target_user,
        'profile': profile,
        'groups': Group.objects.all(),
    })
