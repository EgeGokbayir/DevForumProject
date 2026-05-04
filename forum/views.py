import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, F, Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .models import (
    Answer,
    AnswerVote,
    Follow,
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


def make_tag_slug(tag_name):
    tag_name = tag_name.strip().lower()

    replacements = {
        "c#": "csharp",
        "c++": "cpp",
        ".net": "dotnet",
        "node.js": "nodejs",
    }

    for old, new in replacements.items():
        tag_name = tag_name.replace(old, new)

    tag_name = tag_name.replace("#", "sharp")
    tag_name = tag_name.replace("+", "plus")

    slug = slugify(tag_name)
    return slug or "etiket"


def get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={"avatar_seed": user.username},
    )
    return profile


def notification_context(request):
    if not request.user.is_authenticated:
        return {}

    recent_notifications = (
        Notification.objects
        .filter(user=request.user)
        .select_related('actor', 'question', 'answer', 'tag')[:8]
    )

    return {
        'recent_notifications': recent_notifications,
        'unread_notification_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    }


def render_page(request, template_name, context=None, status=None):
    context = context or {}
    context.update(notification_context(request))
    return render(request, template_name, context, status=status)


def create_notification(user, title, message='', notification_type='system', actor=None, question=None, answer=None, tag=None):
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
    )


