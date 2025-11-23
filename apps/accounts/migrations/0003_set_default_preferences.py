from django.db import migrations

def set_default_preferences(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    for user in CustomUser.objects.all():
        if not user.preferences:
            user.preferences = {
                'theme': 'auto',
                'email_notifications': True,
                'show_search_history': True,
                'items_per_page': 20,
            }
            user.save(update_fields=['preferences'])

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_alter_customuser_options_customuser_bio_and_more'),
    ]
    
    operations = [
        migrations.RunPython(set_default_preferences),
    ]