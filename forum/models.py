from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    github = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    skills = models.CharField(max_length=255, blank=True)
    reputation = models.IntegerField(default=0)
    avatar_seed = models.CharField(max_length=100, default='Felix')

    # Kullanıcı giriş yapabilir ama içerik üretmesi engellenebilir.
    is_platform_active = models.BooleanField(default=True)

    # Profil gizlilik ayarları
    show_favorites_public = models.BooleanField(default=False)
    show_saved_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return f'https://api.dicebear.com/7.x/avataaars/svg?seed={self.avatar_seed or self.user.username}'

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Mevcut tablolara eklenirken migration prompt'u vermemesi için default kullanıldı.
    created_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    followers = models.ManyToManyField(User, through='TagFollow', related_name='followed_tags', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def question_count(self):
        return self.questions.count()

    def __str__(self):
        return self.name


class Question(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=150)
    body = models.TextField()
    code = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, related_name='questions', blank=True)
    views = models.PositiveIntegerField(default=0)
    is_solved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def vote_score(self):
        return sum(vote.value for vote in self.votes.all())

    def answer_count(self):
        return self.answers.filter(parent_answer__isnull=True).count()

    def reply_count(self):
        return self.answers.filter(parent_answer__isnull=False).count()

    def accepted_answer(self):
        return self.answers.filter(is_accepted=True).first()

    def __str__(self):
        return self.title


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    parent_answer = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    body = models.TextField()
    code = models.TextField(blank=True)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def vote_score(self):
        return sum(vote.value for vote in self.votes.all())

    def __str__(self):
        return f"{self.question.title} - {self.author.username}"


class QuestionVote(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.SmallIntegerField()

    class Meta:
        unique_together = ('question', 'user')


class AnswerVote(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.SmallIntegerField()

    class Meta:
        unique_together = ('answer', 'user')


class QuestionView(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='view_records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewed_questions')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('question', 'user')

    def __str__(self):
        return f'{self.user.username} - {self.question.title}'


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_relations')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_relations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower.username} -> {self.following.username}'


class TagFollow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tag')

    def __str__(self):
        return f'{self.user.username} -> {self.tag.name}'


class QuestionFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='favorite_records')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f'{self.user.username} favori: {self.question.title}'


class QuestionFollow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='follow_records')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f'{self.user.username} takip: {self.question.title}'


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def __str__(self):
        return ", ".join(self.participants.values_list('username', flat=True))


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.body[:40]}'


class BlogPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=300)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='blog_posts', blank=True)
    is_published = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'blog'
            slug = base_slug
            counter = 1

            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()

    def __str__(self):
        return self.title


class BlogComment(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.blog.title} - {self.author.username}'


class BlogLike(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('blog', 'user')


class BlogFavorite(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_blogs')

    class Meta:
        unique_together = ('blog', 'user')


class BlogSaved(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='saved_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_blogs')

    class Meta:
        unique_together = ('blog', 'user')


class Notification(models.Model):
    TYPE_CHOICES = [
        ('new_answer', 'Yeni cevap'),
        ('best_answer', 'En iyi cevap'),
        ('followed_tag_question', 'Takip edilen etikette yeni soru'),
        ('new_tag', 'Yeni etiket'),
        ('new_follower', 'Yeni takipçi'),
        ('answer_reply', 'Cevabına yanıt'),
        ('favorite', 'Favori'),
        ('message', 'Mesaj'),
        ('blog_new', 'Yeni blog'),
        ('blog_updated', 'Blog güncellendi'),
        ('blog_comment', 'Blog yorumu'),
        ('system', 'Sistem'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)

    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def target_url(self):
        if self.conversation_id:
            return reverse('mesaj_detay', args=[self.conversation_id])
        if self.blog_id:
            return reverse('blog_detay', args=[self.blog.slug])
        if self.answer_id:
            return f"{reverse('soru_detay', args=[self.answer.question_id])}#answer-{self.answer_id}"
        if self.question_id:
            return reverse('soru_detay', args=[self.question_id])
        if self.tag_id:
            return reverse('etiket_detay', args=[self.tag.slug])
        if self.actor_id:
            return reverse('kullanici_profil', args=[self.actor.username])
        return reverse('bildirimler')

    def icon_class(self):
        icons = {
            'new_answer': 'bi-chat-dots',
            'best_answer': 'bi-trophy-fill',
            'followed_tag_question': 'bi-tags-fill',
            'new_tag': 'bi-tag-fill',
            'new_follower': 'bi-person-plus-fill',
            'answer_reply': 'bi-reply-fill',
            'favorite': 'bi-star-fill',
            'message': 'bi-envelope-fill',
            'blog_new': 'bi-journal-richtext',
            'blog_updated': 'bi-pencil-square',
            'blog_comment': 'bi-chat-left-text-fill',
            'system': 'bi-bell-fill',
        }
        return icons.get(self.notification_type, 'bi-bell-fill')

    def __str__(self):
        return f'{self.user.username} - {self.title}'
