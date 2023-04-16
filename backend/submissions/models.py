from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone

from enumchoicefield import ChoiceEnum, EnumChoiceField
import uuid
import os
import subprocess
import re

def get_hostname():
    print('called')
    try:
        return os.environ["HOSTNAME"]
    except KeyError:
        return "unknown host"

def run_command(command, timeout=None):
    return subprocess.run(command, timeout=timeout, shell=True, capture_output=True, text=True, check=True)
    
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
    
    def run(self):
        try:
            self.initialize_workdir()
            self.compile()
        except subprocess.CalledProcessError as e:
            print(e)
            print(e.stderr)
        except Exception as e:
            print(e)
        finally:
            self.cleanup()
            
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
        
    def initialize_workdir(self):
        # JUST HACKING: TO BE REMOVED
        self.enable_per_process_and_thread_time_limit = True
        self.enable_per_process_and_thread_memory_limit = True
        # REMOVE UNTIL HERE
        
        self.box_id = self.id % 2147483647
        self.cgroups = "--cg" if not self.enable_per_process_and_thread_time_limit or not self.enable_per_process_and_thread_memory_limit else ""
        self.workdir = self.initialize_box()
        self.boxdir = self.workdir + "/box"
        self.tmpdir = self.workdir + "/tmp"
        self.source_file = self.boxdir + "/" + self.language.source_file
        self.stdin_file = self.workdir + "/" + STDIN_FILE_NAME
        self.stdout_file = self.workdir + "/" + STDOUT_FILE_NAME
        self.stderr_file = self.workdir + "/" + STDERR_FILE_NAME
        self.metadata_file = self.workdir + "/" + METADATA_FILE_NAME
        self.additional_files_archive_file = self.boxdir + "/" + ADDITIONAL_FILES_ARCHIVE_FILE_NAME

        for f in [self.source_file, self.stdin_file, self.stdout_file, self.stderr_file, self.metadata_file]:
            self.initialize_file(f)

        with open(self.source_file, 'w') as f:
            f.write(self.source_code)
        
        with open(self.stdin_file, 'w') as f:
            f.write(self.stdin)

        self.extract_archive()
    
    def initialize_box(self):
        return run_command(f'isolate {self.cgroups} --box-id={self.box_id} --init').stdout.strip()
    
    def initialize_file(self, file):
        run_command(f'touch {file} && chown $(whoami): {file}')
    
    def extract_archive(self):
        pass
    
    def compile(self):
        compile_script = self.boxdir + "/" + "compile.sh"
        compiler_options = re.sub("[$&;<>|`]", "", self.compiler_options)
        with open(compile_script, "w") as f:
            f.write(self.language.compile_cmd % compiler_options)
            
        # JUST HACKING: TO BE REMOVED
        with open(compile_script, "w") as f:
            f.write('/usr/bin/gcc main.c')
        # REMOVE UNTIL HERE
        
        compile_output_file = self.workdir + "/" + "compile_output.txt"
        self.initialize_file(compile_output_file)

        command = f'''isolate {self.cgroups} \\
            --silent \\
            --box-id {self.box_id} \\
            --meta {self.metadata_file} \\
            --stderr-to-stdout \\
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
            -- /bin/bash $(basename {compile_script}) > {compile_output_file}
        '''.strip()
        command = re.sub("\s+", " ", command.replace("\\", ""))
        print(f"{Submission.now()} Compiling submission {self}):")
        print('Compile command:', command)
        print()
        
        # JUST HACKING: TO BE REMOVED
        command = f"cd {self.boxdir} && /bin/bash $(basename {compile_script}) > {compile_output_file}"
        with open(self.metadata_file, "w") as f:
            f.write('time:0.029\ntime-wall:0.029\nmax-rss:18108\ncsw-voluntary:18\ncsw-forced:8\nexitcode:0')
        # REMOVE UNTIL HERE
        
        p = run_command(command)

    # `#{command}`
    # process_status = $?

        with open(compile_output_file) as f:
            self.compile_output = f.read()

        if self.compile_output == "": self.compile_output = None
        
        print('Compiler output:', self.compile_output)

        metadata = self.get_metadata()

        self.reset_metadata_file()

        files_to_remove = [compile_output_file, compile_script]
        for f in files_to_remove:
            run_command(f'rm -rf {f}')

        return True
    # return :success if process_status.success?

    # if metadata[:status] == "TO"
    #   submission.compile_output = "Compilation time limit exceeded."
    # end

    # submission.finished_at = DateTime.now
    # submission.time = nil
    # submission.wall_time = nil
    # submission.memory = nil
    # submission.stdout = nil
    # submission.stderr = nil
    # submission.exit_code = nil
    # submission.exit_signal = nil
    # submission.message = nil
    # submission.status = Status.ce
    # submission.save

    # return :failure
    
    def cleanup(self):
        run_command(f'isolate {self.cgroups} --box-id={self.box_id} --cleanup')

    def get_metadata(self):
        metadata = {}
        
        with open(self.metadata_file) as f:
            for line in f.readlines():
                k, v = line.strip().split(':')
                metadata[k] = v
                
        return metadata

    def reset_metadata_file(self):
        run_command(f'rm -rf {self.metadata_file}')  
        self.initialize_file(self.metadata_file)
    
    @staticmethod
    def now():
        return timezone.localtime(timezone.now()).strftime("[%Y-%m-%d %H:%M:%S.%f]")
    
    @staticmethod
    def fetch_one_inqueue_submission(use_transaction=True):
        if use_transaction:
            from django.db import connection

            with connection.cursor() as cursor:
                # cursor.execute("START TRANSACTION;")
                # num = cursor.execute("SELECT id FROM submission WHERE status='%s' ORDER BY created_at LIMIT 1 FOR UPDATE;" % Status.IN_QUEUE.name)
                cursor.execute(
                    "SELECT id FROM submissions_submission WHERE status='%s' ORDER BY created_at LIMIT 1;" % Status.IN_QUEUE.name)
                result = cursor.fetchall()
                if len(result) == 1:
                    submission_id = result[0][0]
                    # cursor.execute("UPDATE submissions_submission SET status='%s' WHERE id='%s';" % (Status.PROCESSING.name, submission_id))
                else:
                    submission_id = None
                # cursor.execute("COMMIT;")

            if submission_id != None:
                return Submission.objects.get(pk=submission_id)
            else:
                return None
        else:
            submissions = (
                Submission.objects
                .filter(status=Status.IN_QUEUE)
                .order_by("created_at")
                .all()[:1])
            if len(submissions) == 1:
                return submissions[0]
            else:
                return None


@receiver(pre_save, sender=Submission)
def parse_source(sender, instance, *args, **kwargs):
    instance.set_defaults()
