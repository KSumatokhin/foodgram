from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import MyUser, Subscription


class MyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    fieldsets += (
        ('Рецепты и подписчики', {'fields': ('recipes', 'subscribers')}),
    )
    readonly_fields = ('recipes', 'subscribers')

    @admin.display(description='Рецепты')
    def recipes(self, obj):
        return obj.recipes.all().count()

    @admin.display(description='Подписчики')
    def subscribers(self, obj):
        return obj.followers.all().count()


admin.site.register(MyUser, MyUserAdmin)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username__istartswith', )
