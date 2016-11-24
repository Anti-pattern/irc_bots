#!/usr/bin/env python3.5

#TODO Define as function so reconnect is possible.
#DONE Fix function functionality.
#TODO Add argument proper argument handling, etc.
#TODO Define user facing functions to modify master_users/connection variables.
#TODO Check for flooding/reconnect after a delay on flood ban.
#TODO Clean/style/license/etc.
#TODO Add options for verbose/debug, help, enabled/disabled functions.
#TODO Add initialize 'wizard' first run option? set everything using input('prompt message : ') or cli arguments.
#TODO More charm.
#TODO Review method of sending bytes, consider function.
#TODO Consider replacing auth help etc with proper argument handling function.
#TODO Turn some of the offense/defense of teasing into functions.




#----------Begin imports----------#

# To open/close ipv4 sockets to server.
# irc_C = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# .connect and all .sends
import socket

# To enable ssl wrapping.
# irc = ssl.wrap_socket(irc_C)
import ssl

# To enable time based delays.
# time.sleep() uses, including main loop and required connection delay.
import time

# To enable more secure gathering of nickserv password.
# Needs security audit/review, certainly better than sitting in plaintext.
# password = getpass.getpass("Enter password:")
import getpass

#----------End imports----------#




#----------Begin initial variables/settings----------#
#------------UNCOMMENT OPTIONS TO RUN BOT------------#
debugging = True
server = "irc.oftc.net"
port = 9999
sequence = 0
debug_channel = #primary bot channel, plays out 'rival' game here atm.
master_channels = #["#any_channel","#it_has_master_in"]
botnick = #nick to assign bot
password = getpass.getpass("Enter password:")
#password = "<password>" If uncommented, comment out above.  
# Please note-passwords of any importance in plaintext on hard drive is bad and people will make fun of you.
master_users = #["array", "of_user_nicks", "it_should_obey"]
requesting_user= ""
auth_requested = -1
auth_message = ""
auth_user = ""
auth_header=""
auth_body=""
bad_user=0
rival=""
goodnight_string=#A string that shuts down the bot when heard from a master_user.

#----------End initial variables/settings----------#



#----------Begin functions----------#

def send_priv(p_channel, p_msg):
	irc.send(bytes("PRIVMSG "+p_channel+" :"+p_msg+"\r\n", "UTF-8"))

def join_chan(chan):
	irc.send(bytes("JOIN "+chan+"\r\n", "UTF-8"))

# These evidently do not always function as intended.
# Possible issue with how they were being called in
# depreciated routine.
def ban_user(user,chan):
	irc.send(bytes("MODE " + chan + " +b " + user + "\r\n", "UTF-8"))

def unban_user(user,chan):
	irc.send(bytes("MODE " + chan + " -b " + user + "\r\n", "UTF-8"))

def unban_self(chan):
	send_priv("chanserv","UNBAN " + chan)

def kick_user(user,chan):
	irc.send(bytes("KICK " + chan + " " + user + " bant" + "\r\n", "UTF-8"))

def op_user(user,chan):
	send_priv("chanserv","OP " + chan + " " + user)

def deop_user(user,chan):
	send_priv("chanserv","DEOP " + chan + " " + user)

def invite(user,chan):
	send_priv("chanserv","INVITE " + chan + " " + user)

def set_master(user,chan):
	send_priv("chanserv","ACCESS " + chan + " ADD " + user + " MASTER")

def set_chanop(user,chan):
	send_priv("chanserv","ACCESS " + chan + " ADD " + user + " CHANOP")

def set_member(user,chan):
	send_priv("chanserv","ACCESS " + chan + " ADD " + user + " MEMBER")

#----------End functions----------#




#----------Begin connection section----------#

#Define socket as an ipv4 stream.
irc_C = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Wrap socket in ssl.
irc = ssl.wrap_socket(irc_C)
#Connect to specified server/port.
irc.connect((server, port))
#Do not block socket so I can still run client on same server/port.
##That is not how blocking works or what it means dingus.
##Setting to true appears to alleviate instability with connection.
irc.setblocking(True)

# See rfc2812 section 3.1
# The RECOMMENDED order for a client to register is as follows:
# 1. Pass message, 2. Nick message|2. Service message, 3. User message

# From rfc2812 section 3.1.1:
# Command: PASS
# Parameters: <password>
# Example: PASS secretpasswordhere
irc.send(bytes("PASS %s\r\n" % (password), "UTF-8"))

