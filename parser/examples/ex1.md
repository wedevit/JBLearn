Labsheet No.1
=============
This is a sample document for testing e-Labsheet project.

@@Config language='python',markers=('{{','}}')

@@BeginCode
def max(a, b):
  if a > b:
    return a
  else:
    return b

@@Hide
def main():
  a = int(input())
  b = int(input())
  print(max(a, b))

@@Exclude
main()

@@Blank
print("You code this")

@@Fixed
@@EndCode

@@BeginTest ignorecase=True,ignorespace=True,timeout=1000,tolerance=1e-6,memlimit=1000
@@Input
1
2
@@Exec
main()
@@Args extra arguments
@@Required for\s*\([^;]*;[^;]*;.*\)
@@Forbidden \.contains\s*\( 
@@Feedback Do not use the contains method!
@@Hint Try larger value
@@EndTest

@@BeginTest
print(max(5, 2))
@@EndTest
