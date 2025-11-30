# Generated migration for adding 'treinada' field to ImagemProduto

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verifik', '__latest__'),  # Django vai resolver para a última migration
    ]

    operations = [
        migrations.AddField(
            model_name='imagemproduto',
            name='treinada',
            field=models.BooleanField(
                default=False,
                verbose_name='Treinada',
                help_text='Se esta imagem já foi usada em treinamento'
            ),
        ),
        migrations.AddField(
            model_name='imagemproduto',
            name='data_treinamento',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Data do Treinamento',
                help_text='Quando esta imagem foi usada pela última vez em treinamento'
            ),
        ),
    ]
