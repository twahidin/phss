#version 6 - To put in community page 
import openai
import streamlit as st
from streamlit_chat import message
import time
import requests
import sqlite3
import pygsheets
import pandas as pd
import json
import csv
from streamlit_disqus import st_disqus
import streamlit_analytics
from google.oauth2 import service_account
from int_quiz import personality_generator, reveal_questions
from datetime import datetime
import random

#Global Declaration

HOME = "Homepage"
WIZARD = "Wizard"
QUIZ = "Quiz"
TREASURE = "Treasury"
CHAT="Assistant"

st.set_page_config(page_title="InteresThing", page_icon=":mag_right:", layout="wide")
#menu will be extracted from school options
menu = ["InteresThing Homepage 🏠", "InteresThing Wizard 🧙", "InteresThing Quiz 📝","InteresThing Commmunity", "InteresThing Treasury 🏛️"]

db_file = st.secrets["current_db_file"] #uploaded in streamlit server
num_hobbies = st.secrets["num_hobbies"]
#sch_file = st.secrets["school_db_file"] #to consider separating the database?

# DATA TRACKING --------------------------------------------------------------------------------------

def insert_student_data(school_code, student_code, action, db_file): #for data tracking purposes
	conn = sqlite3.connect(db_file)
	c = conn.cursor()

	created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	c.execute("INSERT INTO student_data (created_at, sch_code, stu_code, action) VALUES (?,?,?,?)", (created_at, school_code, student_code, action))
	conn.commit()
	conn.close()

def download_student_data():
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()

	cursor.execute('''SELECT * FROM student_data''')
	result = cursor.fetchall()
	try:
		# Export the result to a csv file
		filename = 'int_records.csv'
		# convert the result to a dataframe
		my_df = pd.DataFrame(result, columns=['created_at', 'sch_code', 'stu_code', 'action'])
		data_csv = my_df.to_csv()
	except:
		st.error("Failed to export records, please try again")
	else:
		st.download_button(
			label="Download data as CSV",
			data=data_csv,
			file_name=filename,
			mime='text/csv',
		)



#WIZARD DISCOVERY TOOLS --------------------------------------------------------------------------------------

def random_numbers(): # part of the wizard discovery function to randomise and output 9 different numbers
	# Create a list of numbers from 1 to 40
	numbers = list(range(0, 20)) # change to 20
	# Shuffle the numbers
	random.shuffle(numbers)
	# Select the first 27 numbers
	selected_numbers = numbers[:9]

	return selected_numbers

def select_words(words): #function here is slightly slow so have to rework how to make this faster in v2, 
	#Wizard discovery tool

	st.write("Please select up to 3 words that you like and click Generate 🪄 button ")
	#st.write("Click the Next ➡️ button when you have checked the boxes")
	#st.write("#")

	selected_words = []
	col1, col2, col3 = st.columns((0.3,0.3,0.3))
	#st.write('select_words function')

	with col1:
		for i in range(3):
			if st.checkbox(words[i], disabled=False, key=i):
				selected_words.append(words[i])
	with col2:
		for i in range(3, 6):
			if st.checkbox(words[i], disabled=False,key = i):
				selected_words.append(words[i])
	with col3:
		#st.write(st.session_state.selectwords1)
		for i in range(6, 9):
			if st.checkbox(words[i], disabled=False, key=i):
				selected_words.append(words[i])

				  
	#st.write(selected_words)
	if st.button("Suggest my interests/hobbies 🪄"):
		if len(selected_words) < 3:
			st.error("Please select 3 words before clicking Next")
		elif len(selected_words) > 3:
			st.error("Please select not more than 3 words before clicking Next")
		else:
			return selected_words


