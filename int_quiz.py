import streamlit as st

U = '⬅️ Choose ➡️'


def reveal_questions(question_list):
	ans_pair = []
	val = 0
	answer_list = []
	undecided = True
	for i in question_list:
		ans = st.select_slider( 'q', options=[i[1], U, i[2]], value=U, key=i[0], label_visibility="hidden")
		if ans == i[1]:
			val = 1
			undecided = False
		elif ans == U:
			val = 3
			undecided = True
		elif ans == i[2]:
			val = 5
			undecided = False
		
		answer_list.append(val)
		
	return answer_list, undecided


def personality_generator(ans_list):

	#Open Extended Jungian Type Scales 1.2


	A  = 30 - ans_list[2] - ans_list[6] - ans_list[10] +  ans_list[14] - ans_list[18] + ans_list[22] + ans_list[26] - ans_list[30]
	B  = 12 + ans_list[3] + ans_list[7] + ans_list[11] +  ans_list[15] + ans_list[19] - ans_list[23] - ans_list[27] + ans_list[31]
	C  = 30 - ans_list[1] + ans_list[5] + ans_list[9] -  ans_list[13] - ans_list[17] + ans_list[21] - ans_list[25] - ans_list[29]
	D  = 18 + ans_list[0] + ans_list[4] - ans_list[8] +  ans_list[12] - ans_list[16] + ans_list[20] - ans_list[24] + ans_list[28]

	if A > 24:
		A = 'E'
	else:
		A = 'I'

	if B > 24:
		B = 'N'
	else:
		B = 'S'

	if C > 24:
		C = 'T'
	else:
		C = 'F'

	if D > 24:
		D = 'P'
	else:
		D = 'J'

	personality_code = A + B + C + D    

	return personality_code
