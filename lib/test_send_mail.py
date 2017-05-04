import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.MIMEMultipart import MIMEMultipart
#####################
mailto_list=['hxzhan']
mailcc_list="hxzhan@dolby.com"
#####################
#mail server config
mail_host="mail.dolby.com"
mail_user="hxzhan"
mail_pass=""
mail_postfix="dolby.com"



def send_mail(to_list,sub,content,att_file = '',img = ''):

    '''
    to_list:
    sub:
    content:
    att_file:
    send_mail("hxzhan@dolby.com","sub","content","/var/www/html/report/KVM.xls")
    '''
    me=mail_user+"<"+mail_user+"@"+mail_postfix+">"
    msg = MIMEMultipart()
    msg['Subject'] = sub

    if(att_file != ''):
            att = MIMEText(open(att_file,'rb').read(),'base64','utf8')
            att["Content-Type"] = 'application/octet-stream'
            att_file = ''.join(att_file.split('/')[-1:])
            att["Content-Disposition"] = "attachment;filename=%s" %att_file
            msg.attach(att)
    if(img != ''):
            msg_image = MIMEImage(open(img,'rb').read())
            msg_image.add_header('Content-ID',"<%s>" %img);
            msg.attach(msg_image)
            content += "<td><img src='cid:%s'></td>" %img

    body = MIMEText(content,_subtype='html',_charset='utf8')
    msg.attach(body)

    
    mail_to_list = to_list+"<"+to_list+"@"+mail_postfix+">"

    msg['From'] = "hxzhan@dolby.com"
    msg['To'] = to_list+"@"+mail_postfix
    msg['Cc']=mailcc_list
    try:
        s = smtplib.SMTP()
        s.connect(mail_host)
#       s.login(mail_user,mail_pass)
        s.sendmail(me, mail_to_list, msg.as_string())
        s.close()
        return True
    except Exception, e:
        print str(e)
        return False


if __name__ == '__main__':
    content = 'TEST\n'
    if send_mail(mailto_list[0],'EMAIL Notification of the changelist',content,'','DLB_Ldct4_unscaled_shlLUU_1024.png'):
        print "success"
    else:
        print "fail"