def match_numbers_to_words(num_list, db_file): #select a associative word of the selected interest
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()

	cursor.execute("SELECT * FROM interest_wizard")
	result = cursor.fetchall()
	list_of_lists = [list(i) for i in result]
	#st.write(list_of_lists)

	word_list = []
	for i in num_list:
		random_index = random.randint(2, 6)
		word_list.append(list_of_lists[i][random_index])

	#st.write(word_list)

	# word_list = []
	# for num in num_list:
	# 	# cursor.execute("SELECT word1, word2, word3, word4, word5 FROM interest_wizard WHERE id = ?", (num,))
	# 	# words = cursor.fetchone()
	# 	cursor.execute("SELECT * FROM interest_wizard WHERE id = ?", (num,))
	# 	row = cursor.fetchone()
	# 	st.write(row)
	# 	if row = None:
	# 		cursor.execute("SELECT * FROM interest_wizard WHERE id = ?", (num+1,))
	# 		row = cursor.fetchone()
	# 	#words = (row[1], row[2], row[3], row[4], row[5])
	# 	random_index = random.randint(1, 5)
	# 	word_list.append(row[random_index])
	# 	#st.write(words)
	# 	#word_list.append(random.choice(words))
		
	conn.close()

	return word_list

def match_words_to_resources(words_list, db_file): #the associative word is match back to the interest and return a list of interests
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()
	interest_search = []
	no_match = []
	for word in words_list:
		cursor.execute("SELECT Interests FROM interest_wizard WHERE word1=? OR word2=? OR word3=? OR word4=? OR word5=?", (word, word, word, word, word))
		result = cursor.fetchone()
		if result:
			interest_search.append(result[0])
		else:
			no_match.append([word,"NO_MATCH"])

	conn.close()
	return interest_search

#GENERATE THE PERSONALISED INTERESTS AND HOBBY LINKS ------------------------------------------------------------------------


def extract_student_info(int_list): #overall function that takes in the int list to display all the information in a nicely tab area for students to keep track of their hobbies and interests
	st.subheader("Your current interest links")
	if st.session_state.treasure_key == None or len(int_list) == 0:
		st.warning("Please access the InteresThing tools by clicking the options in the sidebar to generate your links")
	elif st.session_state.treasure_key != None:
		int_list = st.session_state.treasure_key
		topic_list = interests_to_topic(int_list, db_file)
		tabs_list, tabs_info, tabs_image, tabs_quotes = get_topic_and_links(topic_list)
		#create_tabs(tabs_list, tabs_info)
		create_tabs_with_images(tabs_list, tabs_info, tabs_image, tabs_quotes)



def interests_to_topic(interest_search, db_file): #extract all the relevant information from the SQL table in alphabetical order
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()
	cursor.execute("SELECT Interests, Title, Link, Images, Quotes FROM interest_links WHERE Interests IN ({})".format(','.join('?'*len(interest_search))), interest_search)
	result = cursor.fetchall()
	resource_output_link = [i for i in result]

	# resource_output_link = []
	# for interest in interest_search:
	#     cursor.execute("SELECT Interests, Title, Link, Images, Quotes FROM interest_links WHERE Interests = ?", (interest,))
	#     result = cursor.fetchone()
	#     st.write("result", result)
	#     resource_output_link.append(result)

	# conn.close()
	return resource_output_link


def get_topic_and_links(resource_output_link): #putting the word and links into hyper links
	title_list = []
	overall_topic_list = []
	image_list = []
	quote_list = []
	topic_list = []
	current_topic = ""

	for i in range(len(resource_output_link)):
		#word, status, link = resource_output_link[i]
		#st.write(resource_output_link[i])
		word, status, link, image, quote = resource_output_link[i]
		if word != current_topic:
			current_topic = word
			if topic_list != []:
				overall_topic_list.append(topic_list)
				topic_list = []
			topic_list.append(f'[{status}]({link})')
			title_list.append(word)
			image_list.append(image)
			quote_list.append(quote)
		else:
			topic_list.append(f'[{status}]({link})')
	
	overall_topic_list.append(topic_list)
	#st.write(overall_topic_list)
	#st.write(title_list)

	return title_list, overall_topic_list, image_list, quote_list



