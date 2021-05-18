#!/usr/bin/env python3

import datetime
import os
import platform
import smtplib
import subprocess
from email.message import EmailMessage

from database import quotaDb

WORK_DIR = os.path.dirname(os.path.realpath(__file__))

def get_quota_status():
    """
    Parse quota status from command-line tool.
    Return:
        quota_list: [(user, used, soft_limit, hard_limit, status), ...]
    """
    
    report = subprocess.run(['/usr/sbin/repquota', '-a'], capture_output=True, text=True).stdout.split('\n')    # read command output
    # report = os.popen('repquota -a').readlines()    # read command output
    report = report[7:]                             # drop headers
    quota_list = []
    for userquota in report:
        if len(userquota.split()) >= 8 and userquota.split()[3] != '0':
            user, status, used, soft_limit, hard_limit = userquota.split()[:5]
            used, soft_limit, hard_limit = int(used), int(soft_limit), int(hard_limit)
            if used < soft_limit:
                status = 0
            elif used < hard_limit:
                status = 1
            else:
                status = 2
            quota_list.append((user, used, soft_limit, hard_limit, status, used, soft_limit, hard_limit, status)) 
    return quota_list


def get_user_addr(username):
    """
    Get user's email address from alias file.
    """
    with open(os.path.join(WORK_DIR, 'alias'), 'r') as f:
        for line in f:
            if line.split(',')[0] == username:
                return line.split(',')[1]
        return None


def write_email(info_tuple):
    """
    Write an email to the user who needs an alert. 
    User's email address is defined in `alias` file. 
    Use local mail if no address matched. 
    Args:
        info_tuple: (user, used, soft_limit, hard_limit, state, alert)
    """
    hostname = platform.node()
    user = info_tuple[0]
    user_addr = get_user_addr(user)
    limit = 'soft_limit' if info_tuple[4] == 1 else 'hard_limit'
    used = info_tuple[1]/1024/1024
    soft = info_tuple[2]/1024/1024
    hard = info_tuple[3]/1024/1024
    subject = "Disk Limit Exceeded on " + hostname
    if limit == 'soft_limit':
        content = f"You are receiving this message because you have exceeded disk usage limit on {hostname}. \n\n" \
            f"Details: \n" \
            f"\tAccount: {user}\n" \
            f"\tLimit Triggered: {limit}\n" \
            f"\tCurrently Used: {used:.2f}GB\n" \
            f"\tSoft Limit: {soft:.2f}GB\n" \
            f"\tHard Limit: {hard:.2f}GB\n\n" \
            f"Please reduce the size of your home directory. " \
            f"You can use mounted disks located under `/home/sharing` directory with no limits.\n" \
            f"You have 7 days before all your write access will be denied. " \
            f"Run `repquota -as` on the server to see how much time you have left.\n"\
            f"Other than this message, no further notifications will be sent.\n" \
            f"Do not reply this message, but feel free to contact server admin if you have any questions.\n" \
            f"Thank you for your cooperation!\n"
    else:
        content = f"You are receiving this message because you have exceeded disk usage limit on {hostname}. \n\n" \
            f"Details: \n" \
            f"\tAccount: {user}\n" \
            f"\tLimit Triggered: {limit}\n" \
            f"\tCurrently Used: {used:.2f}GB\n" \
            f"\tSoft Limit: {soft:.2f}GB\n" \
            f"\tHard Limit: {hard:.2f}GB\n\n" \
            f"Please reduce the size of your home directory. " \
            f"You can use mounted disks located under `/home/sharing` directory with no limits.\n" \
            f"You can no longer write to the home directory before you're back under quota.\n" \
            f"Run `repquota -as` on the server to inspect your disk quota info.\n"\
            f"Do not reply this message, but feel free to contact server admin if you have any questions.\n" \
            f"Thank you for your cooperation!\n"
    
    if user_addr != None:   # Write Internet Email
        msg = EmailMessage()
        msg['Subject'] = subject
        msg.set_content(content)
        msg['From'] = 'admin@example.org'
        msg['To'] = user_addr

        with smtplib.SMTP_SSL('example.com', 465) as server:
            server.login('username@example.com','password')
            try:
                server.sendmail('username@example.com', user_addr, msg.as_string())
                print(f"mail sent to {user_addr}")
                return 0
            except smtplib.SMTPException as e:
                print(e)
                return 1
    else:   # Write local mail instead, need to install postfix and mailutils
        subject = 'Disk Limit Exceeded'
        message = "You have exceeded disk usage limit. Run `repquota -as` to see details."
        result = subprocess.run(f"echo '{message}' | mail -s '{subject}' {user}", shell=True,
                                capture_output=True, text=True).stdout
        if result != '':    # Can't know if local mail is sent successfully, this is just a placeholder
            return 1
        return 0



if __name__ == '__main__':
    db = quotaDb(os.path.join(WORK_DIR, 'quotastat.db'))
    quota_list = get_quota_status()
    db.update(quota_list)
    alert_list = db.get_alert_list()
    # print(alert_list)
    for user_info in alert_list:
        if write_email(user_info) == 0:
            db.update_alert(user_info[0])
            db.commit()
        else:
            print('Mail not sent due to some error.')

    db.reset_alert()
    db.close()
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ": Script Finished Successfully.")
    
    