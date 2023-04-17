from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils import timezone
from enumchoicefield import ChoiceEnum, EnumChoiceField
import uuid
import os
import subprocess
import re


def echo_file(content, filename):
    if settings.DEBUG:
        print("echo $'" + content.strip().replace('\n',
          '\\n').replace("'", "\\'") + "'", '>', filename)


def get_hostname():
    try:
        return os.environ["HOSTNAME"]
    except KeyError:
        return "unknown host"


def run_shell_command(command, timeout=None, input=None, shell=True, capture_output=True, text=True, check=True):
    if settings.DEBUG:
        print('Running:', command)  
    return subprocess.run(command, timeout=timeout, input=input, shell=shell, capture_output=capture_output, text=text, check=check)


class Status(ChoiceEnum):
    IN_QUEUE = 'In Queue'
    PROCESSING = 'Processing'
    ACCEPTED = 'Accepted'
    WRONG_ANSWER = 'Wrong Answer'
    TIME_LIMIT_EXCEEDED = 'Time Limit Exceeded'
    COMPILATION_ERROR = 'Compilation Error'
    RUNTIME_ERROR_SIGSEGV = 'Runtime Error (SIGSEGV)'
    RUNTIME_ERROR_SIGXFSZ = 'Runtime Error (SIGXFSZ)'
    RUNTIME_ERROR_SIGFPE = 'Runtime Error (SIGFPE)'
    RUNTIME_ERROR_SIGABRT = 'Runtime Error (SIGABRT)'
    RUNTIME_ERROR_NZEC = 'Runtime Error (NZEC)'
    RUNTIME_ERROR_OTHER = 'Runtime Error (Other)'
    INTERNAL_ERROR = 'Internal Error'
    EXEC_FORMAT_ERROR = 'Exec Format Error'

    def find_runtime_error_by_status_code(self, status_code):
        switcher = {
            11: self.RUNTIME_ERROR_SIGSEGV,
            25: self.RUNTIME_ERROR_SIGXFSZ,
            8: self.RUNTIME_ERROR_SIGFPE,
            6: self.RUNTIME_ERROR_SIGABRT
        }
        if status_code in switcher:
            return switcher[status_code]
        else:
            return self.RUNTIME_ERROR_OTHER


# Create your models here.
class Language(models.Model):
    name = models.CharField(max_length=100)
    compile_cmd = models.CharField(max_length=255)
    run_cmd = models.CharField(max_length=255)
    source_file = models.CharField(max_length=100)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


STDIN_FILE_NAME = "stdin.txt"
STDOUT_FILE_NAME = "stdout.txt"
STDERR_FILE_NAME = "stderr.txt"
METADATA_FILE_NAME = "metadata.txt"
ADDITIONAL_FILES_ARCHIVE_FILE_NAME = "additional_files.zip"