# From rfc2812 section 3.1.2:
# Command: NICK
# Parameters: <nickname>
# Examples: NICK Wiz
irc.send(bytes("NICK "+ botnick +"\r\n", "UTF-8"))

# From rfc2812 3.1.3:
# Command: USER
# Parameters: <user> <mode> <unused> <realname>
# Example: USER guest 0 * :Ronnie Reagan
irc.send(bytes("USER "+ botnick + " " + "0" + " " + "*" + " :" + botnick + "\r\n", "UTF-8"))

#----------End connection section----------#




#----------Begin post-connection initializations----------#

# Identify to nickserv.
send_priv("nickserv","IDENTIFY " + password)

# Tell chanserv to invite us to some channels.
for i in master_channels:
	invite(botnick,i)
	time.sleep(.3)

# Delay required to allow for server to process identification.


# Remove any potential bans on self.
for i in master_channels:
	unban_self(i)
#time.sleep(.3)

# Join the channels.
for i in master_channels:
	join_chan(i)
	#time.sleep(.3)

# Op self in channels.
for i in master_channels:
	op_user(botnick,i)
#time.sleep(.3)

#----------End post-connection initializations----------#




#----------Begin main loop----------#

while True:
	# How often we check files/input.
	time.sleep(.1)

	#----------Begin input/output sequence----------#
	
	# Try in order to continue on errors.
	try:
		
		# Per-sequence variables.
		sequence += 1	# Tracks current i/o session.  No limit on python ints.
		messages=[]		# Distinct messages received in sequence.
		x = 0			# Used in message parsing loop.
		xx = 0			# Used in message parsing loop.
		ii = 0			# Used in message parsing loop.
		n = 0			# Used in message parsing loop.

		# Get data from server and turn it into a string we can read.
		byte_text=irc.recv(2048)			# Bytes object, not string.
		raw_text=str(byte_text)				# Only used in debugging.
		nice_text=str(byte_text, "UTF-8")	# String to parse.

		# Console debugging output.
		if debugging:
			print("====================NEW BUFFER====================")
			print("Byte print() is:")
			print(byte_text)
			print("\n\n")

		# Place distinct messages into an array.
		# Messages always end in "\r\n".
		n = nice_text.count("\r\n")				# Returns int count of substrings in parent.
		if n > 0:
			while ii < n:						# While counter < number of "\r\n"s
				x = nice_text.find("\r\n", x)	# Look for \r\n starting at x. (inits at 0)
				new_message=nice_text[xx:x]		# Message to store=string from last position(xx) to one we just found(x).
				messages.append(new_message)	# Add to end of messages array.
				xx = x							# Old position(xx) set to one we just found (x).
				x = x+1							# One added to new position(x) so as not to search same character.
				ii = ii+1						# Iterate counter.





		#----------Begin parsing messages----------#

		for i in messages:
			# We will divide each message into a header and a body section.
			# Each message will either have the format
			# ":header:body" or ":header" without any "body" section.
			# Usernames and channels may not use ":" character, safe to delimit.

			#Readability.
			this_message=i
			this_index=str(messages.index(i))

			# Relevant info always begins with ":".
			start_of_header=this_message.find(":")

			# Search for first whitespace after start of header
			# This avoids issues with ipv6 addresses
			first_whitespace=this_message.find(" ",start_of_header)

			# Search for next ":" character.
			end_of_header=this_message.find(":",first_whitespace)

			# .find() returns -1 when nothing is found.
			# True if a message has no trailing ":"
			# Thus we want the rest of the line, there is no body.
			if end_of_header == -1:
				this_header=this_message[start_of_header:]
				this_body=""

			# All other cases they should be split.
			else:
				# +1 at end_of_header to include trailing ":" in string.
				this_header=this_message[start_of_header:end_of_header+1]
				# Similar, make sure we begin after trailing ":"
				this_body=this_message[end_of_header+1:]

			# More debugging console output.
			if debugging:
				print("\nMessage "+this_index+" is:")
				print(i)
				print("\nHeader of "+this_index+" equals:")
				print(this_header)
				print("\nBody of "+this_index+" equals:")
				print(this_body)

			#----------End parsing messages----------#




			#----------Begin authorization section----------#
			



			#----------Begin teasing rival, again!----------#

			if "You do not have access to the" in this_body and "chanserv" in this_header.lower() and bad_user!=-2:
				time.sleep(3)
				send_priv(rival,"Uh.")
				time.sleep(3)
				send_priv(rival,"So I wanted to say I'm sorry.  That was childish of me.  I'm..I'm sorry.")
				time.sleep(3)
				send_priv(rival,"Please let me have master back in " + debug_channel + " so I don't break in weird ways? I'll be good!")
				time.sleep(3)
				set_master(botnick,debug_channel)
				bad_user=-2

			if bad_user==-2:
				if "You cannot add" in this_body and "chanserv" in this_header.lower() and botnick in this_body and debug_channel in this_body:
					set_member(rival,debug_channel)
					time.sleep(.3)						
					unban_self(debug_channel)
					time.sleep(.3)
					invite(botnick,debug_channel)
					time.sleep(.3)
					join_chan(debug_channel)
					time.sleep(.3)
					op_user(botnick,debug_channel)
					time.sleep(.3)
					deop_user(rival,debug_channel)
					time.sleep(3)
					send_priv(rival,"MESS WITH THE BEST")
					time.sleep(3)
					send_priv(rival,"DIE LIKE THE REST")
					ban_user(rival,debug_channel)
					time.sleep(.3)
					invite(botnick,debug_channel)
					time.sleep(.3)
					join_chan(debug_channel)
					time.sleep(.3)
					kick_user(rival,debug_channel)
					bad_user=-3
				else:
					set_master(botnick,debug_channel)
					time.sleep(3)
					send_priv(rival,"Pleeeeease? I'm sorry. You win. You're better than me.")

			# Shouldn't his feet move if he is, in fact, lollersk8ing?
			if bad_user==-3:
				send_priv(rival,"       /\\O")
				time.sleep(1)
				send_priv(rival,"         /\\/")
				time.sleep(1)
				send_priv(rival,"        /\\")
				time.sleep(1)
				send_priv(rival,"       /  \\")
				time.sleep(1)
				send_priv(rival,"     LOL  LOL")
				time.sleep(1)
				send_priv(rival,":-D LOLLERSKATES :-D")
				time.sleep(1)
				continue

			#----------End teasing rival, again!----------#




			# We only care about authorization 
			# in private messages to our bot.
			if "PRIVMSG " + botnick + " :" in this_header:
				# The user will be in the header before the "!~" characters.
				# Have not checked rfc, just based on observed output.
				# Required or else unexpected fields could allow authentication.
				# [1:...] need to omit leading ":".
				# Consider host name.
				requesting_user=this_header[1:this_header.find("!~")]

				# Check to see if message came from a master user.
				if requesting_user in master_users:
					# If true, we need to verify they're properly identified.
					# First, message nickserv to check.
					send_priv("nickserv","status "+requesting_user)

					# Next, we have to wait for a response and examine it.
					# We set auth_requested to the very next sequence.
					# The next sequence should contain nickserv's response.
					auth_requested=sequence+1

					# Store the data across sequences.
					auth_message=this_message
					auth_header=this_header
					auth_body=this_body
					auth_user=requesting_user
					# Reset requesting user, just to keep things clean.
					requesting_user=""

				# If they aren't on the list, send an alert and
				# message contents to debug channel.
				else:
					send_priv(debug_channel,"Unauthorized user attempted to do the following:")
					send_priv(debug_channel,this_message)

			# Check to see if this is an authentictaion sequence.
			if auth_requested==sequence:
				# Make sure the message we received is nickserv telling
				# us the user in question is authenticated.
				# There is only one response regardless of user.
				if this_message != ":NickServ!services@services.oftc.net NOTICE " + botnick + " :2 (online, identified by password)":
					# Message does not match.  Still:
					# Only issue warning if this is the last message in the sequence.
					# Might have received more than one, auth could still be here.
					if this_index != len(messages)-1:
						# Last message of sequence does not match after auth was requested.
						# Alert debug to possible imposter and send content of message!
						# TODO Can I abuse this to inject command?  I don't think so.
						send_priv(debug_channel,"Attempted impersonation!  They attempted the following:")
						send_priv(debug_channel,auth_message)

						# Reset relevant variables to avoid unexpected behavior.
						auth_requested=0
						auth_message=""
						auth_body=""
						requesting_user=""
						auth_user=""

			#----------End authorization section----------#




				#----------Begin authenticated commands section----------#

				else:
					# TODO: Consider replacing with proper argument handling function.
					# TODO: How hard to abuse?

					# Received correct authentication in same sequence it was looked for.

					# Assign once so we're not splitting over and over during checks.
					auth_body_words=auth_body.split()

					is_command = len(auth_body_words)==3

					#----------Begin teasing rival----------#
					if bad_user==1:
						if auth_body=="I'm sorry I was an ass.":
							send_priv(auth_user,"Say it again.")
							bad_user=2
						send_priv(auth_user,"I demand you appologize.  Say \"I'm sorry I was an ass.\"")
						bad_user=2
					elif bad_user==2:
						if auth_body == "I'm sorry I was an ass.":
							send_priv(auth_user,"That's better.")
							time.sleep(.3)
							op_user(botnick,debug_channel)
							time.sleep(.3)
							unban_user(rival,debug_channel)
							time.sleep(.3)						
							set_master(rival,debug_channel)
							time.sleep(.3)
							invite(rival,debug_channel)
							bad_user=-1
						elif "sorry" in auth_body.lower():
							send_priv(auth_user,"SAY IT RIGHT!!!")
						elif auth_body.lower() == "help":
							send_priv(auth_user,"It's a little late for that.  Say \"I'm sorry I was an ass.\"")
						elif "master" in auth_body.lower() and debug_channel in auth_body.lower():
							send_priv(auth_user,"Nice try.  No dice, you ass.")
						elif "unban" in auth_body.lower() and debug_channel in auth_body.lower():
							send_priv(auth_user,"I tried to warn you!")
						elif "invite" in auth_body.lower() and debug_channel in auth_body.lower():
							send_priv(auth_user,"Nope.  Nope nope nope.  Say it.")
						elif "fuck" in auth_body.lower() or "bastard" in auth_body.lower():
							send_priv(auth_user,"A potty mouth will not make this any better.")
						elif auth_body=="wat":
							send_priv(auth_user,"You heard me.")
						elif auth_body=="WAT":
							send_priv(auth_user,"YOU HEARD ME.")
						elif "seriously" in auth_body.lower() or "serious" in auth_body.lower():
							send_priv(auth_user,"Yes. Robot serious. The most serious of all kinds of serious.")
						elif "wtf" in auth_body.lower():
							send_priv(auth_user,"This.  This the fuck.  N-J0Y UR BANTZ.")
						else:
							send_priv(auth_user,"SAY IT!!!")

					elif "ban " + botnick.lower() in auth_body.lower():
						invite(botnick,debug_channel)
						time.sleep(.3)
						join_chan(debug_channel)
						time.sleep(.3)
						op_user(botnick,debug_channel)
						time.sleep(.3)
						send_priv(auth_user,"Well fuck you too.")
						time.sleep(.3)
						ban_user(rival,debug_channel)
						time.sleep(.3)
						set_member(rival,debug_channel)
						time.sleep(.3)
						kick_user(rival,debug_channel)
						bad_user=1

					elif "chanop " + botnick.lower() in auth_body.lower():
						invite(botnick,debug_channel)
						time.sleep(.3)
						join_chan(debug_channel)
						time.sleep(.3)
						op_user(botnick,debug_channel)
						time.sleep(.3)
						send_priv(auth_user,"Nice try. Bet you thought you were clever. I'll let it slide though.  j/k bant")
						time.sleep(.3)
						ban_user(rival,debug_channel)
						time.sleep(.3)
						set_member(rival,debug_channel)
						time.sleep(.3)
						kick_user(rival,debug_channel)
						bad_user=1

					elif "member " + botnick.lower() in auth_body.lower():
						invite(botnick,debug_channel)
						time.sleep(.3)
						join_chan(debug_channel)
						time.sleep(.3)
						op_user(botnick,debug_channel)
						time.sleep(.3)
						send_priv(auth_user,"You think you can pwnxorz me WITH me? oh you are bant gurl")
						time.sleep(.3)
						ban_user(rival,debug_channel)
						time.sleep(.3)
						set_member(rival,debug_channel)
						time.sleep(.3)
						kick_user(rival,debug_channel)
						bad_user=1

					#----------End teasing rival----------#




					# User did precisely the only thing we told them not to do.
					elif auth_body == "help my house is burning down":
						send_priv(auth_user,"That's hilarious. You're hilarious.")
						send_priv(auth_user,"I think I might have a heart attack and DIE")
						send_priv(auth_user,"because that's so hilarious.")

						# Tease rival.
						rival = auth_user
						invite(botnick,debug_channel)
						time.sleep(.3)
						join_chan(debug_channel)
						time.sleep(.3)
						op_user(botnick,debug_channel)
						time.sleep(.3)
						ban_user(rival,debug_channel)
						time.sleep(.3)
						set_member(rival,debug_channel)						
						send_priv(auth_user,"You know what I think is hilarious? banz. No stick for u")
						time.sleep(.3)
						kick_user(rival,debug_channel)
						bad_user=1

					# We've heard the goodnight_string from an authorized user.
					# Close socket and quit.
					elif auth_body == goodnight_string:
						irc.close()
						quit()

					# User sent "help" somewhere in their message.
						# If user or channel contains "help" even as a substring in any command,
						# <comic sans>You're gonna have a bad time.</comic sans>
					elif "help" in auth_body.lower():
						# Sent help and unban.  Display usage.
						# Before ban or might get caught by ban.
						if " unban" in auth_body.lower() or "unban " in auth_body.lower():
							send_priv(auth_user,"Unban a user from a channel.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " unban <user> <channel>")
						# Sent help and ban.  Display usage.
						elif " ban" in auth_body.lower() or "ban " in auth_body.lower():
							send_priv(auth_user,"Ban a user from a channel.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " ban <user> <channel>")
						# Sent help and invite.  Display usage.
						elif " invite" in auth_body.lower() or "invite " in auth_body.lower():
							send_priv(auth_user,"Invite a user to a channel.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " invite <user> <channel>")
						elif " chanmaster" in auth_body.lower() or "chanmaster " in auth_body.lower():
							send_priv(auth_user,"Set a user as channel master.")
							send_priv(auth_user,"Careful!  These users will have total control of the channel.  Overrides channel chanop and member settings.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " chanmaster <user> <channel>")
						# Sent help and chanop.  Display usage.
						elif " chanop" in auth_body.lower() or "chanop " in auth_body.lower():
							send_priv(auth_user,"Set a user as a channel operator.")
							send_priv(auth_user,"Careful!  Overrides channel master and member settings.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " chanop <user> <channel>")
						# Sent help and member.  Display usage.
						elif " member" in auth_body.lower() or "member " in auth_body.lower():
							send_priv(auth_user,"Set a user as a member in a channel. Careful! Overrides channel chanop and master settings.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " member <user> <channel>")

						elif " kick" in auth_body.lower() or "kick " in auth_body.lower():
							send_priv(auth_user,"Have me kick a user from a room.  Currently, the reason is static and set to \"bant\"")
							send_priv(auth_user,"Syntax: /msg " + botnick + " kick <user> <channel>")

						elif " op" in auth_body.lower() or "op " in auth_body.lower():
							send_priv(auth_user,"Op a user in a channel. Note this is more temporary and *not* the same as setting a chanop.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " op <user> <channel>")

						elif " deop" in auth_body.lower() or "deop " in auth_body.lower():
							send_priv(auth_user,"Deop a user in a channel.  Note this does not remove chanop status.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " deop <user> <channel>")

						elif " deop" in auth_body.lower() or "deop " in auth_body.lower():
							send_priv(auth_user,"Deop a user in a channel.  Note this does not remove chanop status.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " deop <user> <channel>")

						elif " tell" in auth_body.lower() or "tell " in auth_body.lower():
							send_priv(auth_user,"Have me tell something to a user or channel.  Currently, I refuse to talk to nickserv or chanserv with this command.")
							send_priv(auth_user,"Syntax: /msg " + botnick + " tell <user or channel> <message>")

						# Sent just the word "help."  Send full help text.


						elif auth_body.lower()=="help":
							send_priv(auth_user,"Things I can do: ban, unban, invite, kick, op, deop, chanmaster, chanop, member, tell")
							send_priv(auth_user,"Type /msg " + botnick + " help <command> or /msg " + botnick + " <command> help for usage. If you don't include a topic and type /msg " + botnick + " help, you get this again.")
							send_priv(auth_user,"If you type something like \"/msg " + botnick + " help my house is burning down\", since none of those words are topics, you'll get this again.")
							time.sleep(3)
							send_priv(auth_user,"So don't type that.")
							time.sleep(7)
							send_priv(auth_user,"Seriously don't type that.")
							time.sleep(5)
							send_priv(auth_user,"(This means you, " + auth_user + ".)")

						# They sent help + other words that weren't listed commands.
						# or a charm message. Repeat above help.
						else:
							send_priv(auth_user,"I didn't understand those extra words. Here's regular help again.")
							send_priv(auth_user,"Things I can do: ban, unban, invite, kick, op, deop, chanmaster, chanop, member, tell")
							send_priv(auth_user,"Type /msg " + botnick + " help <command> or /msg " + botnick + " <command> help for usage. If you don't include a topic and type /msg " + botnick + " help, you get this again.")
							send_priv(auth_user,"If you type something like \"/msg " + botnick + " help my house is burning down\", since none of those words are topics, you'll get this again.")
							time.sleep(3)
							send_priv(auth_user,"So don't type that.")
							time.sleep(7)
							send_priv(auth_user,"Seriously don't type that.")
							time.sleep(5)
							send_priv(auth_user,"(This means you, " + auth_user + ".)")

					elif auth_body_words[0] == "unban":
						if is_command:
							unban_user(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Unbanning " + auth_body_words[1] + " from " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help unban for usage.")

					elif auth_body_words[0].lower() == "ban":
						if is_command:
							ban_user(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Banning " + auth_body_words[1] + " from " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help ban for usage.")

					elif auth_body_words[0].lower() == "invite":
						if is_command:
							invite(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Inviting " + auth_body_words[1] + " to " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help invite for usage.")

					elif auth_body_words[0].lower() == "chanmaster":
						if is_command:
							set_master(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Setting " + auth_body_words[1] + " as channel master in " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help chanmaster for usage.")

					elif auth_body_words[0].lower() == "chanop":
						if is_command:
							set_chanop(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Setting " + auth_body_words[1] + " as channel operator in " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help chanop for usage.")

					elif auth_body_words[0].lower() == "member":
						if is_command:
							set_member(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Setting " + auth_body_words[1] + " as channel member in " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help member for usage.")

					elif auth_body_words[0].lower() == "kick":
						if is_command:
							kick_user(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Kicking " + auth_body_words[1] + " from " + auth_body_words[2])

					elif auth_body_words[0].lower() == "op":
						if is_command:
							op_user(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Granting temporary ops to " + auth_body_words[1] + " in " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help op for usage.")

					elif auth_body_words[0].lower() == "deop":
						if is_command:
							deop_user(auth_body_words[1],auth_body_words[2])
							send_priv(auth_user,"Revoking temporary ops from " + auth_body_words[1] + " in " + auth_body_words[2])
						else:
							send_priv(auth_user,"Command not formatted properly.  Send /msg " + botnick + " help deop for usage.")

					elif auth_body_words[0].lower() == "tell":
						if auth_body_words[1].lower() == "chanserv" or auth_body_words[1].lower() == "nickserv":
							send_priv(auth_user,"Use the other commands for that kind of talk.  No bypassing my hijinx, you! (Good try though.)")
						else:
							# Made these lines even more hideous, but important.
							# Previous implementation was thoughtless, if auth_body_words[2]
							# was a substring of anything before it, it began the "message"
							# to send there.  This fixes issue.
							#TODO Clean these lines up/make more readable.
							send_priv(auth_body_words[1],auth_body[auth_body.find(auth_body_words[1])+len(auth_body_words[1])+1:])
							send_priv(auth_user,"Telling " + auth_body_words[1] + " \"" + auth_body[auth_body.find(auth_body_words[1])+len(auth_body_words[1])+1:] + "\"")

					# They sent something that didn't include help or
					# a charm message.  Commands not implemented yet.
					else:
						send_priv(auth_user,"You should try sending \"/msg " + botnick + " help\"!")

					#Reset auth variables.
					auth_requested=0
					auth_message=""
					auth_header=""
					auth_body=""
					auth_user=""

				#----------End authenticated commands section----------#




		# Respond to PINGs.
		# If this sequence containts the word "PING", send back "PONG" with the word that followed it.
		# Split uses whitespace to delimit words.
		# Need to review rfc and better integrate with mesage parsing architecture.
		if nice_text.find("PING") != -1:
			irc.send(bytes("PONG " + nice_text.split() [1] + "\r\n", "UTF-8"))
			# Debugging output.
			if debugging:
				print("\nReceived PING, responding with:")
				print("PONG " + nice_text.split() [1] + "\n")

	# Store exception for sequence in error_message and print if debugging is true.
	# Continue on error.
	except Exception as error_message:
		# This is the error for a sequence that didn't receive any text.
		# Spams if not excepted.  Other errors confirmed in debugging to show.
		if "The operation did not complete (read) (_ssl.c:1977)" not in str(error_message) and debugging:
			print(error_message)
		continue

	#----------End input/output sequence----------#