from django.contrib import admin
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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'reputation', 'created_at')
    search_fields = ('user__username', 'bio', 'location', 'skills')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'description')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'views', 'is_solved', 'created_at')
    list_filter = ('is_solved', 'created_at', 'tags')
    search_fields = ('title', 'body')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'parent_answer', 'is_accepted', 'created_at')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('body', 'question__title', 'author__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'actor__username')


admin.site.register(QuestionVote)
admin.site.register(AnswerVote)
admin.site.register(QuestionView)
admin.site.register(QuestionFavorite)
admin.site.register(QuestionFollow)
admin.site.register(Follow)
admin.site.register(TagFollow)