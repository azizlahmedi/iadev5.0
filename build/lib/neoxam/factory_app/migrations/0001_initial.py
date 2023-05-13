# Generated by Django 4.2 on 2023-05-03 16:02

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CompileLegacyTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('schema_version', models.PositiveIntegerField()),
                ('procedure_name', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=32)),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='running', max_length=32)),
                ('output', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompileLegacyUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Compiler',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=32, unique=True)),
                ('enabled', models.BooleanField(default=False)),
                ('compatibility_version', models.CharField(blank=True, editable=False, max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='pProcedure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schema_version', models.PositiveIntegerField(choices=[(2009, 'gp2009'), (2016, 'gp2016')])),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('schema_version', 'name')},
            },
        ),
        migrations.CreateModel(
            name='ProcedureRevision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('revision', models.PositiveIntegerField()),
                ('resource_revision', models.PositiveIntegerField()),
                ('procedure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='factory_app.pprocedure')),
            ],
            options={
                'unique_together': {('procedure', 'revision', 'resource_revision')},
            },
        ),
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('procedure_revisions', models.ManyToManyField(related_name='batches', to='factory_app.procedurerevision')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(choices=[('export_sources', 'Export Sources'), ('compile', 'Compile'), ('compile_resources', 'Compile Resources'), ('synchronize_legacy', 'Synchronize Legacy'), ('technical_tests', 'Technical Tests')], max_length=32)),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='pending', max_length=32)),
                ('priority', models.IntegerField(choices=[(0, 'Normal'), (-10, 'High')], default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('started_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('completed_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('output', models.TextField(blank=True)),
                ('compiler', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='factory_app.compiler')),
                ('procedure_revision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='factory_app.procedurerevision')),
            ],
            options={
                'unique_together': {('key', 'procedure_revision', 'compiler')},
            },
        ),
        migrations.CreateModel(
            name='CompilerHost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(max_length=255)),
                ('compiler', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='factory_app.compiler')),
            ],
            options={
                'unique_together': {('compiler', 'hostname')},
            },
        ),
    ]