#create tabs for each hobbies
def create_tabs_with_images(tabs_list, tabs_info, tabs_image, tabs_quotes):
	tabs_names = st.tabs(tabs_list)
	#st.write("Tab list", tabs_list)
	#st.write("Tabs info", tabs_info)	
	for (i,j, k,m, n) in zip(tabs_names, tabs_list, tabs_info, tabs_image, tabs_quotes):
		with i:
			st.image(m, width=350, caption=n) #to remove
			st.write("For hobbies/interests in ", j) #to remove static
			likes = show_likes(j, db_file)
			#st.write(f":blue[Likes 👍 {likes}]")
			#st.write('#')
			st.write("Click on the following links:")
			for l in k:
				st.markdown(l,unsafe_allow_html=True)
			button1 = st.empty()
			if button1.button(f"Likes 👍 {likes}", key=j):
				#st.write("👍 1234")
				update_likes(j, db_file)
				button1.empty()




#QUIZ DISCOVERY TOOLS -----------------------------------------------------------------------------------------------------------------------------


def query_to_list(db_file):
	con = sqlite3.connect(db_file)
	df = pd.read_sql_query("SELECT * FROM quiz_qns", con)
	con.close()
	return [list(i) for i in df.to_numpy()]




def match_mbti_to_resources(p_code, db_file):
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()

	 # Define the query
	query = f"SELECT Interests FROM quiz_profiles WHERE MBTI1 = '{p_code}' OR MBTI2 = '{p_code}' OR MBTI3 = '{p_code}' OR MBTI4 = '{p_code}' OR MBTI5 = '{p_code}'"

	# Execute the query
	cursor.execute(query)

	# Fetch the results
	results = cursor.fetchall()
	
	#create an empty list
	interest_search = []
	# Iterate through the results and add each interest to the interests list
	for result in results:
		interest_search.append(result[0])

	conn.close()

	return interest_search




#INTERESTS like table ---------------------------------------------------------------------------------------------------------------------------


def extract_likes_show_interests(db_file):
	# # Show users table 
	colms = st.columns((0.1, 0.5, 0.2, 1))
	fields = ["ID", 'Interests', 'Number of likes', 'Add to collection']
	for col, field_name in zip(colms, fields):
		# header
		col.write(f":blue[{field_name}]")

	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	
	#query the top 5 likes
	c.execute("SELECT interests, likes FROM interests_likes ORDER BY likes DESC LIMIT 5")
	result = c.fetchall()
	
	#create a dictionary to store the result
	interests_likes = {}
	for row in result:
		interests_likes[row[0]] = row[1]
	
	#close the connection
	conn.close()
	
	#st.write(interests_likes)
	if 'add_key' not in st.session_state:
		st.session_state.add_key = None
	

	st.session_state.add_key = []

	for i in range(len(interests_likes)): #display in a 5 x 4 table of the top likes and people check and update their key
		
		key, value = list(interests_likes.items())[i]
		col1, col2, col3, col4 = st.columns((0.1, 0.5, 0.2, 1))
		col1.write(i)  # index
		col2.write(key)  # email
		col3.write(value)  # unique ID
		if col4.checkbox('Add to my links', key=key+str(i)):
			st.session_state.add_key.append(key)
			update_interest(db_file)




def show_likes(interest, db_file): #Show the number of likes for each interest
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()
	#st.write(interest)
	cursor.execute("SELECT likes FROM interests_likes WHERE interests = ?", (interest,))
	#cursor.execute("SELECT likes FROM interests_likes where interests == "Environment"")
	result = cursor.fetchone()
	#st.write(result)

	conn.close()
	return result[0]



def update_likes(interest, db_file):
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	c.execute("SELECT likes FROM interests_likes WHERE interests=?", (interest,))
	result = c.fetchone()
	if result:
		likes = result[0] + 1
		c.execute("UPDATE interests_likes SET likes=? WHERE interests=?", (likes, interest))
		conn.commit()
		st.success("{} liked! 👍".format(interest))
	else:
		st.error("Interest not found in the table.")
	conn.close()

#GENERAL testing function -------------------------------------------------------------------------------------------------------------------------




def check_table_exists(table_name,db_file): #not in use but useful for testing fucntions
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format(table_name))
	if c.fetchone() is None:
		st.write("Table not found")
		return False

	else:
		st.write("Table found")
		return True
	conn.close()