class Submission(models.Model):
    source_code = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.RESTRICT)
    compiler_options = models.CharField(max_length=100, null=True, blank=True)
    command_line_arguments = models.CharField(
        max_length=100, null=True, blank=True)
    stdin = models.TextField(null=True, blank=True)
    expected_output = models.TextField(null=True, blank=True)
    cpu_time_limit = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True)
    cpu_extra_time = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True)
    wall_time_limit = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True)
    memory_limit = models.PositiveIntegerField(null=True, blank=True)
    stack_limit = models.PositiveIntegerField(null=True, blank=True)
    max_processes_and_or_threads = models.PositiveIntegerField(
        null=True, blank=True)
    enable_per_process_and_thread_time_limit = models.BooleanField(
        default=False)
    enable_per_process_and_thread_memory_limit = models.BooleanField(
        default=False)
    max_file_size = models.PositiveIntegerField(null=True, blank=True)
    redirect_stderr_to_stdout = models.BooleanField(default=False)
    enable_network = models.BooleanField(default=False)
    number_of_runs = models.PositiveSmallIntegerField(null=True, blank=True)
    additional_files = models.TextField(null=True, blank=True)
    callback_url = models.TextField(max_length=255, null=True, blank=True)

    token = models.UUIDField(default=uuid.uuid4, editable=False)
    status = EnumChoiceField(Status, default=Status.IN_QUEUE)
    stdout = models.TextField(null=True, blank=True)
    time = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True)
    memory = models.PositiveIntegerField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)
    compile_output = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    exit_code = models.PositiveSmallIntegerField(null=True, blank=True)
    exit_signal = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    wall_time = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    queued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    queue_host = models.CharField(max_length=100, default=get_hostname)
    execution_host = models.CharField(max_length=100, null=True, blank=True)

    def set_defaults(self):
        self.cpu_time_limit = self.cpu_time_limit or settings.CPU_TIME_LIMIT
        self.cpu_extra_time = self.cpu_extra_time or settings.CPU_EXTRA_TIME
        self.wall_time_limit = self.wall_time_limit or settings.WALL_TIME_LIMIT
        self.memory_limit = self.memory_limit or settings.MEMORY_LIMIT
        self.stack_limit = self.stack_limit or settings.STACK_LIMIT
        self.max_processes_and_or_threads = self.max_processes_and_or_threads or settings.MAX_PROCESSES_AND_OR_THREADS
        self.enable_per_process_and_thread_time_limit = self.enable_per_process_and_thread_time_limit or \
            settings.ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT
        self.enable_per_process_and_thread_memory_limit = self.enable_per_process_and_thread_memory_limit or \
            settings.ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT
        self.max_file_size = self.max_file_size or settings.MAX_FILE_SIZE
        self.redirect_stderr_to_stdout = self.redirect_stderr_to_stdout or \
            settings.REDIRECT_STDERR_TO_STDOUT
        self.enable_network = self.enable_network or settings.ENABLE_NETWORK
        self.number_of_runs = self.number_of_runs or settings.NUMBER_OF_RUNS
        self.status = self.status or Status.IN_QUEUE

    def __str__(self):
        return str(self.id) + ": " + str(self.token)

    class CompilationError(Exception):
        pass
    
    class TimeoutError(Exception):
        pass

    def run(self):
        try:
            self.status = Status.PROCESSING
            self.started_at = timezone.now()
            self.execution_host = get_hostname()
            self.save()
            
            self.initialize_workdir()
            self.compile()
            self.execute()

        except Submission.TimeoutError as e:
            self.status = Status.TIME_LIMIT_EXCEEDED
        except Submission.CompilationError as e:
            if str(e):
                self.compile_output = str(e)
            self.status = Status.COMPILATION_ERROR
        except:
            self.status = Status.INTERNAL_ERROR
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
        finally:
            self.finished_at = timezone.now()
            self.save()
            self.cleanup()
            if settings.DEBUG:
                print("Submission %s finished with status: %s" % (self, self.status))
                
        # if self.compile() == Status.COMPILATION_ERROR:
        #     self.cleanup()
        #     return
    #     if compile == :failure
    #     cleanup
    #     return
    #   end
    #   run
    #   verify

    #   time << submission.time
    #   memory << submission.memory

    #   cleanup
    #   break if submission.status != Status.ac

    @staticmethod
    def cgroups_allowed():
        p = run_shell_command("isolate --cg --init", check=False)
        run_shell_command("isolate --cleanup", check=False)
        return p.returncode == 0
        
    def initialize_workdir(self):
        # JUST HACKING: TO BE REMOVED
        if settings.DEBUG and not Submission.cgroups_allowed():
            self.enable_per_process_and_thread_time_limit = True
            self.enable_per_process_and_thread_memory_limit = True
        # REMOVE UNTIL HERE

        self.box_id = self.id % 2147483647
        self.cgroups = "--cg" if not self.enable_per_process_and_thread_time_limit or not self.enable_per_process_and_thread_memory_limit else ""
        self.workdir = self.initialize_box()
        self.boxdir = self.workdir + "/box"
        # self.tmpdir = self.workdir + "/tmp"
        self.source_file = self.boxdir + "/" + self.language.source_file
        # self.stdin_file = self.workdir + "/" + STDIN_FILE_NAME
        # self.stdout_file = self.workdir + "/" + STDOUT_FILE_NAME
        # self.stderr_file = self.workdir + "/" + STDERR_FILE_NAME
        self.metadata_file = self.workdir + "/" + METADATA_FILE_NAME
        self.additional_files_archive_file = self.boxdir + \
            "/" + ADDITIONAL_FILES_ARCHIVE_FILE_NAME

        # for f in [self.source_file, self.stdin_file, self.stdout_file, self.stderr_file, self.metadata_file]:
        #     self.initialize_file(f)
            
        # print('touch ' + ' '.join([self.stdout_file, self.stderr_file, self.metadata_file]))
        
        # JUST HACKING: TO BE REMOVED
