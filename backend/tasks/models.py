from parser import parser
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db import models
from django.contrib.auth.models import User

from .fields import CodeField, LongJSONField


class Task(models.Model):
    """
    A task is a unit of learning which can compose of one or more of the following
    - content(s) written in markdown
    - question(s)
    - coding(s)
    in any order
    """

    name = models.CharField(max_length=100)
    description = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='A one-line description of the task'
    )
    source = models.TextField()
    html_template = models.TextField(blank=True)
    code = CodeField(blank=True)
    testcases = LongJSONField(blank=True, null=True)

    creator = models.ForeignKey(
        User,
        related_name='created_tasks',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    owner = models.ForeignKey(
        User,
        related_name='owned_tasks',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    version = models.IntegerField(default=1)
    previous_version = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL
    )

    disabled = models.BooleanField(default=False)
    is_private = models.BooleanField(
        default=False,
        help_text='If checked, this task becomes private to its creator and owner'
    )


@receiver(pre_save, sender=Task)
def parse_source(sender, instance, *args, **kwargs):
    html, code, tests = parser.parse_source(instance.source)
    instance.html_template = html
    instance.code = code
    testcases = []
    for test in tests:
        testcases.append({
            'input' : test.input,
            'output' : None,
            'visible' : test.visible,
            'hint' : test.hint,
            })
    instance.testcases = testcases
    # instance.testcases = tests
    # print(code.sequence)


class Question(models.Model):
    """
    A question is used to assess a student's knowledge or understanding of a particular topic or subject
    """

    html = models.TextField(blank=True)
    answer = models.TextField(blank=True)
    task = models.ForeignKey(
        Task,
        related_name='questions',
        on_delete=models.CASCADE
    )


class Coding(models.Model):
    """
    A coding is used to assess a student's programming skill.
    It can also be used to write a script to create an automated grader.
    """

    code = CodeField(blank=True)
    testcases = LongJSONField(blank=True, null=True)
    task = models.ForeignKey(
        Task,
        related_name='codes',
        on_delete=models.CASCADE
    )