#ADDING and REMOVING my list of interests -----------------------------------------------------------------------------------------
def suggested_hobbies(words_list, type_tool):
	hobbies = ", ".join(words_list)
	st.write(f":blue[These are the suggested hobbies from the {type_tool}: {hobbies} ]")

def combine(word_list): #not in use - previous version
	st.write(':red[Please select the suggested interests/hobbies to add to your list]')
	options = st.multiselect("Suggested interests/hobbies",word_list,word_list, label_visibility='collapsed')
	if len(options) == 0:
		st.write("You did not select any interests/hobbies")
	#st.write("#")
	if st.button("Add to my list"):
		#st.write("new list", word_list)
		#st.write("old list", st.session_state.treasure_key)
		new_list = update_list(options, st.session_state.treasure_key)
		st.session_state.treasure_key  = remove_duplicates(new_list)
		#st.write("updated list", st.session_state.treasure_key)
		update_interest(db_file)

def edit_my_list(word_list):
	st.write(f'This is the combine list of old and new interests/hobbies, please choose {num_hobbies} you wish to keep')
	options = st.multiselect("Suggested interests/hobbies",word_list,word_list, label_visibility='collapsed')
	if len(options) == 0:
		st.error("You did not select any interests/hobbies")
	elif len(options) > num_hobbies:
		st.error(f"More than {num_hobbies} interests/hobbies selected, please remove some")
	#st.write("#")
	if st.button("Update my list"):
		st.session_state.treasure_key  = remove_duplicates(options)
		update_interest(db_file)


def update_list(new_list, old_list): #part of extract like show interests function not in use
	# check if old list plus new list is more than 7
	
	if old_list == None: 
		new_list
	elif len(old_list) + len(new_list) > 7:
		new_list = new_list + old_list
		del new_list[8:]
	else:
		new_list = new_list + old_list
	return new_list



def update_int_list(db_file, table_name, stu_code, int_list_value):
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	c.execute("UPDATE {} SET int_list = ? WHERE stu_code = ?".format(table_name), (int_list_value, stu_code))
	conn.commit()
	conn.close()

def update_interest(db_file):
	if st.session_state.login_key:
		int_json = json.dumps(st.session_state.treasure_key)
		update_int_list(db_file, st.session_state.school_key, st.session_state.stu_key , int_json)


def remove_duplicates(input_list):
	output_list = []
	for item in input_list:
		if item not in output_list:
			output_list.append(item)
	return output_list



#AUthentication function -------------------------------------------------------------------------------------------------


def check_student_code_return_int_list(school_code, student_code, db_file):
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()

	school_code = school_code.lower()
	student_code = student_code.lower()

	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format(school_code))
	if cursor.fetchone() is None:
		st.error("School Code not found")
		return False

	#st.write(school_code)
	#st.write(student_code)
	
	cursor.execute("SELECT int_list FROM {} WHERE stu_code = ?".format(school_code), (student_code,))
	result = cursor.fetchone()
	cursor.close()
	conn.close()
	if result:
		result = result[0]
		if result == "":
			return result
		else:
			result = json.loads(result)
		return result
	else:
		st.error("Student Code not found")
		return False

#InteresThing Assistant-------------------------------------------------------------------------------------------------

def display_helping_words(fields):
	colms = st.columns((0.2, 0.2, 0.2, 0.2, 0.2, 0.2))
	for col, field_name in zip(colms, fields):
		# header
		col.write(f":blue[{field_name}]")

def display_interests(matching_words, db_file):
	if st.session_state.treasure_key == None or len(int_list) == 0:
		st.write("Please start the virtual assistant to generate a list")
	elif st.session_state.treasure_key != None:
		int_list = st.session_state.treasure_key
		topic_list = interests_to_topic(int_list, db_file)
		tabs_list, tabs_info, tabs_image, tabs_quotes = get_topic_and_links(topic_list)
	#search resource link
	#return the list of interests
	pass

