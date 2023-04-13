from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'source', 'html_template', 'code', 'testcases']

    html_template = serializers.CharField(read_only=True)
    testcases = serializers.JSONField(read_only=True)
    code = serializers.SerializerMethodField()

    def get_code(self, obj):
        return obj.code.dump_solution()