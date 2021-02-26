import tweepy
import pandas
import hashlib
import logging
import time
import os
import zipfile
import socket
import fcntl
import struct
from pathlib import Path
from requests import get
from flask import Flask, session, redirect, request, render_template, send_file, flash

api_key = 'xxx'
secret_key = 'xxx'
callback = 'http://framartin11.pythonanywhere.com/callback'
app = Flask(__name__, static_folder='/')
app.secret_key = 'xxx'
app.config['SESSION_TYPE'] = 'filesystem'
md5 = hashlib.md5()
sha1 = hashlib.sha1()
logging.basicConfig(filename="/home/framartin11/mysite/log.log", filemode='a')

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
    screen_name, api = remind_auth()
    inizialize_session(screen_name)
    return render_template("index.html", name=screen_name)

@app.route('/allstatus', methods=['GET', 'POST'])
def all_status():
    name, api = remind_auth()
    user = api.get_user(name)
    user_timeline = user.timeline()
    status_list = [[s.id_str, s.created_at, s.text, s.lang, s.retweeted,
                    s.retweet_count, s.favorite_count, s.place, s.coordinates]
                   for s in user_timeline]
    df = pandas.DataFrame(data=status_list, columns=['Id', 'UTC DateTime', 'Text', 'Lang',
                                                     'IsRt?', 'Retweet', 'Likes', 'Place', 'Coordinates'])
    df.to_csv(f"/home/framartin11/mysite/{name}/allstatus.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/{name}/allstatus.csv")
    flash("Tutti gli status aggiunti")
    ulog(name, "All Status added")
    return welcome()

@app.route('/alldms', methods=['GET', 'POST'])
def allmessages():
    name, api = remind_auth()
    list_message = api.list_direct_messages()
    dm_list=[[]]
    for l in list_message:
        dm_list.append([ l.id, l.created_timestamp, l.message_create['sender_id'],
                         l.message_create['message_data']['text'], api.get_user(l.message_create['sender_id']).screen_name])
    dm_list.pop(0)
    df = pandas.DataFrame(data=dm_list, columns=['Id', 'UTC Timestamp', 'Sender Id', 'Text', 'Username'])
    df.to_csv(f"/home/framartin11/mysite/{name}/dms.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/{name}/dms.csv")
    flash("Tutti i direct messagge aggiunti")
    ulog(name, "All Direct Messages added")
    return redirect("/home")

@app.route('/interactions', methods=['GET', 'POST'])
def interactions():
    name, api = remind_auth()
    interaction_list = [[]]
    user = api.get_user(name)
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
    df = pandas.DataFrame(data=interaction_list, columns=['Id', 'UTCDateTime', 'Text', 'Lang',
                                                     'IsRt?', 'Retweet', 'Likes', 'Place', 'Coordinates'])
    df.to_csv(f"/home/framartin11/mysite/{name}/interaction{username}.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/{name}/interaction{username}.csv")
    flash(f"Tutte le interazioni con {username} aggiunte")
    ulog(name, f"Interactions status with {username} added")
    return welcome()

@app.route('/dms', methods=['GET', 'POST'])
def messages():
    name, api = remind_auth()
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
    df = pandas.DataFrame(data=dm_list, columns=['Id',  'UTC Timestamp', 'Sender Id', 'Text', 'Username'])
    df.to_csv(f"/home/framartin11/mysite/{name}/dms{username}.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    log(f"/home/framartin11/mysite/{name}/dms{username}.csv")
    ulog(name, f"Direct Messages with {username} added")
    flash(f"Tutti i direct message con {username} aggiunti")
    return welcome()

@app.route('/relationship', methods=['GET', 'POST'])
def relationship():
    screen_name, api = remind_auth()
    username = request.form.get('username')
    us = username.split()
    username = username.replace(' ', '')
    show_relation = api.lookup_friendships(screen_names=us)
    relationship = [[r.name, r.screen_name, r.id, r.is_following, r.is_followed_by, r.is_muted, r.is_blocked,
                         r.is_following_requested, r.no_relationship] for r in show_relation]
    df = pandas.DataFrame(data=relationship, columns=['Nome', 'Screen Name', 'Id', 'Is Following?', 'Is Followed?', 'Is Muted?', 'Is Blocked?',
                                                      'Following Request?', 'No Relationship'])
    df.to_csv(f"/home/framartin11/mysite/{screen_name}/relationship{username}.csv", index=False, sep='\t', line_terminator='\n', na_rep='Unknown')
    ulog(screen_name, f"Relationship file with {username} added")
    log(f"/home/framartin11/mysite/{screen_name}/relationship{username}.csv")
    flash(f"Tutte le relationship con {username} aggiunte")
    return welcome()

@app.route('/download', methods=['GET', 'POST'])
def download():
    name, api = remind_auth()
    day = time.strftime("%Y%m%d")
    file =f"/home/framartin11/mysite/{name}_{day}.zip"
    path=f"/home/framartin11/mysite/{name}"
    ulog(name, "Package Download")
    make_zipfile(file, path)
    ulog(name, "MD5 hash created")
    logging.info("MD5:")
    with open(file, "rb") as file_object:
        for el in file_object:
            md5.update(el)
    uhash(name, md5.hexdigest())
    logging.info(md5.hexdigest())
    ulog(name, "SHA1 hash created")
    logging.info("SHA1:")
    with open(file, "rb") as file_object:
        for el in file_object:
            sha1.update(el)
    uhash(name, sha1.hexdigest())
    logging.info(sha1.hexdigest())
    for f in Path(path).glob('*.csv'):
        try:
            f.unlink()
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))
    for f in Path(path).glob('*.log'):
        try:
            f.unlink()
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))
    return send_file(f"/home/framartin11/mysite/{name}_{day}.zip", as_attachment=1)

@app.route('/log',methods=['GET', 'POST'])
def dload():
    name, api = remind_auth()
    day = time.strftime("%Y%m%d")
    return send_file(f"/home/framartin11/mysite/{name}_{day}.log", as_attachment=1)

def inizialize_session(name):
    if not os.path.exists(f"/home/framartin11/mysite/{name}/"):
        os.makedirs(f"/home/framartin11/mysite/{name}/")
    day = time.strftime("%Y%m%d")
    utc = time.strftime("%m-%d-%Y %H : %M : %S")
    log = f"/home/framartin11/mysite/{name}/{name}_{day}.log"
    if os.path.exists(log):
        os.remove(log)
    ulog(name, f"Session started at {utc} UTC; ->\nTwitter Authentication")

def ulog(name, message):
    day = time.strftime("%Y%m%d")
    utc = time.strftime("%m-%d-%Y %H : %M : %S")
    f = open(f"/home/framartin11/mysite/{name}_{day}.log", "a")
    f.write(message + " at " + utc + " UTC ->\n");
    f.close()

def uhash(name, message):
    day = time.strftime("%Y%m%d")
    f = open(f"/home/framartin11/mysite/{name}_{day}.log", "a")
    f.write(message + "\n");
    f.close()

def remind_auth():
    token, token_secret = session['token']
    auth = tweepy.OAuthHandler(api_key, secret_key, callback)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)
    me = api.me()
    return me.screen_name, api

def log(file):
    fil = file.replace("/home/framartin11/mysite", "")
    logging.info(fil +  " ip: " +  get('https://api.ipify.org').text + " Date: " + time.strftime("%d/%m/%Y") + " at " + time.strftime("%H:%M:%S"))

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
        for root, dirs, files in os.walk(source_dir):
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)