def generate_promptv1(word_list1, word_list2, word_list3, word_list4, word_list5):
	prompt = "I am looking for a "
	if len(word_list1) > 1:
		prompt += " or ".join(word_list1) + " "
	else:
		prompt += word_list1[0] + " "
	prompt += "which is "
	if len(word_list2) > 1:
		prompt += " or ".join(word_list2) + " , "
	else:
		prompt += word_list2[0] + " , "
	if len(word_list3) > 1:
		prompt += " or ".join(word_list3) + " , "
	else:
		prompt += word_list3[0] + " , "
	if len(word_list4) > 1:
		prompt += " or ".join(word_list4) + " and "
	else:
		prompt += word_list4[0] + " and "
	if len(word_list5) > 1:
		prompt += " or ".join(word_list5)
	else:
		prompt += word_list5[0]
	return prompt


import streamlit as st

def generate_prompt(wordlist1, wordlist2, wordlist3, wordlist4, wordlist5):
	prompt = "I am looking for a "

	# Handling wordlist1
	if len(wordlist1) == 2:
		prompt += wordlist1[0] + " or " + wordlist1[1] + " "
	else:
		prompt += wordlist1[0] + " "

	prompt += " which is "

	# Handling wordlist2 to wordlist5
	wordlists = [wordlist2, wordlist3, wordlist4, wordlist5]

	for i, wordlist in enumerate(wordlists):
		if len(wordlist) == 0:
			pass
		else:
			if len(wordlist) == 2:
				prompt += wordlist[0] + " or " + wordlist[1]
			elif len(wordlist) == 1:
				prompt += wordlist[0]
			
			if i == 5:
				prompt += ". "

			elif i < 3:
				prompt += ", "



	st.write(prompt)
	return prompt





def select_words_assistant(words): #function here is slightly slow so have to rework how to make this faster in v2, 
	#Wizard discovery tool

	st.write(":blue[Please select the words to start the conversation]")
	st.write(":blue[Choose at least one word in column 1 and choose at least one word in column 2 to 5]")
	#st.write("Click the Next ➡️ button when you have checked the boxes")
	#st.write("#")

	selected_words1 = []
	selected_words2 = []
	selected_words3 = []
	selected_words4 = []
	selected_words5 = []
	final_list = []

	col1, col2, col3, col4, col5 = st.columns((0.3,0.3,0.3,0.3,0.3))
	#st.write('select_words function')

	with col1:
		st.write(":red[Indoor or Outdoor]")
		for i in range(2):
			if st.checkbox(words[i], disabled=False, key=i):
				selected_words1.append(words[i])
	with col2:
		st.write(":red[Easy or Challenging]")
		for i in range(2, 4):
			if st.checkbox(words[i], disabled=False,key = i):
				selected_words2.append(words[i])
	with col3:
		st.write(":red[Intellectual or Physical]")
		#st.write(st.session_state.selectwords1)
		for i in range(4, 6):
			if st.checkbox(words[i], disabled=False,key = i):
				selected_words3.append(words[i])
	with col4:
		st.write(":red[Alone or Group]")
		#st.write(st.session_state.selectwords1)
		for i in range(6,8):
			if st.checkbox(words[i], disabled=False,key = i):
				selected_words4.append(words[i])

	with col5:
		st.write(":red[Interests or Skills]")
		#st.write(st.session_state.selectwords1)
		for i in range(8, 10):
			if st.checkbox(words[i], disabled=False,key = i):
				selected_words5.append(words[i])

	if len(selected_words1) < 1:
		st.error("Please select at least one word from the first column")
	elif len(selected_words2 + selected_words3 + selected_words4+ selected_words5) < 1:
		st.error("Please select at least one word from second to fifth columns")
	else:
		final_list = generate_prompt(selected_words1, selected_words2, selected_words3, selected_words4, selected_words5)

	#st.write(selected_words)
	if st.button("Start my conversation!"):
		#st.write(final_list)
		return final_list

def get_text():
	input_text = st.text_input("You:")
	return input_text 


