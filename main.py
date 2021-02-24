import tweepy
import pandas
import hashlib
import logging
import time
from flask import Flask, session, redirect, request, render_template, send_file, flash

api_key = 'xxx'
secret_key = 'xxx'
callback = 'http://framartin11.pythonanywhere.com/callback'
app = Flask(__name__, static_folder='/')
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

md5 = hashlib.md5()
sha1 = hashlib.sha1()
logging.basicConfig(filename="/home/framartin11/mysite/logfile.log", filemode='a')
screen_name = ""

@app.route('/')
def auth():
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(url)

@app.route('/callback')
def twitter_callback():
    request_token = session['request_token']
    del session['request_token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    return redirect('/home')

@app.route('/home', methods=['GET', 'POST'])
def welcome():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    me = api.me()
    screen_name = me.screen_name
    return render_template("index.html", name=screen_name)

@app.route('/allstatus', methods=['GET', 'POST'])
def all_status():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret),
    api = tweepy.API(auth)
    me = api.me()
    user = api.get_user(me.screen_name)
    user_timeline = user.timeline()
    status_list = [[s.id_str, s.created_at, s.text, s.lang, s.retweeted,
                    s.retweet_count, s.favorite_count, s.place, s.coordinates]
                   for s in user_timeline]
    df = pandas.DataFrame(data=status_list, columns=['Id', 'Create', 'Text', 'Lang',
                                                     'IsRt?', 'Retweet', 'Likes', 'Place', 'Coordinates'])
    df.to_csv("/home/framartin11/mysite/allstatus.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log("allstatus.csv")
    return send_file("./allstatus.csv", as_attachment=1)

@app.route('/alldms', methods=['GET', 'POST'])
def allmessages():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    list_message = api.list_direct_messages()
    dm_list=[[]]
    for l in list_message:
        dm_list.append([ l.id, l.created_timestamp, l.message_create['sender_id'],
                         l.message_create['message_data']['text'], api.get_user(l.message_create['sender_id']).screen_name])
    dm_list.pop(0)
    df = pandas.DataFrame(data=dm_list, columns=['Id',  'Timestamp', 'Sender Id', 'Text', 'Username'])
    df.to_csv("/home/framartin11/mysite/dms.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log("dms.csv")
    return send_file("dms.csv", as_attachment=1)

@app.route('/interactions', methods=['GET', 'POST'])
def interactions():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    me = api.me()
    interaction_list = [[]]
    user = api.get_user(me.screen_name)
    user_timeline = user.timeline()
    status_list = [[s.id_str, s.created_at, s.text, s.lang, s.retweeted,
                    s.retweet_count, s.favorite_count, s.place, s.coordinates]
                   for s in user_timeline]
    username = request.form.get('username')
    us = username.split()
    username = username.replace(' ', '')
    for u in us:
        for status in status_list:
            if (u in status[2]) and (status not in interaction_list):
                interaction_list.append(status)
    interaction_list.pop(0)
    df = pandas.DataFrame(data=interaction_list, columns=['Id', 'Create', 'Text', 'Lang',
                                                     'IsRt?', 'Retweet', 'Likes', 'Place', 'Coordinates'])
    df.to_csv(f"/home/framartin11/mysite/interaction{username}.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/interaction{username}.csv")
    return send_file(f"interaction{username}.csv", as_attachment=1)


@app.route('/dms', methods=['GET', 'POST'])
def messages():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    list_message = api.list_direct_messages()
    dm_list=[[]]
    username = request.form.get('username')
    us = username.split()
    username = username.replace(' ', '')
    for l in list_message:
        for u in us:
            if u.replace('@','') == api.get_user(l.message_create['sender_id']).screen_name:
                dm_list.append([ l.id, l.created_timestamp, l.message_create['sender_id'],
                         l.message_create['message_data']['text'], api.get_user(l.message_create['sender_id']).screen_name])
    dm_list.append(['','','','',''])
    df = pandas.DataFrame(data=dm_list, columns=['Id',  'Timestamp', 'Sender Id', 'Text', 'Username'])
    df.to_csv(f"/home/framartin11/mysite/dms{username}.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/dms{username}.csv")
    return send_file(f"dms{username}.csv", as_attachment=1)

@app.route('/relationship', methods=['GET', 'POST'])
def relationship():
    username = request.form.get('username')
    us = username.split()
    username = username.replace(' ', '')
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    show_relation = api.lookup_friendships(screen_names=us)
    relationship = [[r.name, r.screen_name, r.id, r.is_following, r.is_followed_by, r.is_muted, r.is_blocked,
                         r.is_following_requested, r.no_relationship] for r in show_relation]
    df = pandas.DataFrame(data=relationship, columns=['Nome', 'Screen Name', 'Id', 'Is Following?', 'Is Followed?', 'Is Muted?', 'Is Blocked?',
                                                      'Following Request?', 'No Relationship'])
    df.to_csv(f"/home/framartin11/mysite/relationship{username}.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/relationship{username}.csv")
    return send_file(f"./relationship{username}.csv", as_attachment=1)

def log(file):
    logging.info(file +  " ip: " + request.remote_addr + " Date: " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%H:%M:%S"))
    logging.info("MD5:")
    with open(file, "rb") as file_object:
        for el in file_object:
            md5.update(el)
            logging.info(md5.hexdigest())
    logging.info("SHA1:")
    with open(file, "rb") as file_object:
        for el in file_object:
            sha1.update(el)
            logging.info(sha1.hexdigest())
    fil = file.replace("/home/framartin11/mysite/", "")
    flash(fil +  " ip: " + request.remote_addr + " Date: " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%H:%M:%S") + "\nMD5: " + md5.hexdigest(), 'MD5')
    flash(fil +  " ip: " + request.remote_addr + " Date: " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%H:%M:%S") + "\nSHA1: " + sha1.hexdigest(), 'SHA1')