def create_notifications_for_user_ids(user_ids, title, message='', notification_type='system', actor=None, question=None, answer=None, tag=None):
    user_ids = set(user_ids)
    if actor:
        user_ids.discard(actor.id)

    users = User.objects.filter(id__in=user_ids)
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
        )
        for user in users
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_question_watchers_about_answer(question, answer, actor):
    user_ids = set()

    user_ids.add(question.author_id)
    user_ids.update(
        QuestionFavorite.objects
        .filter(question=question)
        .values_list('user_id', flat=True)
    )
    user_ids.update(
        QuestionFollow.objects
        .filter(question=question)
        .values_list('user_id', flat=True)
    )

    # Aynı soruya daha önce cevap yazan kişiler de yeni cevaplardan haberdar olsun.
    user_ids.update(
        Answer.objects
        .filter(question=question, parent_answer__isnull=True)
        .values_list('author_id', flat=True)
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
    tag_ids = list(question.tags.values_list('id', flat=True))
    if not tag_ids:
        return

    user_ids = (
        TagFollow.objects
        .filter(tag_id__in=tag_ids)
        .values_list('user_id', flat=True)
        .distinct()
    )

    create_notifications_for_user_ids(
        user_ids=user_ids,
        title='Takip ettiğiniz etikette yeni soru var',
        message=f'“{question.title}” sorusu takip ettiğiniz etiketlerden biriyle açıldı.',
        notification_type='followed_tag_question',
        actor=actor,
        question=question,
    )


def notify_new_tag(tag, actor):
    user_ids = User.objects.values_list('id', flat=True)
    create_notifications_for_user_ids(
        user_ids=user_ids,
        title='Yeni etiket oluşturuldu',
        message=f'“{tag.name}” etiketi oluşturuldu.',
        notification_type='new_tag',
        actor=actor,
        tag=tag,
    )


def anasayfa(request):
    questions = (
        Question.objects
        .select_related('author', 'author__profile')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')[:10]
    )
    popular_tags = (
        Tag.objects
        .annotate(question_total=Count('questions', distinct=True))
        .order_by('-question_total', 'name')[:12]
    )

    return render_page(request, 'forum/index.html', {
        'questions': questions,
        'popular_tags': popular_tags,
        'tags': popular_tags,
        'question_count': Question.objects.count(),
        'user_count': User.objects.count(),
        'tag_count': Tag.objects.count(),
        'answer_count': Answer.objects.count(),
    })


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

    questions = questions.order_by('-created_at')
    popular_tags = Tag.objects.annotate(question_total=Count('questions', distinct=True)).order_by('-question_total', 'name')[:10]

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

    # Görüntülenme mantığı:
    # - Giriş yapan kullanıcı aynı soruyu tekrar açarsa artmaz.
    # - Soruyu yazan kişinin kendi görüntülemesi sayılmaz.
    # - Misafir kullanıcı için aynı browser session içinde bir kere artar.
    if request.user.is_authenticated:
        if question.author_id != request.user.id:
            _, created = QuestionView.objects.get_or_create(
                question=question,
                user=request.user,
            )
            if created:
                Question.objects.filter(id=question.id).update(views=F('views') + 1)
                question.refresh_from_db(fields=['views'])
    else:
        viewed_questions = request.session.get('viewed_questions', [])
        question_key = str(question.id)
        if question_key not in viewed_questions:
            viewed_questions.append(question_key)
            request.session['viewed_questions'] = viewed_questions
            request.session.modified = True
            Question.objects.filter(id=question.id).update(views=F('views') + 1)
            question.refresh_from_db(fields=['views'])

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Cevap yazmak için giriş yapmalısınız.')
            return redirect('giris')

        body = request.POST.get('body', '').strip()
        code = request.POST.get('code', '').strip()

        if not body:
            messages.error(request, 'Cevap alanı boş bırakılamaz.')
            return redirect('soru_detay', soru_id=question.id)

        answer = Answer.objects.create(
            question=question,
            author=request.user,
            body=body,
            code=code,
        )
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
        .filter(tags__in=question.tags.all())
        .exclude(id=question.id)
        .distinct()
        .order_by('-created_at')[:5]
    )

    popular_tags = (
        Tag.objects
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
def soru_duzenle(request, soru_id):
    question = get_object_or_404(Question.objects.prefetch_related('tags'), id=soru_id)

    if question.author_id != request.user.id:
        messages.error(request, 'Sadece kendi sorunuzu düzenleyebilirsiniz.')
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

    tag_names = [
        tag.strip().lower()
        for tag in re.split(r'[,\s]+', tag_text)
        if tag.strip()
    ]
    tag_names = list(dict.fromkeys(tag_names))[:5]

    if not tag_names:
        messages.error(request, 'En az bir etiket eklemelisiniz.')
        return redirect('soru_detay', soru_id=question.id)

    tags = []
    created_tags = []
    for tag_name in tag_names:
        tag_slug = make_tag_slug(tag_name)
        tag, created = Tag.objects.get_or_create(
            slug=tag_slug,
            defaults={
                'name': tag_name,
                'description': f'{tag_name} ile ilgili sorular',
            },
        )
        tags.append(tag)
        if created:
            created_tags.append(tag)

    question.title = title
    question.body = body
    question.code = code
    question.save(update_fields=['title', 'body', 'code', 'updated_at'])
    question.tags.set(tags)

    for tag in created_tags:
        notify_new_tag(tag, request.user)

    messages.success(request, 'Sorunuz başarıyla güncellendi.')
    return redirect('soru_detay', soru_id=question.id)


@login_required
def soru_sor(request):
    popular_tags = Tag.objects.annotate(question_total=Count('questions', distinct=True)).order_by('-question_total', 'name')[:12]

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        code = request.POST.get('code', '').strip()
        tag_text = request.POST.get('tags', '').strip()

        if not title or not body:
            messages.error(request, 'Başlık ve soru detayı zorunludur.')
            return redirect('soru_sor')

        tag_names = [
            tag.strip().lower()
            for tag in re.split(r'[,\s]+', tag_text)
            if tag.strip()
        ]
        tag_names = list(dict.fromkeys(tag_names))[:5]

        if not tag_names:
            messages.error(request, 'En az bir etiket eklemelisiniz.')
            return redirect('soru_sor')

        question = Question.objects.create(
            author=request.user,
            title=title,
            body=body,
            code=code,
        )

        created_tags = []
        for tag_name in tag_names:
            tag_slug = make_tag_slug(tag_name)
            tag, created = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={
                    'name': tag_name,
                    'description': f'{tag_name} ile ilgili sorular',
                },
            )
            question.tags.add(tag)
            if created:
                created_tags.append(tag)

        for tag in created_tags:
            notify_new_tag(tag, request.user)

        notify_followed_tags_about_question(question, request.user)

        messages.success(request, 'Sorunuz başarıyla oluşturuldu.')
        return redirect('soru_detay', soru_id=question.id)

    return render_page(request, 'forum/soru-sor.html', {
        'popular_tags': popular_tags,
    })