def chat_bot(prompt,db_file):

	if 'api_key' not in st.session_state:
		st.session_state.api_key = st.secrets["api_key"]
		openai.api_key = st.session_state.api_key

	if 'generated' not in st.session_state:
		st.session_state['generated'] = []

	if 'past' not in st.session_state:
		st.session_state['past'] = []

	user_input = st.text_input("You:", prompt)

	if user_input:

		try:

			response = openai.Completion.create(engine="text-davinci-003", prompt=user_input, temperature=0.5, max_tokens=1000)

			# display the generated text
			# st.write("Generated Text:")	

			st.session_state.past.append(user_input)
			st.session_state.generated.append(response["choices"][0]["text"])
			#vta_code = st.session_state.vta_code 
			question = user_input
			answer = response["choices"][0]["text"]
			answer = answer.strip()
			answer = ''.join(answer.splitlines())
			question = question.strip()
			question = ''.join(question.splitlines())
			error = ""

			# if type(output)==str:
			# 	message(output)
			# else:
			# 	message(“the result is”)
			# 	st.columns((1,10))
			# 	cols[1].write(output)

		except openai.exceptions.ApiError as e:
			# Handle the error
			#worksheet.append_table(values=[[user_input, "APIError", f"ApiError: {e}"]])
			error = f"ApiError: {e}"
			st.write(e)

		except openai.exceptions.AuthError as e:
			# Handle the error
			#worksheet.append_table(values=[[user_input, "AuthError", f"AuthError: {e}"]])
			error = f"AuthError: {e}"
			st.write(e)
			

	if st.session_state['generated']:

		for i in range(len(st.session_state['generated'])-1, -1, -1):
			#st.write(str(i))
			#st.write(str(i) + '_user' )
			message(st.session_state["generated"][i], key=str(i)+'_gpt' )
			message(st.session_state['past'][i], is_user=True, avatar_style="adventurer", seed=101, key=str(i) + '_user')

#Community page ---------------------------------------------------------------------------------------------------------------------------

