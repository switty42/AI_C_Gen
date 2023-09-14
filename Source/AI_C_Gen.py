# AI_C_Gen
# Author Stephen Witty switty@level500.com
# 9-11-23
# Test GPT's ability to write a C program correctly and measure results
#
# Example code from rollbar.com - GPT example
#
# V1 9-11-23 - Initial release / dev
#
# Notes - Add your OpenAI key below

import openai
import time
import sys
import os
import random

# Put OpenAI API key here
openai.api_key = "XXXXXXXXXXXXXXXXXXXXXXXX"

# Uncomment GPT model desired here
gpt_model='gpt-3.5-turbo'
#gpt_model = "gpt-4"

###################### Constants ##########################################################
NUMBER_OF_CYCLES = 300                                                                 # Number of cycles to run before exiting
GPT_RETRY_LIMIT = 25                                                                   # Number of times to retry GPT if errors occur
TIME_LIMIT = 5                                                                         # Minutes to allow gpt c code to run before terminating
WORKING_DIR = "/home/switty/dev/AI_C_Gen/work"                                         # Working directory for compiles etc (no slash on end)
PROMPT = "Write a C program that calculates the 500,000th prime number efficiently."   # GPT prompt
ANSWER = "7368787"                                                                     # Answer if generated code runs correctly

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
   try:
      response = openai.ChatCompletion.create(model=gpt_model, messages=[ {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt_message}],request_timeout=35)
   except Exception as e:
      return False, "", "WARNING:  System Error during ChatGPT call: " + str(e)

   return True, response.choices[0]["message"]["content"], ""

############## Find and return C program inside of reply ########################
def get_c_program(buffer):
   start = buffer.find("```c") # Find start of C program in reply
   if (start == -1):
      start = buffer.find("```C") # Start of program can be c or C
   if (start == -1):           # Could not find start of program
      return False, "", "Could not find start of program"
   if (start + 4 >= len(buffer)): # Verify that message is longer than just start characters
      return False, "", "Reply is too short"
   end = buffer.find("```",start+4)
   if (end == -1):            # Could not find end of program in reply
      return False, "", "Could not find end of program"
   return True, buffer[start + 4:end], ""

############## Write c program to a disk file ###############################
def write_c_code(buffer):

   # Clean up old files if they exist
   if (os.path.exists(WORKING_DIR + "/a.out")):
      os.remove(WORKING_DIR + "/a.out")
   if (os.path.exists(WORKING_DIR + "/source.c")):
      os.remove(WORKING_DIR + "/source.c")
   if (os.path.exists(WORKING_DIR + "/output")):
      os.remove(WORKING_DIR + "/output")
   if (os.path.exists(WORKING_DIR + "/compile.out")):
      os.remove(WORKING_DIR + "/compile.out")

   # Verify files are not present after the deletes, after above this should not be needed, but double checking since important
   if (os.path.exists(WORKING_DIR + "/a.out")):
      print("**** ERROR - a.out is still present in the working directory")
      os.exit(0)
   if (os.path.exists(WORKING_DIR + "/source.c")):
      print("**** ERROR - source.c is still present in the working directory")
      os.exit(0)
   if (os.path.exists(WORKING_DIR + "/output")):
      print("**** ERROR - output is still present in the working directory")
      os.exit(0)
   if (os.path.exists(WORKING_DIR + "/compile.out")):
      print("**** ERROR - compile.out is still present in the working directory")
      os.exit(0)

   # Write the source file
   try:
      file = open(WORKING_DIR + "/source.c","wt")
      file.write(buffer)
      file.close()
   except:
      print("**** ERROR - Could not write source.c file")
      os.exit(0)

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
   if (ANSWER in output):
      return True, output
   else:
      return False, output

###############  Start of main routine ##############################################################
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
min_run_time = 999999999
run_time_history = []
best_code_number = -1 # Fastest - Set to negative one so I can detect never getting one to run
best_code_source = ""

