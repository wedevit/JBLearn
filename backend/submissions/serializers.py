from rest_framework import serializers
from enumchoicefield import EnumChoiceField


from .models import Submission, Language, Status


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class CreateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        read_only_fields = [
            'token',
            'status',
            'stdout',
            'time',
            'memory',
            'stderr',
            'compile_output',
            'message',
        ]
        fields = [
            'source_code',
            'language',
            'compiler_options',
            'command_line_arguments',
            'stdin',
            'expected_output',
            'cpu_time_limit',
            'cpu_extra_time',
            'wall_time_limit',
            'memory_limit',
            'stack_limit',
            'max_processes_and_or_threads',
            'enable_per_process_and_thread_time_limit',
            'enable_per_process_and_thread_memory_limit',
            'max_file_size',
            'redirect_stderr_to_stdout',
            'enable_network',
            'number_of_runs',
            'additional_files',
            'callback_url',
        ] + read_only_fields

        status = EnumChoiceField(enum_class=Status)

        extra_kwargs = {
            'source_code': {'write_only': True},
            'language': {'write_only': True},
            'compiler_options': {'write_only': True},
            'command_line_arguments': {'write_only': True},
            'stdin': {'write_only': True},
            'expected_output': {'write_only': True},
            'cpu_time_limit': {'write_only': True},
            'cpu_extra_time': {'write_only': True},
            'wall_time_limit': {'write_only': True},
            'memory_limit': {'write_only': True},
            'stack_limit': {'write_only': True},
            'max_processes_and_or_threads': {'write_only': True},
            'enable_per_process_and_thread_time_limit': {'write_only': True},
            'enable_per_process_and_thread_memory_limit': {'write_only': True},
            'max_file_size': {'write_only': True},
            'redirect_stderr_to_stdout': {'write_only': True},
            'enable_network': {'write_only': True},
            'number_of_runs': {'write_only': True},
            'additional_files': {'write_only': True},
            'callback_url': {'write_only': True},
        }


class RetrieveSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        # fields = '__all__'
        exclude = ['id']
        # exclude = ['started_at', 'queued_at',
        #            'updated_at', 'queue_host', 'execution_host']

        status = EnumChoiceField(enum_class=Status)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        fields = self.context['request'].query_params.get('fields')
        if fields is None:
            return
            fields = 'token,stdout,time,memory,stderr,compile_output,message,status'
        fields = fields.split(',')
        # Drop any fields that are not specified in the `fields` argument.
        allowed = set(fields)
        existing = set(self.fields.keys())
        for field_name in existing - allowed:
            self.fields.pop(field_name)

    # html_template = serializers.CharField(read_only=True)
    # testcases = serializers.JSONField(read_only=True)
    # code = serializers.SerializerMethodField()

    # def get_code(self, obj):
    #     return obj.code.dump_solution()
