from django.contrib import admin

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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'reputation', 'is_platform_active', 'show_favorites_public', 'show_saved_public')
    search_fields = ('user__username', 'user__email', 'bio', 'location', 'skills')
    list_filter = ('is_platform_active', 'show_favorites_public', 'show_saved_public')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'views', 'is_solved', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'author__username')
    list_filter = ('is_solved', 'created_at', 'tags')
    filter_horizontal = ('tags',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'parent_answer', 'is_accepted', 'created_at')
    search_fields = ('body', 'author__username', 'question__title')
    list_filter = ('is_accepted', 'created_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'views', 'created_at', 'updated_at')
    search_fields = ('title', 'summary', 'content', 'author__username')
    list_filter = ('is_published', 'created_at', 'tags')
    filter_horizontal = ('tags',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('blog', 'author', 'parent', 'created_at')
    search_fields = ('body', 'author__username', 'blog__title')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    list_filter = ('notification_type', 'is_read', 'created_at')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'is_read', 'created_at')
    search_fields = ('body', 'sender__username')


admin.site.register(QuestionVote)
admin.site.register(AnswerVote)
admin.site.register(QuestionView)
admin.site.register(Follow)
admin.site.register(TagFollow)
admin.site.register(QuestionFavorite)
admin.site.register(QuestionFollow)
admin.site.register(BlogLike)
admin.site.register(BlogFavorite)
admin.site.register(BlogSaved)
