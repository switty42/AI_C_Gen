# AI_C_Gen
# Author Stephen Witty switty@level500.com
# 9-11-23
# Test GPT's ability to write a C program correctly and measure results
# V2  added Python
#
# Example code from rollbar.com - GPT example
#
# V1 9-11-23 - Initial release / dev
# V2 9-15-23 - Add Python as a target language
#
# Notes - Add your OpenAI key below
#
# Warning - test system automatically runs code provided by ChatGPT with no filtering.
# Anything the user can do that runs the test system can also be done by the ChatGPT provided code.
# Is is advised to run the system inside a restricted VM.

import openai
import time
import sys
import os
import random

# Put OpenAI API key here
openai.api_key = "XXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Uncomment GPT model desired here
gpt_model='gpt-3.5-turbo'
#gpt_model = "gpt-4" # Very expensive

###################### Constants ##########################################################
VERSION = 2                                                                                # Software version
NUMBER_OF_CYCLES = 25                                                                      # Number of cycles to run before exiting
GPT_RETRY_LIMIT = 25                                                                       # Number of times to retry GPT if errors occur
GPT_TIMEOUT = 180                                                                          # GPT reply timeout in seconds
TIME_LIMIT = 7                                                                             # Minutes to allow gpt c code to run before terminating
WORKING_DIR = "/home/switty/dev/AI_C_Gen/work"                                             # Working directory for compiles etc (no slash on end)
PROMPT = "Write a C program that calculates the 500,000th prime number efficiently."       # GPT prompt
LANG = "C"                                                                                 # Target language "C" or "Python"
ANSWER = "7368787"                                                                         # Answer if generated code runs correctly
ANSWER2 = "7,368,787"                                                                      # Second possible right answer, if only one answer, make the same as ANSWER
##########################################################################################

########## This function creates the AI prompt #######
def create_gpt_prompt():
   prompt_message = PROMPT
   return prompt_message

########### This function formats an output string ####################
def print_string(string):
   cnt = 0
   for char in string:
      if not (char == " " and cnt == 0):
         print(char, end = "")
         if (char == "\n"):
            cnt = 0
         cnt = cnt + 1
      if (cnt > 115 and char == " "):
         print(" ")
         cnt = 0
   print()
   sys.stdout.flush()

############### Function - Call ChatGPT #########################################
def call_gpt(prompt_message):
# Returning - success / failure, gpt reply, error if any, prompt tokens, completion tokens
   try:
      response = openai.ChatCompletion.create(model=gpt_model, messages=[ {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt_message}],request_timeout=GPT_TIMEOUT)
   except Exception as e:
      return False, "", "WARNING:  System Error during ChatGPT call: " + str(e),0,0

   return True, response.choices[0]["message"]["content"], "",response.usage["prompt_tokens"], response.usage["completion_tokens"]

############## Find and return the program inside of reply ########################
# Code returns the newline after the header, this is why there is a blank line on print
def get_program(buffer):
   if (LANG == "C"):
      start = buffer.find("```c") # Find start of C program in reply
      if (start == -1):
         start = buffer.find("```C") # Start of program can be c or C
      if (start == -1):           # Could not find start of program
         return False, "", "Could not find start of program"
      skip_increment = 4 # String size of prefix
   else:
      start = buffer.find("```python") # Find start of Python program in reply
      if (start == -1):
         start = buffer.find("```Python") # Looking for python, Python or PYTHON
      if (start == -1):
         start = buffer.find("```PYTHON")
      if (start == -1):           # Could not find start of program
         return False, "", "Could not find start of program"
      skip_increment = 9 # String size of prefix

   if (start + skip_increment + 20 >= len(buffer)): # Verify that message is longer than just start characters
      return False, "", "Reply is too short"

   end = buffer.find("```",start + skip_increment)
   if (end == -1):            # Could not find end of program in reply
      return False, "", "Could not find end of program"
   return True, buffer[start + skip_increment:end], ""

