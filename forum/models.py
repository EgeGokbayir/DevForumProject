from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
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


class Notification(models.Model):
    TYPE_CHOICES = [
        ('new_answer', 'Yeni cevap'),
        ('best_answer', 'En iyi cevap'),
        ('followed_tag_question', 'Takip edilen etikette yeni soru'),
        ('new_tag', 'Yeni etiket'),
        ('new_follower', 'Yeni takipçi'),
        ('answer_reply', 'Cevabına yanıt'),
        ('favorite', 'Favori'),
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
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def target_url(self):
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
            'system': 'bi-bell-fill',
        }
        return icons.get(self.notification_type, 'bi-bell-fill')

    def __str__(self):
        return f'{self.user.username} - {self.title}'