def etiketler(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'popular')

    tags = Tag.objects.prefetch_related('questions', 'followers').annotate(
        question_total=Count('questions', distinct=True),
        follower_total=Count('followers', distinct=True),
    )

    if q:
        tags = tags.filter(Q(name__icontains=q) | Q(description__icontains=q))

    if sort == 'name':
        tags = tags.order_by('name')
    elif sort == 'new':
        tags = tags.order_by('-id')
    else:
        tags = tags.order_by('-question_total', 'name')

    followed_tag_ids = []
    if request.user.is_authenticated:
        followed_tag_ids = list(
            TagFollow.objects
            .filter(user=request.user)
            .values_list('tag_id', flat=True)
        )

    return render_page(request, 'forum/etiketler.html', {
        'tags': tags,
        'followed_tag_ids': followed_tag_ids,
        'search_query': q,
        'sort': sort,
    })


def etiket_detay(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    questions = (
        tag.questions
        .select_related('author')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')
    )

    return render_page(request, 'forum/sorular.html', {
        'questions': questions,
        'active_tag': tag,
        'total_questions': questions.count(),
        'popular_tags': Tag.objects.annotate(question_total=Count('questions', distinct=True)).order_by('-question_total', 'name')[:10],
    })


def kullanicilar(request):
    q = request.GET.get('q', '').strip()

    users = User.objects.all().order_by('-date_joined')

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
        followed_user_ids = list(
            Follow.objects
            .filter(follower=request.user)
            .values_list('following_id', flat=True)
        )

    return render_page(request, 'forum/kullanicilar.html', {
        'users': users,
        'followed_user_ids': followed_user_ids,
        'search_query': q,
    })


def _build_skill_rows(user_obj, profile):
    """Profilde kullanıcı tarafından yazılan yetenekleri, ilgili etiketlerdeki soru/cevap sayılarıyla hazırlar.

    Kullanıcı profilinde manuel yetenek yazmadıysa otomatik etiket/yetenek üretmez.
    Böylece kullanıcı Python eklemediyse sadece Python etiketinde hareketi var diye
    profilinde Python görünmez.
    """
    manual_skill_names = [
        item.strip()
        for item in re.split(r'[,;]+', profile.skills or '')
        if item.strip()
    ]

    if not manual_skill_names:
        return []

    unique_skill_names = []
    used_manual_slugs = set()
    for skill_name in manual_skill_names:
        skill_slug = make_tag_slug(skill_name)
        if skill_slug in used_manual_slugs:
            continue
        unique_skill_names.append(skill_name)
        used_manual_slugs.add(skill_slug)

    badge_classes = [
        'bg-primary',
        'bg-success',
        'bg-secondary',
        'bg-info text-dark',
        'bg-warning text-dark',
        'bg-danger',
        'bg-dark',
    ]

    rows = []
    for index, skill_name in enumerate(unique_skill_names[:8]):
        skill_slug = make_tag_slug(skill_name)
        tag = Tag.objects.filter(slug=skill_slug).first()

        question_total = 0
        answer_total = 0
        url = None

        if tag:
            question_total = Question.objects.filter(author=user_obj, tags=tag).distinct().count()
            answer_total = Answer.objects.filter(
                author=user_obj,
                parent_answer__isnull=True,
                question__tags=tag,
            ).distinct().count()
            url = reverse('etiket_detay', args=[tag.slug])

        rows.append({
            'name': skill_name,
            'question_total': question_total,
            'answer_total': answer_total,
            'url': url,
            'class': badge_classes[index % len(badge_classes)],
        })

    return rows


@login_required
def profilim(request):
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()

        if new_username and new_username != request.user.username:
            if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor.')
                return redirect('profilim')
            request.user.username = new_username
            request.user.save(update_fields=['username'])

        uploaded_avatar = request.FILES.get('avatar')
        if uploaded_avatar:
            allowed_content_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
            if uploaded_avatar.content_type not in allowed_content_types:
                messages.error(request, 'Lütfen JPG, PNG, GIF veya WEBP formatında bir profil fotoğrafı yükleyin.')
                return redirect('profilim')
            if uploaded_avatar.size > 3 * 1024 * 1024:
                messages.error(request, 'Profil fotoğrafı en fazla 3 MB olabilir.')
                return redirect('profilim')
            profile.avatar = uploaded_avatar

        profile.bio = request.POST.get('bio', '').strip()
        profile.location = request.POST.get('location', '').strip()
        profile.website = request.POST.get('website', '').strip()
        profile.github = request.POST.get('github', '').strip()
        profile.linkedin = request.POST.get('linkedin', '').strip()
        profile.twitter = request.POST.get('twitter', '').strip()
        profile.skills = request.POST.get('skills', '').strip()
        profile.avatar_seed = profile.avatar_seed or request.user.username
        profile.save()

        messages.success(request, 'Profil bilgileriniz başarıyla güncellendi.')
        return redirect('profilim')

    user_obj = request.user

    user_questions = (
        Question.objects
        .filter(author=user_obj)
        .select_related('author')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')[:10]
    )

    user_answers = (
        Answer.objects
        .filter(author=user_obj, parent_answer__isnull=True)
        .select_related('question', 'question__author')
        .prefetch_related('votes')
        .order_by('-created_at')[:10]
    )

    total_questions = Question.objects.filter(author=user_obj).count()
    total_answers = Answer.objects.filter(author=user_obj, parent_answer__isnull=True).count()
    accepted_answer_count = Answer.objects.filter(author=user_obj, is_accepted=True).count()
    follower_count = Follow.objects.filter(following=user_obj).count()
    following_count = Follow.objects.filter(follower=user_obj).count()

    skill_rows = _build_skill_rows(user_obj, profile)
    # Eski template parçalarıyla uyumluluk için bırakıldı.
    skill_tags = []
    profile_skill_names = []

    activity_items = []
    for question in Question.objects.filter(author=user_obj).select_related('author').order_by('-created_at')[:5]:
        activity_items.append({
            'type': 'question',
            'title': 'Soru sordu',
            'icon': 'bi-question-circle',
            'color': 'text-primary',
            'text': question.title,
            'url': reverse('soru_detay', args=[question.id]),
            'meta': f'{question.answer_count()} cevap • {question.views} görüntülenme',
            'created_at': question.created_at,
        })

    for answer in Answer.objects.filter(author=user_obj, parent_answer__isnull=True).select_related('question').order_by('-created_at')[:5]:
        activity_items.append({
            'type': 'answer',
            'title': 'Cevap verdi',
            'icon': 'bi-chat-left-text',
            'color': 'text-success',
            'text': answer.question.title,
            'url': f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}",
            'meta': f'{answer.vote_score()} oy aldı',
            'created_at': answer.created_at,
        })

    for answer in Answer.objects.filter(author=user_obj, is_accepted=True).select_related('question').order_by('-updated_at')[:5]:
        activity_items.append({
            'type': 'accepted',
            'title': 'En iyi cevap seçildi',
            'icon': 'bi-trophy-fill',
            'color': 'text-warning',
            'text': answer.question.title,
            'url': f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}",
            'meta': 'Cevabınız en iyi cevap olarak işaretlendi',
            'created_at': answer.updated_at or answer.created_at,
        })

    activity_items = sorted(activity_items, key=lambda item: item['created_at'], reverse=True)[:10]

    badges = []
    if user_obj.is_staff:
        badges.append({
            'emoji': '👑',
            'title': 'Moderatör',
            'description': 'Topluluk yönetim yetkisine sahip',
            'class': 'bg-success',
        })
    if accepted_answer_count > 0:
        badges.append({
            'emoji': '✅',
            'title': 'En İyi Cevap',
            'description': f'{accepted_answer_count} cevabınız en iyi cevap seçildi',
            'class': 'bg-success',
        })
    if total_answers >= 1:
        badges.append({
            'emoji': '🏆',
            'title': 'İlk Cevap',
            'description': 'İlk cevabınızı verdiniz',
            'class': 'bg-warning text-dark',
        })
    if Question.objects.filter(author=user_obj, views__gte=1000).exists():
        badges.append({
            'emoji': '⭐',
            'title': 'Popüler Soru',
            'description': 'Sorunuz 1000+ görüntüleme aldı',
            'class': 'bg-info',
        })
    if total_questions >= 1:
        badges.append({
            'emoji': '❓',
            'title': 'İlk Soru',
            'description': 'Toplulukta ilk sorunuzu sordunuz',
            'class': 'bg-primary',
        })
    if total_questions + total_answers >= 5:
        badges.append({
            'emoji': '🔥',
            'title': 'Aktif Üye',
            'description': 'Topluluğa düzenli katkı sağlıyor',
            'class': 'bg-danger',
        })
    if not badges:
        badges.append({
            'emoji': '🌱',
            'title': 'Yeni Üye',
            'description': 'Toplulukta yolculuğunuza başladınız',
            'class': 'bg-secondary',
        })

    return render_page(request, 'forum/profilim.html', {
        'profile_user': user_obj,
        'profile': profile,
        'user_questions': user_questions,
        'user_answers': user_answers,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'accepted_answer_count': accepted_answer_count,
        'follower_count': follower_count,
        'following_count': following_count,
        'skill_tags': skill_tags,
        'profile_skill_names': profile_skill_names,
        'skill_rows': skill_rows,
        'activity_items': activity_items,
        'badges': badges,
    })

