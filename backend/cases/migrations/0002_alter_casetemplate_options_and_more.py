# Generated by Django 5.2 on 2025-05-12 00:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='casetemplate',
            options={'ordering': ['case', 'language'], 'verbose_name': 'Expert-Filled Case Template', 'verbose_name_plural': 'Expert-Filled Case Templates'},
        ),
        migrations.AlterModelOptions(
            name='casetemplatesectioncontent',
            options={'ordering': ['case_template', 'master_section__order'], 'verbose_name': 'Expert Template Section Content', 'verbose_name_plural': 'Expert Template Section Contents'},
        ),
        migrations.AlterModelOptions(
            name='mastertemplate',
            options={'ordering': ['name'], 'verbose_name': 'Master Report Template', 'verbose_name_plural': 'Master Report Templates'},
        ),
        migrations.AlterModelOptions(
            name='mastertemplatesection',
            options={'ordering': ['master_template', 'order', 'name'], 'verbose_name': 'Master Template Section', 'verbose_name_plural': 'Master Template Sections'},
        ),
        migrations.AlterModelOptions(
            name='usercaseview',
            options={'ordering': ['-timestamp']},
        ),
        migrations.RenameField(
            model_name='usercaseview',
            old_name='viewed_at',
            new_name='timestamp',
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='case',
            name='clinical_history',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='case',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cases_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='case',
            name='diagnosis',
            field=models.TextField(blank=True, help_text="Expert's final diagnosis.", null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='difficulty',
            field=models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'), ('expert', 'Expert')], default='beginner', max_length=20),
        ),
        migrations.AlterField(
            model_name='case',
            name='discussion',
            field=models.TextField(blank=True, help_text="Expert's discussion points.", null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='key_findings',
            field=models.TextField(blank=True, help_text="Expert's key imaging findings.", null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='master_template',
            field=models.ForeignKey(blank=True, help_text='The master report template structure associated with this case.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cases', to='cases.mastertemplate'),
        ),
        migrations.AlterField(
            model_name='case',
            name='modality',
            field=models.CharField(choices=[('CT', 'Computer Tomography'), ('MR', 'Magnetic Resonance'), ('US', 'Ultrasound'), ('XR', 'X-ray'), ('FL', 'Fluoroscopy'), ('NM', 'Nuclear Medicine'), ('OT', 'Other')], default='OT', max_length=5),
        ),
        migrations.AlterField(
            model_name='case',
            name='patient_age',
            field=models.CharField(blank=True, help_text="e.g., '5 years', '3 months', 'Neonate'", max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='published_at',
            field=models.DateTimeField(blank=True, help_text='Date when the case becomes publicly visible.', null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='references',
            field=models.TextField(blank=True, help_text='References or further reading.', null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('published', 'Active (Published)'), ('archived', 'Archived')], default='draft', max_length=20),
        ),
        migrations.AlterField(
            model_name='case',
            name='subspecialty',
            field=models.CharField(choices=[('BR', 'Breast (Imaging and Interventional)'), ('CA', 'Cardiac Radiology'), ('CH', 'Chest Radiology'), ('ER', 'Emergency Radiology'), ('GI', 'Gastrointestinal Radiology'), ('GU', 'Genitourinary Radiology'), ('HN', 'Head and Neck'), ('IR', 'Interventional Radiology'), ('MK', 'Musculoskeletal Radiology'), ('NM', 'Nuclear Medicine'), ('NR', 'Neuroradiology'), ('OB', 'Obstetric/Gynecologic Radiology'), ('OI', 'Oncologic Imaging'), ('VA', 'Vascular Radiology'), ('PD', 'Pediatric Radiology'), ('OT', 'Other')], default='OT', max_length=5),
        ),
        migrations.AlterField(
            model_name='case',
            name='title',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='case',
            name='viewed_by',
            field=models.ManyToManyField(blank=True, related_name='viewed_cases', through='cases.UserCaseView', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='casetemplate',
            name='case',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applied_expert_templates', to='cases.case'),
        ),
        migrations.AlterField(
            model_name='casetemplate',
            name='language',
            field=models.ForeignKey(help_text='Language of this expert-filled template.', on_delete=django.db.models.deletion.PROTECT, to='cases.language'),
        ),
        migrations.AlterField(
            model_name='casetemplatesectioncontent',
            name='content',
            field=models.TextField(blank=True, help_text='The expert-filled content for this section.'),
        ),
        migrations.AlterField(
            model_name='casetemplatesectioncontent',
            name='master_section',
            field=models.ForeignKey(help_text='The corresponding section from the MasterTemplate.', on_delete=django.db.models.deletion.CASCADE, to='cases.mastertemplatesection'),
        ),
        migrations.AlterField(
            model_name='language',
            name='code',
            field=models.CharField(help_text="Language code (e.g., 'en', 'es')", max_length=5, unique=True),
        ),
        migrations.AlterField(
            model_name='language',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Is this language available for templates?'),
        ),
        migrations.AlterField(
            model_name='language',
            name='name',
            field=models.CharField(help_text="Full language name (e.g., 'English')", max_length=100),
        ),
        migrations.AlterField(
            model_name='mastertemplate',
            name='body_part',
            field=models.CharField(choices=[('BR', 'Breast (Imaging and Interventional)'), ('CA', 'Cardiac Radiology'), ('CH', 'Chest Radiology'), ('ER', 'Emergency Radiology'), ('GI', 'Gastrointestinal Radiology'), ('GU', 'Genitourinary Radiology'), ('HN', 'Head and Neck'), ('IR', 'Interventional Radiology'), ('MK', 'Musculoskeletal Radiology'), ('NM', 'Nuclear Medicine'), ('NR', 'Neuroradiology'), ('OB', 'Obstetric/Gynecologic Radiology'), ('OI', 'Oncologic Imaging'), ('VA', 'Vascular Radiology'), ('PD', 'Pediatric Radiology'), ('OT', 'Other')], default='OT', help_text='Primary body part or region this template is for.', max_length=5),
        ),
        migrations.AlterField(
            model_name='mastertemplate',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='Admin user who created this master template.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='master_templates_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='mastertemplate',
            name='description',
            field=models.TextField(blank=True, help_text='Optional description of the template.', null=True),
        ),
        migrations.AlterField(
            model_name='mastertemplate',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Is this master template currently active and usable?'),
        ),
        migrations.AlterField(
            model_name='mastertemplate',
            name='modality',
            field=models.CharField(choices=[('CT', 'Computer Tomography'), ('MR', 'Magnetic Resonance'), ('US', 'Ultrasound'), ('XR', 'X-ray'), ('FL', 'Fluoroscopy'), ('NM', 'Nuclear Medicine'), ('OT', 'Other')], default='OT', help_text='Primary imaging modality this template is for.', max_length=5),
        ),
        migrations.AlterField(
            model_name='mastertemplate',
            name='name',
            field=models.CharField(help_text="Name of the master template (e.g., 'CT Brain Basic')", max_length=255),
        ),
        migrations.AlterField(
            model_name='mastertemplatesection',
            name='is_required',
            field=models.BooleanField(default=True, help_text='Is this section mandatory for reports using this template?'),
        ),
        migrations.AlterField(
            model_name='mastertemplatesection',
            name='master_template',
            field=models.ForeignKey(help_text='The master template this section belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='cases.mastertemplate'),
        ),
        migrations.AlterField(
            model_name='mastertemplatesection',
            name='name',
            field=models.CharField(help_text="Name of the section (e.g., 'Findings', 'Impression').", max_length=255),
        ),
        migrations.AlterField(
            model_name='mastertemplatesection',
            name='placeholder_text',
            field=models.TextField(blank=True, help_text='Placeholder text or instructions for this section in the report form.', null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='findings',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='report',
            name='impression',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='report',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together={('case', 'user')},
        ),
    ]