#         self.source_code = """
# #include <stdio.h>
# int main() {
#     printf("Hello World");
#     return 0;
# }
#         """
        # REMOVE UNTIL HERE

        with open(self.source_file, 'w') as f:
            f.write(self.source_code)

        if settings.DEBUG:
            echo_file(self.source_code, self.source_file)
        
        # with open(self.stdin_file, 'w') as f:
        #     f.write(self.stdin)

        # echo_file(self.stdin, self.stdin_file)
        
        self.extract_archive()

    def initialize_box(self):
        return run_shell_command(f'isolate {self.cgroups} --box-id={self.box_id} --init').stdout.strip()

    def initialize_file(self, file):
        # run_shell_command(f'touch {file} && chown $(whoami): {file}')
        run_shell_command(f'touch {file}')

    def extract_archive(self):
        pass

    def compile(self):
        if not self.language.compile_cmd:
            return
        
        compile_script = self.boxdir + "/" + "compile.sh"
        compiler_options = re.sub("[$&;<>|`]", "", self.compiler_options) if self.compiler_options else ""
        compile_command = (self.language.compile_cmd % compiler_options).strip()
        with open(compile_script, "w") as f:
            f.write(compile_command)
        
        if settings.DEBUG:
            echo_file(compile_command, compile_script)

        command = f'''isolate {self.cgroups} \\
            --silent \\
            --box-id {self.box_id} \\
            --meta {self.metadata_file} \\
            --stdin /dev/null \\
            --time {settings.MAX_CPU_TIME_LIMIT} \\
            --extra-time 0 \\
            --wall-time {settings.MAX_WALL_TIME_LIMIT} \\
            --stack {settings.MAX_STACK_LIMIT} \\
            --processes={settings.MAX_MAX_PROCESSES_AND_OR_THREADS} \\
            {"--cg-timing" if not self.enable_per_process_and_thread_time_limit else "--no-cg-timing" if self.cgroups else ""} \\
            {"--mem" if self.enable_per_process_and_thread_memory_limit else "--cg-mem"} {settings.MAX_MEMORY_LIMIT} \\
            --fsize {settings.MAX_MAX_FILE_SIZE} \\
            --env HOME=/tmp \\
            --env PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \\
            --env LANG --env=LANGUAGE --env=LC_ALL \\
            --dir /etc:noexec \\
            --run \\
            -- /bin/bash $(basename {compile_script})
        '''.strip()
        command = re.sub("\s+", " ", command.replace("\\", ""))
        
        if settings.DEBUG:
            print(f"{Submission.now()} Compiling submission {self}):")
    
        p = run_shell_command(command, check=False)
        
    
        # JUST HACKING: TO BE REMOVED
        if settings.DEBUG and self.get_metadata().get('status', None) == 'XX':
            command = f"cd {self.boxdir} && /bin/bash $(basename {compile_script})"
            meta_success = """time:0.030
time-wall:0.029
max-rss:17864
csw-voluntary:18
csw-forced:2
exitcode:0"""
            with open(self.metadata_file, "w") as f:
                f.write(meta_success)

            try:
                p = run_shell_command(command, check=False, timeout=settings.MAX_CPU_TIME_LIMIT+settings.MAX_CPU_EXTRA_TIME)
            except subprocess.TimeoutExpired as e:
                raise Submission.CompilationError("Compilation time limit exceeded.")
        # REMOVE UNTIL HERE
        
        metadata = self.get_metadata()

        # Compilation successful
        if p.returncode == 0:
            return

        # Compilation time limit exceeded
        if metadata.get('status', None) == 'TO':
            raise Submission.CompilationError("Compilation time limit exceeded.")

        if p.stderr:
            raise Submission.CompilationError(p.stderr)
        
        raise Submission.CompilationError()

    def execute(self):
        run_script = self.boxdir + "/" + "run.sh"
        command_line_arguments = re.sub("[$&;<>|`]", "", self.command_line_arguments) if self.command_line_arguments else ""
        run_command = f"{self.language.run_cmd} {command_line_arguments}".strip()
        with open(run_script, "w") as f:
            f.write(run_command)
        
        if settings.DEBUG:
            echo_file(run_command, run_script)
        
        command = f'''isolate {self.cgroups} \\
            --silent \\
            --box-id {self.box_id} \\
            --meta {self.metadata_file} \\
            {"--stderr-to-stdout" if self.redirect_stderr_to_stdout else ""} \\
            {"--share-net" if self.enable_network else ""} \\
            --time {self.cpu_time_limit} \\
            --extra-time {self.cpu_extra_time} \\
            --wall-time {self.wall_time_limit} \\
            --stack {self.stack_limit} \\
            --processes={self.max_processes_and_or_threads} \\
            {"--cg-timing" if not self.enable_per_process_and_thread_time_limit else "--no-cg-timing" if self.cgroups else ""} \\
            {"--mem" if self.enable_per_process_and_thread_memory_limit else "--cg-mem"} {self.memory_limit} \\
            --fsize {self.max_file_size} \\
            --env HOME=/tmp \\
            --env PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \\
            --env LANG --env=LANGUAGE --env=LC_ALL \\
            --dir /etc:noexec \\
            --run \\
            -- /bin/bash $(basename {run_script})
        '''.strip()

        command = re.sub("\s+", " ", command.replace("\\", ""))
        
        if settings.DEBUG:
            print(f"{Submission.now()} Executing submission {self}):")
        
        p = run_shell_command(command, check=False)
        
    
        # JUST HACKING: TO BE REMOVED
        if settings.DEBUG and self.get_metadata().get('status', None) == 'XX':
            command = f"cd {self.boxdir} && /bin/bash $(basename {run_script})"
            meta_success = """time:0.003
time-wall:0.004
max-rss:3228
csw-voluntary:6
csw-forced:6
exitcode:0"""
            with open(self.metadata_file, "w") as f:
                f.write(meta_success)
            # REMOVE UNTIL HERE

        try:
            p = run_shell_command(command, input=self.stdin, check=False, timeout=float(self.cpu_time_limit)+float(self.cpu_extra_time))
        except subprocess.TimeoutExpired as e:
            raise Submission.TimeoutError()
        
        metadata = self.get_metadata()

        self.time = metadata['time']
        self.wall_time = metadata['time-wall']
        self.memory = metadata['cg-mem'] if self.cgroups != '' else metadata['max-rss']
        if p.stdout:
            self.stdout = p.stdout
        if p.stderr:
            self.stderr = p.stderr
        try:
            self.exit_code = int(metadata['exitcode'])
        except:
            self.exit_code = 0
        try:
            self.exit_signal = int(metadata['exitsig'])
        except:
            self.exit_signal = 0
        self.message = metadata.get('message', None)
        self.status = self.determine_status(metadata.get('status', None), self.exit_signal)
        
        if self.status == Status.INTERNAL_ERROR and (
            re.match("^execve\(.+\): Exec format error$", self.message) or
            re.match("^execve\(.+\): No such file or directory$", self.message) or
            re.match("^execve\(.+\): Permission denied$", self.message)
        ):
            self.status = Status.EXEC_FORMAT_ERROR

    def determine_status(self, status, exit_signal):
        if status == "TO":
            return Status.TIME_LIMIT_EXCEEDED
        elif status == "SG":
            return Status.find_runtime_error_by_status_code(exit_signal)
        elif status == "RE":
            return Status.RUNTIME_ERROR_NZEC
        elif status == "XX":
            return Status.INTERNAL_ERROR
        elif not self.expected_output or (self.expected_output.strip() == self.stdout.strip()):
            return Status.ACCEPTED
        else:
          return Status.WRONG_ANSWER
    
    def cleanup(self):
        run_shell_command(f'isolate {self.cgroups} --box-id={self.box_id} --cleanup')

    def get_metadata(self):
        metadata = {}

        with open(self.metadata_file) as f:
            for line in f.readlines():
                if line.startswith('message:'):
                    metadata['message'] = line.strip()[8:]
                else:
                    k, v = line.strip().split(':')
                    metadata[k] = v

        return metadata

    def reset_metadata_file(self):
        run_shell_command(f'rm -rf {self.metadata_file}')
        self.initialize_file(self.metadata_file)

    @staticmethod
    def now():
        return timezone.localtime(timezone.now()).strftime("[%Y-%m-%d %H:%M:%S.%f]")

    @staticmethod
    def fetch_one_inqueue_submission(use_transaction=True):
        from django.db import connection

        with connection.cursor() as cursor:
            if use_transaction:
                cursor.execute("START TRANSACTION;")
                cursor.execute(
                    "SELECT id FROM submissions_submission WHERE status='%s' ORDER BY created_at LIMIT 1 FOR UPDATE;" % Status.IN_QUEUE.name)
            else:
                cursor.execute(
                    "SELECT id FROM submissions_submission WHERE status='%s' ORDER BY created_at LIMIT 1;" % Status.IN_QUEUE.name)
            result = cursor.fetchall()
            if len(result) == 1:
                submission_id = result[0][0]
                cursor.execute("UPDATE submissions_submission SET status='%s' WHERE id='%s';" % (Status.PROCESSING.name, submission_id))
            else:
                submission_id = None
                
            if use_transaction:
                cursor.execute("COMMIT;")
            
            if submission_id != None:
                return Submission.objects.get(pk=submission_id)
            else:
                return None


@receiver(pre_save, sender=Submission)
def parse_source(sender, instance, *args, **kwargs):
    instance.set_defaults()