def kullanici_profil(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile = get_or_create_profile(user_obj)

    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user_obj,
        ).exists()

    user_questions = (
        Question.objects
        .filter(author=user_obj)
        .select_related('author')
        .prefetch_related('tags', 'answers', 'votes')
        .order_by('-created_at')[:10]
    )

    user_answers = (
        Answer.objects
        .filter(author=user_obj, parent_answer__isnull=True)
        .select_related('question', 'question__author')
        .prefetch_related('votes')
        .order_by('-created_at')[:10]
    )

    total_questions = Question.objects.filter(author=user_obj).count()
    total_answers = Answer.objects.filter(author=user_obj, parent_answer__isnull=True).count()
    accepted_answer_count = Answer.objects.filter(author=user_obj, is_accepted=True).count()
    follower_count = Follow.objects.filter(following=user_obj).count()
    following_count = Follow.objects.filter(follower=user_obj).count()

    skill_rows = _build_skill_rows(user_obj, profile)
    # Eski template parçalarıyla uyumluluk için boş bırakıldı.
    skill_tags = []
    profile_skill_names = []

    activity_items = []
    for question in Question.objects.filter(author=user_obj).select_related('author').order_by('-created_at')[:5]:
        activity_items.append({
            'type': 'question',
            'title': 'Soru sordu',
            'icon': 'bi-question-circle',
            'color': 'text-primary',
            'text': question.title,
            'url': reverse('soru_detay', args=[question.id]),
            'meta': f'{question.answer_count()} cevap • {question.views} görüntülenme',
            'created_at': question.created_at,
        })

    for answer in Answer.objects.filter(author=user_obj, parent_answer__isnull=True).select_related('question').order_by('-created_at')[:5]:
        activity_items.append({
            'type': 'answer',
            'title': 'Cevap verdi',
            'icon': 'bi-chat-left-text',
            'color': 'text-success',
            'text': answer.question.title,
            'url': f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}",
            'meta': f'{answer.vote_score()} oy aldı',
            'created_at': answer.created_at,
        })

    activity_items = sorted(activity_items, key=lambda item: item['created_at'], reverse=True)[:10]

    badges = []
    if user_obj.is_staff:
        badges.append({
            'emoji': '👑',
            'title': 'Moderatör',
            'description': 'Topluluk yönetim yetkisine sahip',
            'class': 'bg-success',
        })
    if accepted_answer_count > 0:
        badges.append({
            'emoji': '🏆',
            'title': 'En İyi Cevap Sahibi',
            'description': f'{accepted_answer_count} cevabı en iyi cevap seçildi',
            'class': 'bg-warning text-dark',
        })
    if total_answers >= 5:
        badges.append({
            'emoji': '🎓',
            'title': 'Yardımsever',
            'description': 'Topluluğa düzenli cevap veriyor',
            'class': 'bg-info text-dark',
        })
    if total_questions >= 5:
        badges.append({
            'emoji': '🔥',
            'title': 'Aktif Soru Sahibi',
            'description': 'Toplulukta aktif şekilde soru soruyor',
            'class': 'bg-danger',
        })
    if not badges:
        badges.append({
            'emoji': '🌱',
            'title': 'Yeni Üye',
            'description': 'Toplulukta yolculuğuna başladı',
            'class': 'bg-secondary',
        })

    return render_page(request, 'forum/kullanici-profil.html', {
        'profile_user': user_obj,
        'profile': profile,
        'is_following': is_following,
        'is_own_profile': request.user.is_authenticated and request.user.id == user_obj.id,
        'user_questions': user_questions,
        'user_answers': user_answers,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'accepted_answer_count': accepted_answer_count,
        'follower_count': follower_count,
        'following_count': following_count,
        'skill_rows': skill_rows,
        'skill_tags': skill_tags,
        'profile_skill_names': profile_skill_names,
        'activity_items': activity_items,
        'badges': badges,
    })


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

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        get_or_create_profile(user)
        login(request, user)
        messages.success(request, 'Kayıt başarılı.')
        return redirect('anasayfa')

    return render_page(request, 'forum/kayit.html')