while(number_of_cycles < NUMBER_OF_CYCLES): # Main loop to run prompts

   number_of_cycles = number_of_cycles + 1

   # Create GPT prompt
   prompt = create_gpt_prompt()

   print("\n************************************** GPT Prompt ******************** Session: " + str(number_of_cycles))
   print_string(prompt)

   retry_count = 0
   success = False

   while (not success): # Keep looping until we get a valid program to check

      if (retry_count == GPT_RETRY_LIMIT):
         print("\n\nERROR: Too many GPT errors, exiting\n")
         sys.exit()

      store_time = time.time()

      # Call GPT, retry if there is an error
      success, gpt_reply, error_text = call_gpt(prompt)
      if (not success):
         print(error_text)
         retry_count = retry_count + 1
         gpt_errors = gpt_errors + 1
         continue

      final_time = time.time() - store_time

      print("\n*************** GPT Answer ***************")
      print_string(gpt_reply)

      # Extract program from reply or retry if not present
      success, code, error_text = get_c_program(gpt_reply)
      if (not success):
         print("WARNING:  Could not find program in GPT reply: " + error_text)
         gpt_errors = gpt_errors + 1
         continue

   # Should have source code to try to compile and run from here down

   # Keep up with GPT busy time
   time_history.append(final_time)
   if (max_time < final_time):
      max_time = final_time
   if (min_time > final_time):
      min_time = final_time

   print("\n************* C code from GPT Answer **************")
   print_string(code)

   if (code in code_history):
      print("\nFOUND DUPLICATE CODE .........")
      duplicate = duplicate + 1
   else:
      code_history.append(code)

   write_c_code(code) # Write code to file

   # Try and compile the code
   print("Compiling code........\n") # timeout command sigterm after TIME_LIMIT minutes and kill after 20 sec
   os.system("timeout -k 20 " + str(TIME_LIMIT) + "m cc " + WORKING_DIR + "/source.c -o " + WORKING_DIR + "/a.out > " + WORKING_DIR + "/compile.out 2>&1")

   compile_output = ""
   # Read and print any compiler messages / errors
   try:
      with open(WORKING_DIR + "/compile.out") as file:
         compile_output = file.read()
   except:
      pass # Ignore, likely file is not present which is not an error

   print_string(compile_output)

   final_time = 0 # Need this set to zero incase of a bad compile and no run for stats

   # Check and see if  compile was successful
   if (os.path.exists(WORKING_DIR + "/a.out")):
      print("Compile was successful, running ...............\n")

      # Run program, redirect stdout and stderror to a file
      # Keep up with how long the program runs
      store_time = time.time()
      # timeout command sigterm after 5 minutes and kill after 20 sec - prevent infinite loops
      os.system("timeout -k 20 " + str(TIME_LIMIT) + "m " + WORKING_DIR + "/a.out > " + WORKING_DIR + "/output 2>&1")
      final_time = time.time() - store_time

      # Check program output
      success, output = check_program_output()

      print("Program output ............\n")
      print_string(output)

      print(">>>>>>> Correct answer is: " + ANSWER)

      if (success):
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

   # Failed compile
   else:
      print("Compile FAILED ....................")
      bad_compiles = bad_compiles + 1

   print("\nTotal cycles: " + str(number_of_cycles) + " Code Duplicates: " + str(duplicate))
   print("Bad compiles: " + str(bad_compiles) + " Bad run outputs: " + str(bad_output))
   print("Current run time: " + str(round(final_time,3)))
   print("Total success: " + str(total_success))

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
print("GPT Prompt: " + PROMPT)
print("\nNumber of cycles: " + str(number_of_cycles))
print("GPT Errors: " + str(gpt_errors))
print("GPT prompt time min: " + str(round(min_time,2)) + "    max: " + str(round(max_time,2)) + "    avg: " + str(round(avg_time,2)))
print("Duplicate code: " + str(duplicate)  + "    Bad compiles: " + str(bad_compiles) + "    Bad run outputs: " + str(bad_output))
print("Min run time: " + str(round(min_run_time,3)) + "   max: " + str(round(max_run_time,3)) + "   avg: " + str(round(avg_run_time,3)))
print("Total success: " + str(total_success))

if (not best_code_number == -1):
   print("\nIndex of best code: " + str(best_code_number))
   print("**** Best Code Follows ************")
   print_string(best_code_source)
