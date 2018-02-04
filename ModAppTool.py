################################
# ModAppTool by /u/x_minus_one #
################################

import traceback
import time
import praw
import sqlite3
import urllib
import datetime

""" USER CONFIG """
r = praw.Reddit(user_agent='ModAppTool by /u/x_minus_one', client_id='CLIENT ID', client_secret='CLIENT SECRET', username='NTOModApps', password='PASSWORD')
FORWARD_FROM = "NTOModApps"
USERAGENT = 'ModAppTool by /u/x_minus_one'

FORWARD_TO = ["THREAD ID"]
# This is the thread id you want it to post to

FORWARD_SUBJECT = "_sender_: _subject_"
# This will be the subject of the submission
# _sender_ and _subject_ will be auto-replaced if you have them
# but these injectors are optional.
# Subjects have a max of 100 chars and will be cut off if too long

FORWARD_FOOTER = "\n\n____\n\n[Click here to message the user.](_replylink_)\n\nSubmitted at _timestamp_."
# This will be at the bottom of the submission
# _replylink_ will be replaced by a message_link or a permalink
# _timestamp_ will be replaced by the UTC HH:MM time of the original message

WAIT = 240
# Number of seconds to wait in between each run
# The bot is completely inactive during this time.

WAIT_EACH = 5
# Number of seconds to wait after sending each forward
# and before the next -- just to be nice to reddit's servers

""" All done! """


MESSAGE_LINK = "http://www.reddit.com/message/compose/?to=%s&subject=%s"
# This is the URL which will be included so you may reply to 
# the sender. Do not edit.

try:
	import bot
	USERNAME = bot.u7
	PASSWORD = bot.p7
	USERAGENT = bot.a7
except ImportError:
	pass

print('Loading unsent mail...')
sql = sqlite3.connect('unsent_mail.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS unsent(id TEXT, subject TEXT, body TEXT)')

print('Logging in...')
#r = praw.Reddit(USERAGENT)
#r.login(FORWARD_FROM, PASSWORD, disable_warning = True)


def prepareforwards():
	print('Checking unread messages...')
	unread = r.inbox.unread(limit=None)

	for message in unread:
		# Skip comment replies
		if message.subject == 'comment reply':
			continue
		mid = message.fullname
		print(mid)
		if indb(mid):
			print('\tAlready in ')
			message.mark_read()
			continue

		msubject = message.subject
		mbody = message.body
		try:
			mauthor = message.author.name
			forward_author = '\/u/' + mauthor
		except AttributeError:
			mauthor = None
			forward_author = '[deleted user]'

		forward_subject = FORWARD_SUBJECT
		forward_subject = forward_subject.replace('_sender_', forward_author)
		forward_subject = forward_subject.replace('_subject_', msubject)

		if isinstance(message, praw.models.Message):
			msubject_return = "re: " + msubject
			if mauthor:
				msubject_return = urllib.parse.quote(msubject_return)
				replylink = MESSAGE_LINK % (mauthor, msubject_return)
				forward_footer = FORWARD_FOOTER.replace('_replylink_', replylink)
			else:
				forward_footer = ""
		else:
			replylink = createpermalink(message)
			forward_footer = FORWARD_FOOTER.replace('_replylink_', replylink)

		mtimestamp = datetime.datetime.utcfromtimestamp(message.created_utc)
		mtimestamp = datetime.datetime.strftime(mtimestamp, "%B %d %Y @ %H:%M UTC")
		forward_footer = forward_footer.replace('_timestamp_', mtimestamp)

		forward_body = mbody + forward_footer

		forward_subject = forward_subject[:100]
		forward_body = forward_body[:10000]

		adddb(mid, forward_subject, forward_body)
		sql.commit()
		print('\tPrepared for sending')
		message.mark_read()

def sendforwards():
	while True:
		try:
			cur.execute('SELECT * FROM unsent')
			fetch = cur.fetchone()
			if not fetch:
				break
			mid = fetch[0]
			print('%s Submitting post...' % mid)
			for thread_id in FORWARD_TO:
				subm = r.submission(id=thread_id)
				print('Submitting to thread:')
				print('\t%s' % subm.title)
				outgoing = subm.reply(fetch[1] + "\n\n" + fetch[2])
			print('\tSuccessfully submitted!')
			dropdb(mid)
			sql.commit()
		except Exception as exc:
			traceback.print_exc()
		time.sleep(WAIT_EACH)


def indb(mid):
	cur.execute('SELECT * FROM unsent WHERE ID=?', [mid])
	if cur.fetchone():
		return True
	return False

def adddb(mid, msubject, mbody):
	cur.execute('INSERT INTO unsent VALUES(?, ?, ?)', [mid, msubject, mbody])

def dropdb(mid):
	cur.execute('DELETE FROM unsent WHERE ID=?', [mid])

def createpermalink(obj):
	# PRAW's comment.permalink is slow, I don't know why!
	pid = obj.id
	if 't1_' in obj.fullname:
		sub = obj.subreddit.display_name
		post = obj.submission.id
		return 'http://reddit.com/r/%s/comments/%s/x/%s' % (sub, post, pid)
	if 't3_' in obj.fullname:
		return 'http://reddit.com/%s' % pid
	if 't4_' in obj.fullname:
		return 'http://reddit.com/message/messages/%s' % pid

while True:
	try:
		prepareforwards()
		sendforwards()
	except:
		traceback.print_exc()
	print('Sleeping %d seconds\n' % WAIT)
	time.sleep(WAIT)