def cikis_yap(request):
    logout(request)
    messages.success(request, 'Çıkış yaptınız.')
    return redirect('anasayfa')


def ara(request):
    q = request.GET.get('q', '').strip()
    questions = Question.objects.none()

    if q:
        questions = (
            Question.objects
            .filter(
                Q(title__icontains=q) |
                Q(body__icontains=q) |
                Q(tags__name__icontains=q)
            )
            .distinct()
            .select_related('author')
            .prefetch_related('tags', 'answers', 'votes')
            .order_by('-created_at')
        )

    return render_page(request, 'forum/sorular.html', {
        'questions': questions,
        'search_query': q,
        'total_questions': questions.count(),
        'popular_tags': Tag.objects.annotate(question_total=Count('questions', distinct=True)).order_by('-question_total', 'name')[:10],
    })


@login_required
def soru_oyla(request, soru_id, yon):
    question = get_object_or_404(Question, id=soru_id)

    if question.author_id == request.user.id:
        messages.error(request, 'Kendi sorunuzu oylayamazsınız.')
        return redirect('soru_detay', soru_id=question.id)

    value = 1 if yon == 'up' else -1

    QuestionVote.objects.update_or_create(
        question=question,
        user=request.user,
        defaults={'value': value},
    )

    return redirect('soru_detay', soru_id=question.id)