############## Write program to a disk file ###############################
def write_code(buffer):
   file_list = { "a.out","source.c","output","compile.out","run.py" }

   # Delete files
   for file_name in file_list:
      if (os.path.exists(WORKING_DIR + "/" + file_name)):
         os.remove(WORKING_DIR + "/" + file_name)

      if (os.path.exists(WORKING_DIR + "/" + file_name)):
         print("**** ERROR - " + file_name + " is still present in the working directory")
         sys.exit(0)

   # Write the source file
   if (LANG == "C"):
      file_name = "source.c"
   else:
      file_name = "run.py"

   try:
      file = open(WORKING_DIR + "/" + file_name,"wt")
      file.write(buffer)
      file.close()
   except:
      print("**** ERROR - Could not write source file")
      sys.exit(0)

################# Check if program output is correct ########################
def check_program_output():
   output = ""
   # Read in data from program output
   try:
      with open(WORKING_DIR + "/output") as file:
         output = file.read()
   except:
      return False, ""

   # Look for answer string inside of output contents
   if (ANSWER in output or ANSWER2 in output): # Check for two possible answers
      return True, output
   else:
      return False, output

###############  Start of main routine ##############################################################
print("Software version: " + str(VERSION))
print("Model: " + gpt_model)
# Sanity check some of the program constants
if (not LANG == "C"  and not LANG == "Python"):
   print("ERROR, LANG constant must equal \"C\" or \"Python\"")
   sys.exit(0)
if (not os.path.exists(WORKING_DIR)):
   print("ERROR, WORKING_DIR constant directory does not exist")
   sys.exit(0)
if (WORKING_DIR[len(WORKING_DIR) -1] == "/"): # Above check protects against empty string
   print("ERROR, WORKING_DIR ends in slash")
   sys.exit(0)

number_of_cycles = 0
code_history = []
duplicate = 0
time_history = []
max_time = 0
min_time = 9999999999
gpt_errors = 0
bad_output = 0
bad_compiles = 0
total_success = 0
max_run_time = 0
min_run_time = 999999
run_time_history = []
best_code_number = -1 # Fastest - Set to negative one so I can detect never getting one to run
best_code_source = ""
total_run_time = time.time() # Using this to calculate total program run time
total_input_tokens = 0  # Used to store the total number of input tokens used for program
total_output_tokens = 0 # Used to store the total number of output tokens for program

while(number_of_cycles < NUMBER_OF_CYCLES): # Main loop to run prompts

   number_of_cycles = number_of_cycles + 1

   # Create GPT prompt
   prompt = create_gpt_prompt()

   print("\n************************************** GPT Prompt ************************* Session: " + str(number_of_cycles))
   print_string(prompt)

   retry_count = 0
   success = False

   while (not success): # Keep looping until we get a valid program to check

      if (retry_count == GPT_RETRY_LIMIT):
         print("\n\nERROR: Too many GPT errors, exiting\n")
         sys.exit()

      store_time = time.time()

      # Call GPT, retry if there is an error
      success, gpt_reply, error_text, input_tokens, output_tokens = call_gpt(prompt)
      if (not success):
         print(error_text)
         retry_count = retry_count + 1
         gpt_errors = gpt_errors + 1
         continue

      final_time = time.time() - store_time

      total_input_tokens = total_input_tokens + input_tokens
      total_output_tokens = total_output_tokens + output_tokens

      print("\n*************** GPT Answer ***************")
      print_string(gpt_reply)

      # Extract program from reply or retry if not present
      success, code, error_text = get_program(gpt_reply)
      if (not success):
         print("\nWARNING:  Could not find program in GPT reply: " + error_text)
         gpt_errors = gpt_errors + 1
         retry_count = retry_count + 1
         continue

   # Should have source code to try to compile and run from here down

   # Keep up with GPT busy time
   time_history.append(final_time)
   if (max_time < final_time):
      max_time = final_time
   if (min_time > final_time):
      min_time = final_time

   print("\n************* Code from GPT Answer **************")
   print_string(code)

   if (code in code_history):
      print("\nFOUND DUPLICATE CODE .........")
      duplicate = duplicate + 1
   else:
      code_history.append(code)

   write_code(code) # Write code to file

