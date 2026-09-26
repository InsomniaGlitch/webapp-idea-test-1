from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, related_name='purchases', to='auth.user')),
                ('audio_file', models.ForeignKey(on_delete=models.CASCADE, related_name='purchases', to='catalog.audiofile')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('user', 'audio_file')},
            },
        ),
    ]