@login_required
def cevap_oyla(request, cevap_id, yon):
    answer = get_object_or_404(Answer, id=cevap_id)

    if answer.author_id == request.user.id:
        messages.error(request, 'Kendi cevabınızı oylayamazsınız.')
        return HttpResponseRedirect(f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}")

    value = 1 if yon == 'up' else -1

    AnswerVote.objects.update_or_create(
        answer=answer,
        user=request.user,
        defaults={'value': value},
    )

    return HttpResponseRedirect(f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}")


@login_required
def cevap_kabul_et(request, cevap_id):
    answer = get_object_or_404(Answer.objects.select_related('question', 'author'), id=cevap_id)
    question = answer.question

    if question.author_id != request.user.id:
        messages.error(request, 'Sadece soruyu oluşturan kişi en iyi cevabı seçebilir.')
        return redirect('soru_detay', soru_id=question.id)

    if answer.is_accepted:
        answer.is_accepted = False
        answer.save(update_fields=['is_accepted'])
        question.is_solved = False
        question.save(update_fields=['is_solved'])
        messages.success(request, 'En iyi cevap işareti kaldırıldı.')
    else:
        Answer.objects.filter(question=question).update(is_accepted=False)
        answer.is_accepted = True
        answer.save(update_fields=['is_accepted'])
        question.is_solved = True
        question.save(update_fields=['is_solved'])

        watcher_ids = set(
            QuestionFavorite.objects.filter(question=question).values_list('user_id', flat=True)
        )
        watcher_ids.update(
            QuestionFollow.objects.filter(question=question).values_list('user_id', flat=True)
        )
        watcher_ids.update(
            Answer.objects.filter(question=question).values_list('author_id', flat=True)
        )
        watcher_ids.add(answer.author_id)

        create_notifications_for_user_ids(
            user_ids=watcher_ids,
            title='Bir soruda en iyi cevap seçildi',
            message=f'“{question.title}” sorusunda en iyi cevap seçildi.',
            notification_type='best_answer',
            actor=request.user,
            question=question,
            answer=answer,
        )

        messages.success(request, 'Cevap en iyi cevap olarak işaretlendi.')

    return HttpResponseRedirect(f"{reverse('soru_detay', args=[question.id])}#answer-{answer.id}")


@login_required
def cevap_duzenle(request, cevap_id):
    answer = get_object_or_404(Answer, id=cevap_id)

    if answer.author_id != request.user.id:
        messages.error(request, 'Sadece kendi cevabınızı düzenleyebilirsiniz.')
        return HttpResponseRedirect(f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}")

    if request.method != 'POST':
        return redirect('soru_detay', soru_id=answer.question_id)

    body = request.POST.get('body', '').strip()
    code = request.POST.get('code', '').strip()

    if not body:
        messages.error(request, 'Cevap alanı boş bırakılamaz.')
        return HttpResponseRedirect(f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}")

    answer.body = body
    answer.code = code
    answer.save(update_fields=['body', 'code', 'updated_at'])
    messages.success(request, 'Cevabınız güncellendi.')
    return HttpResponseRedirect(f"{reverse('soru_detay', args=[answer.question_id])}#answer-{answer.id}")