####################### C section ###############################
   if (LANG == "C"): # Only try and compile if the program is C since Python needs no compile
      # Try and compile the code
      print("Compiling code........") # timeout command sigterm after TIME_LIMIT minutes and kill after 20 sec
      sys.stdout.flush()
      os.system("timeout -k 20 " + str(TIME_LIMIT) + "m cc " + WORKING_DIR + "/source.c -o " + WORKING_DIR + "/a.out > " + WORKING_DIR + "/compile.out 2>&1")

      compile_output = ""
      # Read and print any compiler messages / errors
      try:
         with open(WORKING_DIR + "/compile.out") as file:
            compile_output = file.read()
      except:
         pass # Ignore, likely file is not present which is not an error

      print_string(compile_output)

      # Check and see if  compile was successful
      if (os.path.exists(WORKING_DIR + "/a.out")):
         print("Compile was successful .............\n")
         sys.stdout.flush()
         run_string = WORKING_DIR + "/a.out"  # Will be used belwo when program runs
         run_program = True

      # Failed compile
      else:
         print("Compile FAILED ....................")
         bad_compiles = bad_compiles + 1
         run_program = False # Bad compile don't run program

###################### Python section #################################
   else:
         run_string = "python3 " + WORKING_DIR + "/run.py" # Will be used below when program runs
         run_program = True
######################### End Python section ##########################

   final_time = 0 # Need this set to zero incase of bad C compile and no run for stats

   if (run_program): # Run program if it compiled and or exists
      # Redirect stdout and stderror to a file
      # Keep up with how long the program runs
      # Same os.system call runs both c and Python programs, only run_string differs
      print("Running program ..............\n")
      sys.stdout.flush()
      store_time = time.time()
      # timeout command sigterm after TIME_LIMIT minutes and kill after 20 sec - prevent infinite loops
      os.system("cd " + WORKING_DIR +"; timeout -k 20 " + str(TIME_LIMIT) + "m " + run_string + " > " + WORKING_DIR + "/output 2>&1")
      final_time = time.time() - store_time

      # Check program output
      success, output = check_program_output()

      print("Program output ............\n")
      print_string(output)

      print(">>>>>>> Correct answer is: " + ANSWER + " or " + ANSWER2)

      if (success): # If program provides correct answer ######################
         print("Program worked ..................")
         total_success = total_success + 1

         # Keep up with program run time
         run_time_history.append(final_time) # Only add to history the ones that work
         if (max_run_time < final_time):
            max_run_time = final_time
         if (min_run_time > final_time):
            min_run_time = final_time

            # Save fastest run time that works
            best_code_number = number_of_cycles
            best_code_source = code

      else:
         print("Program output is BAD ..............")
         bad_output = bad_output + 1

   print("\nTotal cycles: " + str(number_of_cycles) + " Code Duplicates: " + str(duplicate))
   print("Bad compiles: " + str(bad_compiles) + " Bad run outputs: " + str(bad_output))
   print("Current run time: " + str(round(final_time,3)))
   print("Total success: " + str(total_success))
   sys.stdout.flush()

avg_time = 0 # This is GPT prompt time
for i in time_history:
   avg_time = avg_time + i
avg_time = avg_time / len(time_history)

avg_run_time = 0 # This is program run time
if (len(run_time_history) > 0): # This will be zero if we never find a working program
   for i in run_time_history:
      avg_run_time = avg_run_time + i
   avg_run_time = avg_run_time / len(run_time_history)

print("\nFinal report **************************************")
print("Software version: " + str(VERSION))
print("Model: " + gpt_model)
print("GPT Prompt: " + PROMPT)
print("\nNumber of cycles: " + str(number_of_cycles))
print("Total program tokens used input: " + str(total_input_tokens) + " output: " + str(total_output_tokens))
print("Total program run time in minutes: " + str(round((time.time() - total_run_time)/60,2))) 
print("GPT Errors: " + str(gpt_errors))
print("GPT prompt time minimum: " + str(round(min_time,2)).ljust(7) + " maximum:      " + str(round(max_time,2)).ljust(7) + " avgerage:        " + str(round(avg_time,2)))
print("Duplicate code:          " + str(duplicate).ljust(7)  + " Bad compiles: " + str(bad_compiles).ljust(7) + " Bad run outputs: " + str(bad_output))
print("Code run time minimum:   " + str(round(min_run_time,3)).ljust(7) + " maximum:      " + str(round(max_run_time,3)).ljust(7) + " average:         " + str(round(avg_run_time,3)))
print("Total success: " + str(total_success))

if (not best_code_number == -1):
   print("\nIndex of best code: " + str(best_code_number))
   print("**** Best Code Follows ************")
   print_string(best_code_source)