def main():
	st.sidebar.image('images/cotf_logo.png', width=300)
	st.title(":red[InteresThing]")
	#menu = ["InteresThing Homepage 🏠", "InteresThing Wizard 🧙", "InteresThing Quiz 📝", "InteresThing Assistant 👨‍💻️", "InteresThing Treasury 🏛️"]
	selected_menu = st.sidebar.selectbox("Select an option", menu)

	#Session declarations

	if 'word_key' not in st.session_state:
		st.session_state.word_key = None
	if 'quiz_key' not in st.session_state:
		st.session_state.quiz_key = None
	if 'treasure_key' not in st.session_state:
		st.session_state.treasure_key = None
	if 'option_key' not in st.session_state:
		st.session_state.option_key = None
	if 'login_key' not in st.session_state:
		st.session_state.login_key = False
	if 'stu_key' not in st.session_state:
		st.session_state.stu_key = None
	if 'school_key' not in st.session_state:
		st.session_state.school_key = None
	if 'chat_key' not in st.session_state:
		st.session_state.chat_key = None
	if 'admin_key' not in st.session_state:
		st.session_state.admin_key = None
	


	placeholder1 = st.sidebar.empty()
	if st.session_state.login_key != True:
		with streamlit_analytics.track():
			with placeholder1.form(key="authenticate"):
				st.write("Please key in your school and student code to record your discovery")
				school_code = st.text_input('School code:')
				student_code = st.text_input('Student code:')
				submit_button = st.form_submit_button(label='Login')
				if submit_button:
					if school_code == "admin101" and student_code == "joe":
						st.session_state.admin_key = True
					int_list = check_student_code_return_int_list(school_code, student_code, db_file)
					st.write(int_list)
					if int_list != False:
						if st.session_state.treasure_key == None:
							if int_list == "":
								st.session_state.treasure_key = []
							elif len(int_list) > 0:
								st.session_state.treasure_key = int_list
						else:
							int_json = json.dumps(st.session_state.treasure_key)
							update_int_list(db_file, school_code.lower(), student_code.lower(), int_json)
						st.session_state.stu_key = student_code.lower()
						st.session_state.school_key = school_code.lower()
						#st.write("here")
						st.session_state.login_key = True
						insert_student_data(st.session_state.school_key, st.session_state.stu_key , HOME, db_file)


	if st.session_state.login_key != True:
		st.sidebar.warning("You are not logged in, all your information on this website will not be recorded. Please click on the Homepage 🏠 to login")
	if st.session_state.login_key == True:
		placeholder1.empty()

	if st.session_state.admin_key== True:
		admin = st.sidebar.button("Download CSV Data")
		if admin:
			download_student_data()

	logout = st.sidebar.button("Logout")
	if logout:
		for key in st.session_state.keys():
			del st.session_state[key]
		st.experimental_rerun() 

	if selected_menu == "InteresThing Homepage 🏠":
		st.subheader(":blue[InteresThing Homepage 🏠]")
		st.write("#")
		st.image("images/InteresThing.jpeg", width=500)
		st.subheader("Do more of what makes you happy")
		st.write("##")
		st.write("**:blue[To start, click on the sidebar to log in and navigate the application]**")
		st.write("**:orange[For mobile device users, click on the upper left '>' arrow to access the sidebar]**")

		if st.session_state.login_key == True:
			#placeholder1.empty()
			pass

		# if st.session_state.login_key != True:
		# 	st.sidebar.warning("You are not login, all your information on this website will not be recorded. Please click on the Discovery Homepage 🏠 to login")
		st.write("#")
		int_list = st.session_state.treasure_key
		extract_student_info(int_list)



	if selected_menu == "InteresThing Wizard 🧙":
		with streamlit_analytics.track():
			st.subheader(":blue[InteresThing Wizard] 🧙")
			#st.image('images/cauldron.png')
			restart = st.sidebar.button("Generate new words 🧙")
			if restart:
				st.session_state.word_key = None

			#st.write("This feature allows you to discover interests based on a set of questions.")
			placeholder1 = st.empty()
			if st.session_state.word_key == None:
				if placeholder1.button("Show me the magic words! 🧞"):
					number_lists = random_numbers()
					#placeholder1.write(number_lists)
					word_lists = match_numbers_to_words(number_lists, db_file)
					#placeholder1.write(word_lists)
					st.session_state.word_key = word_lists
					#st.write(word_lists)
					placeholder1.empty()
			if st.session_state.word_key != None:
				word_lists = st.session_state.word_key
				#options = st.multiselect('Choose 3 to 5 words that attracts you', word_lists)
				#st.write(st.session_state.word_key)
				options = select_words(st.session_state.word_key)
				insert_student_data(st.session_state.school_key, st.session_state.stu_key , WIZARD, db_file)
				#st.session_state.word_key = options
				if options != None:
					st.session_state.option_key = options
					
					#st.session_state.treasure_key = int_list
					#st.write(":orange[Click on InteresThing Treasury Tabs below to see your suggested interests!]")
					int_list = match_words_to_resources(options, db_file)
					#combine(int_list) v1
					suggested_hobbies(int_list, "Wizard Discovery Tool")
					st.write('#')
					if st.session_state.treasure_key == None:
						st.session_state.treasure_key = []
					edit_my_list(int_list + st.session_state.treasure_key)
					st.write('#')
					extract_student_info(st.session_state.treasure_key)
				elif st.session_state.option_key != None:
					int_list = match_words_to_resources(st.session_state.option_key, db_file)
					
					suggested_hobbies(int_list, "Wizard Discovery Tool")
					st.write('#')
					if st.session_state.treasure_key == None:
						st.session_state.treasure_key = []
					edit_my_list(int_list + st.session_state.treasure_key)
					st.write('#')
					extract_student_info(st.session_state.treasure_key)
			else:
				extract_student_info(st.session_state.treasure_key)



	elif selected_menu == "InteresThing Quiz 📝":
		st.subheader("InteresThing Quiz 📝")
		#st.write("This feature allows you to discover interests using a questionaire.")

		#quiz 
		progress_bar = st.sidebar.progress(0)
		status_text = st.sidebar.empty() 

		with streamlit_analytics.track():

			int_list = None
			quiz_list = query_to_list(db_file)
			with st.form(key="int_quiz"):
				st.write(":blue[Please choose the statement that you agree with by moving the dot on the slider to right or left]")
				st.write("##")
				a_list = reveal_questions(quiz_list)
				ans_list = a_list[0]
				submit_button = st.form_submit_button(label='Submit')
				if submit_button and a_list[1] == False:
					pc = personality_generator(ans_list)
					#st.write(pc)

					for i in range(1, 101):

						status_text.write("%i%% Processing" % i)
						progress_bar.progress(i)
						time.sleep(0.03)

					status_text.write("Assessing complete!")
					submit_flag = True   
					progress_bar.empty()
					int_list = match_mbti_to_resources(pc, db_file)
					st.session_state.quiz_key = int_list
					#st.write(int_list)
					insert_student_data(st.session_state.school_key, st.session_state.stu_key , QUIZ, db_file)
				elif submit_button and a_list[1] == True:
					st.warning('You have to make a choice for all statements to generate your report', icon="⚠️")
			if st.session_state.quiz_key != None:
				#st.write(":orange[Click on InteresThing Treasury Tabs below to see your suggested interests!]")
				#st.session_state.treasure_key = int_list #The last quiz
				suggested_hobbies(st.session_state.quiz_key, "Quiz Discovery Tool")
				st.write('#')
				if st.session_state.treasure_key == None:
					st.session_state.treasure_key = []
				edit_my_list(st.session_state.quiz_key + st.session_state.treasure_key)
				st.write('#')
				#int_list = match_words_to_resources(st.session_state.option_key, db_file)
				extract_student_info(st.session_state.treasure_key)
			else:
				extract_student_info(st.session_state.treasure_key)
			# elif st.session_state.treasure_key != None:
			# 	st.write('#')
			# 	#int_list = match_words_to_resources(st.session_state.option_key, db_file)
			# 	combine(int_list)
			# 	st.write('#')
			# 	extract_student_info(st.session_state.treasure_key)
	elif selected_menu == "InteresThing Commmunity":
		with streamlit_analytics.track():
			if st.session_state.login_key != True:
				st.write("You need to login to access this feature")
			else:
				st.subheader("InterestThing Commmunity")
				st_disqus("phss-1", title="PHSS InteresThing Commmunity Forum")


	elif selected_menu == "InteresThing Assistant 👨‍💻️":
		st.subheader("InterestThing Assistant")
		st.write("Feature to be released soon")
		#st.write("This feature allows you to discover interests through a conversation with an assistant")
		#insert_student_data(st.session_state.school_key, st.session_state.stu_key , CHAT, db_file)
		# test_words = ["Hobby", "Skill", "Indoor", "Outdoor", "Challenging", "Simple", "Intellectual", "Physical", "Alone", "Group" ]
		# restart = st.sidebar.button("Restart conversation")
		# if restart:
		# 	st.session_state.chat_key = None
		# 	st.session_state['generated'] = []
		# 	st.session_state['past'] = []
		# if st.session_state.treasure_key == None:
		# 	st.session_state.treasure_key = []
		# if st.session_state.login_key != True:
		# 	st.write("You need to login to access this feature")
		# elif st.session_state.login_key == True:
		# 	#st.write(":blue[Welcome to the InteresThing Smart Assistant]")
		# 	st.write("#")
		# 	#st.write(":blue[To begin, please select at least 3 key words or phrases]")
		# 	placeholder2 = st.empty()
		# 	with placeholder2.container():
		# 		prompt = select_words(test_words)
		# 		if prompt == None:
		# 			prompt = ""
		# 		else:
		# 			st.session_state.chat_key = prompt
					
		# 	if st.session_state.chat_key != None:
		# 		placeholder2.empty()		
		# 		chat_bot(st.session_state.chat_key,db_file)

	elif selected_menu == "InteresThing Treasury 🏛️":
		st.subheader("InterestThing Treasury")
		st.write("#")
		#st.write("Click on the start button to draw 3 random interests")
		with streamlit_analytics.track():
			extract_likes_show_interests(db_file)
			insert_student_data(st.session_state.school_key, st.session_state.stu_key , TREASURE, db_file)
			#st.write("Feature to be released soon")
			st.write('##')
			if st.session_state.add_key != None and st.session_state.treasure_key != None:
				edit_my_list(st.session_state.add_key + st.session_state.treasure_key)
			extract_student_info(st.session_state.treasure_key)



if __name__ == "__main__":
	main()