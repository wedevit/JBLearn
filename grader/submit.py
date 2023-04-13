import subprocess

# Define the path to the isolate executable
ISOLATE_EXECUTABLE = "isolate"

# Define the path to the program you want to execute
PROGRAM_PATH = "run.sh"

# Define any command line arguments to pass to the program
ARGS = []#["arg1", "arg2", "arg3"]

# Define the input file to pass to the program (optional)
INPUT_FILE = None

# Define the output file to write program output to (optional)
OUTPUT_FILE = None

# Define the timeout for the program (in seconds)
TIMEOUT = 10
BOXID = 1

# Build the isolate command
command = [
    ISOLATE_EXECUTABLE,
    "--run",
    "--box-id=%d" % BOXID,
    "--env=PATH=/usr/bin:/bin",
    "--dir=/etc:noexec",
    # "--time=%d" % TIMEOUT,
    "--",
    "/bin/bash",
    PROGRAM_PATH,
] + ARGS

# Add input file argument (if provided)
if INPUT_FILE is not None:
    command += ["<", INPUT_FILE]

# Add output file argument (if provided)
if OUTPUT_FILE is not None:
    command += [">", OUTPUT_FILE]

# Execute the isolate command
result = subprocess.run(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
)

# Print the program output and error messages
print("Program Output:")
print(result.stdout)

print("Error Messages:")
print(result.stderr)