@login_required
def cevap_cevapla(request, cevap_id):
    parent_answer = get_object_or_404(Answer.objects.select_related('question', 'author'), id=cevap_id)

    if request.method != 'POST':
        return redirect('soru_detay', soru_id=parent_answer.question_id)

    body = request.POST.get('body', '').strip()

    if not body:
        messages.error(request, 'Yanıt alanı boş bırakılamaz.')
        return HttpResponseRedirect(f"{reverse('soru_detay', args=[parent_answer.question_id])}#answer-{parent_answer.id}")

    reply = Answer.objects.create(
        question=parent_answer.question,
        parent_answer=parent_answer,
        author=request.user,
        body=body,
    )

    create_notification(
        user=parent_answer.author,
        title='Cevabınıza yanıt geldi',
        message=f'“{parent_answer.question.title}” sorusundaki cevabınıza yanıt yazıldı.',
        notification_type='answer_reply',
        actor=request.user,
        question=parent_answer.question,
        answer=reply,
    )

    messages.success(request, 'Yanıtınız eklendi.')
    return HttpResponseRedirect(f"{reverse('soru_detay', args=[parent_answer.question_id])}#answer-{reply.id}")


@login_required
def soru_favori_toggle(request, soru_id):
    question = get_object_or_404(Question.objects.select_related('author'), id=soru_id)
    favorite, created = QuestionFavorite.objects.get_or_create(user=request.user, question=question)

    if created:
        create_notification(
            user=question.author,
            title='Sorunuz favorilere eklendi',
            message=f'“{question.title}” sorunuz bir kullanıcı tarafından favorilere eklendi.',
            notification_type='favorite',
            actor=request.user,
            question=question,
        )
        messages.success(request, 'Soru favorilere eklendi.')
    else:
        favorite.delete()
        messages.success(request, 'Soru favorilerden çıkarıldı.')

    return redirect('soru_detay', soru_id=question.id)


@login_required
def soru_takip_toggle(request, soru_id):
    question = get_object_or_404(Question, id=soru_id)
    follow, created = QuestionFollow.objects.get_or_create(user=request.user, question=question)

    if created:
        messages.success(request, 'Soru takip listenize eklendi.')
    else:
        follow.delete()
        messages.success(request, 'Soru takip listenizden çıkarıldı.')

    return redirect('soru_detay', soru_id=question.id)


@login_required
def etiket_takip(request, etiket_id):
    tag = get_object_or_404(Tag, id=etiket_id)

    follow, created = TagFollow.objects.get_or_create(
        user=request.user,
        tag=tag,
    )

    if not created:
        follow.delete()
        messages.success(request, f'{tag.name} etiketi takipten çıkarıldı.')
    else:
        messages.success(request, f'{tag.name} etiketi takip edildi.')

    return redirect('etiketler')


@login_required
def kullanici_takip(request, user_id):
    following_user = get_object_or_404(User, id=user_id)

    if following_user == request.user:
        messages.error(request, 'Kendinizi takip edemezsiniz.')
        return redirect('kullanici_profil', username=following_user.username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=following_user,
    )

    if not created:
        follow.delete()
        messages.success(request, f'{following_user.username} takipten çıkarıldı.')
    else:
        create_notification(
            user=following_user,
            title='Yeni takipçiniz var',
            message=f'{request.user.username} sizi takip etmeye başladı.',
            notification_type='new_follower',
            actor=request.user,
        )
        messages.success(request, f'{following_user.username} takip edildi.')

    return redirect('kullanici_profil', username=following_user.username)


@login_required
def bildirimler(request):
    notifications = (
        Notification.objects
        .filter(user=request.user)
        .select_related('actor', 'question', 'answer', 'tag')[:50]
    )
    return render_page(request, 'forum/bildirimler.html', {
        'notifications': notifications,
    })


@login_required
def bildirim_okundu(request, bildirim_id):
    notification = get_object_or_404(Notification, id=bildirim_id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.target_url())


@login_required
def tum_bildirimleri_okundu_yap(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Tüm bildirimler okundu olarak işaretlendi.')
    return redirect('bildirimler')

def custom_404(request, exception):
    return render(request, 'forum/404.html', status=404)