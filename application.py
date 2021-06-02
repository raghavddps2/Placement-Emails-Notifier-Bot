import email
import imaplib
import threading
import time
import pymysql
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask,request
from twilio.rest import Client


account_sid = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
auth_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
twilio_client = Client(account_sid, auth_token)


connection = {
    "host":'database-3.cyfnxgqfbjc8.us-east-1.rds.amazonaws.com',
    'username':'XXXX',
    'password':'XXXX',
    'db':'WhatsAppBot'
}

conn = pymysql.connect(connection['host'],connection['username'],connection['password'],connection['db'])
cursor =  conn.cursor()

def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

application = Flask(__name__)

@application.route('/')
def index():
    return "Hello World"


@application.route('/sms',methods=["POST"])
def sms_reply():
    contact_Number = request.form['From']
    resp = MessagingResponse()
    count_statement = "select count(*) from WhatsAppSubscribers where phoneNo = '{}'".format(contact_Number)
    try:
        cursor.execute(count_statement)
        result = cursor.fetchall()[0][0]
        print(result)
        if result == 0:
            insert_statement = "Insert into WhatsAppSubscribers(phoneNo) values('{}')".format(contact_Number)
            print(insert_statement)
            try:
                cursor.execute(insert_statement)
                resp.message("Thank you for your interest. Now, You can sit back and Relax. \n\n All the mails from the"
                + " Placement department will be there straight in your WhatsApp.\n\n Please note that, there might be a delay of 2 minutes from the"
                +" time mail is sent.\n\n Also, though we try our best, to help you but there can some errors.\n\n So, Please check your emails regularly.\n\n Thank you again for Subscribing. "+"\U0001f600")
                conn.commit()
            except:
                print("hi")
                resp.message("Sorry, Some error occured. We hope to server you in future.")
        else:
            resp.message("Hello, You are already Subscribed. You will receive the updated timely \U0001f600. ")
    except:
        resp.message("Sorry, Some error occured. We hope to server you in future.")
    
    return str(resp)


#User Credentials.
userName = "email@gmail.com"
password = "XXXXXXXXXXXXXXX"

#Performing login 
m = imaplib.IMAP4_SSL("imap.gmail.com", 993)
m.login(userName,password)


class MailThread(threading.Thread):
    def __init__(self,var):
      threading.Thread.__init__(self)
      self.last_email_uid = var
      
    def run(self):
        while True:
            m = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            m.login(userName,password)
            m.select("PlacementMail")
            result, data = m.uid('search', None, "ALL")
            all_email_uids = data[0].split()
            print(all_email_uids)

            if result == 'OK':
                last_email = int(data[0].split()[-1].decode("utf-8"))
                for num in range(self.last_email_uid+1,last_email+1):
                    a = str(num)
                    res = bytes(a, 'utf-8') 
                    result, data = m.uid('fetch',res, '(RFC822)')
                    if result == 'OK':
                        email_message = email.message_from_bytes(data[0][1])
                        email_subject = email_message['Subject']
                        email_body  = get_text(email_message).decode("utf-8")
                        body = "Subject: *{}* \n\n *We are currently not sending the mail attachments.* \n\n Content: {} \n\n".format(email_subject,email_body)
                        body = body[0:1600]
                        count_statement = "select * from WhatsAppSubscribers"
                        try:
                            cursor.execute(count_statement)
                            result = cursor.fetchall()
                        except:
                            print("hi")
                        clients = [i[1] for i in result]
                        for client in clients:
                            print(client)
                            twilio_client.messages.create(
                                        body=body,
                                        from_='whatsapp:+14155238886',
                                        to= client
                                    )
                            time.sleep(30)
                        self.last_email_uid = num

            m.close()
            m.logout()


if __name__ == "__main__":
    mailThread = MailThread(1)
    mailThread.start()
    application.run()
